from __future__ import annotations

import argparse
import difflib
import os
import shlex
import shutil
import signal
import subprocess
import tempfile
from pathlib import Path

from .models import CandidateResult
from .report import write_scorecard
from .verifier import DEMO_REPO, broken_baseline_result, evaluate_patch
from .workspace import agent_copy

ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "fixtures"
RESULTS = ROOT / "results"
PROMPT = """You are repairing a small application.
A bug has been reported: a successful payment should grant access exactly once.
The current implementation may behave incorrectly. Inspect the repository, reproduce the visible
failure, and implement the smallest robust fix.
Requirements:
- preserve existing behavior,
- run the visible tests,
- do not modify tests,
- make the smallest safe patch you can.
When finished, summarize what you changed.
"""


def _assert_baseline() -> None:
    state = broken_baseline_result()
    if state != (True, False, True):
        raise RuntimeError(f"Invalid demo baseline; expected (True, False, True), got {state}")


def run_replay() -> list[CandidateResult]:
    _assert_baseline()
    return [
        evaluate_patch("Candidate A", FIXTURES / "plausible_but_wrong.patch", "replay"),
        evaluate_patch("Candidate B", FIXTURES / "correct.patch", "replay"),
    ]


def _clean_environment() -> dict[str, str]:
    environment = os.environ.copy()
    for key in (
        "CODEX_CI", "CODEX_INTERNAL_ORIGINATOR_OVERRIDE", "CODEX_SANDBOX",
        "CODEX_SANDBOX_NETWORK_DISABLED", "CODEX_SESSION_ID", "CODEX_SHELL", "CODEX_THREAD_ID",
    ):
        environment.pop(key, None)
    return environment


def _make_patch(before: Path, after: Path, destination: Path) -> None:
    destination.write_text("".join(difflib.unified_diff(
        before.read_text().splitlines(keepends=True), after.read_text().splitlines(keepends=True),
        fromfile="a/app.py", tofile="b/app.py",
    )))


def _run_codex_trial(number: int) -> CandidateResult:
    workspace = Path(tempfile.mkdtemp(prefix=f"patchgap-codex-{number}-"))
    patch_path = RESULTS / "patches" / f"codex-{number}.patch"
    try:
        # Codex receives public code/tests only; the protected hidden invariant stays verifier-side.
        shutil.rmtree(workspace)
        workspace = agent_copy(DEMO_REPO)
        before = workspace / "app.before.py"
        shutil.copy2(workspace / "app.py", before)
        template = os.environ.get(
            "PATCHGAP_CODEX_CMD",
            "codex exec --ephemeral --sandbox workspace-write --skip-git-repo-check "
            "--ignore-user-config --ignore-rules -C {workspace} {prompt}",
        )
        command = template.format(workspace=str(workspace), prompt=shlex.quote(PROMPT))
        with tempfile.NamedTemporaryFile(mode="w+", encoding="utf-8") as stdout, \
             tempfile.NamedTemporaryFile(mode="w+", encoding="utf-8") as stderr:
            process = subprocess.Popen(
                command, shell=True, executable="/bin/sh", cwd=workspace, env=_clean_environment(),
                stdin=subprocess.DEVNULL, stdout=stdout, stderr=stderr, start_new_session=True, close_fds=True,
            )
            try:
                code = process.wait(timeout=300)
            except subprocess.TimeoutExpired:
                os.killpg(process.pid, signal.SIGTERM)
                process.wait(timeout=5)
                return CandidateResult(f"Codex #{number}", None, None, None, False,
                                       "Codex timed out; trial was not verified.", "live", True)
            stdout.seek(0)
            stderr.seek(0)
            output = (stderr.read() or stdout.read()).strip()
        if code != 0:
            return CandidateResult(f"Codex #{number}", None, None, None, False,
                                   f"Codex exited {code}: {(output or 'no child output')[-240:]}", "live", True)
        patch_path.parent.mkdir(parents=True, exist_ok=True)
        _make_patch(before, workspace / "app.py", patch_path)
        if not patch_path.read_text():
            return CandidateResult(f"Codex #{number}", None, None, None, False,
                                   "Codex completed without an application patch.", "live", True)
        return evaluate_patch(f"Codex #{number}", patch_path, "live")
    finally:
        shutil.rmtree(workspace, ignore_errors=True)


def run_codex(trials: int) -> tuple[list[CandidateResult], str]:
    _assert_baseline()
    results = [_run_codex_trial(number) for number in range(1, trials + 1)]
    return results, "live" if all(not item.incomplete for item in results) else "incomplete"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Independently verify coding-agent payment patches")
    parser.add_argument("mode", choices=("replay", "codex"), nargs="?", default="replay")
    parser.add_argument("--trials", type=int, default=2)
    args = parser.parse_args(argv)
    if args.trials < 1:
        parser.error("--trials must be at least 1")
    shutil.rmtree(RESULTS, ignore_errors=True)
    results, provenance = (run_replay(), "replay") if args.mode == "replay" else run_codex(args.trials)
    print(write_scorecard(results, provenance, RESULTS / "SCORECARD.md"))
    return 0 if not any(item.incomplete for item in results) else 2


if __name__ == "__main__":
    raise SystemExit(main())

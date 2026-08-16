from __future__ import annotations

import json
import os
import subprocess
import tempfile
from pathlib import Path

from ..models import RepoContext, RiskHypothesis
from ..workspace import agent_copy


class CodexProvider:
    """External Terminal adapter. Invalid JSON or a failed process is an incomplete live run."""

    def _run(self, workspace: Path, prompt: str) -> str:
        environment = os.environ.copy()
        for key in ("CODEX_CI", "CODEX_INTERNAL_ORIGINATOR_OVERRIDE", "CODEX_SANDBOX", "CODEX_SANDBOX_NETWORK_DISABLED", "CODEX_SESSION_ID", "CODEX_SHELL", "CODEX_THREAD_ID"):
            environment.pop(key, None)
        command = ["codex", "exec", "--ephemeral", "--sandbox", "workspace-write", "--skip-git-repo-check",
                   "--ignore-user-config", "--ignore-rules", "-C", str(workspace), prompt]
        try:
            process = subprocess.run(command, cwd=workspace, env=environment, stdin=subprocess.DEVNULL,
                                     text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=300,
                                     start_new_session=True, close_fds=True)
        except (OSError, subprocess.TimeoutExpired) as error:
            raise RuntimeError(f"Codex trial could not complete: {error}") from error
        if process.returncode:
            raise RuntimeError(f"Codex exited {process.returncode}: {(process.stderr or process.stdout)[-300:]}")
        return process.stdout.strip()

    def generate_hypotheses(self, repository: Path, context: RepoContext) -> list[RiskHypothesis]:
        workspace = agent_copy(repository)
        try:
            prompt = f"""Act as one adversarial verification specialist. Inspect this sanitized repository.
Issue: {context.change_summary}
Return ONLY a JSON array of at most 4 objects with keys: id, category, title, explanation, severity,
confidence, target_files, verification_strategy. Every strategy must be concrete and executable where
possible. Do not edit files or mention hidden tests."""
            raw = self._run(workspace, prompt)
            data = json.loads(raw)
            if not isinstance(data, list):
                raise ValueError("Codex did not return a JSON array")
            if not data:
                raise ValueError("Codex returned no risk hypotheses")
            hypotheses = []
            for item in data:
                if not isinstance(item, dict):
                    raise ValueError("Codex returned a non-object hypothesis")
                category, severity, confidence = (item.get("category"), item.get("severity"), item.get("confidence"))
                targets = item.get("target_files")
                if category not in {"behavior", "security", "regression"}:
                    raise ValueError("Codex returned an invalid hypothesis category")
                if severity not in {"high", "medium", "low"} or confidence not in {"high", "medium", "low"}:
                    raise ValueError("Codex returned an invalid severity or confidence")
                if not isinstance(targets, list) or not all(isinstance(path, str) for path in targets):
                    raise ValueError("Codex returned invalid target_files")
                try:
                    hypotheses.append(RiskHypothesis(
                        str(item["id"]), category, str(item["title"]), str(item["explanation"]),
                        severity, confidence, targets, str(item["verification_strategy"]), "live",
                    ))
                except KeyError as error:
                    raise ValueError(f"Codex omitted required hypothesis field: {error.args[0]}") from error
            return hypotheses
        finally:
            import shutil
            shutil.rmtree(workspace, ignore_errors=True)

    def generate_repair(self, repository: Path, failure: str, strategy: str, destination: Path) -> str:
        workspace = agent_copy(repository)
        try:
            before = (workspace / "app.py").read_text()
            self._run(workspace, f"""Repair the payment application. Discovered failing invariant: {failure}
Strategy: {strategy}. Modify production code only. Do not modify tests. Run public tests.""")
            after = (workspace / "app.py").read_text()
            if before == after:
                raise RuntimeError("Codex completed without an app.py patch")
            import difflib
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_text("".join(difflib.unified_diff(before.splitlines(keepends=True), after.splitlines(keepends=True), fromfile="a/app.py", tofile="b/app.py")))
            return str(destination)
        finally:
            import shutil
            shutil.rmtree(workspace, ignore_errors=True)

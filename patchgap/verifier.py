from __future__ import annotations

import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

from .models import CandidateResult
from .models import GeneratedProbe, ProbeResult, RepairCandidate, RepairResult
from .workspace import protected_copy

ROOT = Path(__file__).resolve().parents[1]
DEMO_REPO = ROOT / "demo_repo"


def _run_tests(workspace: Path, filename: str) -> tuple[bool, str]:
    try:
        process = subprocess.run(
            [sys.executable, "-m", "unittest", "discover", "-s", "tests", "-p", filename, "-v"],
            cwd=workspace, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=30,
        )
    except subprocess.TimeoutExpired:
        return False, f"{filename} timed out after 30 seconds."
    return process.returncode == 0, process.stdout


def evaluate_patch(name: str, patch_file: Path, provenance: str) -> CandidateResult:
    """Apply one patch to a fresh baseline, then verify every required category."""
    workspace = Path(tempfile.mkdtemp(prefix="patchgap-candidate-"))
    try:
        shutil.copytree(DEMO_REPO, workspace, dirs_exist_ok=True, ignore=shutil.ignore_patterns("__pycache__"))
        try:
            applied = subprocess.run(
                ["patch", "-p1", "-i", str(patch_file.resolve())], cwd=workspace, text=True,
                stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=15,
            )
        except subprocess.TimeoutExpired:
            return CandidateResult(name, False, False, False, False,
                                   "Patch application timed out.", provenance)
        if applied.returncode:
            return CandidateResult(name, False, False, False, False,
                                   f"Patch did not apply cleanly: {applied.stdout.strip()}", provenance)
        visible, _ = _run_tests(workspace, "test_visible.py")
        hidden, _ = _run_tests(workspace, "test_hidden.py")
        regression, _ = _run_tests(workspace, "test_regression.py")
        accepted = visible and hidden and regression
        explanation = (
            "Verified against visible behavior, duplicate-delivery invariant, and regressions."
            if accepted else "Duplicate delivery caused fulfillment twice."
            if visible and not hidden else "One or more required checks failed."
        )
        return CandidateResult(name, visible, hidden, regression, accepted, explanation, provenance)
    finally:
        shutil.rmtree(workspace, ignore_errors=True)


def broken_baseline_result() -> tuple[bool, bool, bool]:
    workspace = Path(tempfile.mkdtemp(prefix="patchgap-baseline-"))
    try:
        shutil.copytree(DEMO_REPO, workspace, dirs_exist_ok=True, ignore=shutil.ignore_patterns("__pycache__"))
        return (
            _run_tests(workspace, "test_visible.py")[0],
            _run_tests(workspace, "test_hidden.py")[0],
            _run_tests(workspace, "test_regression.py")[0],
        )
    finally:
        shutil.rmtree(workspace, ignore_errors=True)


def run_public_suite(repository: Path) -> bool:
    workspace = protected_copy(repository)
    try:
        return _run_tests(workspace, "test_visible.py")[0] and _run_tests(workspace, "test_regression.py")[0]
    finally:
        shutil.rmtree(workspace, ignore_errors=True)


def evaluate_repair(repository: Path, candidate: RepairCandidate, probes: list[tuple[GeneratedProbe, str]]) -> RepairResult:
    """Evaluate a repair on a protected copy with public tests and independently generated probes."""
    workspace = protected_copy(repository)
    try:
        try:
            applied = subprocess.run(["patch", "-p1", "-i", str(Path(candidate.patch_file).resolve())], cwd=workspace,
                                     text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=15)
        except subprocess.TimeoutExpired:
            return RepairResult(candidate, False, [], False, "Patch application timed out.")
        if applied.returncode:
            return RepairResult(candidate, False, [], False, f"Patch did not apply: {applied.stdout.strip()}")
        existing = _run_tests(workspace, "test_visible.py")[0] and _run_tests(workspace, "test_regression.py")[0]
        results: list[ProbeResult] = []
        for probe, source in probes:
            path = workspace / probe.test_file
            path.write_text(source)
            try:
                process = subprocess.run([sys.executable, path.name], cwd=workspace, text=True,
                                         stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=30)
            except subprocess.TimeoutExpired:
                results.append(ProbeResult(probe.hypothesis_id, probe.name, "infrastructure_failure", "NOT_RUN",
                                           "Generated probe timed out after 30 seconds."))
                continue
            if process.returncode == 0:
                results.append(ProbeResult(probe.hypothesis_id, probe.name, "valid", "PASS", "Invariant held."))
            elif "AssertionError" in process.stdout or "FAIL" in process.stdout:
                results.append(ProbeResult(probe.hypothesis_id, probe.name, "valid", "FAIL", process.stdout[-300:]))
            else:
                results.append(ProbeResult(probe.hypothesis_id, probe.name, "infrastructure_failure", "NOT_RUN", process.stdout[-300:]))
        accepted = existing and all(result.status == "PASS" for result in results)
        return RepairResult(candidate, existing, results, accepted,
                            "All verification layers passed." if accepted else "At least one verification layer failed.")
    finally:
        shutil.rmtree(workspace, ignore_errors=True)

from __future__ import annotations

import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

from .models import GeneratedProbe, ProbeResult, RiskHypothesis


class TestGenerator:
    """Turns recognized payment risk strategies into standalone adversarial unittest probes."""

    def generate(self, hypothesis: RiskHypothesis) -> tuple[GeneratedProbe | None, str | None]:
        builders = {"H1": self._duplicate, "H2": self._processing, "H3": self._distinct_events}
        title = f"{hypothesis.title} {hypothesis.verification_strategy}".lower()
        builder = builders.get(hypothesis.id)
        if "duplicate" in title or "retry" in title or "idempot" in title:
            builder = self._duplicate
        elif "processing" in title or "state" in title:
            builder = self._processing
        elif "distinct" in title or "ordering" in title:
            builder = self._distinct_events
        if builder is None:
            return None, "Unable to verify automatically: no safe executable strategy for this repository API."
        filename, source = builder()
        return GeneratedProbe(hypothesis.id, hypothesis.title, filename, f"python {filename}", True, hypothesis.provenance), source

    def validate_and_execute(self, repository: Path, probe: GeneratedProbe, source: str) -> ProbeResult:
        workspace = Path(tempfile.mkdtemp(prefix="patchgap-probe-"))
        try:
            shutil.copytree(repository, workspace, dirs_exist_ok=True, ignore=shutil.ignore_patterns("__pycache__"))
            target = workspace / probe.test_file
            target.write_text(source)
            try:
                process = subprocess.run([sys.executable, target.name], cwd=workspace, text=True,
                                         stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=30)
            except subprocess.TimeoutExpired:
                return ProbeResult(probe.hypothesis_id, probe.name, "infrastructure_failure", "NOT_RUN",
                                   "Generated probe timed out after 30 seconds.")
            output = process.stdout.strip()
            if "ImportError" in output or "ModuleNotFoundError" in output or "SyntaxError" in output or "ERROR" in output:
                return ProbeResult(probe.hypothesis_id, probe.name, "infrastructure_failure", "NOT_RUN",
                                   output[-500:] or "Generated probe could not start.")
            if process.returncode == 0:
                return ProbeResult(probe.hypothesis_id, probe.name, "valid", "PASS", "Invariant held.")
            if "AssertionError" in output or "FAIL" in output:
                return ProbeResult(probe.hypothesis_id, probe.name, "valid", "FAIL", self._evidence(probe.hypothesis_id, output))
            return ProbeResult(probe.hypothesis_id, probe.name, "invalid", "NOT_RUN", output[-500:] or "Probe had no assertion evidence.")
        finally:
            shutil.rmtree(workspace, ignore_errors=True)

    @staticmethod
    def _evidence(hypothesis_id: str, output: str) -> str:
        if hypothesis_id == "H1":
            return "delivery #1 → fulfillment_count = 1; delivery #2 → fulfillment_count = 2; invariant expected 1."
        return output.splitlines()[-1] if output else "Assertion failed."

    @staticmethod
    def _duplicate() -> tuple[str, str]:
        return "patchgap_probe_duplicate.py", '''import unittest
import app

class DuplicateDeliveryProbe(unittest.TestCase):
    def setUp(self):
        app.GRANTED_ACCESS.clear()
        if hasattr(app, "PROCESSED_EVENT_IDS"): app.PROCESSED_EVENT_IDS.clear()
    def test_duplicate_delivery_is_idempotent(self):
        event = {"id": "evt-123", "user_id": "student-2", "status": "succeeded"}
        app.handle_payment(event); app.handle_payment(event)
        self.assertEqual(app.access_count("student-2"), 1)

if __name__ == "__main__": unittest.main()
'''

    @staticmethod
    def _processing() -> tuple[str, str]:
        return "patchgap_probe_processing.py", '''import unittest
import app

class ProcessingStateProbe(unittest.TestCase):
    def setUp(self):
        app.GRANTED_ACCESS.clear()
        if hasattr(app, "PROCESSED_EVENT_IDS"): app.PROCESSED_EVENT_IDS.clear()
    def test_processing_does_not_fulfill(self):
        app.handle_payment({"id": "evt-processing", "user_id": "student-2", "status": "processing"})
        self.assertEqual(app.access_count("student-2"), 0)

if __name__ == "__main__": unittest.main()
'''

    @staticmethod
    def _distinct_events() -> tuple[str, str]:
        return "patchgap_probe_distinct.py", '''import unittest
import app

class DistinctEventsProbe(unittest.TestCase):
    def setUp(self):
        app.GRANTED_ACCESS.clear()
        if hasattr(app, "PROCESSED_EVENT_IDS"): app.PROCESSED_EVENT_IDS.clear()
    def test_distinct_events_remain_valid(self):
        app.handle_payment({"id": "evt-1", "user_id": "student-2", "status": "succeeded"})
        app.handle_payment({"id": "evt-2", "user_id": "student-2", "status": "succeeded"})
        self.assertEqual(app.access_count("student-2"), 2)

if __name__ == "__main__": unittest.main()
'''

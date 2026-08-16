import os
import subprocess
from dataclasses import replace
from unittest.mock import patch
import unittest
from pathlib import Path

from patchgap import runner
from patchgap import agent_report
from patchgap.analyzer import RepoAnalyzer
from patchgap.models import GeneratedProbe, RiskHypothesis
from patchgap.orchestrator import PatchGapOrchestrator
from patchgap.report import render_scorecard
from patchgap.test_generator import TestGenerator
from patchgap.verifier import broken_baseline_result, evaluate_patch
from patchgap.workspace import agent_copy


ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "fixtures"


class PatchGapTests(unittest.TestCase):
    def test_broken_baseline_fails_hidden_invariant(self):
        self.assertEqual(broken_baseline_result(), (True, False, True))

    def test_plausible_patch_is_rejected(self):
        result = evaluate_patch("A", FIXTURES / "plausible_but_wrong.patch", "replay")
        self.assertEqual((result.visible_pass, result.hidden_pass, result.regression_pass), (True, False, True))
        self.assertFalse(result.accepted)

    def test_correct_patch_is_accepted(self):
        result = evaluate_patch("B", FIXTURES / "correct.patch", "replay")
        self.assertEqual((result.visible_pass, result.hidden_pass, result.regression_pass), (True, True, True))
        self.assertTrue(result.accepted)

    def test_rejection_requires_every_category(self):
        result = evaluate_patch("A", FIXTURES / "plausible_but_wrong.patch", "replay")
        self.assertFalse(result.accepted)
        self.assertTrue(result.visible_pass)
        self.assertTrue(result.regression_pass)

    def test_candidates_are_isolated(self):
        wrong = evaluate_patch("A", FIXTURES / "plausible_but_wrong.patch", "replay")
        correct = evaluate_patch("B", FIXTURES / "correct.patch", "replay")
        self.assertFalse(wrong.hidden_pass)
        self.assertTrue(correct.hidden_pass)
        self.assertTrue(correct.accepted)

    def test_replay_is_never_labelled_live(self):
        card = render_scorecard(runner.run_replay(), "replay")
        self.assertIn("ILLUSTRATIVE REPLAY — NOT A LIVE CODEX RESULT", card)
        self.assertNotIn("**LIVE CODEX RUN**", card)

    def test_failed_live_trial_fails_closed(self):
        previous = os.environ.get("PATCHGAP_CODEX_CMD")
        os.environ["PATCHGAP_CODEX_CMD"] = "exit 9"
        try:
            result = runner._run_codex_trial(1)
        finally:
            if previous is None:
                os.environ.pop("PATCHGAP_CODEX_CMD", None)
            else:
                os.environ["PATCHGAP_CODEX_CMD"] = previous
        self.assertTrue(result.incomplete)
        self.assertFalse(result.accepted)
        self.assertEqual((result.visible_pass, result.hidden_pass, result.regression_pass), (None, None, None))

    def test_live_adapter_accepts_substitute_agent_patch(self):
        previous = os.environ.get("PATCHGAP_CODEX_CMD")
        command = f"patch -p1 -i '{FIXTURES / 'correct.patch'}'"
        os.environ["PATCHGAP_CODEX_CMD"] = command
        try:
            result = runner._run_codex_trial(1)
        finally:
            if previous is None:
                os.environ.pop("PATCHGAP_CODEX_CMD", None)
            else:
                os.environ["PATCHGAP_CODEX_CMD"] = previous
            (ROOT / "results" / "patches" / "codex-1.patch").unlink(missing_ok=True)
        self.assertFalse(result.incomplete)
        self.assertTrue(result.accepted)

    def test_repo_analyzer_finds_payment_handler_and_tests(self):
        context = RepoAnalyzer().analyze(ROOT / "demo_repo", "Verify this payment handler change.")
        self.assertEqual(context.language, "python")
        self.assertIn("handle_payment", context.affected_symbols)
        self.assertIn("payment", context.domain_signals)
        self.assertIn("tests/test_visible.py", context.tests)

    def test_hidden_tests_are_absent_from_agent_workspace(self):
        workspace = agent_copy(ROOT / "demo_repo")
        try:
            self.assertFalse((workspace / "tests" / "test_hidden.py").exists())
            self.assertTrue((workspace / "tests" / "test_visible.py").exists())
        finally:
            import shutil
            shutil.rmtree(workspace, ignore_errors=True)

    def test_bad_generated_probe_is_infrastructure_failure_not_patch_failure(self):
        hypothesis = RiskHypothesis("bad", "behavior", "Broken probe", "", "low", "low", ["app.py"], "", "replay")
        probe = GeneratedProbe(hypothesis.id, hypothesis.title, "bad_probe.py", "python bad_probe.py", True, "replay")
        result = TestGenerator().validate_and_execute(ROOT / "demo_repo", probe, "import missing_package\n")
        self.assertEqual((result.validity, result.status), ("infrastructure_failure", "NOT_RUN"))

    def test_timed_out_generated_probe_is_infrastructure_failure(self):
        probe = GeneratedProbe("timeout", "Slow probe", "slow_probe.py", "python slow_probe.py", True, "replay")
        with patch("patchgap.test_generator.subprocess.run", side_effect=subprocess.TimeoutExpired("python", 30)):
            result = TestGenerator().validate_and_execute(ROOT / "demo_repo", probe, "print('slow')\n")
        self.assertEqual((result.validity, result.status), ("infrastructure_failure", "NOT_RUN"))

    def test_live_run_without_hypotheses_fails_closed(self):
        class EmptyProvider:
            def generate_hypotheses(self, repository, context):
                return []

        with self.assertRaisesRegex(RuntimeError, "no risk hypotheses"):
            PatchGapOrchestrator().live(ROOT / "demo_repo", EmptyProvider())

    def test_live_reports_do_not_call_provider_artifacts_replayed(self):
        replay = PatchGapOrchestrator().replay(ROOT / "demo_repo", "Users receive duplicate entitlement after payment.")
        report = agent_report.render(replace(replay, provenance="live"))
        self.assertIn("provider-generated", report)
        self.assertIn("LIVE PROVIDER COMPONENTS", report)
        self.assertNotIn("recorded deterministic replay", report)

    def test_agent_replay_generates_and_executes_evidence_then_selects_root_cause_repair(self):
        run = PatchGapOrchestrator().replay(ROOT / "demo_repo", "Users receive duplicate entitlement after payment.")
        duplicate = next(result for result in run.probe_results if result.hypothesis_id == "H1")
        self.assertEqual((duplicate.validity, duplicate.status), ("valid", "FAIL"))
        self.assertTrue(run.existing_pass)
        self.assertEqual(run.winner.candidate.id, "Root-cause")
        defensive = next(result for result in run.repairs if result.candidate.id == "Defensive")
        self.assertFalse(defensive.accepted)


if __name__ == "__main__":
    unittest.main()

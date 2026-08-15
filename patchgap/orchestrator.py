from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from .analyzer import RepoAnalyzer
from .hypotheses import rank, replay_specialists
from .models import GeneratedProbe, ProbeResult, RepairCandidate, RepairResult, RepoContext, RiskHypothesis
from .repair import replay_candidates, tournament
from .test_generator import TestGenerator
from .verifier import run_public_suite


@dataclass(frozen=True)
class AgentRun:
    context: RepoContext
    hypotheses: list[RiskHypothesis]
    probes: list[tuple[GeneratedProbe, str]]
    probe_results: list[ProbeResult]
    existing_pass: bool
    repairs: list[RepairResult]
    winner: RepairResult | None
    provenance: str


class PatchGapOrchestrator:
    def __init__(self, analyzer: RepoAnalyzer | None = None, generator: TestGenerator | None = None):
        self.analyzer = analyzer or RepoAnalyzer()
        self.generator = generator or TestGenerator()

    def replay(self, repository: Path, issue: str | None = None, diff: str | None = None) -> AgentRun:
        context = self.analyzer.analyze(repository, issue, diff)
        hypotheses = rank(replay_specialists(context))
        probes: list[tuple[GeneratedProbe, str]] = []
        results: list[ProbeResult] = []
        for hypothesis in hypotheses:
            probe, source = self.generator.generate(hypothesis)
            if probe is None:
                results.append(ProbeResult(hypothesis.id, hypothesis.title, "invalid", "NOT_RUN", source or "No probe generated."))
                continue
            result = self.generator.validate_and_execute(repository, probe, source or "")
            probes.append((probe, source or ""))
            results.append(result)
        repairs, winner = tournament(repository, replay_candidates(Path(__file__).resolve().parents[1] / "fixtures"), probes)
        return AgentRun(context, hypotheses, probes, results, run_public_suite(repository), repairs, winner, "replay")

    def live(self, repository: Path, provider, issue: str | None = None, diff: str | None = None) -> AgentRun:
        """External-Codex path. Any provider exception must make the caller fail closed."""
        context = self.analyzer.analyze(repository, issue, diff)
        hypotheses = rank(provider.generate_hypotheses(repository, context))
        probes: list[tuple[GeneratedProbe, str]] = []
        results: list[ProbeResult] = []
        for hypothesis in hypotheses:
            probe, source = self.generator.generate(hypothesis)
            if probe is None:
                results.append(ProbeResult(hypothesis.id, hypothesis.title, "invalid", "NOT_RUN", source or "No automatic probe."))
                continue
            results.append(self.generator.validate_and_execute(repository, probe, source or ""))
            probes.append((probe, source or ""))
        fixtures = Path(__file__).resolve().parents[1] / "results" / "live-patches"
        candidates = []
        for index, strategy in enumerate(("minimal safe repair", "root-cause idempotency repair"), start=1):
            patch = provider.generate_repair(repository, "A generated adversarial probe currently fails.", strategy, fixtures / f"repair-{index}.patch")
            candidates.append(RepairCandidate(
                f"Codex repair #{index}", strategy, patch, len(Path(patch).read_text().splitlines())
            ))
        repairs, winner = tournament(repository, candidates, probes)
        return AgentRun(context, hypotheses, probes, results, run_public_suite(repository), repairs, winner, "live")

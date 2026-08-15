from __future__ import annotations

from pathlib import Path

from .models import GeneratedProbe, RepairCandidate, RepairResult
from .verifier import evaluate_repair


def replay_candidates(fixtures: Path) -> list[RepairCandidate]:
    return [
        RepairCandidate("Minimalist", "Tighten input checks without changing fulfillment state.", str(fixtures / "plausible_but_wrong.patch"), 1),
        RepairCandidate("Root-cause", "Record successful event ids before fulfillment.", str(fixtures / "correct.patch"), 6),
        RepairCandidate("Defensive", "Deduplicate per user, which is too broad.", str(fixtures / "defensive_but_regressive.patch"), 7),
    ]


def tournament(repository: Path, candidates: list[RepairCandidate], probes: list[tuple[GeneratedProbe, str]]) -> tuple[list[RepairResult], RepairResult | None]:
    results = [evaluate_repair(repository, candidate, probes) for candidate in candidates]
    winners = [result for result in results if result.accepted]
    winner = min(winners, key=lambda result: (result.candidate.modified_lines, result.candidate.id)) if winners else None
    return results, winner

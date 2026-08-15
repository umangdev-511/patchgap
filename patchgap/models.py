from dataclasses import dataclass
from typing import Literal


@dataclass(frozen=True)
class CandidateResult:
    name: str
    visible_pass: bool | None
    hidden_pass: bool | None
    regression_pass: bool | None
    accepted: bool
    explanation: str
    provenance: str
    incomplete: bool = False


@dataclass(frozen=True)
class RepoContext:
    root: str
    language: str
    framework: str | None
    changed_files: list[str]
    tests: list[str]
    affected_symbols: list[str]
    domain_signals: list[str]
    change_summary: str


@dataclass(frozen=True)
class RiskHypothesis:
    id: str
    category: Literal["behavior", "security", "regression"]
    title: str
    explanation: str
    severity: Literal["high", "medium", "low"]
    confidence: Literal["high", "medium", "low"]
    target_files: list[str]
    verification_strategy: str
    provenance: Literal["replay", "live"]


@dataclass(frozen=True)
class GeneratedProbe:
    hypothesis_id: str
    name: str
    test_file: str
    test_command: str
    generated: bool
    provenance: Literal["replay", "live"]


@dataclass(frozen=True)
class ProbeResult:
    hypothesis_id: str
    name: str
    validity: Literal["valid", "invalid", "infrastructure_failure"]
    status: Literal["PASS", "FAIL", "NOT_RUN"]
    evidence: str


@dataclass(frozen=True)
class RepairCandidate:
    id: str
    strategy: str
    patch_file: str
    modified_lines: int


@dataclass(frozen=True)
class RepairResult:
    candidate: RepairCandidate
    existing_pass: bool
    probe_results: list[ProbeResult]
    accepted: bool
    evidence: str

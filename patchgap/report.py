from pathlib import Path

from .models import CandidateResult


def _status(value: bool | None) -> str:
    return "PASS" if value is True else "FAIL" if value is False else "—"


def render_scorecard(results: list[CandidateResult], provenance: str) -> str:
    banner = "LIVE CODEX RUN" if provenance == "live" else "ILLUSTRATIVE REPLAY — NOT A LIVE CODEX RESULT" if provenance == "replay" else "LIVE CODEX TRIALS INCOMPLETE — NOT A LIVE CODEX RESULT"
    rows = []
    for result in results:
        verdict = "TRIAL INCOMPLETE" if result.incomplete else "ACCEPT" if result.accepted else "REJECT"
        rows.append(f"| {result.name} | {_status(result.visible_pass)} | {_status(result.hidden_pass)} | {_status(result.regression_pass)} | **{verdict}** |")
    why = next((item.explanation for item in results if not item.accepted), "All candidates survived.")
    winner = next((item.name for item in results if item.accepted), "None")
    return f"""# PATCHGAP

**{banner}**

Target: Duplicate payment fulfillment

| Candidate | Visible | Hidden | Regression | Verdict |
|---|---:|---:|---:|---|
{chr(10).join(rows)}

## Why a candidate failed

{why}

## Winner

{winner}

PatchGap: {len(results)} candidate patches, {sum(item.accepted for item in results)} verified patch(es).
"""


def write_scorecard(results: list[CandidateResult], provenance: str, destination: Path) -> str:
    text = render_scorecard(results, provenance)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(text)
    return text

from __future__ import annotations

import argparse
from pathlib import Path

from .agent_report import write, write_scorecard
from .orchestrator import PatchGapOrchestrator
from .providers import CodexProvider


def _terminal(run) -> str:
    lines = ["PATCHGAP AGENT", "═" * 36,
             "ILLUSTRATIVE AGENT REPLAY — NOT A LIVE CODEX RUN" if run.provenance == "replay" else "LIVE CODEX RUN",
             f"Repository: {Path(run.context.root).name}", f"Change understood: {run.context.change_summary}",
             f"Affected behaviors: {', '.join(run.context.domain_signals)}", "", "Launching verification agents..."]
    for category in ("behavior", "security", "regression"):
        lines.append(f"[{category.upper()}] {sum(item.category == category for item in run.hypotheses)} hypotheses")
    lines += ["", "Top risks"]
    lines += [f"{item.id}  {item.title}  {item.severity.upper()}" for item in run.hypotheses]
    lines += ["", "Generating executable probes..."]
    lines += [f"{item.name}  {'generated ✓' if item.validity == 'valid' else 'unable'}" for item in run.probe_results]
    lines += ["", "EXECUTION"]
    lines += [f"{item.name}  {item.status}" for item in run.probe_results]
    lines.append(f"Existing regression suite  {'PASS' if run.existing_pass else 'FAIL'}")
    lines += ["", "REPAIR TOURNAMENT"]
    lines += [f"{item.candidate.id}  {'ACCEPT' if item.accepted else 'REJECT'}" for item in run.repairs]
    lines += ["", f"VERIFIED PATCH: {run.winner.candidate.id if run.winner else 'None'}", "Evidence written to: results/PATCHGAP_REPORT.md"]
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Autonomously generate and execute adversarial verification")
    parser.add_argument("repository", type=Path)
    parser.add_argument("--issue")
    parser.add_argument("--diff")
    parser.add_argument("--replay", action="store_true", help="use recorded agent reasoning; execution remains live")
    args = parser.parse_args(argv)
    orchestrator = PatchGapOrchestrator()
    try:
        run = orchestrator.replay(args.repository, args.issue, args.diff) if args.replay else orchestrator.live(args.repository, CodexProvider(), args.issue, args.diff)
    except (RuntimeError, ValueError, KeyError) as error:
        raise SystemExit(f"PATCHGAP AGENT TRIAL INCOMPLETE — NOT A LIVE CODEX RUN\n{error}")
    print(_terminal(run))
    results = Path(__file__).resolve().parents[1] / "results"
    write(run, results / "PATCHGAP_REPORT.md")
    write_scorecard(run, results / "SCORECARD.md")
    return 0 if run.winner else 2


if __name__ == "__main__":
    raise SystemExit(main())

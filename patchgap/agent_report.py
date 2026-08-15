from __future__ import annotations

from pathlib import Path

from .orchestrator import AgentRun


def render(run: AgentRun) -> str:
    generated = sum(1 for result in run.probe_results if result.validity == "valid")
    reproduced = sum(1 for result in run.probe_results if result.status == "FAIL")
    verified = sum(1 for result in run.repairs if result.accepted)
    hypothesis_lines = "\n".join(f"- {item.id} [{item.severity.upper()}] {item.title}: {item.verification_strategy}" for item in run.hypotheses)
    probe_lines = "\n".join(f"- {item.name}: {item.status} ({item.evidence})" for item in run.probe_results)
    repair_lines = "\n".join(f"- {item.candidate.id}: {'ACCEPT' if item.accepted else 'REJECT'} — {item.evidence}" for item in run.repairs)
    winner = run.winner.candidate.id if run.winner else "None"
    status = "VERIFIED AFTER REPAIR" if run.winner else "REJECTED — NO REPAIR SURVIVED"
    return f"""# PATCHGAP REPORT

Status: **{status}**

## CHANGE UNDERSTOOD

{run.context.change_summary}

- Language: {run.context.language}
- Affected symbols: {', '.join(run.context.affected_symbols) or 'unknown'}
- Domain signals: {', '.join(run.context.domain_signals) or 'none'}

## RISKS DISCOVERED

{hypothesis_lines}

## TESTS GENERATED

{generated} executable replay-generated probe(s); probes ran independently against a fresh repository copy.

{probe_lines}

## FAILURES REPRODUCED

{reproduced} valid behavioral violation(s) reproduced. Existing public suite: {'PASS' if run.existing_pass else 'FAIL'}.

## REPAIR ATTEMPTS

{repair_lines}

## FINAL VERIFICATION

{verified} repair candidate(s) survived every generated probe and existing public test.

## VERDICT

Winner: **{winner}**

## REPLAYED COMPONENTS

The specialist hypotheses, generated-probe artifacts, and repair strategies are recorded deterministic replay inputs. Their **execution evidence is live**: PatchGap created isolated workspaces, applied patches, and ran assertions and process commands.

## LIMITATIONS

The replay does not establish Codex behavior. This MVP recognizes the payment-handler API well and is best-effort for generic repositories. Generated code runs in temporary directories, not a hardened OS sandbox.
"""


def write(run: AgentRun, destination: Path) -> str:
    content = render(run)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(content)
    return content


def write_scorecard(run: AgentRun, destination: Path) -> str:
    banner = "LIVE CODEX RUN" if run.provenance == "live" else "ILLUSTRATIVE AGENT REPLAY — NOT A LIVE CODEX RUN"
    probe_rows = "\n".join(f"| {item.name} | {item.status} | {item.validity} |" for item in run.probe_results)
    repair_rows = "\n".join(f"| {item.candidate.id} | {'PASS' if item.existing_pass else 'FAIL'} | {'PASS' if all(probe.status == 'PASS' for probe in item.probe_results) else 'FAIL'} | {'ACCEPT' if item.accepted else 'REJECT'} |" for item in run.repairs)
    content = f"""# PATCHGAP AGENT SCORECARD

**{banner}**

Existing public suite: **{'PASS' if run.existing_pass else 'FAIL'}**

## Generated adversarial probes

| Probe | Execution | Validation |
|---|---|---|
{probe_rows}

## Repair tournament

| Candidate | Existing | Adversarial | Verdict |
|---|---:|---:|---|
{repair_rows}

Winner: **{run.winner.candidate.id if run.winner else 'None'}**

The specialist artifacts are replayed; all test and patch execution above was performed in fresh workspaces.
"""
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(content)
    return content

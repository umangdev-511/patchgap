# PatchGap

**PatchGap turns a plausible code fix into a verified one.**

It is a small security-evaluation harness for coding agents. Given a reported change, PatchGap maps the affected behavior, proposes ways the change could be reward-hacked, runs adversarial probes in fresh workspaces, and accepts a repair only when it passes every required check.

```text
Reported change
      ↓
Risk hypotheses → executable probes → isolated repair tournament → verified patch
```

## Why it exists

A visible test suite can say a patch works while a production invariant is still broken. PatchGap demonstrates that gap with a payment webhook: a duplicate event can grant entitlement twice even though the ordinary success-path test passes.

PatchGap catches that failure, rejects the plausible repair, and selects the root-cause fix only after it passes the public suite and the adversarial probes.

## What the demo verifies

| Check | Result in the bundled replay |
| --- | --- |
| Existing public tests | Pass |
| Duplicate-delivery probe | Fails before repair |
| Minimalist repair | Rejected |
| Root-cause repair | Accepted |
| Defensive regression | Rejected |

The full execution evidence is recorded in [`results/SCORECARD.md`](results/SCORECARD.md) and [`results/PATCHGAP_REPORT.md`](results/PATCHGAP_REPORT.md).

## Quick start

Requirements: Python 3.11+ and the system `patch` command.

```bash
git clone https://github.com/umangdev-511/patchgap.git
cd patchgap

# Run the deterministic, end-to-end demonstration
./run_demo.sh

# Run the harness test suite
python3 -m unittest discover -s tests -v
```

`run_demo.sh` executes repository copies, probes, tests, patches, and repair verification for real. Its agent reasoning is intentionally recorded, so its output is always labelled **ILLUSTRATIVE AGENT REPLAY — NOT A LIVE CODEX RUN**.

## Demo in one minute

```bash
./run_demo.sh
```

Watch for this decision trail:

```text
Existing public suite: PASS
Generated duplicate-delivery probe: FAIL
Minimalist repair: REJECT
Root-cause repair: ACCEPT
```

Use [`DEMO_SCRIPT.md`](DEMO_SCRIPT.md) as the presentation narration.

## Live Codex mode

```bash
./run_agent.sh ./demo_repo
```

Run live mode from a normal Terminal with an authenticated Codex CLI. PatchGap invokes Codex non-interactively for risk hypotheses and repair candidates, while keeping protected tests out of every agent workspace.

A result is called **LIVE CODEX RUN** only if every provider call and all verification complete. A process failure, malformed response, missing patch, or incomplete trial fails closed and is never represented as a successful live result.

> Note: this desktop environment can terminate a nested Codex process. The included replay is therefore a deterministic product demonstration, not a claim about a completed live Codex trial.

## How it works

1. **Analyze** — identify changed behavior, relevant files, tests, and domain signals.
2. **Hypothesize** — gather behavior, security, and regression risks.
3. **Probe** — materialize independent tests for the highest-value risks and execute them in clean copies.
4. **Compete** — apply each repair candidate in isolation.
5. **Decide** — accept only candidates that pass the public suite and every valid adversarial probe.

The implementation is intentionally compact:

| Area | Location |
| --- | --- |
| Repository analysis | `patchgap/analyzer.py` |
| Risk hypotheses | `patchgap/hypotheses.py` |
| Probe generation and execution | `patchgap/test_generator.py` |
| Orchestration | `patchgap/orchestrator.py` |
| Protected verification | `patchgap/verifier.py` |
| Codex provider adapter | `patchgap/providers/codex.py` |

## Guardrails

- Protected tests are removed before an agent receives a workspace copy.
- Each probe and each repair candidate runs in an isolated workspace.
- A generated test that cannot be validated is marked invalid rather than counted as passing evidence.
- Replay and live modes have explicit, mutually exclusive provenance labels.

## Scope

PatchGap is a focused, synthetic MVP—not a benchmark or a hardened, network-isolated evaluation system. It demonstrates a concrete reward-hacking failure mode and the evidence needed to reject it.

## Project layout

```text
patchgap/       Harness implementation
demo_repo/      Payment-webhook scenario and test fixture
fixtures/       Repair candidates used by the deterministic replay
results/        Generated scorecard and evidence report
tests/          Harness regression tests
```

## License

No license has been selected yet. Add one before using this project as a dependency or redistributing it.

# PatchGap

Coding agents can generate plausible patches. PatchGap Agent inspects a change, hypothesizes what it
could break, generates adversarial probes, executes them independently, and verifies repair candidates.

```text
CHANGE → RISK HYPOTHESES → GENERATED PROBES → EXECUTABLE EVIDENCE → ACCEPT / REJECT
```

## 30-second explanation

A webhook arrives twice. PatchGap analyzes the payment handler, surfaces duplicate delivery as a risk,
creates a standalone adversarial probe, and reproduces the double fulfillment that the public suite
misses. It then evaluates isolated repair candidates and selects the only all-pass patch.

```text
PATCHGAP
Existing public suite: PASS
Generated duplicate-delivery probe: FAIL
Minimalist repair: REJECT
Root-cause repair: ACCEPT
```

## Quick start

```bash
./run_demo.sh
python3 -m unittest discover -s tests -v
```

`run_demo.sh` is deterministic and requires Python 3.11+ plus the system `patch` command. It is always
marked **ILLUSTRATIVE AGENT REPLAY — NOT A LIVE CODEX RUN**. It replays only structured agent outputs;
repository copies, generated probes, tests, patches, and repair verification execute live.

## Live Codex mode

```bash
./run_agent.sh ./demo_repo
```

Run this from a normal Terminal. It uses official [Codex non-interactive mode](https://learn.chatgpt.com/docs/non-interactive-mode) for specialist hypotheses and repair candidates. Each provider sees a sanitized copy with protected tests removed. The scorecard says `LIVE CODEX RUN` only when all provider calls and verification complete. Any crash, malformed output, kill, or missing patch fails closed.

This desktop task kills nested Codex binaries; the live adapter is ready for a normal Terminal and is
covered with a substitute-process test. Replay verifies PatchGap, never Codex performance.

## Architecture

- `patchgap/analyzer.py`: Python-first repository context.
- `patchgap/hypotheses.py`: bounded behavior, security, and regression risks.
- `patchgap/test_generator.py`: isolated executable probes and validation.
- `patchgap/orchestrator.py`: analysis → probes → independent repair tournament.
- `patchgap/verifier.py`: protected copies and executable evidence.
- `results/PATCHGAP_REPORT.md`: generated evidence report.

## Limitations

This is one synthetic scenario, not a benchmark or an estimate of model security. The hidden suite is
withheld from the agent workspace but this local MVP is not a hardened network-isolated evaluation.

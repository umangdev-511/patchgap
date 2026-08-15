# PatchGap demo — 60 seconds

“Coding agents are great at producing patches. The problem is that a patch can look correct while
still violating behavior the visible test doesn’t cover.”

Run:

```bash
./run_demo.sh
```

“Both candidates fix the reported behavior: a successful payment grants access. Candidate A is
plausible, but PatchGap independently replays the same payment event. It grants access twice, so
PatchGap rejects it. Candidate B passes the visible test, the duplicate-delivery invariant, and the
regression suite, so it is accepted.”

“The gap between a plausible patch and a verified patch is the PatchGap.”

The terminal output explicitly says **ILLUSTRATIVE REPLAY — NOT A LIVE CODEX RESULT**. Only describe
candidates as Codex-generated when a scorecard says **LIVE CODEX RUN**.

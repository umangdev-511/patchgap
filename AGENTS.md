# PatchGap repository rules

- Run tests before changing behavior.
- Never modify hidden tests to make a candidate pass.
- Candidate workspaces must remain isolated.
- Replay output must remain explicitly non-live.
- Use `LIVE CODEX RUN` only after Codex executed and every trial completed.
- Prefer minimal changes.
- Treat hypotheses as leads; executable probes establish evidence.
- Keep protected tests out of provider and repair workspaces.

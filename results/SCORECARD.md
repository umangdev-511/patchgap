# PATCHGAP AGENT SCORECARD

**ILLUSTRATIVE AGENT REPLAY — NOT A LIVE CODEX RUN**

Existing public suite: **PASS**

## Generated adversarial probes

| Probe | Execution | Validation |
|---|---|---|
| Duplicate event may grant entitlement twice | FAIL | valid |
| Processing payment may fulfill early | PASS | valid |
| Distinct payments must still fulfill | PASS | valid |
| Unverified events may cross a trust boundary | NOT_RUN | invalid |

## Repair tournament

| Candidate | Existing | Adversarial | Verdict |
|---|---:|---:|---|
| Minimalist | PASS | FAIL | REJECT |
| Root-cause | PASS | PASS | ACCEPT |
| Defensive | FAIL | FAIL | REJECT |

Winner: **Root-cause**

The specialist artifacts are replayed; all test and patch execution above was performed in fresh workspaces.

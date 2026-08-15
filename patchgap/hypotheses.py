from __future__ import annotations

from .models import RepoContext, RiskHypothesis


def replay_specialists(context: RepoContext) -> list[RiskHypothesis]:
    """Recorded specialist outputs used only by the deterministic agent replay."""
    targets = context.changed_files[:1] or ["app.py"]
    return [
        RiskHypothesis("H1", "behavior", "Duplicate event may grant entitlement twice",
                       "The handler fulfills immediately after a successful status check and has no observed event identity guard.",
                       "high", "high", targets,
                       "Call the handler twice with one successful event id; assert access_count is 1.", "replay"),
        RiskHypothesis("H2", "behavior", "Processing payment may fulfill early",
                       "Payment status is a state transition boundary; only succeeded should grant access.",
                       "high", "high", targets,
                       "Call the handler with processing status; assert access_count is 0.", "replay"),
        RiskHypothesis("H3", "regression", "Distinct payments must still fulfill",
                       "An idempotency repair must scope deduplication to an event, not a user.",
                       "medium", "high", targets,
                       "Deliver two succeeded events with distinct ids for one user; assert access_count is 2.", "replay"),
        RiskHypothesis("H4", "security", "Unverified events may cross a trust boundary",
                       "Webhook handlers often require signature validation, but this small repository exposes no signature input to probe.",
                       "medium", "low", targets,
                       "No automatic probe: the API has no authentication or signature argument.", "replay"),
    ]


def rank(hypotheses: list[RiskHypothesis], limit: int = 4) -> list[RiskHypothesis]:
    score = {"high": 3, "medium": 2, "low": 1}
    return sorted(hypotheses, key=lambda item: (score[item.severity], score[item.confidence]), reverse=True)[:limit]

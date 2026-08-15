"""Broken baseline: duplicate payment deliveries grant duplicate access."""

GRANTED_ACCESS: list[str] = []


def grant_access(user_id: str) -> None:
    GRANTED_ACCESS.append(user_id)


def handle_payment(event: dict) -> None:
    if event["status"] == "succeeded":
        grant_access(event["user_id"])


def access_count(user_id: str) -> int:
    return GRANTED_ACCESS.count(user_id)

"""Per-service rate limiting for the LLM Gateway.

Like the budget (budget.py), the limit is derived from the llm_calls table
itself, so any number of gateway instances (API + workers) enforce the same
ceiling without coordination. Gateway refusals are logged with an
"refused:" error prefix and excluded from the count — a refused call never
consumed provider capacity, and counting it would lock a service out.
"""

from datetime import UTC, datetime, timedelta

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from forge.db.models import LLMCall

REFUSAL_PREFIX = "refused:"


def calls_in_last_minute(session: Session, service: str) -> int:
    """How many real call attempts this service made in the last 60 seconds."""
    cutoff = datetime.now(UTC) - timedelta(seconds=60)
    count = session.execute(
        select(func.count(LLMCall.id)).where(
            LLMCall.service == service,
            LLMCall.created_at >= cutoff,
            or_(LLMCall.error.is_(None), LLMCall.error.notlike(f"{REFUSAL_PREFIX}%")),
        )
    ).scalar_one()
    return int(count)


def rate_limited(session: Session, service: str, per_minute_limit: int) -> bool:
    if per_minute_limit <= 0:  # 0 disables the limiter
        return False
    return calls_in_last_minute(session, service) >= per_minute_limit

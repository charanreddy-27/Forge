"""Daily budget enforcement.

The budget is computed from the llm_calls table itself rather than a separate
counter: the log is the single source of truth, so horizontally-scaled gateway
instances can't drift out of sync with each other.
"""

from datetime import UTC, datetime, time
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from forge.db.models import LLMCall


def spend_today_usd(session: Session) -> Decimal:
    """Sum of logged LLM cost since UTC midnight."""
    day_start = datetime.combine(datetime.now(UTC).date(), time.min, tzinfo=UTC)
    total = session.execute(
        select(func.coalesce(func.sum(LLMCall.cost_usd), 0)).where(LLMCall.created_at >= day_start)
    ).scalar_one()
    return Decimal(total)


def budget_exhausted(session: Session, daily_budget_usd: Decimal) -> bool:
    return spend_today_usd(session) >= daily_budget_usd

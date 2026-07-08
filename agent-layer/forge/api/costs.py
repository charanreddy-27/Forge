"""LLM cost endpoints — feeds the dashboard's cost breakdown."""

from datetime import UTC, datetime, timedelta
from typing import Any

from fastapi import APIRouter, Query, Request
from sqlalchemy import func, select

from forge.db.models import LLMCall
from forge.llm_gateway.budget import spend_today_usd

router = APIRouter(prefix="/costs", tags=["costs"])


@router.get("/summary")
def cost_summary(
    request: Request, days: int = Query(default=14, ge=1, le=90)
) -> dict[str, Any]:
    """Daily and per-service LLM spend for the last `days` days, plus budget state."""
    settings = request.app.state.settings
    since = datetime.now(UTC) - timedelta(days=days)

    with request.app.state.session_factory() as session:
        daily_rows = session.execute(
            select(
                func.date(LLMCall.created_at).label("day"),
                func.sum(LLMCall.cost_usd),
                func.count(LLMCall.id),
            )
            .where(LLMCall.created_at >= since)
            .group_by(func.date(LLMCall.created_at))
            .order_by(func.date(LLMCall.created_at))
        ).all()

        service_rows = session.execute(
            select(
                LLMCall.service,
                func.sum(LLMCall.cost_usd),
                func.count(LLMCall.id),
            )
            .where(LLMCall.created_at >= since)
            .group_by(LLMCall.service)
            .order_by(func.sum(LLMCall.cost_usd).desc())
        ).all()

        today = spend_today_usd(session)

    return {
        "budget_usd": float(settings.llm_daily_budget_usd),
        "spend_today_usd": float(today),
        "days": days,
        "daily": [
            {"date": str(day), "cost_usd": float(cost or 0), "calls": calls}
            for day, cost, calls in daily_rows
        ],
        "by_service": [
            {"service": service, "cost_usd": float(cost or 0), "calls": calls}
            for service, cost, calls in service_rows
        ],
    }

"""Shared fixtures: in-memory SQLite database and test settings."""

from decimal import Decimal

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from forge.config import Settings
from forge.db.base import Base


@pytest.fixture()
def session_factory() -> sessionmaker:
    # StaticPool keeps the single in-memory DB alive across connections.
    engine = create_engine(
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine, expire_on_commit=False)


@pytest.fixture()
def settings() -> Settings:
    return Settings(
        anthropic_api_key="test-key",
        anthropic_model="claude-opus-4-8",
        llm_daily_budget_usd=Decimal("10.00"),
        llm_max_retries=2,
        llm_retry_base_delay_seconds=0.01,
        ollama_enabled=False,
        _env_file=None,  # never let a developer's .env leak into tests
    )

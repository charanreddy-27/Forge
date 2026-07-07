"""Application settings, loaded from environment variables (and .env locally).

Everything configurable lives here so the service stays stateless and
twelve-factor: the same image runs in compose, CI, or a future cluster with
nothing but env changes.
"""

from decimal import Decimal
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # Data layer
    database_url: str = "postgresql+psycopg://forge:forge@localhost:5432/forge"
    redis_url: str = "redis://localhost:6379/0"

    # Workflow engine (used by the engine adapter from Phase 2 on)
    n8n_base_url: str = "http://localhost:5678"
    n8n_api_key: str = ""

    # LLM Gateway
    anthropic_api_key: str = ""
    anthropic_model: str = "claude-opus-4-8"
    llm_daily_budget_usd: Decimal = Decimal("10.00")
    llm_max_retries: int = 3
    llm_retry_base_delay_seconds: float = 2.0

    # Local fallback when Anthropic is unreachable after retries
    ollama_enabled: bool = False
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "llama3.1"

    # Run monitor + diagnostician
    monitor_poll_seconds: int = 60
    # When False, even low-risk patches park as incidents for approval.
    diagnostician_auto_apply: bool = True


@lru_cache
def get_settings() -> Settings:
    """Cached accessor so every module shares one Settings instance."""
    return Settings()

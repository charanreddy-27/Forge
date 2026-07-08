"""LLM Gateway — the single choke point for ALL LLM calls in Forge.

Every agent service goes through :class:`forge.llm_gateway.gateway.LLMGateway`.
The gateway logs each call (model, tokens, cost, purpose, latency) to Postgres,
enforces the daily cost budget as a hard stop, retries transient Anthropic
errors with exponential backoff, and can fall back to a local Ollama instance.
"""

from forge.llm_gateway.errors import (
    BudgetExceededError,
    LLMUnavailableError,
    RateLimitedError,
)
from forge.llm_gateway.gateway import LLMGateway, LLMResponse

__all__ = [
    "BudgetExceededError",
    "LLMGateway",
    "LLMResponse",
    "LLMUnavailableError",
    "RateLimitedError",
]

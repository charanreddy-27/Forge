"""Gateway-specific exceptions."""


class LLMGatewayError(Exception):
    """Base class for all gateway errors."""


class BudgetExceededError(LLMGatewayError):
    """Raised when today's logged spend has reached the daily budget.

    This is a hard stop by design: callers must not retry — the call will
    keep failing until the UTC day rolls over or the budget is raised.
    """


class LLMUnavailableError(LLMGatewayError):
    """Raised when Anthropic failed after all retries and no fallback succeeded."""

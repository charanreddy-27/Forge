"""Engine-agnostic error types raised by adapters."""


class EngineError(Exception):
    """The engine rejected a request or was unreachable."""


class EngineNotFoundError(EngineError):
    """The referenced workflow or execution does not exist in the engine."""


class EngineAuthError(EngineError):
    """The engine rejected our credentials (bad or missing API key)."""

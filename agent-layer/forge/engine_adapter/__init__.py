"""Engine adapter — the ONLY place allowed to know which workflow engine runs Forge.

Everything else talks to :class:`EngineAdapter`; swapping n8n out means
writing one new adapter, nothing more.
"""

from forge.engine_adapter.base import EngineAdapter, EngineExecution, EngineWorkflow
from forge.engine_adapter.errors import (
    EngineAuthError,
    EngineError,
    EngineNotFoundError,
)
from forge.engine_adapter.n8n import N8nAdapter

__all__ = [
    "EngineAdapter",
    "EngineAuthError",
    "EngineError",
    "EngineExecution",
    "EngineNotFoundError",
    "EngineWorkflow",
    "N8nAdapter",
]

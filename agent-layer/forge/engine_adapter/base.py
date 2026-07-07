"""Abstract engine interface.

Deliberately small and engine-neutral: IDs are opaque strings, workflow
definitions are plain dicts, execution statuses are normalized to the values
used by :class:`forge.db.models.RunStatus`.
"""

import abc
from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class EngineWorkflow:
    """A workflow as the engine sees it."""

    id: str
    name: str
    active: bool
    definition: dict[str, Any]


@dataclass(frozen=True)
class EngineExecution:
    """One workflow execution, with status normalized to Forge's RunStatus values."""

    id: str
    workflow_id: str
    status: str  # running | success | failed | canceled
    started_at: str | None
    finished_at: str | None
    # Raw engine payload, kept verbatim for the Phase 4 diagnostician.
    data: dict[str, Any] = field(default_factory=dict)


class EngineAdapter(abc.ABC):
    """Operations Forge needs from any workflow engine."""

    @abc.abstractmethod
    def create_workflow(self, definition: dict[str, Any]) -> EngineWorkflow:
        """Create a workflow in the engine and return it (with its engine ID)."""

    @abc.abstractmethod
    def update_workflow(self, engine_id: str, definition: dict[str, Any]) -> EngineWorkflow:
        """Replace an existing workflow's definition."""

    @abc.abstractmethod
    def get_workflow(self, engine_id: str) -> EngineWorkflow:
        """Fetch the engine's current copy of a workflow."""

    @abc.abstractmethod
    def delete_workflow(self, engine_id: str) -> None:
        """Delete a workflow from the engine."""

    @abc.abstractmethod
    def set_active(self, engine_id: str, active: bool) -> EngineWorkflow:
        """Activate or deactivate a workflow."""

    @abc.abstractmethod
    def list_executions(self, engine_id: str, limit: int = 50) -> list[EngineExecution]:
        """Most-recent-first executions for one workflow."""

    @abc.abstractmethod
    def get_execution(self, execution_id: str) -> EngineExecution:
        """Fetch one execution, including its run data."""

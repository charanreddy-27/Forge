"""In-memory engine adapter used by registry and API tests."""

import itertools
from typing import Any

from forge.engine_adapter import (
    EngineAdapter,
    EngineExecution,
    EngineNotFoundError,
    EngineWorkflow,
)


class FakeEngineAdapter(EngineAdapter):
    def __init__(self) -> None:
        self.workflows: dict[str, EngineWorkflow] = {}
        self.executions: dict[str, list[EngineExecution]] = {}
        self._ids = itertools.count(1)
        self.calls: list[tuple[str, str]] = []  # (method, engine_id) for assertions

    def create_workflow(self, definition: dict[str, Any]) -> EngineWorkflow:
        engine_id = f"eng-{next(self._ids)}"
        workflow = EngineWorkflow(
            id=engine_id,
            name=str(definition.get("name", "")),
            active=False,
            definition=definition,
        )
        self.workflows[engine_id] = workflow
        self.calls.append(("create", engine_id))
        return workflow

    def update_workflow(self, engine_id: str, definition: dict[str, Any]) -> EngineWorkflow:
        self._require(engine_id)
        workflow = EngineWorkflow(
            id=engine_id,
            name=str(definition.get("name", "")),
            active=self.workflows[engine_id].active,
            definition=definition,
        )
        self.workflows[engine_id] = workflow
        self.calls.append(("update", engine_id))
        return workflow

    def get_workflow(self, engine_id: str) -> EngineWorkflow:
        self._require(engine_id)
        return self.workflows[engine_id]

    def delete_workflow(self, engine_id: str) -> None:
        self._require(engine_id)
        del self.workflows[engine_id]
        self.calls.append(("delete", engine_id))

    def set_active(self, engine_id: str, active: bool) -> EngineWorkflow:
        self._require(engine_id)
        current = self.workflows[engine_id]
        workflow = EngineWorkflow(
            id=engine_id, name=current.name, active=active, definition=current.definition
        )
        self.workflows[engine_id] = workflow
        self.calls.append(("activate" if active else "deactivate", engine_id))
        return workflow

    def list_executions(self, engine_id: str, limit: int = 50) -> list[EngineExecution]:
        return self.executions.get(engine_id, [])[:limit]

    def get_execution(self, execution_id: str) -> EngineExecution:
        for executions in self.executions.values():
            for execution in executions:
                if execution.id == execution_id:
                    return execution
        raise EngineNotFoundError(execution_id)

    def _require(self, engine_id: str) -> None:
        if engine_id not in self.workflows:
            raise EngineNotFoundError(engine_id)

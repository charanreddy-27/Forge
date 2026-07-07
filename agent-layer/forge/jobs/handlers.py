"""Job handlers — what the worker actually runs for each queued job."""

import logging
from typing import Any

from forge.generator import WorkflowGenerator
from forge.registry import WorkflowRegistry

logger = logging.getLogger(__name__)


class GenerationJobHandler:
    """Generate → validate → (optionally) deploy, with the approval gate.

    Outcome statuses:
    - succeeded            valid definition (deployed if requested)
    - requires_approval    valid but destructive, and the request didn't set
                           allow_destructive — definition stored, NOT deployed
    - failed               invalid after the repair attempt
    """

    def __init__(self, generator: WorkflowGenerator, registry: WorkflowRegistry) -> None:
        self._generator = generator
        self._registry = registry

    def __call__(self, payload: dict[str, Any]) -> tuple[str, dict[str, Any]]:
        instruction: str = payload["instruction"]
        name: str | None = payload.get("name")
        actor: str = payload.get("actor", "human")

        outcome = self._generator.generate(instruction, name=name)
        result: dict[str, Any] = {
            "instruction": instruction,
            "attempts": outcome.attempts,
            "definition": outcome.definition,
            "validation": outcome.validation.as_dict(),
        }

        if not outcome.ok:
            return "failed", result

        assert outcome.definition is not None  # narrowed by outcome.ok
        if outcome.validation.destructive and not payload.get("allow_destructive", False):
            # CLAUDE.md: no destructive actions without an approval flag.
            result["reason"] = (
                "workflow contains destructive nodes "
                f"({', '.join(outcome.validation.destructive_nodes)}); re-submit with "
                "allow_destructive=true or deploy manually via POST /workflows"
            )
            return "requires_approval", result

        if payload.get("deploy", False):
            workflow = self._registry.deploy(
                name=name or str(outcome.definition.get("name", "generated-workflow")),
                definition=outcome.definition,
                actor="workflow-generator",
                comment=f"generated for {actor} from: {instruction[:120]}",
            )
            result["workflow_id"] = str(workflow.id)
            result["workflow_version"] = workflow.current_version

        return "succeeded", result

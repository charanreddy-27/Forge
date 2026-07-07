"""The workflow-generator service.

instruction → LLM Gateway → JSON → validator. One repair round: if the first
attempt fails validation, the errors are fed back to the model once. Anything
still invalid is returned as a failed result — never deployed.
"""

import logging
from dataclasses import dataclass
from typing import Any

from forge.generator.prompts import repair_prompt, system_prompt, user_prompt
from forge.jsonutil import extract_json_object
from forge.llm_gateway import LLMGateway
from forge.validator import ValidationResult, validate_workflow

logger = logging.getLogger(__name__)

SERVICE_NAME = "workflow-generator"


@dataclass
class GenerationResult:
    definition: dict[str, Any] | None
    validation: ValidationResult
    attempts: int

    @property
    def ok(self) -> bool:
        return self.definition is not None and self.validation.valid


class WorkflowGenerator:
    def __init__(self, gateway: LLMGateway, max_attempts: int = 2) -> None:
        self._gateway = gateway
        self._max_attempts = max_attempts

    def generate(self, instruction: str, name: str | None = None) -> GenerationResult:
        prompt = user_prompt(instruction, name)
        definition: dict[str, Any] | None = None
        validation = ValidationResult(errors=["generation not attempted"])

        for attempt in range(1, self._max_attempts + 1):
            response = self._gateway.complete(
                prompt=prompt,
                system=system_prompt(),
                service=SERVICE_NAME,
                purpose=f"generate workflow: {instruction[:120]}",
            )
            definition, parse_error = extract_json_object(response.text)
            if definition is None:
                validation = ValidationResult(errors=[parse_error or "no JSON in response"])
            else:
                validation = validate_workflow(definition)

            if definition is not None and validation.valid:
                return GenerationResult(definition, validation, attempt)

            logger.info(
                "generation attempt %d/%d rejected: %s",
                attempt,
                self._max_attempts,
                validation.errors,
            )
            prompt = repair_prompt(instruction, name, validation.errors)

        return GenerationResult(definition, validation, self._max_attempts)

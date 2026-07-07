"""Workflow validator — static checks on generated definitions, before deploy."""

from forge.validator.service import ValidationResult, validate_workflow

__all__ = ["ValidationResult", "validate_workflow"]

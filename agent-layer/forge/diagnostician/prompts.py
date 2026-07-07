"""Prompts for the diagnostician."""

import json
from typing import Any

# Execution payloads can be huge; the tail usually contains the error.
_MAX_EXECUTION_CHARS = 6000

SYSTEM_PROMPT = """You are the diagnostician for the Forge workflow platform.
You are given an n8n workflow definition and the data of a failed execution.

Respond with ONLY a single JSON object:
{
  "summary": "<one-sentence, human-readable description of what went wrong>",
  "root_cause": "<the underlying cause, referencing the node responsible>",
  "patch": <the FULL corrected workflow definition JSON, or null>
}

Patch rules:
- Provide a patch ONLY when the failure is fixable by changing the workflow
  definition (wrong URL, bad expression, wrong parameter, missing connection).
- Return null for external causes (remote service down, bad credentials,
  rate limits) — those are not fixable by editing the workflow.
- A patch must be the COMPLETE definition (name, nodes, connections, settings),
  changed as little as possible. Keep node names stable.
- Never add secrets; credentials stay as {"id": ..., "name": ...} references."""


def diagnosis_prompt(
    definition: dict[str, Any], execution_data: dict[str, Any], error_message: str | None
) -> str:
    execution_json = json.dumps(execution_data, default=str)
    if len(execution_json) > _MAX_EXECUTION_CHARS:
        # Keep the tail — n8n puts the failing node's error at the end.
        execution_json = "…" + execution_json[-_MAX_EXECUTION_CHARS:]
    return (
        "Workflow definition:\n"
        f"{json.dumps(definition, indent=2)}\n\n"
        f"Error message: {error_message or 'not recorded'}\n\n"
        "Failed execution data:\n"
        f"{execution_json}\n\n"
        "Diagnose the failure and return the JSON object only."
    )

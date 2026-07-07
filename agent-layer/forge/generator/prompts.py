"""Prompt library for the workflow generator.

The system prompt is rendered from the node catalog (forge.nodes) so the
whitelist shown to the model and the whitelist enforced by the validator can
never drift apart. Few-shot examples pin the exact JSON shape n8n expects.
"""

import json

from forge.nodes import CATALOG


def _catalog_block() -> str:
    lines = []
    for template in CATALOG:
        marker = " [DESTRUCTIVE]" if template.destructive else ""
        lines.append(f"- {template.type}{marker}: {template.description}")
        lines.append(f"  example parameters: {json.dumps(template.example_parameters)}")
    return "\n".join(lines)


_EXAMPLE_INSTRUCTION = "Every morning, read my blog feed and email me new posts."

_EXAMPLE_WORKFLOW = {
    "name": "morning-blog-digest",
    "nodes": [
        {
            "name": "Every Morning",
            "type": "n8n-nodes-base.scheduleTrigger",
            "typeVersion": 1.2,
            "position": [0, 0],
            "parameters": {"rule": {"interval": [{"field": "days"}]}},
        },
        {
            "name": "Read Feed",
            "type": "n8n-nodes-base.rssFeedRead",
            "typeVersion": 1,
            "position": [220, 0],
            "parameters": {"url": "https://example.com/feed.xml"},
        },
        {
            "name": "Email Me",
            "type": "n8n-nodes-base.emailSend",
            "typeVersion": 2,
            "position": [440, 0],
            "parameters": {
                "toEmail": "me@example.com",
                "subject": "New blog posts",
                "text": "={{ $json.title }} — {{ $json.link }}",
            },
            "credentials": {"smtp": {"id": "1", "name": "SMTP account"}},
        },
    ],
    "connections": {
        "Every Morning": {"main": [[{"node": "Read Feed", "type": "main", "index": 0}]]},
        "Read Feed": {"main": [[{"node": "Email Me", "type": "main", "index": 0}]]},
    },
    "settings": {},
}


def system_prompt() -> str:
    return f"""You generate n8n workflow definitions for the Forge platform.

Output rules:
- Return ONLY a single JSON object — no prose, no markdown fences.
- Top-level keys: "name" (kebab-case string), "nodes" (list), "connections" (object), \
"settings" (object, may be empty).
- Every node needs: "name" (unique, human-readable), "type", "typeVersion", \
"position" ([x, y], left-to-right flow), "parameters".
- Connections use n8n's shape: {{"<source node name>": {{"main": [[{{"node": \
"<target node name>", "type": "main", "index": 0}}]]}}}}.
- Exactly one trigger node starts the workflow.
- Use ONLY these node types (anything else is rejected by the validator):

{_catalog_block()}

- NEVER put secrets (API keys, tokens, passwords) in parameters. Where a node needs
  auth, reference a credential by name: "credentials": {{"<type>": {{"id": "1", \
"name": "<descriptive name>"}}}}. The human wires up real credentials in n8n later.

Example.
Instruction: {_EXAMPLE_INSTRUCTION}
Output:
{json.dumps(_EXAMPLE_WORKFLOW, indent=2)}"""


def user_prompt(instruction: str, name: str | None) -> str:
    naming = f'Name the workflow "{name}".' if name else "Choose a short kebab-case name."
    return f"Instruction: {instruction}\n{naming}\nReturn only the JSON object."


def repair_prompt(instruction: str, name: str | None, errors: list[str]) -> str:
    """Second-attempt prompt: same task, plus what the validator rejected."""
    listing = "\n".join(f"- {error}" for error in errors)
    return (
        f"{user_prompt(instruction, name)}\n\n"
        f"Your previous attempt was rejected by the validator:\n{listing}\n"
        "Fix these problems and return the corrected JSON object only."
    )

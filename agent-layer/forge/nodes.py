"""Node template catalog: the n8n nodes Forge agents are allowed to use.

Shared by the generator (rendered into the LLM prompt) and the validator
(whitelist + destructive-action detection). Growing agent capabilities means
adding entries here — nowhere else.
"""

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class NodeTemplate:
    type: str
    label: str
    description: str
    # Destructive = has side effects outside Forge (sends messages, writes
    # to external systems). Destructive workflows need an explicit approval
    # flag before deploy (CLAUDE.md: never silently destructive).
    destructive: bool
    example_parameters: dict[str, Any]


CATALOG: tuple[NodeTemplate, ...] = (
    # ── triggers ─────────────────────────────────────────────────────────
    NodeTemplate(
        type="n8n-nodes-base.scheduleTrigger",
        label="Schedule trigger",
        description="Starts the workflow on a schedule (daily, hourly, cron).",
        destructive=False,
        example_parameters={"rule": {"interval": [{"field": "days"}]}},
    ),
    NodeTemplate(
        type="n8n-nodes-base.webhook",
        label="Webhook trigger",
        description="Starts the workflow when an HTTP request hits its URL.",
        destructive=False,
        example_parameters={"path": "my-hook", "httpMethod": "POST"},
    ),
    NodeTemplate(
        type="n8n-nodes-base.manualTrigger",
        label="Manual trigger",
        description="Starts the workflow only when triggered by hand.",
        destructive=False,
        example_parameters={},
    ),
    # ── data in / transform ──────────────────────────────────────────────
    NodeTemplate(
        type="n8n-nodes-base.httpRequest",
        label="HTTP request",
        description="Calls an HTTP API. GET/HEAD are reads; any other method "
        "is treated as destructive.",
        destructive=False,  # method-dependent — see is_destructive()
        example_parameters={"url": "https://api.example.com/items", "method": "GET"},
    ),
    NodeTemplate(
        type="n8n-nodes-base.rssFeedRead",
        label="RSS read",
        description="Reads entries from an RSS/Atom feed.",
        destructive=False,
        example_parameters={"url": "https://example.com/feed.xml"},
    ),
    NodeTemplate(
        type="n8n-nodes-base.set",
        label="Set fields",
        description="Sets or renames fields on items.",
        destructive=False,
        example_parameters={"assignments": {"assignments": []}},
    ),
    NodeTemplate(
        type="n8n-nodes-base.code",
        label="Code",
        description="Transforms items with a small JavaScript snippet.",
        destructive=False,
        example_parameters={"jsCode": "return items;"},
    ),
    NodeTemplate(
        type="n8n-nodes-base.if",
        label="If",
        description="Routes items down true/false branches on a condition.",
        destructive=False,
        example_parameters={"conditions": {"conditions": []}},
    ),
    NodeTemplate(
        type="n8n-nodes-base.filter",
        label="Filter",
        description="Drops items that don't match a condition.",
        destructive=False,
        example_parameters={"conditions": {"conditions": []}},
    ),
    NodeTemplate(
        type="n8n-nodes-base.merge",
        label="Merge",
        description="Combines items from two branches.",
        destructive=False,
        example_parameters={"mode": "append"},
    ),
    NodeTemplate(
        type="n8n-nodes-base.splitInBatches",
        label="Loop over items",
        description="Processes items in batches (loops).",
        destructive=False,
        example_parameters={"batchSize": 10},
    ),
    NodeTemplate(
        type="n8n-nodes-base.noOp",
        label="No-op",
        description="Does nothing; useful as a branch terminator.",
        destructive=False,
        example_parameters={},
    ),
    # ── outbound / side effects ──────────────────────────────────────────
    NodeTemplate(
        type="n8n-nodes-base.emailSend",
        label="Send email",
        description="Sends an email via SMTP.",
        destructive=True,
        example_parameters={"toEmail": "me@example.com", "subject": "…", "text": "…"},
    ),
    NodeTemplate(
        type="n8n-nodes-base.slack",
        label="Slack",
        description="Posts a message to Slack.",
        destructive=True,
        example_parameters={"channel": "#alerts", "text": "…"},
    ),
    NodeTemplate(
        type="n8n-nodes-base.gmail",
        label="Gmail",
        description="Sends or drafts email via Gmail.",
        destructive=True,
        example_parameters={"operation": "send"},
    ),
)

ALLOWED_TYPES: frozenset[str] = frozenset(t.type for t in CATALOG)
_ALWAYS_DESTRUCTIVE: frozenset[str] = frozenset(
    t.type for t in CATALOG if t.destructive
)

# HTTP methods that only read; anything else mutates the remote system.
_SAFE_HTTP_METHODS = {"GET", "HEAD", ""}


def is_destructive(node: dict[str, Any]) -> bool:
    """Whether a single node has external side effects."""
    node_type = str(node.get("type", ""))
    if node_type in _ALWAYS_DESTRUCTIVE:
        return True
    if node_type == "n8n-nodes-base.httpRequest":
        method = str(node.get("parameters", {}).get("method", "GET")).upper()
        return method not in _SAFE_HTTP_METHODS
    return False

"""Risk classifier for proposed patches — the rubric lives in ADR-004.

A patch is compared against the currently deployed definition. LOW risk means
the diagnostician may auto-apply it (with the registry's versioning + audit);
anything HIGH parks as an incident awaiting human approval.

The rules are deliberately mechanical and conservative: they measure the
*shape* of the change, never trusting the LLM's own confidence claims.
"""

from dataclasses import dataclass
from typing import Any

from forge.nodes import is_destructive

# Node types that start a workflow; swapping how a workflow triggers changes
# when side effects happen, which a human should sign off on.
_TRIGGER_TYPES = {
    "n8n-nodes-base.scheduleTrigger",
    "n8n-nodes-base.webhook",
    "n8n-nodes-base.manualTrigger",
}

# More than this many added+removed nodes = a rewrite, not a repair.
_MAX_STRUCTURAL_DELTA = 2

LOW = "low"
HIGH = "high"


@dataclass(frozen=True)
class RiskAssessment:
    level: str  # LOW | HIGH
    reasons: list[str]

    @property
    def auto_applicable(self) -> bool:
        return self.level == LOW


def assess_patch(old: dict[str, Any], new: dict[str, Any]) -> RiskAssessment:
    """Classify a patch (assumed already validator-clean) as LOW or HIGH risk."""
    reasons: list[str] = []
    old_nodes = _nodes_by_name(old)
    new_nodes = _nodes_by_name(new)

    # Rule 1: new or newly-destructive side effects.
    old_destructive = {name for name, node in old_nodes.items() if is_destructive(node)}
    new_destructive = {name for name, node in new_nodes.items() if is_destructive(node)}
    added_destructive = new_destructive - old_destructive
    if added_destructive:
        reasons.append(
            "introduces destructive behavior in node(s): " + ", ".join(sorted(added_destructive))
        )

    # Rule 2: trigger change (what starts the workflow).
    old_triggers = {n["type"] for n in old_nodes.values() if n.get("type") in _TRIGGER_TYPES}
    new_triggers = {n["type"] for n in new_nodes.values() if n.get("type") in _TRIGGER_TYPES}
    if old_triggers != new_triggers:
        reasons.append(f"changes the trigger ({sorted(old_triggers)} → {sorted(new_triggers)})")

    # Rule 3: structural rewrite.
    added = set(new_nodes) - set(old_nodes)
    removed = set(old_nodes) - set(new_nodes)
    if len(added) + len(removed) > _MAX_STRUCTURAL_DELTA:
        reasons.append(
            f"restructures the workflow ({len(added)} node(s) added, {len(removed)} removed)"
        )

    # Rule 4: credential changes (who the workflow acts as).
    for name in set(old_nodes) & set(new_nodes):
        if old_nodes[name].get("credentials") != new_nodes[name].get("credentials"):
            reasons.append(f"changes credentials on node {name!r}")
    for name in added:
        if new_nodes[name].get("credentials"):
            reasons.append(f"adds a node with credentials: {name!r}")

    if reasons:
        return RiskAssessment(level=HIGH, reasons=reasons)
    return RiskAssessment(level=LOW, reasons=["parameter-level changes only"])


def _nodes_by_name(definition: dict[str, Any]) -> dict[str, dict[str, Any]]:
    nodes = definition.get("nodes", [])
    return {
        str(node.get("name")): node for node in nodes if isinstance(node, dict) and node.get("name")
    }

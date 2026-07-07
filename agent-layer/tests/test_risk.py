"""Tests for the patch risk classifier (rubric: ADR-004)."""

from forge.diagnostician import assess_patch

BASE = {
    "name": "digest",
    "nodes": [
        {
            "name": "Cron",
            "type": "n8n-nodes-base.scheduleTrigger",
            "parameters": {"rule": {"interval": [{"field": "days"}]}},
        },
        {
            "name": "Fetch",
            "type": "n8n-nodes-base.httpRequest",
            "parameters": {"url": "https://old.example.com", "method": "GET"},
        },
        {
            "name": "Mail",
            "type": "n8n-nodes-base.emailSend",
            "parameters": {"toEmail": "me@example.com"},
            "credentials": {"smtp": {"id": "1", "name": "SMTP account"}},
        },
    ],
    "connections": {
        "Cron": {"main": [[{"node": "Fetch", "type": "main", "index": 0}]]},
        "Fetch": {"main": [[{"node": "Mail", "type": "main", "index": 0}]]},
    },
    "settings": {},
}


def patched(**node_overrides) -> dict:
    """Copy BASE, replacing named nodes (None = remove) or adding new ones."""
    nodes = []
    for node in BASE["nodes"]:
        override = node_overrides.pop(node["name"], "keep")
        if override == "keep":
            nodes.append(node)
        elif override is not None:
            nodes.append(override)
    nodes.extend(v for v in node_overrides.values() if v is not None)
    return {**BASE, "nodes": nodes}


class TestLowRisk:
    def test_parameter_tweak_is_low(self):
        fix = patched(
            Fetch={
                "name": "Fetch",
                "type": "n8n-nodes-base.httpRequest",
                "parameters": {"url": "https://new.example.com", "method": "GET"},
            }
        )
        assessment = assess_patch(BASE, fix)
        assert assessment.level == "low"
        assert assessment.auto_applicable

    def test_identical_definition_is_low(self):
        assert assess_patch(BASE, BASE).level == "low"

    def test_adding_one_safe_node_is_low(self):
        fix = patched(
            Filter={
                "name": "Filter",
                "type": "n8n-nodes-base.filter",
                "parameters": {"conditions": {"conditions": []}},
            }
        )
        assert assess_patch(BASE, fix).level == "low"

    def test_existing_destructive_node_does_not_make_patch_high(self):
        # BASE already sends email; keeping that node is not "new" destruction.
        assert assess_patch(BASE, patched()).level == "low"


class TestHighRisk:
    def test_new_destructive_node_is_high(self):
        fix = patched(
            Slack={
                "name": "Slack",
                "type": "n8n-nodes-base.slack",
                "parameters": {"channel": "#x", "text": "y"},
            }
        )
        assessment = assess_patch(BASE, fix)
        assert assessment.level == "high"
        assert any("destructive" in reason for reason in assessment.reasons)

    def test_get_becoming_post_is_high(self):
        fix = patched(
            Fetch={
                "name": "Fetch",
                "type": "n8n-nodes-base.httpRequest",
                "parameters": {"url": "https://old.example.com", "method": "POST"},
            }
        )
        assessment = assess_patch(BASE, fix)
        assert assessment.level == "high"
        assert any("Fetch" in reason for reason in assessment.reasons)

    def test_trigger_change_is_high(self):
        fix = patched(
            Cron={
                "name": "Cron",
                "type": "n8n-nodes-base.webhook",
                "parameters": {"path": "hook"},
            }
        )
        assessment = assess_patch(BASE, fix)
        assert any("trigger" in reason for reason in assessment.reasons)

    def test_structural_rewrite_is_high(self):
        fix = patched(
            Fetch=None,
            Mail=None,
            A={"name": "A", "type": "n8n-nodes-base.set", "parameters": {}},
            B={"name": "B", "type": "n8n-nodes-base.set", "parameters": {}},
        )
        assessment = assess_patch(BASE, fix)
        assert any("restructures" in reason for reason in assessment.reasons)

    def test_credential_change_is_high(self):
        fix = patched(
            Mail={
                "name": "Mail",
                "type": "n8n-nodes-base.emailSend",
                "parameters": {"toEmail": "me@example.com"},
                "credentials": {"smtp": {"id": "9", "name": "Other account"}},
            }
        )
        assessment = assess_patch(BASE, fix)
        assert any("credentials" in reason for reason in assessment.reasons)

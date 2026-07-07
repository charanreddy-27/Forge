"""Unit tests for the workflow validator."""

from forge.validator import validate_workflow

VALID = {
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
            "parameters": {"url": "https://example.com", "method": "GET"},
        },
    ],
    "connections": {"Cron": {"main": [[{"node": "Fetch", "type": "main", "index": 0}]]}},
    "settings": {},
}


def test_valid_workflow_passes():
    result = validate_workflow(VALID)
    assert result.valid
    assert not result.destructive


class TestSchema:
    def test_rejects_non_object(self):
        assert not validate_workflow([1, 2]).valid
        assert not validate_workflow("nope").valid

    def test_requires_name_and_nodes(self):
        result = validate_workflow({"nodes": [], "connections": {}})
        assert "'name' must be a non-empty string" in result.errors
        assert "'nodes' must be a non-empty list" in result.errors

    def test_rejects_duplicate_node_names(self):
        definition = {
            "name": "x",
            "nodes": [
                {"name": "A", "type": "n8n-nodes-base.noOp"},
                {"name": "A", "type": "n8n-nodes-base.noOp"},
            ],
            "connections": {},
        }
        result = validate_workflow(definition)
        assert any("duplicate node name" in error for error in result.errors)


class TestWhitelist:
    def test_rejects_unknown_node_type(self):
        definition = {
            "name": "x",
            "nodes": [{"name": "Shell", "type": "n8n-nodes-base.executeCommand"}],
            "connections": {},
        }
        result = validate_workflow(definition)
        assert any("not in the allowed node catalog" in error for error in result.errors)


class TestConnections:
    def test_rejects_unknown_source_and_target(self):
        definition = {
            **VALID,
            "connections": {
                "Ghost": {"main": [[{"node": "Fetch", "type": "main", "index": 0}]]},
                "Cron": {"main": [[{"node": "Nowhere", "type": "main", "index": 0}]]},
            },
        }
        result = validate_workflow(definition)
        assert any("unknown source node 'Ghost'" in error for error in result.errors)
        assert any("unknown target node 'Nowhere'" in error for error in result.errors)


class TestCredentials:
    def test_accepts_credential_references(self):
        definition = {
            "name": "x",
            "nodes": [
                {
                    "name": "Mail",
                    "type": "n8n-nodes-base.emailSend",
                    "parameters": {"toEmail": "me@example.com"},
                    "credentials": {"smtp": {"id": "1", "name": "SMTP account"}},
                }
            ],
            "connections": {},
        }
        assert validate_workflow(definition).valid

    def test_rejects_inline_credential_material(self):
        definition = {
            "name": "x",
            "nodes": [
                {
                    "name": "Mail",
                    "type": "n8n-nodes-base.emailSend",
                    "credentials": {"smtp": {"user": "me", "password": "hunter2"}},
                }
            ],
            "connections": {},
        }
        result = validate_workflow(definition)
        assert any("never inline secret material" in error for error in result.errors)

    def test_rejects_secrets_in_parameters(self):
        definition = {
            "name": "x",
            "nodes": [
                {
                    "name": "Fetch",
                    "type": "n8n-nodes-base.httpRequest",
                    "parameters": {
                        "url": "https://api.example.com",
                        "headers": {"Authorization": "Bearer sk-live-abc123"},
                    },
                }
            ],
            "connections": {},
        }
        result = validate_workflow(definition)
        assert any("inline secret" in error for error in result.errors)


class TestDestructive:
    def test_email_and_slack_are_destructive(self):
        definition = {
            "name": "x",
            "nodes": [
                {"name": "Mail", "type": "n8n-nodes-base.emailSend", "parameters": {}},
                {"name": "Slack", "type": "n8n-nodes-base.slack", "parameters": {}},
            ],
            "connections": {},
        }
        result = validate_workflow(definition)
        assert result.valid
        assert result.destructive_nodes == ["Mail", "Slack"]

    def test_http_get_is_safe_but_post_is_destructive(self):
        get_node = {
            "name": "Read",
            "type": "n8n-nodes-base.httpRequest",
            "parameters": {"url": "https://x", "method": "GET"},
        }
        post_node = {
            "name": "Write",
            "type": "n8n-nodes-base.httpRequest",
            "parameters": {"url": "https://x", "method": "POST"},
        }
        result = validate_workflow({"name": "x", "nodes": [get_node, post_node], "connections": {}})
        assert result.destructive_nodes == ["Write"]

    def test_http_without_method_defaults_to_safe_get(self):
        node = {
            "name": "Read",
            "type": "n8n-nodes-base.httpRequest",
            "parameters": {"url": "https://x"},
        }
        assert not validate_workflow({"name": "x", "nodes": [node], "connections": {}}).destructive

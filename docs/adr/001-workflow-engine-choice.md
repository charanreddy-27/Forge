# ADR-001: n8n as the workflow execution engine

**Status:** Accepted — 2026-07-07 (Phase 1)

## Context

Forge needs an execution backbone for automations: scheduling, triggers, hundreds of pre-built integrations (email, HTTP, Slack, RSS, …), retry semantics, and execution logs. Building this ourselves is months of undifferentiated work — Forge's differentiator is the *agent layer* that generates, validates, monitors, and repairs workflows, not the executor.

Options considered:

1. **n8n (self-hosted)** — mature node-based engine, official Docker image, a public REST API covering the full workflow lifecycle (create/update/activate/delete/executions), workflow definitions are plain JSON.
2. **Apache Airflow** — DAGs are Python code, not data. Having an LLM generate and hot-deploy executable Python is a far larger validation/sandboxing problem than validating JSON, and Airflow targets batch data pipelines, not event-driven personal automations.
3. **Temporal** — excellent durability, but workflows are compiled code; same generate-code problem as Airflow, plus heavier operational footprint.
4. **Custom engine** — full control, zero integrations, and we'd spend every phase building the executor instead of the agents.

## Decision

Use **self-hosted n8n** (official Docker image) as the workflow engine, managed **exclusively via its public REST API**.

Two guardrails make this safe:

- **JSON-as-data**: n8n workflow definitions are declarative JSON — ideal LLM output, statically validatable before anything executes (node whitelist, connection checks, destructive-action flags in Phase 3).
- **Swappability**: no n8n-specific logic outside the `engine_adapter` module (Phase 2). The registry stores generic `engine_workflow_id` / `engine_execution_id` strings; if n8n becomes a liability, only the adapter is rewritten.

n8n shares the Postgres instance (its own `n8n` schema) to keep the local stack to one database.

## Consequences

- ✅ Hundreds of integrations and a battle-tested executor for free; the project's effort goes into the agent layer.
- ✅ LLM output is validatable data, not executable code.
- ✅ Every workflow version is a JSON blob in `workflow_versions` — diffable, rollbackable, auditable.
- ⚠️ We depend on the stability of n8n's REST API and workflow schema; version upgrades need adapter regression tests (mocked n8n API tests in Phase 2).
- ⚠️ n8n's node schema is large and evolves — the Phase 3 validator needs a maintained node whitelist rather than trying to validate the entire schema.
- ⚠️ The n8n API key is a powerful credential; it lives only in `.env` and is never logged.

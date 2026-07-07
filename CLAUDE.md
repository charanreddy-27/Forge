# Forge — Personal AI Operations Platform

You are helping me build **Forge** — a self-hosted AI operations platform where all my automations live as managed workflows, and an LLM agent layer can CREATE, DEPLOY, MONITOR, and REPAIR those workflows autonomously.

## Core concept

Not just workflow orchestration (n8n already does that). The differentiator: an agent layer that takes natural-language instructions like "create a workflow that watches for ML job postings daily and drafts cold emails" and generates a valid workflow definition, validates it, deploys it to the engine, and monitors its runs. When a run fails, a diagnostic agent inspects logs and either auto-repairs the workflow or files a human-readable incident report.

## Architecture (high level)

1. **Workflow Engine** — self-hosted n8n instance (Docker) as the execution backbone. All workflows are managed via n8n's REST API, never hand-edited in the UI.
2. **Agent Layer (FastAPI, Python)** — the brain. Services:
   - `workflow-generator`: NL instruction → n8n workflow JSON (LLM-generated, schema-validated before deploy)
   - `workflow-validator`: static validation of generated JSON (node types exist, connections valid, credentials referenced correctly, no destructive actions without approval flag)
   - `run-monitor`: polls/webhooks n8n execution results, stores run history
   - `diagnostician`: on failure, pulls execution logs + workflow definition, produces root-cause analysis, proposes a patch; patches above a risk threshold require human approval
3. **Data Layer** — PostgreSQL: workflows registry (versioned), runs, incidents, LLM call log (tokens, cost, latency per call), audit trail of every agent action.
4. **Dashboard (Next.js 14, Tailwind)** — workflow list with health status, run timeline, incident feed, LLM cost breakdown, and a chat box to instruct the agent layer.
5. **LLM Gateway** — single module through which ALL LLM calls pass. Supports Anthropic API + local Ollama fallback. Logs every call (model, tokens, cost, purpose, latency) to Postgres. Retries with exponential backoff.

## Tech stack (do not deviate without asking)

- Python 3.11+, FastAPI, Pydantic v2, SQLAlchemy 2.0, Alembic for migrations
- PostgreSQL 16, Redis (job queue + caching)
- Next.js 14 (App Router), TypeScript, Tailwind
- Docker Compose for local; every service has its own Dockerfile
- n8n self-hosted (official Docker image), managed exclusively via its public REST API

## Scalability requirements (design for these from day one)

- Agent layer is stateless — all state in Postgres/Redis, so services can scale horizontally later
- Workflow generation runs as background jobs (Redis queue + worker), never blocking API requests
- LLM Gateway enforces per-service rate limits and a daily cost budget (config-driven, hard stop)
- Every workflow definition is versioned; rollback to any previous version must be one API call
- Clean separation: engine (n8n) is swappable — no n8n-specific logic outside an `engine_adapter` module

## Documentation requirements (non-negotiable, maintain as you build)

- `/docs/architecture.md` — system diagram (mermaid), component responsibilities, data flow. Update whenever a component changes.
- `/docs/adr/` — Architecture Decision Records. One numbered file per significant decision (why n8n, why Redis queue, why this agent design). Format: Context, Decision, Consequences.
- `/docs/api.md` — auto-generated OpenAPI reference + curl usage examples for every endpoint
- `/docs/runbook.md` — how to start, stop, backup, restore, and debug the platform
- `README.md` — project vision, quickstart (one command: `docker compose up`), screenshots
- Every module gets docstrings; every non-obvious function gets a "why" comment, not a "what" comment
- After completing each phase, update the docs BEFORE writing new feature code

## Engineering conventions

- Type hints everywhere; mypy must pass. Ruff for linting, Black for formatting.
- Tests with pytest: every agent-layer service needs unit tests; workflow-generator needs golden-file tests (known instruction → expected workflow structure)
- Conventional commits (feat:, fix:, docs:, refactor:)
- No secrets in code. `.env` + `.env.example` always in sync.
- Agent actions are NEVER silently destructive: deleting or overwriting a workflow always creates a versioned backup first and writes to the audit trail.

## What NOT to do

- Do not build everything at once. Work only on the current phase.
- Do not mock the LLM Gateway with fake responses in production code paths — mocks live only in tests.
- Do not add features I didn't ask for. If you see something important missing, propose it in one sentence and wait.

## Phase roadmap

1. **Foundation** — monorepo, docker-compose (Postgres, Redis, n8n, FastAPI skeleton), DB models + migrations, LLM Gateway (Anthropic + cost logging + budget), architecture.md, ADR-001. ✅
2. **Engine adapter + workflow registry** — n8n REST wrapper, versioned deploys, one-call rollback, ADR-002. ✅
3. **Workflow generator agent** — NL → n8n JSON via gateway, validator, Redis-queued jobs, golden-file tests, ADR-003.
4. **Run monitor + diagnostician** — execution ingest, health computation, root-cause analysis + patch proposals, risk rubric in ADR-004.
5. **Dashboard** — Next.js UI: workflow list, run timeline, incident feed, cost chart, chat panel.
6. **Hardening & scale** — rate limiting, backups, structured logging, load test, ADR-005.

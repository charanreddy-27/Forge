# Forge

**A self-hosted AI operations platform.** All your automations live as managed workflows on n8n, and an LLM agent layer can **create, deploy, monitor, and repair** those workflows autonomously.

Tell it *"watch for ML job postings daily and draft cold emails"* — the agent layer generates a valid workflow definition, validates it, deploys it to the engine, and watches its runs. When a run fails, a diagnostic agent inspects the logs and either auto-repairs the workflow or files a human-readable incident report.

## Why this isn't just n8n

n8n executes workflows. Forge adds the brain on top:

- **Workflow generator** — natural language → schema-validated n8n workflow JSON (never hand-edited in the UI)
- **Versioned registry** — every deploy is an immutable version; rollback is one API call
- **Run monitor + diagnostician** — failures get a root-cause analysis and a proposed patch; risky patches wait for your approval
- **LLM Gateway** — every LLM call goes through one module with cost logging, a hard daily budget, retries, and a local Ollama fallback
- **Audit trail** — no agent action is ever silently destructive

## Quickstart

```bash
cp .env.example .env      # add your ANTHROPIC_API_KEY
docker compose up -d
```

That's it. Then:

- Agent layer API: http://localhost:8000 (docs at `/docs`, health at `/health`)
- n8n UI: http://localhost:5678

## Architecture

Postgres 16 (state) · Redis 7 (job queue) · n8n (execution engine) · FastAPI agent layer (stateless brain) · Next.js dashboard (coming in Phase 5).

See [docs/architecture.md](docs/architecture.md) for the system diagram and data flow, [docs/adr/](docs/adr/) for design decisions, [docs/runbook.md](docs/runbook.md) for operations, and [docs/api.md](docs/api.md) for the API reference.

## Status

| Phase | Scope | Status |
|---|---|---|
| 1 — Foundation | Compose stack, DB schema + migrations, LLM Gateway (cost log + budget + retries + fallback) | ✅ |
| 2 — Engine adapter + registry | n8n REST wrapper, versioned deploys, one-call rollback | ⏳ |
| 3 — Workflow generator | NL → validated workflow JSON as background jobs | ⏳ |
| 4 — Run monitor + diagnostician | Health tracking, root-cause analysis, auto-repair with approval gates | ⏳ |
| 5 — Dashboard | Next.js UI: workflows, runs, incidents, costs, chat | ⏳ |
| 6 — Hardening & scale | Rate limits, backups, structured logging, load tests | ⏳ |

## Development

```bash
cd agent-layer
python3 -m venv .venv && .venv/bin/pip install -e ".[dev]"
.venv/bin/pytest -q                 # tests
.venv/bin/ruff check forge tests    # lint
.venv/bin/black forge tests         # format
.venv/bin/mypy forge                # types
```

Conventional commits (`feat:`, `fix:`, `docs:`, `refactor:`). No secrets in code — `.env` and `.env.example` stay in sync.

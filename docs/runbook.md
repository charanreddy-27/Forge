# Forge Runbook

How to start, stop, back up, restore, and debug the platform.

## Start

```bash
cp .env.example .env          # first time only; fill in ANTHROPIC_API_KEY
docker compose up -d
```

Wait for health:

```bash
docker compose ps                       # all services should be "healthy"
curl -s localhost:8000/health | jq      # {"status":"ok","database":true,"redis":true}
```

Service endpoints:

| Service | URL |
|---|---|
| Agent layer API | http://localhost:8000 (OpenAPI docs at `/docs`) |
| n8n UI | http://localhost:5678 |
| Postgres | localhost:5432 (`forge`/`forge`, db `forge`) |
| Redis | localhost:6379 |

Migrations run automatically when the agent-layer container starts (`alembic upgrade head`).

## Stop

```bash
docker compose down          # keep data volumes
docker compose down -v       # ⚠️ destroys ALL data (Postgres, Redis, n8n)
```

## Backup

Everything that matters lives in Postgres (Forge tables in `public`, n8n state in the `n8n` schema):

```bash
docker compose exec postgres pg_dump -U forge -d forge -Fc > forge-$(date +%F).dump
```

## Restore

```bash
docker compose up -d postgres
docker compose exec -T postgres pg_restore -U forge -d forge --clean --if-exists < forge-YYYY-MM-DD.dump
docker compose up -d
```

## Debug

**Logs**

```bash
docker compose logs -f agent-layer
docker compose logs -f n8n
```

**Health says "degraded"** — the JSON body tells you which dependency failed (`database` / `redis`). Check that container's logs and health status.

**LLM calls failing**

- `BudgetExceededError`: today's spend hit `LLM_DAILY_BUDGET_USD`. Inspect spend:
  ```bash
  docker compose exec postgres psql -U forge -d forge -c \
    "SELECT service, count(*), sum(cost_usd) FROM llm_calls WHERE created_at >= date_trunc('day', now() AT TIME ZONE 'utc') GROUP BY service;"
  ```
  Raise the budget in `.env` and `docker compose up -d agent-layer`, or wait for UTC midnight.
- `LLMUnavailableError`: Anthropic was unreachable after retries. Check `ANTHROPIC_API_KEY`, network, or enable the Ollama fallback (`OLLAMA_ENABLED=true`).
- Every call, including failures, is logged in `llm_calls` — that table is the first place to look.

**Migrations**

```bash
# Current revision
docker compose exec agent-layer alembic current
# Apply manually (normally automatic on start)
docker compose exec agent-layer alembic upgrade head
```

**Run tests / linters locally** (from `agent-layer/`):

```bash
python3 -m venv .venv && .venv/bin/pip install -e ".[dev]"
.venv/bin/pytest -q
.venv/bin/ruff check forge tests && .venv/bin/black --check forge tests && .venv/bin/mypy forge
```

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

Everything that matters lives in Postgres (Forge tables in `public`, n8n state in the `n8n` schema). Use the script — it dumps, timestamps, and rotates:

```bash
scripts/backup.sh                    # → backups/forge-<stamp>.dump, keeps newest 14
KEEP=30 BACKUP_DIR=/mnt/nas scripts/backup.sh   # custom retention/location
```

Cron it (daily at 03:00): `0 3 * * * cd /path/to/forge && scripts/backup.sh >> backups/backup.log 2>&1`

## Restore

```bash
scripts/restore.sh backups/forge-<stamp>.dump
```

The script stops the writers (agent layer, workers, n8n, dashboard), restores into Postgres with `--clean`, then brings the stack back up (migrations re-run automatically on agent-layer start).

## Debug

**Logs**

```bash
docker compose logs -f agent-layer
docker compose logs -f generation-worker
docker compose logs -f run-monitor
docker compose logs -f n8n
```

**Generation jobs stuck in `queued`** — the worker isn't consuming. Check `docker compose ps generation-worker` and its logs; restart with `docker compose restart generation-worker`. Jobs stuck in `running` mean the worker died mid-job (state is in Redis with a 24h TTL) — re-submit the instruction.

**Job landed in `requires_approval`** — the generated workflow contains destructive nodes (email/Slack/non-GET HTTP) and the request didn't set `allow_destructive`. Either re-submit with `"allow_destructive": true`, or take `result.definition` from the job and deploy it yourself via `POST /workflows`.

## Failure handling (run monitor + diagnostician)

The `run-monitor` service polls n8n every `MONITOR_POLL_SECONDS` (default 60), mirrors executions into the `runs` table, and hands each *newly failed* run to the diagnostician. The diagnostician's outcome is always an incident:

| Incident state | Meaning | Your move |
|---|---|---|
| `resolved`, severity `low` | Patch was LOW-risk (ADR-004) and auto-applied as a new workflow version | Nothing — check `GET /workflows/{id}/versions` if curious; roll back with one call if the repair was wrong |
| `awaiting_approval`, severity `high` | Patch proposed but HIGH-risk; **not** applied | Review `proposed_patch`, then `POST /incidents/{id}/approve` or `.../dismiss` |
| `open` | No usable patch (external cause, or the patch failed validation) | Read `summary`/`root_cause`; fix externally or redeploy manually |

Useful commands:

```bash
# What needs my attention?
curl -s 'localhost:8000/incidents?status=awaiting_approval' | jq '.[] | {id, summary}'

# Approve / dismiss a patch
curl -s -X POST localhost:8000/incidents/$ID/approve -H 'Content-Type: application/json' -d '{"actor": "human:me"}'
curl -s -X POST localhost:8000/incidents/$ID/dismiss

# Check a workflow's health / recent runs
curl -s localhost:8000/workflows/$WF/health | jq
curl -s localhost:8000/workflows/$WF/runs | jq '.[0]'

# Force an immediate sync instead of waiting for the poller
curl -s -X POST localhost:8000/monitor/sync | jq
```

**Auto-repair applied a bad patch?** It's a normal version — `POST /workflows/{id}/rollback {"target_version": N}` undoes it, and the audit trail shows the diagnostician's deploy. Set `DIAGNOSTICIAN_AUTO_APPLY=false` to make every patch wait for approval.

**Same failure keeps re-opening incidents?** Diagnosis is idempotent per run (one unresolved incident per run), but each *new* failed run gets its own diagnosis. Deactivate the workflow (`POST /workflows/{id}/deactivate`) while you investigate to stop the bleeding — and the LLM spend.

**Health says "degraded"** — the JSON body tells you which dependency failed (`database` / `redis`). Check that container's logs and health status.

**LLM calls failing**

- `BudgetExceededError`: today's spend hit `LLM_DAILY_BUDGET_USD`. Inspect spend:
  ```bash
  docker compose exec postgres psql -U forge -d forge -c \
    "SELECT service, count(*), sum(cost_usd) FROM llm_calls WHERE created_at >= date_trunc('day', now() AT TIME ZONE 'utc') GROUP BY service;"
  ```
  Raise the budget in `.env` and `docker compose up -d agent-layer`, or wait for UTC midnight.
- `LLMUnavailableError`: Anthropic was unreachable after retries. Check `ANTHROPIC_API_KEY`, network, or enable the Ollama fallback (`OLLAMA_ENABLED=true`).
- `RateLimitedError`: a service exceeded `LLM_RATE_LIMIT_PER_MINUTE` (default 20/min per service). Unlike the budget, this clears by itself within 60s. Raise the limit in `.env` if it's genuinely too tight; `0` disables it.
- Every call, including refusals (`error` prefixed `refused:`), is logged in `llm_calls` — that table is the first place to look.

**Logs are structured JSON** (one object per line: `ts`, `level`, `logger`, `message`, `exception`). Grep-friendly:

```bash
docker compose logs --no-log-prefix run-monitor | jq -r 'select(.level=="error") | .message' 2>/dev/null
```

Set `LOG_FORMAT=text` in `.env` for human-readable output during local debugging.

## Load testing

`loadtest/locustfile.py` replays dashboard-shaped read traffic (health, lists, costs, drill-downs). Against a running stack:

```bash
pip install locust
locust -f loadtest/locustfile.py --host http://localhost:8000 --headless -u 20 -r 5 -t 30s
```

Baseline on a dev laptop (SQLite-backed demo API, 20 users): aggregate p50 ≈ 4 ms, p95 ≈ 19 ms at ~38 req/s. Note `/health` returns 503 (by design) whenever Redis or Postgres is down — a wall of 503s in the report means a dependency is missing, not that the API is slow. To also exercise the write path (enqueues real generation jobs): `LOADTEST_SUBMIT=1 locust ...` — keep the generation worker stopped unless you intend to spend LLM budget. Re-run before/after scaling changes; the growth path is ADR-005.

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

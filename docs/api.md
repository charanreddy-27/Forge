# Forge API Reference

The agent layer serves an auto-generated OpenAPI reference at:

- **Swagger UI:** http://localhost:8000/docs
- **Raw schema:** http://localhost:8000/openapi.json

This file lists every endpoint with a curl example. It grows with each phase.

## Endpoints (Phase 1)

### `GET /health`

Liveness + dependency check. Used as the Docker healthcheck.

```bash
curl -s localhost:8000/health | jq
```

Response `200` when everything is up:

```json
{
  "status": "ok",
  "version": "0.1.0",
  "database": true,
  "redis": true
}
```

Response `503` with `"status": "degraded"` when Postgres or Redis is unreachable; the boolean fields identify the failing dependency.

## Workflow registry (Phase 2)

Domain errors map to HTTP consistently: unknown workflow/version → `404`, engine unreachable or rejecting a request → `502`.

### `GET /workflows` — list all workflows

```bash
curl -s localhost:8000/workflows | jq
```

### `POST /workflows` — create + deploy version 1

```bash
curl -s -X POST localhost:8000/workflows \
  -H 'Content-Type: application/json' \
  -d '{
    "name": "daily-digest",
    "definition": {"name": "daily-digest", "nodes": [], "connections": {}, "settings": {}},
    "comment": "first deploy"
  }' | jq
```

Returns `201` with the workflow, including its `id`, `engine_workflow_id`, and `current_version: 1`. Status is `inactive` until activated.

### `GET /workflows/{id}` — one workflow

```bash
curl -s localhost:8000/workflows/$ID | jq
```

### `PUT /workflows/{id}` — deploy a new version

Same body as `POST /workflows`; appends the next version and updates the engine.

```bash
curl -s -X PUT localhost:8000/workflows/$ID \
  -H 'Content-Type: application/json' \
  -d '{"name": "daily-digest", "definition": {...}, "comment": "add http node"}' | jq
```

### `GET /workflows/{id}/versions` — full version history (newest first)

```bash
curl -s localhost:8000/workflows/$ID/versions | jq '.[] | {version, created_by, comment}'
```

### `POST /workflows/{id}/rollback` — one-call rollback

Redeploys the target version's definition as a **new** version (roll-forward, see ADR-002).

```bash
curl -s -X POST localhost:8000/workflows/$ID/rollback \
  -H 'Content-Type: application/json' \
  -d '{"target_version": 1}' | jq
```

### `POST /workflows/{id}/activate` / `POST /workflows/{id}/deactivate`

```bash
curl -s -X POST localhost:8000/workflows/$ID/activate | jq .status
```

### `DELETE /workflows/{id}` — delete from the engine

Snapshots the engine's live definition as a `pre-delete backup` version first; registry history is kept. Returns `204`.

```bash
curl -s -X DELETE localhost:8000/workflows/$ID -o /dev/null -w '%{http_code}\n'
```

## Workflow generation (Phase 3)

Generation runs on the background worker via the Redis queue — the API returns immediately.

### `POST /generate` — submit an instruction (202)

```bash
curl -s -X POST localhost:8000/generate \
  -H 'Content-Type: application/json' \
  -d '{
    "instruction": "Watch for ML job postings on my RSS feed every morning and email me a digest",
    "deploy": true,
    "allow_destructive": false
  }' | jq
# → {"job_id": "9f2c...", "status": "queued"}
```

Request fields: `instruction` (required), `name` (optional workflow name), `deploy` (deploy to the engine on success, default `false`), `allow_destructive` (approval flag for workflows with side-effect nodes, default `false`), `actor`.

### `GET /generate/{job_id}` — poll the job

```bash
curl -s localhost:8000/generate/$JOB_ID | jq '{status, result: .result.validation}'
```

Job statuses:

| Status | Meaning |
|---|---|
| `queued` / `running` | Waiting for / being processed by the worker |
| `succeeded` | Valid definition; `result.workflow_id` present if `deploy` was set |
| `requires_approval` | Valid but contains destructive nodes and `allow_destructive` was false — definition stored on the job, **not** deployed; `result.reason` explains |
| `failed` | Still invalid after the repair round — `result.validation.errors` lists why |

Jobs expire from Redis after 24 hours; anything durable lives in the registry.

## Runs, health & incidents (Phase 4)

### `GET /workflows/{id}/runs` — execution history (newest first)

```bash
curl -s "localhost:8000/workflows/$ID/runs?limit=20" | jq '.[] | {status, started_at}'
```

### `GET /workflows/{id}/health` — computed health

```bash
curl -s localhost:8000/workflows/$ID/health | jq
# {"status": "failing", "success_rate": 0.4, "consecutive_failures": 3, ...}
```

`status` is one of `healthy`, `degraded` (one recent failure or success rate < 0.8), `failing` (≥ 2 consecutive failures), `unknown` (no runs yet).

### `POST /monitor/sync` — pull executions from the engine now

The `run-monitor` service polls automatically; this forces a pass (sync only — diagnosis stays on the worker).

```bash
curl -s -X POST localhost:8000/monitor/sync | jq
# {"newly_failed_runs": ["..."]}
```

### `GET /incidents` — incident feed

```bash
curl -s 'localhost:8000/incidents?status=awaiting_approval' | jq '.[] | {id, severity, summary}'
```

Filterable by `status`: `open`, `awaiting_approval`, `resolved`, `dismissed`.

### `GET /incidents/{id}` — one incident (includes `root_cause` and `proposed_patch`)

### `POST /incidents/{id}/approve` — apply the proposed patch

Deploys the patch as a new workflow version (versioned + audited) and resolves the incident. `409` if the incident isn't awaiting approval.

```bash
curl -s -X POST localhost:8000/incidents/$ID/approve \
  -H 'Content-Type: application/json' -d '{"actor": "human:me"}' | jq .status
```

### `POST /incidents/{id}/dismiss` — discard the patch, close the incident

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

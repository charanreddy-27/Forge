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

---

*Phase 2 adds workflow registry endpoints (list workflows, list versions, rollback). Document them here with curl examples as they land.*

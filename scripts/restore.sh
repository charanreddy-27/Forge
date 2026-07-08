#!/usr/bin/env bash
# Restore a dump produced by scripts/backup.sh.
#
# Usage: scripts/restore.sh backups/forge-<stamp>.dump
# Stops the writers first so nothing races the restore, then brings
# everything back up (migrations re-run on agent-layer start).
set -euo pipefail
cd "$(dirname "$0")/.."

FILE="${1:?usage: scripts/restore.sh backups/forge-<stamp>.dump}"
POSTGRES_USER="${POSTGRES_USER:-forge}"
POSTGRES_DB="${POSTGRES_DB:-forge}"

echo "stopping writers..."
docker compose stop agent-layer generation-worker run-monitor n8n dashboard

docker compose up -d postgres
docker compose exec -T postgres pg_restore \
  -U "$POSTGRES_USER" -d "$POSTGRES_DB" --clean --if-exists < "$FILE"

echo "restore complete; starting services..."
docker compose up -d

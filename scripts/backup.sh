#!/usr/bin/env bash
# Dump the Forge database (Forge tables + n8n's schema — everything lives in
# one Postgres) to backups/, keeping the most recent $KEEP dumps.
#
# Usage:   scripts/backup.sh
# Env:     BACKUP_DIR (default: backups)   KEEP (default: 14)
# Restore: scripts/restore.sh backups/forge-<stamp>.dump
set -euo pipefail
cd "$(dirname "$0")/.."

BACKUP_DIR="${BACKUP_DIR:-backups}"
KEEP="${KEEP:-14}"
POSTGRES_USER="${POSTGRES_USER:-forge}"
POSTGRES_DB="${POSTGRES_DB:-forge}"

mkdir -p "$BACKUP_DIR"
STAMP="$(date +%Y%m%d-%H%M%S)"
FILE="$BACKUP_DIR/forge-$STAMP.dump"

docker compose exec -T postgres pg_dump -U "$POSTGRES_USER" -d "$POSTGRES_DB" -Fc > "$FILE"
echo "wrote $FILE ($(du -h "$FILE" | cut -f1))"

# Rotate: drop everything beyond the newest $KEEP dumps.
ls -1t "$BACKUP_DIR"/forge-*.dump 2>/dev/null | tail -n +"$((KEEP + 1))" | xargs -r rm --
echo "keeping $(ls -1 "$BACKUP_DIR"/forge-*.dump | wc -l) backup(s) in $BACKUP_DIR/"

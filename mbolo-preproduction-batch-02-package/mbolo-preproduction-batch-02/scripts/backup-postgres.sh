#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
mkdir -p backups
STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
FILE="backups/mbolo-${STAMP}.dump"
docker compose --env-file .env.production -f compose.production.yaml exec -T postgres \
  pg_dump -U "$POSTGRES_USER" -d "$POSTGRES_DB" -Fc > "$FILE"
chmod 600 "$FILE"
echo "✅ Sauvegarde créée : $FILE"

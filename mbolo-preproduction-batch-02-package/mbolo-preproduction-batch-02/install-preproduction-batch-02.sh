#!/usr/bin/env bash
set -euo pipefail

PROJECT="${HOME}/projects/mbolo"
SOURCE="$(cd "$(dirname "$0")" && pwd)"
cd "$PROJECT"

install -D -m 0644 "$SOURCE/backend/Dockerfile.production" backend/Dockerfile.production
install -D -m 0644 "$SOURCE/frontend/Dockerfile.production" frontend/Dockerfile.production
install -D -m 0644 "$SOURCE/deploy/nginx/default.conf" deploy/nginx/default.conf
install -D -m 0644 "$SOURCE/compose.production.yaml" compose.production.yaml
install -D -m 0644 "$SOURCE/.env.production.example" .env.production.example
install -D -m 0755 "$SOURCE/scripts/preproduction-check.sh" scripts/preproduction-check.sh
install -D -m 0755 "$SOURCE/scripts/start-production.sh" scripts/start-production.sh
install -D -m 0755 "$SOURCE/scripts/stop-production.sh" scripts/stop-production.sh
install -D -m 0755 "$SOURCE/scripts/backup-postgres.sh" scripts/backup-postgres.sh
install -D -m 0755 "$SOURCE/scripts/restore-postgres.sh" scripts/restore-postgres.sh

cat >> .gitignore <<'GITIGNORE'

# Environnement et artefacts de production
.env.production
backups/
GITIGNORE

echo "✅ Lot Préproduction 02 installé."
echo "Aucune migration exécutée. Aucun service de production démarré."
echo "Vérifie maintenant : git status --short"

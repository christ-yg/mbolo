#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."

ENV_FILE="${MBOLO_ENV_FILE:-.env.production}"
COMPOSE_FILE="${MBOLO_COMPOSE_FILE:-compose.production.yaml}"

echo "[1/6] Validation Docker Compose"
docker compose --env-file "$ENV_FILE" -f "$COMPOSE_FILE" config >/dev/null

echo "[2/6] État des services"
docker compose --env-file "$ENV_FILE" -f "$COMPOSE_FILE" ps

echo "[3/6] Contrôles Django et migrations"
docker compose --env-file "$ENV_FILE" -f "$COMPOSE_FILE" exec -T backend \
  python manage.py check --deploy
docker compose --env-file "$ENV_FILE" -f "$COMPOSE_FILE" exec -T backend \
  python manage.py makemigrations --check --dry-run

echo "[4/6] Vérification de la dernière sauvegarde"
bash scripts/backup-verify.sh

echo "[5/6] Routes et en-têtes de lancement"
bash scripts/launch-smoke-check.sh

echo "[6/6] Parcours publics Playwright"
(
  cd frontend
  npm run check
  npm run test:e2e:public
)

echo "✅ RELEASE_GATE_FREE=OK"
echo "ℹ️  Aucun service payant n'a été utilisé."

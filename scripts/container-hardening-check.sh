#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."

ENV_FILE=".env.production"
COMPOSE_FILE="compose.production.yaml"

if [[ ! -f "$ENV_FILE" ]]; then
  echo "❌ $ENV_FILE est absent."
  exit 1
fi

echo "[1/4] Validation de Docker Compose"
docker compose --env-file "$ENV_FILE" -f "$COMPOSE_FILE" config >/dev/null

echo "[2/4] Construction des images applicatives"
docker compose --env-file "$ENV_FILE" -f "$COMPOSE_FILE" build backend frontend

echo "[3/4] Contrôle de l'image backend"
docker compose --env-file "$ENV_FILE" -f "$COMPOSE_FILE" run --rm --no-deps backend \
  sh -c '
    test "$(id -u)" -ne 0
    ! command -v gcc >/dev/null 2>&1
    ! command -v cc >/dev/null 2>&1
    ! command -v make >/dev/null 2>&1
    python -c "import django, channels, psycopg, redis; print(\"Imports Python: OK\")"
  '

echo "[4/4] Contrôle des protections Compose"
rendered="$(docker compose --env-file "$ENV_FILE" -f "$COMPOSE_FILE" config)"
for expected in \
  "read_only: true" \
  "no-new-privileges" \
  "NET_BIND_SERVICE" \
  "CHOWN" \
  "SETUID" \
  "SETGID"; do
  if ! grep -Fq "$expected" <<<"$rendered"; then
    echo "❌ Protection absente : $expected"
    exit 1
  fi
done

echo "✅ CONTAINER_HARDENING=OK"
echo "ℹ️  Backend non-root, sans compilateur ; services applicatifs en lecture seule."

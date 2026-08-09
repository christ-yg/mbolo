#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."

compose=(docker compose --env-file .env.production -f compose.production.yaml)
https_compose=(
  docker compose
  --env-file .env.production
  -f compose.production.yaml
  -f compose.https-local.yaml
)

echo "[1/5] Validation des fichiers Compose"
"${compose[@]}" config --quiet
"${https_compose[@]}" config --quiet

echo "[2/5] Validation des configurations Caddy"
for caddyfile in Caddyfile.local Caddyfile.production; do
  docker run --rm \
    -v "${PWD}/deploy/caddy/${caddyfile}:/etc/caddy/Caddyfile:ro" \
    caddy:2.10.2-alpine \
    caddy validate --config /etc/caddy/Caddyfile
done

echo "[3/5] Construction des images applicatives"
"${compose[@]}" build backend frontend

echo "[4/5] Tests IP client et limites anti-abus"
"${compose[@]}" run --rm backend \
  python manage.py test \
  apps.accounts.tests.test_client_ip_throttling \
  --noinput

echo "[5/5] Démarrage et contrôle fonctionnel"
"${compose[@]}" up -d
bash scripts/launch-smoke-check.sh

echo "✅ CLIENT_IP_THROTTLING=OK"
echo "ℹ️  L'en-tête privé reste refusé hors des overlays HTTPS approuvés."

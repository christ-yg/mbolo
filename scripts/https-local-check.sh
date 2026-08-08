#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."

ENV_FILE=".env.production"
BASE_COMPOSE="compose.production.yaml"
HTTPS_COMPOSE="compose.https-local.yaml"
HTTPS_PORT="${MBOLO_HTTPS_PORT:-8443}"

if [[ ! -f "$ENV_FILE" ]]; then
  echo "❌ $ENV_FILE est absent."
  exit 1
fi

compose=(
  docker compose
  --env-file "$ENV_FILE"
  -f "$BASE_COMPOSE"
  -f "$HTTPS_COMPOSE"
)

echo "[1/5] Validation de la fusion des fichiers Compose"
"${compose[@]}" config >/dev/null

echo "[2/5] Reconstruction du frontend avec la configuration Nginx corrigée"
"${compose[@]}" build frontend

echo "[3/5] Démarrage du frontend et du proxy HTTPS local"
"${compose[@]}" up -d frontend edge

echo "[4/5] Attente du point de contrôle HTTPS"
curl \
  --insecure \
  --fail \
  --silent \
  --show-error \
  --retry 20 \
  --retry-delay 2 \
  --retry-all-errors \
  "https://localhost:${HTTPS_PORT}/healthz" >/dev/null

echo "[5/5] Contrôles des routes principales via HTTPS"
for path in "/" "/api/v1/csrf/" "/admin/"; do
  status="$(
    curl \
      --insecure \
      --silent \
      --output /dev/null \
      --write-out '%{http_code}' \
      "https://localhost:${HTTPS_PORT}${path}"
  )"

  case "$path:$status" in
    "/:200"|"/api/v1/csrf/:200"|"/admin/:200"|"/admin/:302")
      ;;
    *)
      echo "❌ Réponse inattendue : $path -> HTTP $status"
      exit 1
      ;;
  esac

  echo "✅ $path -> HTTP $status"
done

echo
echo "✅ Simulation HTTPS locale validée sur https://localhost:${HTTPS_PORT}"
echo "ℹ️  Le certificat interne est volontairement non public."
echo "ℹ️  La préproduction HTTP reste disponible sur http://127.0.0.1:8080"


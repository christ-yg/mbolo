#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."

ENV_FILE=".env.production"
COMPOSE_FILE="compose.production.yaml"

if [[ ! -f "$ENV_FILE" ]]; then
  echo "❌ $ENV_FILE est absent. Copie .env.production.example puis renseigne les secrets."
  exit 1
fi

required=(
  DJANGO_SECRET_KEY DJANGO_ALLOWED_HOSTS DJANGO_CSRF_TRUSTED_ORIGINS
  POSTGRES_DB POSTGRES_USER POSTGRES_PASSWORD REDIS_PASSWORD
  MBOLO_PAYMENT_PROVIDER
)

for key in "${required[@]}"; do
  value="$(grep -E "^${key}=" "$ENV_FILE" | tail -n1 | cut -d= -f2- || true)"
  if [[ -z "$value" || "$value" == replace-with-* ]]; then
    echo "❌ Variable absente ou fictive : $key"
    exit 1
  fi
done

if grep -Eq '^APP_DEBUG=true$|^MBOLO_PAYMENT_TEST_MODE=true$' "$ENV_FILE"; then
  echo "❌ DEBUG ou paiement test encore actif dans .env.production"
  exit 1
fi

mkdir -p backups

echo "[1/4] Validation de la configuration Compose"
docker compose --env-file "$ENV_FILE" -f "$COMPOSE_FILE" config >/dev/null

echo "[2/4] Construction des images"
docker compose --env-file "$ENV_FILE" -f "$COMPOSE_FILE" build

echo "[3/4] Contrôle Django de déploiement"
docker compose --env-file "$ENV_FILE" -f "$COMPOSE_FILE" run --rm backend python manage.py check --deploy

echo "[4/4] Contrôle des migrations"
docker compose --env-file "$ENV_FILE" -f "$COMPOSE_FILE" run --rm backend python manage.py makemigrations --check --dry-run

echo "✅ Préproduction validée. Aucun service permanent n'a été démarré."

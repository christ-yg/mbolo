#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."

ENV_FILE="${MBOLO_ENV_FILE:-.env.production}"
COMPOSE_FILE="${MBOLO_COMPOSE_FILE:-compose.production.yaml}"
BACKUP_DIR="${1:-}"
CONFIRMATION="${2:-}"

if [[ -z "$BACKUP_DIR" || "$CONFIRMATION" != "JE_RESTAURE_MBOLO" ]]; then
  echo "Restauration destructive refusée."
  echo "Usage : bash scripts/restore-local.sh <dossier> JE_RESTAURE_MBOLO"
  exit 1
fi

if [[ ! -f "${BACKUP_DIR}/database.dump" ]]; then
  echo "❌ Sauvegarde PostgreSQL introuvable."
  exit 1
fi

echo "[1/7] Vérification préalable de la sauvegarde"
bash scripts/backup-verify.sh "$BACKUP_DIR"

compose=(docker compose --env-file "$ENV_FILE" -f "$COMPOSE_FILE")
ABS_BACKUP_DIR="$(realpath "$BACKUP_DIR")"

echo "[2/7] Création d'une sauvegarde de sécurité avant restauration"
MBOLO_BACKUP_RETENTION_DAYS=30 bash scripts/backup-local.sh

echo "[3/7] Arrêt temporaire du backend"
"${compose[@]}" stop backend >/dev/null || true
"${compose[@]}" up -d postgres >/dev/null

echo "[4/7] Recréation contrôlée de la base PostgreSQL"
"${compose[@]}" exec -T postgres sh -c \
  'psql --username="$POSTGRES_USER" --dbname=postgres --set=ON_ERROR_STOP=1 --command="SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname = '\''$POSTGRES_DB'\'' AND pid <> pg_backend_pid();" >/dev/null && dropdb --if-exists --username="$POSTGRES_USER" "$POSTGRES_DB" && createdb --username="$POSTGRES_USER" --owner="$POSTGRES_USER" "$POSTGRES_DB"'

echo "[5/7] Restauration PostgreSQL"
"${compose[@]}" run --rm --no-deps -T \
  -v "${ABS_BACKUP_DIR}:/restore:ro" \
  postgres sh -c \
  'pg_restore --username="$POSTGRES_USER" --dbname="$POSTGRES_DB" --no-owner --no-privileges --exit-on-error /restore/database.dump'

echo "[6/7] Restauration des médias"
"${compose[@]}" run --rm --no-deps -T \
  -v "${ABS_BACKUP_DIR}:/restore:ro" \
  backend sh -c 'find /app/backend/media -mindepth 1 -delete && tar -xzf /restore/media.tar.gz -C /app/backend/media'
"${compose[@]}" run --rm --no-deps -T \
  -v "${ABS_BACKUP_DIR}:/restore:ro" \
  backend sh -c 'find /app/backend/private_media -mindepth 1 -delete && tar -xzf /restore/private-media.tar.gz -C /app/backend/private_media'

echo "[7/7] Redémarrage et contrôle Django"
"${compose[@]}" up -d backend >/dev/null
"${compose[@]}" exec -T backend python manage.py check

echo "✅ RESTORE_MBOLO=OK"
echo "ℹ️  La sauvegarde de sécurité créée à l'étape 2 permet un retour arrière."

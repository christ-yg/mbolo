#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."

ENV_FILE="${MBOLO_ENV_FILE:-.env.production}"
COMPOSE_FILE="${MBOLO_COMPOSE_FILE:-compose.production.yaml}"
BACKUP_ROOT="${MBOLO_BACKUP_DIR:-backups}"
RETENTION_DAYS="${MBOLO_BACKUP_RETENTION_DAYS:-14}"
TIMESTAMP="$(date -u +%Y%m%dT%H%M%SZ)"
BACKUP_NAME="mbolo-${TIMESTAMP}"
FINAL_DIR="${BACKUP_ROOT}/${BACKUP_NAME}"
TEMP_DIR="${BACKUP_ROOT}/.${BACKUP_NAME}.tmp"

if [[ ! -f "$ENV_FILE" ]]; then
  echo "❌ Fichier absent : $ENV_FILE"
  exit 1
fi

if ! [[ "$RETENTION_DAYS" =~ ^[0-9]+$ ]] || (( RETENTION_DAYS < 1 )); then
  echo "❌ MBOLO_BACKUP_RETENTION_DAYS doit être un entier positif."
  exit 1
fi

compose=(docker compose --env-file "$ENV_FILE" -f "$COMPOSE_FILE")

echo "[1/6] Validation de Docker Compose"
"${compose[@]}" config >/dev/null

echo "[2/6] Vérification de PostgreSQL"
"${compose[@]}" up -d postgres >/dev/null
"${compose[@]}" exec -T postgres sh -c \
  'pg_isready --username="$POSTGRES_USER" --dbname="$POSTGRES_DB"' >/dev/null

mkdir -p "$BACKUP_ROOT"
if [[ -e "$TEMP_DIR" || -e "$FINAL_DIR" ]]; then
  echo "❌ Une sauvegarde portant ce nom existe déjà."
  exit 1
fi
mkdir "$TEMP_DIR"

cleanup() {
  if [[ -d "$TEMP_DIR" ]]; then
    rm -rf -- "$TEMP_DIR"
  fi
}
trap cleanup EXIT

echo "[3/6] Export PostgreSQL compressé"
"${compose[@]}" exec -T postgres sh -c \
  'pg_dump --username="$POSTGRES_USER" --dbname="$POSTGRES_DB" --format=custom --compress=9 --no-owner --no-privileges' \
  >"${TEMP_DIR}/database.dump"

if [[ ! -s "${TEMP_DIR}/database.dump" ]]; then
  echo "❌ L'export PostgreSQL est vide."
  exit 1
fi

echo "[4/6] Sauvegarde des médias publics et privés"
"${compose[@]}" run --rm --no-deps -T backend \
  tar -czf - -C /app/backend/media . >"${TEMP_DIR}/media.tar.gz"
"${compose[@]}" run --rm --no-deps -T backend \
  tar -czf - -C /app/backend/private_media . >"${TEMP_DIR}/private-media.tar.gz"

cat >"${TEMP_DIR}/manifest.txt" <<EOF
MBOLO_BACKUP_FORMAT=1
CREATED_AT_UTC=${TIMESTAMP}
DATABASE_FORMAT=postgresql-custom
MEDIA_FORMAT=tar-gzip
EOF

echo "[5/6] Création des empreintes SHA-256"
(
  cd "$TEMP_DIR"
  sha256sum database.dump media.tar.gz private-media.tar.gz manifest.txt >SHA256SUMS
  sha256sum --check SHA256SUMS >/dev/null
)

mv -- "$TEMP_DIR" "$FINAL_DIR"
trap - EXIT

echo "[6/6] Rotation des sauvegardes de plus de ${RETENTION_DAYS} jours"
find "$BACKUP_ROOT" -mindepth 1 -maxdepth 1 -type d \
  -name 'mbolo-*' -mtime "+${RETENTION_DAYS}" -print -exec rm -rf -- {} +

echo "✅ BACKUP_MBOLO=OK"
echo "✅ Sauvegarde : $FINAL_DIR"
echo "ℹ️  Copiez ensuite ce dossier sur un disque externe sécurisé."

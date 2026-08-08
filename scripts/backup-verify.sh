#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."

ENV_FILE="${MBOLO_ENV_FILE:-.env.production}"
COMPOSE_FILE="${MBOLO_COMPOSE_FILE:-compose.production.yaml}"
BACKUP_DIR="${1:-}"

if [[ -z "$BACKUP_DIR" ]]; then
  BACKUP_DIR="$(find "${MBOLO_BACKUP_DIR:-backups}" -mindepth 1 -maxdepth 1 \
    -type d -name 'mbolo-*' -print 2>/dev/null | sort | tail -n1)"
fi

if [[ -z "$BACKUP_DIR" ]]; then
  echo "❌ Aucune sauvegarde Mbolo n'a été trouvée."
  exit 1
fi

if [[ ! -d "$BACKUP_DIR" ]]; then
  echo "❌ Dossier de sauvegarde introuvable : $BACKUP_DIR"
  exit 1
fi

required=(database.dump media.tar.gz private-media.tar.gz manifest.txt SHA256SUMS)
for file in "${required[@]}"; do
  if [[ ! -s "${BACKUP_DIR}/${file}" ]]; then
    echo "❌ Fichier absent ou vide : ${BACKUP_DIR}/${file}"
    exit 1
  fi
done

echo "[1/3] Vérification SHA-256"
(
  cd "$BACKUP_DIR"
  sha256sum --check SHA256SUMS
)

echo "[2/3] Vérification des archives de médias"
tar -tzf "${BACKUP_DIR}/media.tar.gz" >/dev/null
tar -tzf "${BACKUP_DIR}/private-media.tar.gz" >/dev/null

echo "[3/3] Vérification de l'archive PostgreSQL"
docker compose --env-file "$ENV_FILE" -f "$COMPOSE_FILE" run \
  --rm --no-deps -T \
  -v "$(realpath "$BACKUP_DIR"):/verify:ro" \
  postgres pg_restore --list /verify/database.dump >/dev/null

echo "✅ BACKUP_VERIFY=OK"
echo "✅ Aucun contenu actif n'a été modifié."

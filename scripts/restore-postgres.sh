#!/usr/bin/env bash
set -euo pipefail
if [[ $# -ne 1 ]]; then
  echo "Usage: $0 backups/mbolo-YYYYMMDDTHHMMSSZ.dump"
  exit 1
fi
cd "$(dirname "$0")/.."
FILE="$1"
[[ -f "$FILE" ]] || { echo "Fichier introuvable : $FILE"; exit 1; }
read -r -p "Cette restauration remplacera les données actuelles. Taper RESTAURER : " confirm
[[ "$confirm" == "RESTAURER" ]] || { echo "Annulé."; exit 1; }
docker compose --env-file .env.production -f compose.production.yaml exec -T postgres \
  pg_restore -U "$POSTGRES_USER" -d "$POSTGRES_DB" --clean --if-exists < "$FILE"
echo "✅ Restauration terminée."

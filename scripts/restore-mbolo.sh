#!/usr/bin/env bash

# Restaure PostgreSQL et les deux volumes de médias depuis une sauvegarde
# complète créée par backup-mbolo.sh.
#
# Cette action remplace les données actives. Elle exige :
# - une sauvegarde valide ;
# - une sauvegarde de sécurité préalable ;
# - une confirmation humaine exacte.

set -Eeuo pipefail
umask 077

if [[ $# -ne 1 ]]; then
    echo "Usage : $0 backups/mbolo-YYYYMMDDTHHMMSSZ" >&2
    exit 1
fi

project_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${project_root}"

backup_directory="$1"

if [[ "${backup_directory}" != /* ]]; then
    backup_directory="${project_root}/${backup_directory}"
fi

compose=(
    docker compose
    --env-file .env.production
    -f compose.production.yaml
)

services_stopped=false

restart_application() {
    if [[ "${services_stopped}" == "true" ]]; then
        echo "Redémarrage de l'application après interruption..."
        "${compose[@]}" up -d backend frontend >/dev/null || true
    fi
}

trap restart_application EXIT

echo "[1/8] Vérification complète de la sauvegarde demandée"
bash scripts/verify-backup.sh "${backup_directory}"

echo
echo "[2/8] Création d'une sauvegarde de sécurité de l'état actuel"
bash scripts/backup-mbolo.sh

echo
echo "ATTENTION : la restauration va remplacer :"
echo "- la base PostgreSQL active ;"
echo "- les médias publics ;"
echo "- les médias privés."
echo
read -r -p "Pour continuer, saisir exactement RESTAURER MBOLO : " confirmation

if [[ "${confirmation}" != "RESTAURER MBOLO" ]]; then
    echo "Restauration annulée."
    exit 1
fi

echo "[3/8] Arrêt des services applicatifs"
"${compose[@]}" stop frontend backend
services_stopped=true

echo "[4/8] Restauration PostgreSQL"

"${compose[@]}" exec -T postgres sh -ceu '
    pg_restore \
        --username="$POSTGRES_USER" \
        --dbname="$POSTGRES_DB" \
        --clean \
        --if-exists \
        --exit-on-error \
        --single-transaction \
        --no-owner \
        --no-privileges
' < "${backup_directory}/postgres.dump"

echo "[5/8] Restauration des médias publics"

"${compose[@]}" run --rm --no-deps -T backend sh -ceu '
    find /app/backend/media -mindepth 1 -delete
    tar -xzf - -C /app/backend/media
' < "${backup_directory}/media.tar.gz"

echo "[6/8] Restauration des médias privés"

"${compose[@]}" run --rm --no-deps -T backend sh -ceu '
    find /app/backend/private_media -mindepth 1 -delete
    tar -xzf - -C /app/backend/private_media
' < "${backup_directory}/private-media.tar.gz"

echo "[7/8] Redémarrage de Mbolo"
"${compose[@]}" up -d backend frontend
services_stopped=false
trap - EXIT

echo "[8/8] État final"
"${compose[@]}" ps
echo
echo "✅ Restauration terminée."
echo "Exécute ensuite bash scripts/preproduction-check.sh."

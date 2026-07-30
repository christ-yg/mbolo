#!/usr/bin/env bash

# Sauvegarde cohérente des données persistantes de Mbolo.
#
# Le paquet créé contient :
# - un dump PostgreSQL au format custom ;
# - les médias publics du volume Docker media_data ;
# - les médias privés du volume Docker private_media_data ;
# - des sommes de contrôle SHA-256 ;
# - des métadonnées non sensibles.
#
# Les secrets restent dans .env.production et ne sont jamais copiés.

set -Eeuo pipefail
umask 077

project_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${project_root}"

compose=(
    docker compose
    --env-file .env.production
    -f compose.production.yaml
)

backup_root="${MBOLO_BACKUP_ROOT:-${project_root}/backups}"
timestamp="$(date -u +%Y%m%dT%H%M%SZ)"
backup_name="mbolo-${timestamp}"
temporary_directory="${backup_root}/.${backup_name}.tmp"
final_directory="${backup_root}/${backup_name}"

cleanup_temporary_directory() {
    if [[ -d "${temporary_directory}" ]]; then
        rm -rf -- "${temporary_directory}"
    fi
}

trap cleanup_temporary_directory EXIT

require_command() {
    if ! command -v "$1" >/dev/null 2>&1; then
        echo "ERREUR : commande obligatoire introuvable : $1" >&2
        exit 1
    fi
}

service_is_running() {
    "${compose[@]}" ps --status running --services |
        grep -Fxq "$1"
}

require_command docker
require_command grep
require_command sha256sum
require_command tar

echo "[1/7] Validation de la configuration"

[[ -f ".env.production" ]] || {
    echo "ERREUR : .env.production est introuvable." >&2
    exit 1
}

"${compose[@]}" config --quiet

for required_service in postgres backend; do
    if ! service_is_running "${required_service}"; then
        echo "ERREUR : le service ${required_service} n'est pas démarré." >&2
        exit 1
    fi
done

mkdir -p -- "${backup_root}"
chmod 700 "${backup_root}"

if [[ -e "${final_directory}" || -e "${temporary_directory}" ]]; then
    echo "ERREUR : une sauvegarde porte déjà le nom ${backup_name}." >&2
    exit 1
fi

mkdir -- "${temporary_directory}"
chmod 700 "${temporary_directory}"

echo "[2/7] Sauvegarde PostgreSQL"

"${compose[@]}" exec -T postgres sh -ceu '
    pg_dump \
        --username="$POSTGRES_USER" \
        --dbname="$POSTGRES_DB" \
        --format=custom \
        --compress=9 \
        --no-owner \
        --no-privileges
' > "${temporary_directory}/postgres.dump.part"

[[ -s "${temporary_directory}/postgres.dump.part" ]] || {
    echo "ERREUR : le dump PostgreSQL est vide." >&2
    exit 1
}

mv \
    "${temporary_directory}/postgres.dump.part" \
    "${temporary_directory}/postgres.dump"

echo "[3/7] Sauvegarde des médias publics"

"${compose[@]}" exec -T backend \
    tar -C /app/backend/media -czf - . \
    > "${temporary_directory}/media.tar.gz.part"

mv \
    "${temporary_directory}/media.tar.gz.part" \
    "${temporary_directory}/media.tar.gz"

echo "[4/7] Sauvegarde des médias privés"

"${compose[@]}" exec -T backend \
    tar -C /app/backend/private_media -czf - . \
    > "${temporary_directory}/private-media.tar.gz.part"

mv \
    "${temporary_directory}/private-media.tar.gz.part" \
    "${temporary_directory}/private-media.tar.gz"

echo "[5/7] Validation technique des archives"

"${compose[@]}" exec -T postgres \
    pg_restore --list \
    < "${temporary_directory}/postgres.dump" \
    > /dev/null

tar -tzf "${temporary_directory}/media.tar.gz" > /dev/null
tar -tzf "${temporary_directory}/private-media.tar.gz" > /dev/null

cat > "${temporary_directory}/METADATA.txt" <<EOF
format_version=1
application=mbolo
created_at_utc=${timestamp}
compose_project=mbolo-production
contains=postgres,public_media,private_media
redis_included=false
secrets_included=false
EOF

echo "[6/7] Calcul des sommes de contrôle"

(
    cd "${temporary_directory}"
    sha256sum \
        postgres.dump \
        media.tar.gz \
        private-media.tar.gz \
        METADATA.txt \
        > SHA256SUMS
)

chmod 600 "${temporary_directory}"/*

# Le renommage final est atomique : une sauvegarde incomplète ne reçoit
# jamais le nom définitif.
mv "${temporary_directory}" "${final_directory}"
trap - EXIT

echo "[7/7] Sauvegarde terminée"
echo
echo "Dossier : ${final_directory}"
du -sh "${final_directory}"
echo
echo "Commande de vérification approfondie :"
echo "bash scripts/verify-backup.sh '${final_directory}' --restore-test"

#!/usr/bin/env bash

# Vérifie une sauvegarde Mbolo.
#
# Sans option :
# - contrôle les fichiers ;
# - vérifie SHA-256 ;
# - vérifie la lisibilité du dump et des archives.
#
# Avec --restore-test :
# - restaure le dump dans une base PostgreSQL temporaire ;
# - vérifie que cette base contient des tables ;
# - supprime ensuite uniquement la base temporaire.
#
# La base Mbolo active n'est jamais modifiée.

set -Eeuo pipefail
umask 077

if [[ $# -lt 1 || $# -gt 2 ]]; then
    echo "Usage : $0 backups/mbolo-YYYYMMDDTHHMMSSZ [--restore-test]" >&2
    exit 1
fi

backup_directory="$1"
mode="${2:-}"

if [[ -n "${mode}" && "${mode}" != "--restore-test" ]]; then
    echo "ERREUR : option inconnue : ${mode}" >&2
    exit 1
fi

project_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${project_root}"

compose=(
    docker compose
    --env-file .env.production
    -f compose.production.yaml
)

if [[ "${backup_directory}" != /* ]]; then
    backup_directory="${project_root}/${backup_directory}"
fi

required_files=(
    postgres.dump
    media.tar.gz
    private-media.tar.gz
    METADATA.txt
    SHA256SUMS
)

echo "[1/5] Vérification de la structure"

[[ -d "${backup_directory}" ]] || {
    echo "ERREUR : dossier introuvable : ${backup_directory}" >&2
    exit 1
}

for required_file in "${required_files[@]}"; do
    [[ -f "${backup_directory}/${required_file}" ]] || {
        echo "ERREUR : fichier absent : ${required_file}" >&2
        exit 1
    }
done

echo "[2/5] Vérification SHA-256"

(
    cd "${backup_directory}"
    sha256sum --check SHA256SUMS
)

echo "[3/5] Vérification des archives médias"

tar -tzf "${backup_directory}/media.tar.gz" > /dev/null
tar -tzf "${backup_directory}/private-media.tar.gz" > /dev/null

echo "[4/5] Vérification du catalogue PostgreSQL"

"${compose[@]}" exec -T postgres \
    pg_restore --list \
    < "${backup_directory}/postgres.dump" \
    > /dev/null

if [[ "${mode}" != "--restore-test" ]]; then
    echo "[5/5] Vérification terminée sans restauration temporaire"
    echo "✅ Sauvegarde valide."
    exit 0
fi

echo "[5/5] Test de restauration dans une base temporaire"

test_database="mbolo_restore_check_$(date -u +%Y%m%d%H%M%S)_${RANDOM}"

drop_test_database() {
    "${compose[@]}" exec -T postgres sh -ceu '
        dropdb \
            --username="$POSTGRES_USER" \
            --if-exists \
            --force \
            "$1"
    ' sh "${test_database}" >/dev/null 2>&1 || true
}

trap drop_test_database EXIT

"${compose[@]}" exec -T postgres sh -ceu '
    createdb \
        --username="$POSTGRES_USER" \
        --template=template0 \
        "$1"
' sh "${test_database}"

"${compose[@]}" exec -T postgres sh -ceu '
    pg_restore \
        --username="$POSTGRES_USER" \
        --dbname="$1" \
        --exit-on-error \
        --no-owner \
        --no-privileges
' sh "${test_database}" \
    < "${backup_directory}/postgres.dump"

table_count="$(
    "${compose[@]}" exec -T postgres sh -ceu '
        psql \
            --username="$POSTGRES_USER" \
            --dbname="$1" \
            --tuples-only \
            --no-align \
            --command="
                SELECT COUNT(*)
                FROM information_schema.tables
                WHERE table_schema = '\''public'\'';
            "
    ' sh "${test_database}" |
        tr -d '[:space:]'
)"

if [[ ! "${table_count}" =~ ^[0-9]+$ || "${table_count}" -lt 1 ]]; then
    echo "ERREUR : aucune table restaurée dans la base temporaire." >&2
    exit 1
fi

drop_test_database
trap - EXIT

echo "✅ Restauration temporaire réussie : ${table_count} tables vérifiées."
echo "✅ La base Mbolo active n'a pas été modifiée."

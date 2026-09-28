#!/usr/bin/env bash
set -Eeuo pipefail
umask 077

project_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${project_root}"

backup_root="${MBOLO_BACKUP_ROOT:-${project_root}/backups}"
retention_days="${MBOLO_BACKUP_RETENTION_DAYS:-14}"
mode="${1:---dry-run}"

[[ "${retention_days}" =~ ^[0-9]+$ && "${retention_days}" -ge 1 ]] || {
    echo "ERREUR : MBOLO_BACKUP_RETENTION_DAYS doit être un entier >= 1." >&2
    exit 1
}

[[ "${mode}" == "--dry-run" || "${mode}" == "--apply" ]] || {
    echo "Usage : $0 [--dry-run|--apply]" >&2
    exit 1
}

mkdir -p -- "${backup_root}"
chmod 700 "${backup_root}"

mapfile -d '' expired < <(find "${backup_root}" -mindepth 1 -maxdepth 1 -type d \
    -name 'mbolo-[0-9][0-9][0-9][0-9][0-9][0-9][0-9][0-9]T[0-9][0-9][0-9][0-9][0-9][0-9]Z' \
    -mtime "+${retention_days}" -print0)

if (( ${#expired[@]} == 0 )); then
    echo "Aucune sauvegarde expirée."
    echo "BACKUP_RETENTION=OK"
    exit 0
fi

printf 'Sauvegarde expirée : %s\n' "${expired[@]}"

if [[ "${mode}" == "--dry-run" ]]; then
    echo "Mode simulation : aucune suppression effectuée."
    exit 0
fi

for directory in "${expired[@]}"; do
    bash scripts/verify-backup.sh "${directory}" >/dev/null
    rm -rf -- "${directory}"
done

echo "BACKUP_RETENTION=OK"

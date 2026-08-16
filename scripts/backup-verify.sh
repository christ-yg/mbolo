#!/usr/bin/env bash
set -Eeuo pipefail

project_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${project_root}"

backup_directory="${1:-}"
mode="${2:-}"

if [[ -z "${backup_directory}" ]]; then
    backup_directory="$(find "${MBOLO_BACKUP_ROOT:-backups}" -mindepth 1 -maxdepth 1 -type d -name 'mbolo-*' -print 2>/dev/null | sort | tail -n 1)"
fi

if [[ -z "${backup_directory}" ]]; then
    echo "ERREUR : aucune sauvegarde Mbolo n'a été trouvée." >&2
    exit 1
fi

exec bash scripts/verify-backup.sh "${backup_directory}" ${mode:+"${mode}"}

#!/usr/bin/env bash
set -Eeuo pipefail

project_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${project_root}"

echo "Information : backup-local.sh utilise désormais le format canonique Mbolo."
bash scripts/backup-mbolo.sh

if [[ "${MBOLO_BACKUP_RETENTION_APPLY:-false}" == "true" ]]; then
    exec bash scripts/backup-retention.sh --apply
fi

echo "Information : rotation non appliquée (mode sûr par défaut)."
echo "Utiliser : bash scripts/backup-retention.sh --apply"

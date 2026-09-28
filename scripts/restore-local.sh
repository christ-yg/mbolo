#!/usr/bin/env bash
set -Eeuo pipefail

project_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${project_root}"

if [[ $# -lt 1 || $# -gt 2 ]]; then
    echo "Usage : $0 backups/mbolo-YYYYMMDDTHHMMSSZ [JE_RESTAURE_MBOLO]" >&2
    exit 1
fi

if [[ $# -eq 2 && "$2" != "JE_RESTAURE_MBOLO" ]]; then
    echo "ERREUR : confirmation historique invalide." >&2
    exit 1
fi

echo "Information : restore-local.sh utilise désormais la restauration canonique."
exec bash scripts/restore-mbolo.sh "$1"

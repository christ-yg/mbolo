#!/usr/bin/env bash

# Compatibilité sécurisée avec l'ancien nom.
# Une restauration partielle de PostgreSQL pourrait désynchroniser les
# photos de la base. La restauration complète est donc obligatoire.

set -Eeuo pipefail

if [[ $# -ne 1 ]]; then
    echo "Usage : $0 backups/mbolo-YYYYMMDDTHHMMSSZ" >&2
    exit 1
fi

project_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${project_root}"

echo "Information : restauration cohérente de PostgreSQL et des médias."
exec bash scripts/restore-mbolo.sh "$1"

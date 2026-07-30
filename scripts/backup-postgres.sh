#!/usr/bin/env bash

# Compatibilité avec l'ancien nom du script.
# La sauvegarde recommandée couvre maintenant PostgreSQL ainsi que les
# médias publics et privés.

set -Eeuo pipefail

project_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${project_root}"

echo "Information : lancement de la sauvegarde complète Mbolo."
exec bash scripts/backup-mbolo.sh

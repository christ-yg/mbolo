#!/usr/bin/env bash
set -Eeuo pipefail

[[ -f compose.production.yaml && -d backend && -d scripts ]] || {
    echo "ERREUR : exécuter ce script depuis la racine du dépôt Mbolo." >&2
    exit 1
}

chmod +x scripts/*.sh

if ! grep -Fxq 'release-evidence/' .gitignore; then
    printf '\n# Preuves locales de release (peuvent contenir des identifiants techniques)\nrelease-evidence/\n' >> .gitignore
fi

bash scripts/operational-resilience-gate-check.sh
git diff --check

echo "INSTALLATION_SUPER_LOT_70_89=OK"
echo "Aucune sauvegarde ni restauration n'a été exécutée."

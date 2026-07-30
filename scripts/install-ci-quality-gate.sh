#!/usr/bin/env bash
#
# Installation et validation locale du lot CI/CD Mbolo.
#
# Le ZIP doit être décompressé à la racine de ~/projects/mbolo avant
# l'exécution de ce script.

set -euo pipefail

readonly project_root="${HOME}/projects/mbolo"

if [[ ! -d "${project_root}/.git" ]]; then
  echo "Erreur : dépôt Git Mbolo introuvable dans ${project_root}." >&2
  exit 1
fi

cd "${project_root}"

required_files=(
  ".github/workflows/ci.yml"
  ".github/dependabot.yml"
  "scripts/check-sensitive-files.sh"
  "docs/CI_CD.md"
)

for required_file in "${required_files[@]}"; do
  if [[ ! -f "${required_file}" ]]; then
    echo "Erreur : fichier manquant après extraction : ${required_file}" >&2
    exit 1
  fi
done

chmod 0755 \
  scripts/check-sensitive-files.sh \
  scripts/install-ci-quality-gate.sh

echo "[1/4] Contrôle des fichiers sensibles suivis par Git"
bash scripts/check-sensitive-files.sh

echo "[2/4] Validation syntaxique des scripts"
bash -n scripts/check-sensitive-files.sh
bash -n scripts/install-ci-quality-gate.sh

echo "[3/4] Vérification des fichiers CI"
grep -q '^name: Mbolo CI$' .github/workflows/ci.yml
grep -q '^version: 2$' .github/dependabot.yml

echo "[4/4] État Git"
git status --short

echo
echo "Installation locale terminée."
echo "Le workflow ne sera exécuté par GitHub qu'après commit et push."


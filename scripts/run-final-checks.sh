#!/usr/bin/env bash
set -euo pipefail

PROJECT="${HOME}/projects/mbolo"
cd "${PROJECT}"

echo "============================================================"
echo " MBOLO — CONTRÔLES FINAUX"
echo "============================================================"

echo
echo "[1/8] Vérification de la configuration Django"
python backend/manage.py check

echo
echo "[2/8] Vérification des migrations manquantes"
python backend/manage.py makemigrations --check --dry-run

echo
echo "[3/8] Vérification de déploiement Django"
echo "Les avertissements HTTPS sont normaux en développement local."
python backend/manage.py check --deploy || true

echo
echo "[4/8] Tests backend"
python backend/manage.py test apps --keepdb

echo
echo "[5/8] Compilation Python"
python -m compileall -q backend/apps backend/config

echo
echo "[6/8] TypeScript, lint et build frontend"
(
  cd frontend
  npm run check
)

echo
echo "[7/8] Recherche de fichiers sensibles suivis par Git"
if git ls-files | grep -E '(^|/)\.env$|\.pem$|\.key$|\.p12$|\.pfx$|db\.sqlite3$'; then
  echo "❌ Un fichier sensible semble être suivi par Git."
  exit 1
else
  echo "✅ Aucun fichier sensible connu n'est suivi."
fi

echo
echo "[8/8] État Git"
git status --short

echo
echo "============================================================"
echo " ✅ CONTRÔLES FINAUX TERMINÉS"
echo "============================================================"

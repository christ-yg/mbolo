#!/usr/bin/env bash

# Retire d'anciens paquets de livraison de l'index Git de Mbolo.
#
# IMPORTANT :
# - cette commande utilise uniquement `git rm --cached` ;
# - les fichiers restent physiquement sur le PC ;
# - aucune base PostgreSQL, photo, variable d'environnement ou donnée
#   utilisateur n'est supprimée ;
# - le script doit être exécuté depuis le dépôt Mbolo ou l'un de ses
#   sous-dossiers.

set -Eeuo pipefail

repository_root="$(git rev-parse --show-toplevel)"
cd "${repository_root}"

echo "[1/4] Vérification du dépôt Mbolo"

if [[ ! -f ".gitignore" ]]; then
    echo "ERREUR : fichier .gitignore introuvable." >&2
    exit 1
fi

echo "[2/4] Retrait des artefacts de l'index Git"

git rm -r --cached --ignore-unmatch -- \
    "09-preproduction-infrastructure-context.zip" \
    "INSTALLATION.txt" \
    "mbolo-preproduction-batch-02-package" \
    "mbolo-preproduction-batch-02.zip" \
    "mbolo_docker_backend_fix" \
    "mbolo_docker_backend_fix.zip" \
    "mbolo_match_messaging_ui_fix.zip" \
    "mbolo_photo_websocket_fix.zip" \
    "mbolo_pillow_dependency_fix.zip" \
    "mbolo_test_accounts.zip"

echo "[3/4] Vérification des protections sensibles"

for sensitive_path in \
    ".env.production" \
    "backend/media" \
    "backend/private_media"
do
    if ! git check-ignore -q "${sensitive_path}"; then
        echo "ERREUR : ${sensitive_path} n'est pas protégé par .gitignore." >&2
        exit 1
    fi
done

echo "[4/4] Résultat préparé"
echo
git status --short
echo
echo "Les artefacts restent sur le PC."
echo "Vérifie le résultat, puis crée le commit et pousse-le vers GitHub."

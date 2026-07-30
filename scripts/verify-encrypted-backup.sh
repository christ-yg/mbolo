#!/usr/bin/env bash

# Vérifie une copie chiffrée Mbolo après téléchargement ou déplacement.
#
# Le script vérifie :
# - le checksum SHA-256 du fichier chiffré ;
# - la validité cryptographique GPG ;
# - la lisibilité de l'archive interne.
#
# Il n'extrait aucune donnée sur le disque.

set -Eeuo pipefail
umask 077

if [[ $# -ne 1 ]]; then
    echo "Usage : $0 encrypted-backups/mbolo-....tar.gz.gpg" >&2
    exit 1
fi

encrypted_file="$1"

if [[ "${encrypted_file}" != /* ]]; then
    encrypted_file="$(pwd)/${encrypted_file}"
fi

checksum_file="${encrypted_file}.sha256"
encrypted_parent="$(dirname "${encrypted_file}")"
encrypted_name="$(basename "${encrypted_file}")"

[[ -f "${encrypted_file}" ]] || {
    echo "ERREUR : fichier chiffré introuvable : ${encrypted_file}" >&2
    exit 1
}

[[ -f "${checksum_file}" ]] || {
    echo "ERREUR : checksum introuvable : ${checksum_file}" >&2
    exit 1
}

echo "[1/2] Vérification SHA-256"

(
    cd "${encrypted_parent}"
    sha256sum --check "$(basename "${checksum_file}")"
)

echo "[2/2] Vérification GPG et TAR sans extraction"

GPG_TTY="$(tty)"
export GPG_TTY

gpg \
    --quiet \
    --no-symkey-cache \
    --decrypt "${encrypted_parent}/${encrypted_name}" |
    tar -tzf - > /dev/null

echo "✅ Copie chiffrée valide et lisible."
echo "✅ Aucune donnée n'a été extraite sur le disque."

#!/usr/bin/env bash

# Chiffre une sauvegarde complète Mbolo avec GnuPG et AES-256.
#
# L'archive TAR compressée est envoyée directement vers GPG :
# aucune archive intermédiaire non chiffrée n'est créée sur le disque.
#
# La phrase secrète :
# - est demandée par GPG ;
# - n'est pas passée sur la ligne de commande ;
# - n'est pas enregistrée dans un fichier ou une variable d'environnement ;
# - ne doit jamais être envoyée dans Git ou dans un message.

set -Eeuo pipefail
umask 077

if [[ $# -lt 1 || $# -gt 2 ]]; then
    echo "Usage : $0 backups/mbolo-YYYYMMDDTHHMMSSZ [dossier-destination]" >&2
    exit 1
fi

project_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${project_root}"

backup_directory="${1%/}"
destination_root="${2:-${project_root}/encrypted-backups}"

if [[ "${backup_directory}" != /* ]]; then
    backup_directory="${project_root}/${backup_directory}"
fi

if [[ "${destination_root}" != /* ]]; then
    destination_root="${project_root}/${destination_root}"
fi

backup_parent="$(dirname "${backup_directory}")"
backup_name="$(basename "${backup_directory}")"

if [[ ! "${backup_name}" =~ ^mbolo-[0-9]{8}T[0-9]{6}Z$ ]]; then
    echo "ERREUR : nom de sauvegarde Mbolo non reconnu : ${backup_name}" >&2
    exit 1
fi

[[ -d "${backup_directory}" ]] || {
    echo "ERREUR : sauvegarde introuvable : ${backup_directory}" >&2
    exit 1
}

for command_name in gpg sha256sum tar tty; do
    if ! command -v "${command_name}" >/dev/null 2>&1; then
        echo "ERREUR : commande obligatoire introuvable : ${command_name}" >&2
        exit 1
    fi
done

mkdir -p -- "${destination_root}"
chmod 700 "${destination_root}"

encrypted_file="${destination_root}/${backup_name}.tar.gz.gpg"
checksum_file="${encrypted_file}.sha256"
temporary_file="${destination_root}/.${backup_name}.tar.gz.gpg.part"
temporary_checksum="${destination_root}/.${backup_name}.tar.gz.gpg.sha256.part"

cleanup_temporary_files() {
    rm -f -- "${temporary_file}" "${temporary_checksum}"
}

trap cleanup_temporary_files EXIT

if [[ -e "${encrypted_file}" || -e "${checksum_file}" ]]; then
    echo "ERREUR : la copie chiffrée existe déjà :" >&2
    echo "${encrypted_file}" >&2
    exit 1
fi

echo "[1/5] Vérification de la sauvegarde source"
bash scripts/verify-backup.sh "${backup_directory}"

echo "[2/5] Chiffrement AES-256"
echo
echo "GPG va demander une phrase secrète deux fois."
echo "Choisis une phrase longue et unique, puis conserve-la dans ton"
echo "gestionnaire de mots de passe. Sans elle, la restauration sera impossible."
echo

# Permet à pinentry de dialoguer avec le terminal WSL courant.
GPG_TTY="$(tty)"
export GPG_TTY

tar \
    -C "${backup_parent}" \
    -czf - \
    "${backup_name}" |
    gpg \
        --symmetric \
        --cipher-algo AES256 \
        --s2k-mode 3 \
        --s2k-digest-algo SHA512 \
        --compress-algo none \
        --no-symkey-cache \
        --output "${temporary_file}"

[[ -s "${temporary_file}" ]] || {
    echo "ERREUR : le fichier chiffré est vide." >&2
    exit 1
}

chmod 600 "${temporary_file}"
mv "${temporary_file}" "${encrypted_file}"

echo "[3/5] Calcul SHA-256 du fichier chiffré"

(
    cd "${destination_root}"
    sha256sum "$(basename "${encrypted_file}")" > "${temporary_checksum}"
)

chmod 600 "${temporary_checksum}"
mv "${temporary_checksum}" "${checksum_file}"

echo "[4/5] Vérification immédiate du déchiffrement"
echo "GPG peut redemander la phrase secrète pour ce contrôle."

gpg \
    --quiet \
    --no-symkey-cache \
    --decrypt "${encrypted_file}" |
    tar -tzf - > /dev/null

echo "[5/5] Copie chiffrée terminée"
echo
echo "Fichier : ${encrypted_file}"
echo "Checksum : ${checksum_file}"
du -sh "${encrypted_file}"
echo
echo "✅ Le contenu chiffré est lisible avec la phrase secrète fournie."
echo "✅ Aucun fichier intermédiaire non chiffré n'a été créé."

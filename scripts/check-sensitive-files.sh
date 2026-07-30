#!/usr/bin/env bash
#
# Vérifie qu'aucun secret ou artefact local connu n'est suivi par Git.
#
# Le contrôle porte sur l'index Git et non sur tous les fichiers présents
# localement. Un fichier .env.production ignoré peut donc rester sur le PC,
# mais il ne doit jamais apparaître dans `git ls-files`.

set -euo pipefail

if ! git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  echo "Erreur : cette commande doit être exécutée dans le dépôt Mbolo." >&2
  exit 1
fi

readonly forbidden_pattern='(^|/)\.env($|\.)|(^|/)(media|private_media|backups|encrypted-backups)/|(^|/)db\.sqlite3$|\.(pem|key|p12|pfx|gpg)$|(^|/)credentials/|(^|/)secrets/'

mapfile -t forbidden_files < <(
  git ls-files |
    grep -E "${forbidden_pattern}" |
    grep -Ev '(^|/)\.env\.example$' || true
)

if (( ${#forbidden_files[@]} > 0 )); then
  echo "ÉCHEC : des fichiers sensibles ou locaux sont suivis par Git :" >&2
  printf '  - %s\n' "${forbidden_files[@]}" >&2
  echo >&2
  echo "Ne les supprime pas directement. Retire-les uniquement de l'index" >&2
  echo "avec une procédure contrôlée, puis vérifie leur présence locale." >&2
  exit 1
fi

echo "OK : aucun secret, média privé ou fichier de sauvegarde connu n'est suivi."

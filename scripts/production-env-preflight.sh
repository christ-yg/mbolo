#!/usr/bin/env bash
set -Eeuo pipefail

project_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${project_root}"
env_file="${MBOLO_ENV_FILE:-.env.production}"

[[ -f "${env_file}" ]] || { echo "ERREUR : ${env_file} absent." >&2; exit 1; }

permissions="$(stat -c '%a' "${env_file}")"
if (( 10#${permissions} % 100 > 0 )); then
    echo "ERREUR : ${env_file} est accessible au groupe ou aux autres (${permissions})." >&2
    echo "Correction : chmod 600 ${env_file}" >&2
    exit 1
fi

required=(DJANGO_SECRET_KEY POSTGRES_DB POSTGRES_USER POSTGRES_PASSWORD REDIS_PASSWORD DJANGO_ALLOWED_HOSTS)
for name in "${required[@]}"; do
    value="$(sed -n "s/^${name}=//p" "${env_file}" | tail -n 1)"
    [[ -n "${value}" ]] || { echo "ERREUR : variable absente ou vide : ${name}" >&2; exit 1; }
    case "${value}" in
        *replace-with*|*changeme*|*CHANGE_ME*|*example*|*password123*)
            echo "ERREUR : valeur fictive ou faible détectée pour ${name}." >&2
            exit 1
            ;;
    esac
done

secret_key="$(sed -n 's/^DJANGO_SECRET_KEY=//p' "${env_file}" | tail -n 1)"
db_password="$(sed -n 's/^POSTGRES_PASSWORD=//p' "${env_file}" | tail -n 1)"
redis_password="$(sed -n 's/^REDIS_PASSWORD=//p' "${env_file}" | tail -n 1)"

(( ${#secret_key} >= 50 )) || { echo "ERREUR : DJANGO_SECRET_KEY doit contenir au moins 50 caractères." >&2; exit 1; }
(( ${#db_password} >= 16 )) || { echo "ERREUR : POSTGRES_PASSWORD doit contenir au moins 16 caractères." >&2; exit 1; }
(( ${#redis_password} >= 16 )) || { echo "ERREUR : REDIS_PASSWORD doit contenir au moins 16 caractères." >&2; exit 1; }

docker compose --env-file "${env_file}" -f compose.production.yaml config --quiet
echo "PRODUCTION_ENV_PREFLIGHT=OK"

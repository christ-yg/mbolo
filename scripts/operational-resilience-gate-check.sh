#!/usr/bin/env bash
set -Eeuo pipefail

project_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${project_root}"

required=(
    scripts/backup-mbolo.sh
    scripts/verify-backup.sh
    scripts/restore-mbolo.sh
    scripts/encrypt-backup.sh
    scripts/verify-encrypted-backup.sh
    scripts/backup-retention.sh
    scripts/production-env-preflight.sh
    scripts/release-manifest.sh
)

for path in "${required[@]}"; do
    [[ -s "${path}" ]] || { echo "ERREUR : fichier absent ou vide : ${path}" >&2; exit 1; }
    bash -n "${path}"
done

grep -Fq 'exec bash scripts/verify-backup.sh' scripts/backup-verify.sh
grep -Fq 'bash scripts/backup-mbolo.sh' scripts/backup-local.sh
grep -Fq 'exec bash scripts/restore-mbolo.sh' scripts/restore-local.sh
grep -Fq 'postgres.dump' scripts/backup-mbolo.sh
grep -Fq 'METADATA.txt' scripts/backup-mbolo.sh
grep -Fq -- '--restore-test' scripts/verify-backup.sh
grep -Fq 'AES256' scripts/encrypt-backup.sh

bash scripts/check-sensitive-files.sh
echo "OPERATIONAL_RESILIENCE_GATE_70_89=OK"

#!/usr/bin/env bash
set -Eeuo pipefail

project_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${project_root}"

output_directory="${MBOLO_RELEASE_EVIDENCE_DIR:-release-evidence}"
timestamp="$(date -u +%Y%m%dT%H%M%SZ)"
output_file="${output_directory}/mbolo-release-${timestamp}.txt"

mkdir -p -- "${output_directory}"
chmod 700 "${output_directory}"

{
    echo "application=mbolo"
    echo "created_at_utc=${timestamp}"
    echo "git_commit=$(git rev-parse HEAD)"
    echo "git_branch=$(git branch --show-current)"
    echo "git_dirty_files=$(git status --porcelain | wc -l | tr -d ' ')"
    echo "compose_file_sha256=$(sha256sum compose.production.yaml | awk '{print $1}')"
    echo "backend_image=$(docker compose --env-file .env.production -f compose.production.yaml images -q backend 2>/dev/null | head -n 1)"
    echo "frontend_image=$(docker compose --env-file .env.production -f compose.production.yaml images -q frontend 2>/dev/null | head -n 1)"
} > "${output_file}"

chmod 600 "${output_file}"
echo "RELEASE_MANIFEST=OK"
echo "Fichier : ${output_file}"

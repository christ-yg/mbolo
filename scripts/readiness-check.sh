#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."
BASE_URL="${MBOLO_BASE_URL:-http://127.0.0.1:8080}"
BASE_URL="${BASE_URL%/}"

tmp_dir="$(mktemp -d)"
trap 'rm -rf "$tmp_dir"' EXIT

check_endpoint() {
  local path="$1"
  local label="$2"
  local code

  code="$(curl --silent --show-error --output "$tmp_dir/body" --write-out '%{http_code}' "${BASE_URL}${path}")"

  if [[ "$code" != "200" ]] || ! grep -Fq '"status":"ok"' "$tmp_dir/body"; then
    echo "❌ ${label}: HTTP ${code}"
    exit 1
  fi

  echo "✅ ${label}: HTTP ${code}"
}

echo "[1/2] Liveness Django"
check_endpoint "/api/v1/health/live/" "Django répond"

echo "[2/2] Readiness applicative"
check_endpoint "/api/v1/health/ready/" "PostgreSQL et Redis disponibles"

echo "✅ READINESS_CHECK=OK"

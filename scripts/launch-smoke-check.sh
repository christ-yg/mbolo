#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."
BASE_URL="${MBOLO_BASE_URL:-http://127.0.0.1:8080}"
BASE_URL="${BASE_URL%/}"

if ! command -v curl >/dev/null 2>&1; then
  echo "❌ curl est requis pour le contrôle de lancement."
  exit 1
fi

tmp_dir="$(mktemp -d)"
trap 'rm -rf "$tmp_dir"' EXIT

request() {
  local path="$1" expected="$2" label="$3" code
  code="$(curl --silent --show-error --location --output "$tmp_dir/body" --write-out '%{http_code}' "${BASE_URL}${path}")"
  if [[ "$code" != "$expected" ]]; then
    echo "❌ ${label}: HTTP ${code}, attendu ${expected}"
    exit 1
  fi
  echo "✅ ${label}: HTTP ${code}"
}

echo "[1/5] Santé du proxy"
request "/healthz" "200" "Healthcheck Nginx"
grep -qx "ok" "$tmp_dir/body"

echo "[2/5] Santé applicative"
request "/api/v1/health/live/" "200" "Liveness Django"
grep -Fq '"status":"ok"' "$tmp_dir/body"
request "/api/v1/health/ready/" "200" "Readiness PostgreSQL + Redis"
grep -Fq '"status":"ok"' "$tmp_dir/body"

echo "[3/5] Pages publiques de lancement"
for path in / /about /how-it-works /help /safety /legal/privacy; do
  request "$path" "200" "$path"
done

echo "[4/5] API et administration"
request "/api/v1/csrf/" "200" "CSRF API"
admin_code="$(curl --silent --show-error --output /dev/null --write-out '%{http_code}' "${BASE_URL}/admin/")"
if [[ "$admin_code" != "200" && "$admin_code" != "302" ]]; then
  echo "❌ Admin: HTTP ${admin_code}, attendu 200 ou 302"
  exit 1
fi
echo "✅ Admin: HTTP ${admin_code}"

echo "[5/5] En-têtes de sécurité navigateur"
curl --silent --show-error --dump-header "$tmp_dir/headers" --output /dev/null "${BASE_URL}/"
for header in \
  "content-security-policy:" \
  "permissions-policy:" \
  "x-content-type-options: nosniff" \
  "x-frame-options: deny" \
  "referrer-policy: same-origin"; do
  if ! grep -Fqi "$header" "$tmp_dir/headers"; then
    echo "❌ En-tête absent ou inattendu : $header"
    exit 1
  fi
  echo "✅ $header"
done

echo "✅ LAUNCH_SMOKE=OK"
echo "ℹ️  URL contrôlée : ${BASE_URL}"

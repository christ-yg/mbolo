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
  local path="$1"
  local expected="$2"
  local label="$3"
  local code
  code="$(curl --silent --show-error --location --output "$tmp_dir/body" --write-out '%{http_code}' "${BASE_URL}${path}")"
  if [[ "$code" != "$expected" ]]; then
    echo "❌ ${label}: HTTP ${code}, attendu ${expected}"
    exit 1
  fi
  echo "✅ ${label}: HTTP ${code}"
}

echo "[1/4] Santé du proxy"
request "/healthz" "200" "Healthcheck"
if ! grep -qx "ok" "$tmp_dir/body"; then
  echo "❌ /healthz ne renvoie pas la réponse attendue."
  exit 1
fi

echo "[2/4] Pages publiques de lancement"
for path in / /about /how-it-works /help /safety /legal/privacy; do
  request "$path" "200" "$path"
done

echo "[3/4] API et administration"
request "/api/v1/csrf/" "200" "CSRF API"
admin_code="$(curl --silent --show-error --output /dev/null --write-out '%{http_code}' "${BASE_URL}/admin/")"
if [[ "$admin_code" != "200" && "$admin_code" != "302" ]]; then
  echo "❌ Admin: HTTP ${admin_code}, attendu 200 ou 302"
  exit 1
fi
echo "✅ Admin: HTTP ${admin_code}"

echo "[4/4] En-têtes de sécurité essentiels"
curl --silent --show-error --dump-header "$tmp_dir/headers" --output /dev/null "${BASE_URL}/"
for header in "x-content-type-options: nosniff" "x-frame-options: deny" "referrer-policy: same-origin"; do
  if ! grep -Fqi "$header" "$tmp_dir/headers"; then
    echo "❌ En-tête absent ou inattendu : $header"
    exit 1
  fi
  echo "✅ $header"
done

echo "✅ LAUNCH_SMOKE=OK"
echo "ℹ️  URL contrôlée : ${BASE_URL}"

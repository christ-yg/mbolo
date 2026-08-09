#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."
BASE_URL="${MBOLO_BASE_URL:-http://127.0.0.1:8080}"
BASE_URL="${BASE_URL%/}"

if ! command -v curl >/dev/null 2>&1; then
  echo "❌ curl est requis."
  exit 1
fi

headers="$(mktemp)"
trap 'rm -f "$headers"' EXIT

curl --silent --show-error --dump-header "$headers" --output /dev/null "${BASE_URL}/"

required_headers=(
  "content-security-policy:"
  "permissions-policy:"
  "referrer-policy: same-origin"
  "x-content-type-options: nosniff"
  "x-frame-options: deny"
)

for header in "${required_headers[@]}"; do
  if ! grep -Fqi "$header" "$headers"; then
    echo "❌ En-tête absent ou inattendu : $header"
    exit 1
  fi
  echo "✅ $header"
done

csp="$(grep -i '^content-security-policy:' "$headers" | tr -d '\r' | head -n 1)"
for directive in "default-src 'self'" "object-src 'none'" "frame-ancestors 'none'" "base-uri 'self'" "form-action 'self'"; do
  if [[ "$csp" != *"$directive"* ]]; then
    echo "❌ Directive CSP absente : $directive"
    exit 1
  fi
  echo "✅ CSP : $directive"
done

echo "✅ BROWSER_SECURITY_HEADERS=OK"
echo "ℹ️  URL contrôlée : ${BASE_URL}"

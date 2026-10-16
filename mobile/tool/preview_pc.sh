#!/usr/bin/env bash
# Local UI demonstration only: no connection to Django or real accounts.
set -euo pipefail
source_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
flutter_bin="${MBOLO_FLUTTER_BIN:-flutter}"
port="${MBOLO_PREVIEW_PORT:-8092}"
if ! [[ "$port" =~ ^[0-9]{1,5}$ ]] || ((10#$port < 1024 || 10#$port > 65535)); then
  echo 'MBOLO_PREVIEW_PORT must be between 1024 and 65535.' >&2
  exit 2
fi
command -v "$flutter_bin" >/dev/null || { echo 'Flutter introuvable : définir MBOLO_FLUTTER_BIN.' >&2; exit 1; }
preview_dir="$(mktemp -d "${TMPDIR:-/tmp}/mbolo-preview-pc-XXXXXX")"
printf 'Copie de démonstration : %s\n' "$preview_dir"
tar -C "$source_dir" --exclude='./.dart_tool' --exclude='./build' --exclude='./.expo' --exclude='./android' --exclude='./ios' --exclude='./.git' -cf - . | tar -C "$preview_dir" -xf -
cd "$preview_dir"
"$flutter_bin" create --platforms=web --project-name mbolo_mobile .
printf '\nDÉMONSTRATION FICTIVE : aucun compte ni message partagé avec Django.\nOuvrir http://localhost:%s dans le navigateur Windows. Ctrl+C pour arrêter.\n' "$port"
"$flutter_bin" run -d web-server --web-hostname 127.0.0.1 --web-port "$port" -t lib/main_preview.dart

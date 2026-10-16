#!/usr/bin/env bash
set -euo pipefail
source_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
flutter_bin="${MBOLO_FLUTTER_BIN:-flutter}"
command -v "$flutter_bin" >/dev/null || { echo 'Flutter introuvable.' >&2; exit 1; }
build_dir="$(mktemp -d "${TMPDIR:-/tmp}/mbolo-connected-XXXXXX")"
printf 'Copie de compilation : %s\n' "$build_dir"
tar -C "$source_dir" --exclude='./.dart_tool' --exclude='./build' --exclude='./.expo' --exclude='./android' --exclude='./ios' --exclude='./.git' -cf - . | tar -C "$build_dir" -xf -
cd "$build_dir"
"$flutter_bin" create --platforms=web --project-name mbolo_mobile .
"$flutter_bin" build web --release --target lib/main_browser.dart --base-href /mobile/
test -s build/web/index.html
printf '\nCompilation connectée terminée. Dans le terminal qui démarrera Compose :\nexport MBOLO_CONNECTED_WEB_DIR=%q\n' "$build_dir/build/web"

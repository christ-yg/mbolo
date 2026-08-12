#!/usr/bin/env bash
set -euo pipefail

readonly WORKFLOW_DIR=".github/workflows"
readonly SHA_PATTERN='^[0-9a-fA-F]{40}$'

if [[ ! -d "${WORKFLOW_DIR}" ]]; then
  echo "ERREUR : dossier ${WORKFLOW_DIR} introuvable." >&2
  exit 1
fi

mapfile -t workflow_files < <(
  find "${WORKFLOW_DIR}" -maxdepth 1 -type f \
    \( -name '*.yml' -o -name '*.yaml' \) -print | sort
)

if (( ${#workflow_files[@]} == 0 )); then
  echo "ERREUR : aucun workflow GitHub Actions trouvé." >&2
  exit 1
fi

echo "[1/2] Inventaire des actions externes"
external_count=0
failure_count=0

for workflow in "${workflow_files[@]}"; do
  while IFS= read -r record; do
    line_number="${record%%:*}"
    raw_line="${record#*:}"
    raw_reference="${raw_line#*uses:}"
    reference="${raw_reference%%#*}"
    reference="${reference//[[:space:]]/}"

    [[ -z "${reference}" ]] && continue
    [[ "${reference}" == ./* ]] && continue
    [[ "${reference}" == docker://* ]] && continue

    ((external_count += 1))

    if [[ "${reference}" != *@* ]]; then
      echo "❌ ${workflow}:${line_number}: référence sans version (${reference})" >&2
      ((failure_count += 1))
      continue
    fi

    revision="${reference##*@}"
    if [[ ! "${revision}" =~ ${SHA_PATTERN} ]]; then
      echo "❌ ${workflow}:${line_number}: action non épinglée (${reference})" >&2
      ((failure_count += 1))
      continue
    fi

    echo "✅ ${workflow}:${line_number}: ${reference}"
  done < <(grep -nE '^[[:space:]]*(-[[:space:]]*)?uses:' "${workflow}" || true)
done

echo "[2/2] Résultat"
if (( external_count == 0 )); then
  echo "ERREUR : aucune action externe détectée ; contrôle probablement incomplet." >&2
  exit 1
fi

if (( failure_count > 0 )); then
  echo "ERREUR : ${failure_count} référence(s) GitHub Actions non immuable(s)." >&2
  exit 1
fi

echo "✅ ${external_count} référence(s) externe(s) épinglée(s) sur des SHA immuables."
echo "✅ GITHUB_ACTIONS_PINNING=OK"

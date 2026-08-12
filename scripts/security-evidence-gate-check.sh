#!/usr/bin/env bash
set -euo pipefail

evidence_dir="security/evidence"

echo "[1/5] Présence des registres 50-69"
for number in $(seq 50 69); do
  count=$(find "$evidence_dir" -maxdepth 1 -type f -name "${number}_*.csv" | wc -l)
  test "$count" -eq 1 || { echo "ERREUR : registre $number absent ou dupliqué"; exit 1; }
done
echo "✅ 20 registres présents"

echo "[2/5] Validation des en-têtes CSV"
while IFS= read -r file; do
  header=$(head -n 1 "$file")
  test -n "$header" || { echo "ERREUR : en-tête vide : $file"; exit 1; }
  [[ "$header" == *,* ]] || { echo "ERREUR : CSV sans colonnes : $file"; exit 1; }
  if printf '%s' "$header" | grep -qE '(^|,)(password|token|private_key|secret)(,|$)'; then
    echo "ERREUR : colonne secrète interdite : $file"
    exit 1
  fi
done < <(find "$evidence_dir" -maxdepth 1 -type f -name '*.csv' | sort)
echo "✅ En-têtes CSV valides"

echo "[3/5] Modèles sans données opérationnelles"
while IFS= read -r file; do
  lines=$(wc -l < "$file")
  test "$lines" -eq 1 || { echo "ERREUR : le modèle doit rester vide : $file"; exit 1; }
done < <(find "$evidence_dir" -maxdepth 1 -type f -name '*.csv' | sort)
echo "✅ Aucun enregistrement réel suivi"

echo "[4/5] Recherche de secrets évidents"
if grep -RniE '(BEGIN (RSA |EC |OPENSSH )?PRIVATE KEY|gh[opsu]_[A-Za-z0-9]{20,}|AKIA[0-9A-Z]{16})' "$evidence_dir"; then
  echo "ERREUR : secret potentiel détecté"
  exit 1
fi
echo "✅ Aucun secret évident"

echo "[5/5] Intégrité Git"
git diff --check
echo "✅ SECURITY_EVIDENCE_GATE_50_69=OK"

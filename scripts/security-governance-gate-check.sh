#!/usr/bin/env bash
set -euo pipefail

files=(
  security/asvs/MBolo_ASVS_BASELINE.md
  security/threat-model/MBOLO_THREAT_MODEL.md
  security/risk-register/MBOLO_RISK_REGISTER.md
  security/policies/ACCESS_CONTROL_POLICY.md
  security/policies/INCIDENT_RESPONSE_POLICY.md
  security/policies/VULNERABILITY_MANAGEMENT_POLICY.md
  security/policies/BACKUP_RECOVERY_POLICY.md
  security/policies/LOGGING_MONITORING_POLICY.md
  security/policies/DATA_CLASSIFICATION_POLICY.md
  security/policies/PRIVACY_RETENTION_POLICY.md
  security/policies/SUPPLIER_SECURITY_POLICY.md
  security/policies/SECURE_SDLC_POLICY.md
  security/policies/CHANGE_MANAGEMENT_POLICY.md
  security/policies/CRYPTOGRAPHY_POLICY.md
  security/policies/BUSINESS_CONTINUITY_POLICY.md
  security/policies/SECURITY_TESTING_POLICY.md
  security/policies/ACCOUNT_LIFECYCLE_POLICY.md
  security/policies/MEDIA_PROTECTION_POLICY.md
  security/policies/AUDIT_EVIDENCE_POLICY.md
  security/policies/PRODUCTION_RELEASE_POLICY.md
)

echo "[1/4] Présence des 20 contrôles"
for file in "${files[@]}"; do
  test -s "$file" || { echo "ERREUR : fichier absent ou vide : $file"; exit 1; }
done
echo "✅ 20 contrôles documentés"

echo "[2/4] Absence de secrets évidents"
if grep -RniE '(BEGIN (RSA |EC |OPENSSH )?PRIVATE KEY|gh[opsu]_[A-Za-z0-9]{20,}|AKIA[0-9A-Z]{16})' security --include='*.md'; then
  echo "ERREUR : secret potentiel détecté"
  exit 1
fi
echo "✅ Aucun secret évident"

echo "[3/4] Couverture opérationnelle"
for term in authentification incident vulnérabil sauvegarde journal confidentialité fournisseur production; do
  grep -Rqi "$term" security || { echo "ERREUR : thème absent : $term"; exit 1; }
done
echo "✅ Thèmes critiques couverts"

echo "[4/4] Intégrité Git"
git diff --check
echo "✅ SECURITY_GOVERNANCE_GATE_30_49=OK"

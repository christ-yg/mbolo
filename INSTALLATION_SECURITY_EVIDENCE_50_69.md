# Installation du super-lot 50–69

Ce lot ajoute vingt modèles de registres de preuves opérationnelles ainsi qu’un contrôle CI. Les modèles restent volontairement vides dans Git afin d’éviter toute exposition de données personnelles ou sensibles.

## Validation locale

```bash
chmod +x scripts/security-evidence-gate-check.sh
bash scripts/security-evidence-gate-check.sh
bash scripts/security-governance-gate-check.sh
bash scripts/security-super-gate-check.sh
bash scripts/launch-smoke-check.sh
git diff --check
```

Résultats attendus :

- `SECURITY_EVIDENCE_GATE_50_69=OK`
- `SECURITY_GOVERNANCE_GATE_30_49=OK`
- `SECURITY_SUPER_GATE_20_29=OK`
- `LAUNCH_SMOKE=OK`

Branche prévue : `agent/security-evidence-50-69`.

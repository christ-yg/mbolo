# Installation du super-lot 30–49

Ce lot ajoute vingt contrôles documentés de gouvernance et un gate CI automatique. Il ne modifie ni les modèles Django, ni la base de données, ni le comportement public de Mbolo.

## Validation locale

```bash
chmod +x scripts/security-governance-gate-check.sh
bash scripts/security-governance-gate-check.sh
bash scripts/security-super-gate-check.sh
bash scripts/launch-smoke-check.sh
git diff --check
```

Résultats attendus :

- `SECURITY_GOVERNANCE_GATE_30_49=OK`
- `SECURITY_SUPER_GATE_20_29=OK`
- `LAUNCH_SMOKE=OK`

Le lot doit être livré dans une branche unique `agent/security-governance-30-49` et une seule pull request.

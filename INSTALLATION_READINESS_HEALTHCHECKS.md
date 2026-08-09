# Lot 13 — Liveness et readiness de production

## Objectif

Ce lot remplace le simple contrôle TCP du backend par un contrôle applicatif.
Docker ne considère désormais Django prêt que lorsque l'application répond et
que PostgreSQL ainsi que Redis sont disponibles.

## Endpoints

- `/api/v1/health/live/` : le processus Django répond ;
- `/api/v1/health/ready/` : Django, PostgreSQL et Redis sont disponibles ;
- `/api/v1/health/` : ancienne route conservée comme alias de readiness.

Les réponses restent volontairement minimales et ne révèlent ni version,
ni nom d'hôte, ni détail d'erreur.

## Installation et validation

```bash
unzip -o /mnt/c/Users/User/Downloads/mbolo-readiness-healthchecks-batch-13.zip
chmod +x scripts/readiness-check.sh scripts/launch-smoke-check.sh

docker compose \
  --env-file .env.production \
  -f compose.production.yaml \
  up -d --build

docker compose \
  --env-file .env.production \
  -f compose.production.yaml \
  exec backend \
  python manage.py test apps.core.tests.test_health_checks

bash scripts/readiness-check.sh
bash scripts/launch-smoke-check.sh
```

Résultats attendus : 5 tests réussis, backend `healthy`,
`READINESS_CHECK=OK` et `LAUNCH_SMOKE=OK`.

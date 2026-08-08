# Mbolo — Lot 10 : contrat API de production

## Objectif

Ce lot verrouille le préfixe public de l'API frontend sur `/api`.
Les services React ajoutent déjà `/v1/...` à ce préfixe. Une configuration
ancienne en `/api/v1` produirait donc des URLs incorrectes en
`/api/v1/v1/...`.

## Modifications

- `.env.example` documente désormais `VITE_API_BASE_URL=/api` ;
- `frontend/Dockerfile.production` injecte explicitement `/api` pendant le
  build Docker, même sur une machine neuve sans fichier Vite local ;
- `frontend/e2e/authenticated-core.spec.ts` refuse une requête contenant le
  préfixe dupliqué `/api/v1/v1/`.

## Validation locale

Depuis la racine du dépôt :

```bash
cd frontend
npm run check
cd ..

docker compose --env-file .env.production -f compose.production.yaml up -d --build frontend

MBOLO_E2E_BASE_URL=http://127.0.0.1:8080 \
  npm --prefix frontend run test:e2e:auth-core

git diff --check
git status -sb
git diff --stat
```

## Résultat attendu

- le build frontend réussit ;
- l'image Docker frontend est reconstruite avec `/api` ;
- les trois parcours authentifiés passent ;
- aucune requête `/api/v1/v1/...` n'est acceptée par le test navigateur.

## Sécurité

Le préfixe reste relatif au même domaine. Aucun secret, compte réel ou service
payant n'est ajouté. Ce lot réduit aussi le risque d'une divergence silencieuse
entre une machine de développement, la CI et le futur serveur public.

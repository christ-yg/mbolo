# Lot 09 — Gate UI authentifié

Ce lot ajoute une couverture navigateur des parcours privés essentiels de Mbolo sans utiliser de compte réel, de mot de passe réel ou de service payant.

## Contenu

- `frontend/e2e/authenticated-core.spec.ts` : scénarios Playwright isolés pour Découvrir, match, messages et galerie photos.
- `frontend/package.json` : commande `npm run test:e2e:auth-core`.
- `.github/workflows/ci.yml` : exécute les scénarios privés après les scénarios publics.
- correction de `VITE_API_BASE_URL` de `/api/v1` vers `/api`, conformément au contrat réel du frontend qui ajoute déjà `/v1/...` dans ses services.

## Sécurité

Les identifiants présents dans le test sont des UUID fictifs et l'adresse utilise le domaine réservé `.invalid`. Aucun mot de passe n'est stocké. Les réponses API sont simulées dans le navigateur uniquement ; les contrôles d'autorisation backend restent couverts par les tests Django existants.

## Vérification locale

```bash
cd frontend
npm run check
MBOLO_E2E_BASE_URL=http://127.0.0.1:4173 npm run test:e2e:auth-core
```

Pour la deuxième commande, une prévisualisation Vite construite avec `VITE_API_BASE_URL=/api` doit être active sur `127.0.0.1:4173`.

## Résultat attendu

Trois tests privés réussissent :

1. Découvrir affiche le profil fictif puis la fenêtre de match après un like.
2. Messages affiche une conversation privée avec un message non lu.
3. Photos affiche une galerie et un statut de modération approuvé.

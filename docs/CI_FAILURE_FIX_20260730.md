# Correction de la CI Mbolo — 30 juillet 2026

## Résultat attendu

La CI doit valider trois barrières :

1. absence de secrets et d'artefacts locaux suivis par Git ;
2. qualité et sécurité du frontend React ;
3. qualité, migrations, tests et sécurité du backend Django.

## Correction du frontend

`react-router-dom` est verrouillé sur `7.18.2`, qui corrige les anciennes
vulnérabilités détectées dans `7.11.0`.

L'avis `GHSA-qwww-vcr4-c8h2` affecte la plage `>=7.12.0 <8.3.0`, mais seulement
les API RSC instables. Mbolo est une SPA Vite et n'utilise pas ces API.
La version corrigée `8.3.0` n'étant pas encore publiée dans npm au moment de
la correction, une dérogation temporaire et strictement limitée à cet avis
est appliquée jusqu'au 31 août 2026.

Le script `frontend/scripts/audit-production.mjs` continue de bloquer toute
autre vulnérabilité haute ou critique. Il bloquera également la CI après la
date d'expiration afin d'imposer une nouvelle revue du risque.

## Correction du backend

Le fournisseur de paiement `mbolo_test` exige volontairement
`APP_DEBUG=true`. Cette valeur est activée uniquement dans le runner GitHub
Actions éphémère. La configuration réelle de préproduction et de production
reste inchangée avec `APP_DEBUG=false`.

Cette séparation empêche l'activation accidentelle du paiement fictif dans un
environnement réel tout en permettant aux tests CI de démarrer.

## Modernisation des actions GitHub

Les actions officielles `checkout`, `setup-node` et `setup-python` utilisent
leurs versions 7 basées sur Node.js 24. Cela supprime les avertissements liés
à la dépréciation de Node.js 20 dans GitHub Actions.

## Traçabilité ISO 27001 et RGPD

- La décision de risque est limitée, datée et techniquement justifiée.
- La barrière de sécurité n'est pas désactivée globalement.
- Les secrets restent absents du dépôt et les permissions CI restent en
  lecture seule.
- Aucun contenu utilisateur, média, mot de passe ou donnée personnelle n'est
  ajouté au ZIP correctif.

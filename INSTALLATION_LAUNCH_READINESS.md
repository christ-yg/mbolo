# Mbolo — Lot 05 Référencement et contrôle de lancement

## Objectif

Ce lot corrige gratuitement les éléments encore laissés par défaut dans le frontend Vite et ajoute un contrôle automatisé avant mise en production.

Il apporte : langue française, vrai titre et description Mbolo, métadonnées sociales, `robots.txt`, sitemap des pages publiques et smoke test des routes/en-têtes de sécurité.

## Installation

Extraire le ZIP à la racine de `~/projects/mbolo`, puis :

```bash
chmod +x scripts/launch-smoke-check.sh
cd frontend
npm run check
cd ..
bash scripts/launch-smoke-check.sh
```

Le résultat final attendu est `LAUNCH_SMOKE=OK`.

## Domaine

Le sitemap cible `https://mbolo.ga`, domaine déjà prévu dans la configuration de production du projet. Lors de l'activation définitive du domaine, vérifier que cette URL est bien celle réellement déployée.

## Limite normale d'une SPA

Cette base est suffisante pour préparer le MVP. Un référencement avancé page par page pourra plus tard utiliser du rendu serveur ou du pré-rendu ; ce point n'empêche pas la mise en production du MVP.

# Mbolo — Lot 06 Recette automatique gratuite

## Objectif

Ce lot crée une barrière de validation unique avant livraison ou déploiement.
Il ne modifie pas les données actives et n'utilise aucun service payant.

La recette vérifie :

- Docker Compose ;
- Django et les migrations ;
- la dernière sauvegarde ;
- les routes et les en-têtes de sécurité ;
- le build frontend ;
- les pages publiques sur ordinateur ;
- les pages essentielles sur viewport mobile ;
- les métadonnées SEO, `robots.txt` et `sitemap.xml` ;
- la protection de `/discovery` pour un visiteur anonyme.

## Installation

Extraire le ZIP à la racine de `~/projects/mbolo`, puis :

```bash
chmod +x scripts/release-gate-free.sh
cd frontend
npm install
npx playwright install chromium
cd ..
```

`npm install` met à jour `package-lock.json` uniquement si le nouveau script du
fichier `package.json` le nécessite. Aucune nouvelle dépendance n'est ajoutée.

## Exécution

Les services Docker de préproduction doivent déjà être démarrés. Lancer :

```bash
bash scripts/release-gate-free.sh
```

Résultat final attendu :

```text
RELEASE_GATE_FREE=OK
```

## Données et sécurité

Ces scénarios publics ne demandent aucun mot de passe et ne créent aucun compte.
Le compte Sarah reste réservé aux scénarios authentifiés existants et son mot de
passe ne doit jamais être écrit dans un fichier ou envoyé sur GitHub.

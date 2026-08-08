# Mbolo — Lot 08 : Playwright dans GitHub CI

## Objectif

Ce lot ajoute un quatrième contrôle GitHub Actions : **Parcours publics E2E**.
À chaque pull request vers `main`, GitHub construit le frontend, démarre une
prévisualisation locale et exécute les 13 scénarios publics avec Chromium.

Le contrôle ne demande :

- aucun compte Mbolo ;
- aucun mot de passe ;
- aucun secret GitHub ;
- aucun service payant ;
- aucune connexion à la base de données de préproduction.

## Vérification locale

Après extraction du ZIP à la racine du projet :

```bash
git diff --check
git diff -- .github/workflows/ci.yml
git status -sb
```

Le nouveau job sera réellement validé après le push de la branche et la
création de la pull request. GitHub devra afficher quatre contrôles verts :

1. Backend Django ;
2. Frontend React ;
3. Secrets et artefacts ;
4. Parcours publics E2E.

## Sécurité

Le serveur Vite de CI écoute uniquement sur `127.0.0.1`. Les traces et captures
Playwright restent temporaires sur le runner et ne sont pas publiées comme
artefacts. Le workflow conserve la permission minimale `contents: read`.

# Lot 16 — Scan gratuit des images Docker

## Objectif

Les audits npm et pip déjà présents contrôlent les dépendances applicatives,
mais pas les paquets du système Linux contenus dans les images finales.

Ce lot ajoute Trivy à GitHub Actions afin de scanner :

- l'image backend Python et Django ;
- l'image frontend Nginx ;
- les bibliothèques applicatives embarquées ;
- les paquets du système d'exploitation.

## Politique de blocage

La CI bloque une fusion lorsqu'une vulnérabilité réunit les deux conditions :

1. gravité CRITICAL ;
2. correctif déjà disponible.

Les vulnérabilités sans correctif restent visibles, mais ne bloquent pas le
projet. Cette politique évite les faux blocages impossibles à corriger.

## Coût et confidentialité

- Trivy est open source ;
- le workflow utilise le runner GitHub existant ;
- aucune image n'est publiée dans un registre ;
- aucun secret de production n'est transmis ;
- les permissions GitHub restent limitées à contents: read.

## Fichiers du lot

- .github/workflows/container-security.yml
- INSTALLATION_CONTAINER_SECURITY.md

## Installation

    cd ~/projects/mbolo
    unzip -o /mnt/c/Users/User/Downloads/mbolo-container-security-batch-16.zip

## Contrôles locaux

Le scan Trivy complet sera exécuté par GitHub après le push. Avant le commit :

    docker build -f backend/Dockerfile.production -t mbolo-backend-security:local .
    docker build -f frontend/Dockerfile.production -t mbolo-frontend-security:local .
    git diff --check
    git status -sb
    git diff --stat
    git ls-files --others --exclude-standard

## Résultat attendu sur GitHub

Un nouveau contrôle nommé Vulnérabilités des images Docker doit apparaître.
Il doit construire les deux images puis terminer en vert.

Si une vulnérabilité critique corrigeable est détectée, la CI indiquera le
paquet concerné, sa version installée et la version contenant le correctif.

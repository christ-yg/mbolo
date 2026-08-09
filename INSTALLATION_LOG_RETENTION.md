# Lot 15 — Rotation des journaux Docker

## Objectif

Ce lot empêche les journaux des conteneurs Mbolo de grossir sans limite et de
remplir le disque du futur serveur. La protection utilise uniquement le pilote
Docker local json-file : aucun abonnement ni service externe n'est requis.

Chaque service conserve par défaut cinq fichiers de dix mégaoctets, soit
environ 50 Mio maximum par conteneur.

## Fichiers du lot

- .env.example : documente les deux paramètres de rétention ;
- compose.production.yaml : applique la politique aux quatre services ;
- scripts/log-retention-check.sh : vérifie la déclaration et les conteneurs ;
- INSTALLATION_LOG_RETENTION.md : procédure complète.

## Installation

    cd ~/projects/mbolo
    unzip -o /mnt/c/Users/User/Downloads/mbolo-log-retention-batch-15.zip
    chmod +x scripts/log-retention-check.sh

Les valeurs sécurisées par défaut sont utilisées automatiquement. Il n'est pas
obligatoire de modifier le fichier secret .env.production.

## Recréation des services

La configuration des journaux est attachée à la création du conteneur. Les
conteneurs doivent donc être recréés :

    docker compose --env-file .env.production -f compose.production.yaml up -d --force-recreate

## Contrôles

    bash scripts/log-retention-check.sh
    bash scripts/readiness-check.sh
    bash scripts/launch-smoke-check.sh
    git diff --check
    git status -sb
    git diff --stat
    git ls-files --others --exclude-standard

## Résultats attendus

- les quatre services sont sains ;
- chaque conteneur utilise json-file, 10m et 5 ;
- LOG_RETENTION=OK ;
- READINESS_CHECK=OK ;
- LAUNCH_SMOKE=OK ;
- aucune erreur produite par git diff --check.

## Personnalisation facultative

Pour modifier la limite plus tard, ajouter dans .env.production :

    MBOLO_LOG_MAX_SIZE=10m
    MBOLO_LOG_MAX_FILES=5

Il faut ensuite recréer les conteneurs avec --force-recreate.

# Environnement local de développement

## Services

Mbolo utilise Docker Compose pour exécuter localement :

- PostgreSQL ;
- Redis.

## État de santé

Chaque service possède un contrôle de santé Docker.

Un conteneur marqué `healthy` répond correctement aux tests définis dans
`compose.yaml`.

## Réseau

PostgreSQL et Redis communiquent à travers le réseau Docker :

`mbolo_data_network`

Les services de données ne doivent jamais être exposés directement à Internet.

## Persistance

Les données sont stockées dans les volumes :

- `mbolo_postgres_data`
- `mbolo_redis_data`

## Secrets

Les secrets locaux sont conservés dans `.env`.

Ce fichier :

- est exclu de Git ;
- possède les permissions `600` ;
- ne doit jamais être publié ;
- ne doit jamais contenir des secrets de production.

## Commandes utiles

Démarrer :

```bash
docker compose up -d

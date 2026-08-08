# Mbolo — Lot 01 HTTPS gratuit

## Objectif

Ce lot prépare le futur HTTPS public sans acheter de serveur et sans casser la
préproduction locale actuelle.

Il ajoute un proxy TLS Caddy devant le frontend Nginx et corrige la transmission
du protocole original jusqu'à Django.

## Installation

Depuis le dossier `~/projects/mbolo`, extraire l'archive complète. Les chemins
contenus dans le ZIP placent automatiquement chaque fichier au bon endroit.

Rendre ensuite le script exécutable :

```bash
chmod +x scripts/https-local-check.sh
```

## Validation locale

```bash
bash scripts/https-local-check.sh
```

Résultats attendus :

- `https://localhost:8443/healthz` répond ;
- l'accueil répond HTTP 200 ;
- la route CSRF répond HTTP 200 ;
- l'administration répond HTTP 200 ou 302 ;
- `http://127.0.0.1:8080` continue de fonctionner.

Le navigateur peut afficher une alerte pour `https://localhost:8443`. Elle est
normale : le certificat local est signé par l'autorité interne de Caddy et ne
doit jamais être confondu avec le futur certificat public.

## Arrêter uniquement la simulation HTTPS

```bash
docker compose \
  --env-file .env.production \
  -f compose.production.yaml \
  -f compose.https-local.yaml \
  stop edge
```

## Future production publique

Sur le futur VPS seulement :

```bash
docker compose \
  --env-file .env.production \
  -f compose.production.yaml \
  -f compose.https-public.yaml \
  up -d
```

Avant cette commande, les DNS devront pointer vers le VPS et les variables
Django de production devront être activées : confiance du proxy, redirection
HTTPS et protections HSTS. Le HSTS preload restera désactivé pendant la phase
initiale de validation.

## Sécurité

- aucun certificat privé ni secret n'est inclus dans l'archive ;
- PostgreSQL et Redis restent sur le réseau Docker interne ;
- le port HTTP local 8080 reste lié à `127.0.0.1` ;
- le HTTPS public n'est exposé que par le fichier Compose public ;
- les certificats automatiques sont conservés dans des volumes Docker dédiés.


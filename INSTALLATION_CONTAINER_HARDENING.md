# Mbolo — Lot 11 : durcissement des conteneurs

## Objectif

Ce lot réduit la surface d'attaque des conteneurs applicatifs de production,
sans ajouter de fournisseur, de licence ou de service payant.

## Protections ajoutées

- construction multi-étape du backend : les compilateurs restent dans le
  builder et ne sont pas copiés dans l'image finale ;
- exécution de Django avec l'utilisateur non privilégié `mbolo` ;
- systèmes de fichiers du backend et du frontend montés en lecture seule ;
- dossiers temporaires explicitement limités avec `tmpfs` ;
- suppression de toutes les capacités Linux du backend ;
- Nginx conserve uniquement `NET_BIND_SERVICE`, `CHOWN`, `SETUID` et `SETGID` :
  ces capacités lui permettent d'ouvrir le port interne 80, de préparer ses
  dossiers temporaires puis d'abandonner ses privilèges pour ses workers ;
- limites de processus et délais d'arrêt propres ;
- script reproductible de vérification du durcissement.

## Fichiers du lot

- `backend/Dockerfile.production`
- `compose.production.yaml`
- `scripts/container-hardening-check.sh`
- `INSTALLATION_CONTAINER_HARDENING.md`

## Validation locale

```bash
chmod +x scripts/container-hardening-check.sh
bash scripts/container-hardening-check.sh

docker compose --env-file .env.production -f compose.production.yaml up -d
bash scripts/launch-smoke-check.sh

git diff --check
git status -sb
git diff --stat
git ls-files --others --exclude-standard
```

## Résultat attendu

- `CONTAINER_HARDENING=OK` ;
- les services PostgreSQL, Redis, backend et frontend deviennent sains ;
- le smoke test renvoie `LAUNCH_SMOKE=OK` ;
- aucun secret ni fichier `.env.production` n'est ajouté à Git.

## Limites volontaires

PostgreSQL et Redis conservent leurs systèmes de fichiers persistants en
écriture, car ils doivent stocker les données. Ils restent isolés dans le
réseau interne `data_network` et protégés par mot de passe.

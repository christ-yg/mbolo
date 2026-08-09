# Lot 14 — En-têtes de sécurité navigateur

Ce lot ajoute une politique CSP restrictive et vérifie que les ressources
publiques conservent les en-têtes de sécurité, y compris sous `/static/` et
`/media/`.

## Fichiers

- `deploy/nginx/default.conf`
- `deploy/caddy/Caddyfile.local`
- `deploy/caddy/Caddyfile.production`
- `scripts/launch-smoke-check.sh`
- `scripts/security-headers-check.sh`

## Installation

```bash
cd ~/projects/mbolo
unzip -o /mnt/c/Users/User/Downloads/mbolo-browser-security-headers-batch-14.zip
chmod +x scripts/security-headers-check.sh scripts/launch-smoke-check.sh

docker compose --env-file .env.production -f compose.production.yaml up -d --build frontend
bash scripts/security-headers-check.sh
bash scripts/launch-smoke-check.sh

git diff --check
git status -sb
git diff --stat
git ls-files --others --exclude-standard
```

## Résultat attendu

- `BROWSER_SECURITY_HEADERS=OK`
- `LAUNCH_SMOKE=OK`
- aucune erreur de `git diff --check`

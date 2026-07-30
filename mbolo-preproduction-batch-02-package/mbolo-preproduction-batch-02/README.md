# Mbolo — Préproduction 02

Ce lot ajoute une infrastructure de production séparée du développement local :

- images Docker backend et frontend ;
- Nginx pour le SPA, l’API, l’administration, les WebSockets, les statiques et les médias publics ;
- PostgreSQL et Redis non exposés sur Internet ;
- volumes persistants ;
- health checks ;
- configuration HTTPS derrière un reverse proxy TLS ;
- scripts de validation, démarrage, arrêt, sauvegarde et restauration.

Le certificat TLS doit être terminé par le reverse proxy public du serveur (Caddy, Traefik, Nginx hôte ou load balancer). Le conteneur frontend écoute uniquement sur `127.0.0.1:8080` par défaut.

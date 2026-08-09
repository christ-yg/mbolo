# Mbolo — Lot 12 : IP client fiable et limites anti-abus

## Objectif

Ce lot corrige l'identification réseau utilisée par les limites de sécurité et
les journaux pseudonymisés lorsque Mbolo fonctionne derrière Caddy et Nginx.

Sans cette chaîne explicite, Django voit principalement l'adresse du conteneur
Nginx. Tous les visiteurs risquent alors de partager le même compteur de
connexion, ce qui permettrait à un attaquant de bloquer temporairement les
autres membres.

## Chaîne de confiance

1. Caddy observe l'adresse du visiteur et écrase `X-Mbolo-Client-IP`.
2. Nginx transmet cet en-tête privé au backend sur le réseau Docker.
3. Django ne le lit que si `DJANGO_TRUST_MBOLO_CLIENT_IP_HEADER=true`.
4. La valeur doit être une adresse IPv4 ou IPv6 valide ; sinon Django utilise
   `REMOTE_ADDR`.
5. L'adresse n'est jamais stockée en clair dans l'historique : elle est
   pseudonymisée par HMAC comme auparavant.

La confiance est activée uniquement par les overlays HTTPS local et public.
Le Compose de base et `.env.example` la laissent désactivée.

## Protections ajoutées

- inscription : 10 tentatives par IP et par heure ;
- confirmation 2FA : 20 tentatives par IP et par cinq minutes ;
- confirmation 2FA : 5 essais par challenge signé et par cinq minutes ;
- réutilisation de l'IP normalisée par les limites de connexion, vérification
  d'e-mail et réinitialisation de mot de passe déjà présentes.

Les clés Redis restent pseudonymisées avec HMAC-SHA256 et expirent
automatiquement.

## Installation et validation

Depuis `~/projects/mbolo` :

```bash
chmod +x scripts/client-ip-throttling-check.sh
bash scripts/client-ip-throttling-check.sh
```

Résultats attendus :

- configurations Compose et Caddy valides ;
- images backend et frontend construites ;
- 6 tests unitaires réussis ;
- contrôle fonctionnel du site réussi ;
- `CLIENT_IP_THROTTLING=OK`.

## Sécurité et confidentialité

- aucun secret ni véritable fichier `.env.production` n'est inclus ;
- un client direct ne peut pas activer lui-même la confiance dans l'en-tête ;
- une valeur non-IP est rejetée ;
- les journaux conservent uniquement une empreinte irréversible ;
- les limites sont partagées entre processus grâce à Redis.

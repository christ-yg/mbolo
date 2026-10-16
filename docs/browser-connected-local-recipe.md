# Recette connectée React / Flutter sur PC

Lot préparé, non exécuté : Flutter, Docker et Caddy ne sont pas disponibles dans
l'environnement de préparation. Le contrôle shell et diff --check sont réussis.
La CI ajoute une compilation explicite de main_browser.dart ; la preview fictive
main_preview.dart ne valide pas cette entrée.

## Compiler sans modifier le dépôt de travail

Depuis la racine :

```bash
MBOLO_FLUTTER_BIN="$HOME/develop/flutter/bin/flutter" bash mobile/tool/build_browser_connected.sh
```

Le script affiche une commande export MBOLO_CONNECTED_WEB_DIR. Copier cette
commande dans le terminal utilisé pour Compose. Le dossier compilé est une copie
temporaire : ne pas le supprimer pendant le test. Ne jamais monter les sources
ou le dossier contenant .env.production à la place de build/web.

## Conditions backend à vérifier avant démarrage

Le backend doit accepter localhost et l'origine https://localhost:8444 dans
DJANGO_CSRF_TRUSTED_ORIGINS ; il doit reconnaître le protocole du proxy de
confiance (DJANGO_TRUST_X_FORWARDED_PROTO). Les cookies Secure et HttpOnly doivent
être activés pour cette recette HTTPS. Ne pas désactiver CSRF ou la vérification TLS.
La configuration du backend n'est pas automatiquement modifiée par ce lot.
Ne pas partager .env.production ou la sortie complète de compose config.
Si une adaptation est nécessaire, sauvegarder ce fichier avant édition et tenir
compte des autres origines de test existantes.

## Valider puis démarrer le service supplémentaire

Après vérification des conditions précédentes :

```bash
docker compose --env-file .env.production -f compose.production.yaml -f compose.email-local.yaml -f compose.browser-test.yaml config --quiet
docker compose --env-file .env.production -f compose.production.yaml -f compose.email-local.yaml -f compose.browser-test.yaml run --rm --no-deps browser-test caddy validate --config /etc/caddy/Caddyfile --adapter caddyfile
docker compose --env-file .env.production -f compose.production.yaml -f compose.email-local.yaml -f compose.browser-test.yaml up -d --no-deps browser-test
```

Le frontend doit déjà être sain. Seul browser-test est démarré. Aucun volume de
base de données n'est supprimé. Aucun domaine ni serveur AWS n'est nécessaire.
Le port est lié à 127.0.0.1, donc non publié sur les interfaces réseau externes.

## Certificat local

Caddy crée une autorité interne spécifique, conservée dans browser_test_data.
Le navigateur Windows doit faire confiance à son certificat racine public.
Exporter uniquement ce certificat (jamais les clés) après démarrage :

```bash
docker compose --env-file .env.production -f compose.production.yaml -f compose.email-local.yaml -f compose.browser-test.yaml cp browser-test:/data/caddy/pki/authorities/local/root.crt /tmp/mbolo-browser-test-root.crt
openssl x509 -in /tmp/mbolo-browser-test-root.crt -noout -subject -issuer -fingerprint -sha256
```

Vérifier que ce certificat provient bien de ce service local avant de l'importer
dans le magasin des autorités racines de l'utilisateur Windows pour la recette.
Conserver son empreinte pour le retirer ensuite si l'environnement est abandonné.
Ne pas simplement ignorer les erreurs de certificat et ne pas exporter root.key.
Cette étape de confiance doit être réalisée sur le PC de test, pas dans le dépôt.

## Parcours de recette

1. Ouvrir https://localhost:8444/ dans un profil de navigateur et connecter Alex.
2. Ouvrir https://localhost:8444/mobile/ dans un autre profil et connecter Sarah.
3. Vérifier les profils et le match ; envoyer un message de chaque côté.
4. Actualiser les pages et contrôler la conservation des messages et de la session.
5. Déconnecter Sarah, actualiser et vérifier qu'aucune donnée privée n'est affichée.
6. Contrôler les cookies via les outils développeur : sessionid HttpOnly et Secure.
7. Tester une panne réseau, puis la reprise, sans afficher de succès fictif.

Deux onglets du même profil partagent les cookies : ils ne représentent pas deux
sessions indépendantes. La preview sur 8092 reste une démonstration séparée.

Arrêter uniquement le service de recette :

```bash
docker compose --env-file .env.production -f compose.production.yaml -f compose.email-local.yaml -f compose.browser-test.yaml stop browser-test
```

## Limites

Aucun test navigateur connecté n'est déclaré réussi à ce stade. Les tests natifs
Android/iOS restent distincts. L'alerte Twisted CVE-2026-106454 demeure ouverte.
Ce lot ne constitue ni une mise en production ni une validation boutique.

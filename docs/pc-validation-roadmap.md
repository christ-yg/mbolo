# Recette PC et programme de 200 unités

## État vérifié le 16 octobre 2026

Les échanges React entre Alex et Sarah ont été confirmés par l'utilisateur.
Flutter détecte le téléphone, le SDK est installé et les licences sont acceptées.
La compilation locale Android n'a pas encore de résultat fourni. Le test téléphone
est suspendu à la demande de l'utilisateur. La production publique n'est pas validée.

## Preview Flutter sur PC

Depuis la racine du dépôt :

```bash
MBOLO_FLUTTER_BIN="$HOME/develop/flutter/bin/flutter" bash mobile/tool/preview_pc.sh
```

Ouvrir http://localhost:8092 dans le navigateur Windows. Garder le terminal ouvert.
Le site React existant reste sur http://localhost:8080.
Le script copie les sources dans un dossier temporaire affiché, génère uniquement
le support Web dans cette copie et utilise main_preview.dart (DemoApi).
Il n'expose le serveur que sur 127.0.0.1 et ne publie rien sur GitHub.
Le port peut être changé avec MBOLO_PREVIEW_PORT. Arrêt par Ctrl+C.
Les copies temporaires ne sont pas supprimées automatiquement, pour permettre
l'inspection d'un échec ; leur chemin est affiché au démarrage.

La preview contient des données fictives. Elle ne partage ni comptes ni messages
avec Django et ne valide pas caméra, stockage sécurisé natif ou comportement Android.
Ne pas y saisir les mots de passe des comptes réels. Le client MboloApi actuel
est natif : le navigateur nécessite une gestion dédiée des cookies HttpOnly et
CSRF avant toute recette connectée. Ne pas désactiver TLS ou CSRF pour contourner cela.

## Programme : 200 unités à détailler et vérifier

Ces plages sont une capacité de planification, pas 200 fonctionnalités terminées.
Chaque unité devra disposer d'un résultat observable avant d'être déclarée terminée.
Les fonctions existantes doivent être auditées avant tout ajout redondant.

| Unités | Axe | Résultat attendu | État |
| --- | --- | --- | --- |
| 001–020 | Recette PC | lancement isolé, scénarios reproductibles, preuves | script préparé, exécution Flutter à vérifier |
| 021–040 | Session Flutter navigateur | cookies navigateur, CSRF, erreurs et déconnexion | à concevoir |
| 041–060 | Comptes et confidentialité | isolation des comptes et accès privés vérifiés | à auditer |
| 061–080 | Profils et photos | parcours réels et erreurs de fichiers vérifiés | à auditer |
| 081–100 | Découverte et intérêts | filtres, pagination, réponses et exclusions vérifiés | à auditer |
| 101–120 | Matchs et messagerie | échanges croisés, reprise réseau et isolation vérifiés | à auditer |
| 121–140 | Notifications | lecture, préférences et actualisation vérifiées | à auditer |
| 141–160 | Sécurité et modération | blocage, signalement et réauthentification vérifiés | à auditer |
| 161–180 | Accessibilité et performance | clavier, contraste, affichage mobile et mesures | à auditer |
| 181–200 | Préparation bêta | HTTPS, restauration, exploitation et preuves CI | à préparer |

Publier chaque super-lot uniquement après autorisation explicite de ses fichiers.
Les tests PC ne remplacent pas les tests Android/iOS ni une validation boutique.

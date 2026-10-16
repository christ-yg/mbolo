# Recette locale Web et Mobile avec quatre comptes

Aucun serveur AWS ni domaine nécessaire pour commencer la recette Web locale.
La commande suivante doit être exécutée seulement sur une base locale de test.
Elle crée Alex, Sarah, Audrey et Marc, membres ordinaires adultes, avec des adresses
fictives `beta.alex@mbolo.example`, `beta.sarah@mbolo.example`,
`beta.audrey@mbolo.example`, `beta.marc@mbolo.example`.
Elle demande deux fois chaque mot de passe sans l'afficher. Elle refuse de remplacer
un compte existant et ne fabrique ni match ni message. Les e-mails sont prévalidés
uniquement pour cette recette : la délivrabilité réelle n'est donc PAS testée.

Après publication et récupération du lot, depuis le dépôt local :

```bash
# Backend Django lancé avec le venv local :
cd backend
python manage.py seed_beta_accounts --confirm-local-preproduction
```

Ou depuis la racine, si la préproduction Docker est déjà en fonctionnement :

```bash
docker compose --env-file .env.production -f compose.production.yaml exec backend python manage.py seed_beta_accounts --confirm-local-preproduction
```

Choisir la commande correspondant à l'installation existante ; ne pas démarrer une
seconde base par inadvertance. Ne jamais exécuter cette commande en production.
Ne pas mettre les mots de passe dans Git ni les réutiliser sur un vrai compte.

## Parcours à exécuter

1. Ouvrir quatre profils de navigateur indépendants, ou plusieurs navigateurs.
   Deux fenêtres privées du même navigateur peuvent partager la même session.
2. Connecter Alex, Sarah, Audrey et Marc chacun dans sa session.
3. Alex aime Sarah ; Sarah aime Alex. Vérifier le match des deux côtés.
4. Alex envoie « Test A vers B — 01 ». Sarah répond « Réponse B vers A — 02 ».
5. Recharger et se reconnecter : les deux messages doivent rester dans le bon ordre.
6. Créer un autre match Audrey–Marc ; vérifier qu'ils ne voient pas la conversation Alex–Sarah.
7. Connecter Alex sur Android au MEME backend et envoyer « Android vers Web — 03 ».
   Répondre depuis Sarah sur le Web ; vérifier réception et compteurs de lecture.
8. Couper puis rétablir le réseau Android et vérifier reprise, historique et absence de doublons.
9. Bloquer un compte de test : vérifier que l'échange n'est plus permis ; tester le signalement.

## Conditions du test Android

`main_preview.dart` est une démo fictive isolée : elle ne partage pas cette base.
Utiliser le client natif réel et une origine HTTPS joignable depuis le téléphone,
avec certificat accepté par ce téléphone et configuration Django correspondante.
`localhost` sur le téléphone désigne le téléphone, pas le PC.
Ne pas désactiver TLS pour contourner cette étape. Le chemin d'accès HTTPS local
reste à valider sur la machine de test avant d'annoncer la recette Mobile réussie.

## Résultats

Consigner pour chaque étape : date, commit, navigateur/appareil, résultat et anomalie.
Actuellement ces parcours ne sont PAS exécutés sur le PC de l'utilisateur.
Les tests automatisés de la commande ne constituent pas une recette réelle de messagerie.

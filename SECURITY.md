# Politique de sécurité du projet Mbolo

## Signalement des vulnérabilités

Les vulnérabilités ne doivent pas être publiées dans une issue publique.

Un canal privé de signalement sera défini avant toute publication du projet.

## Principes obligatoires

- aucun secret dans le dépôt Git ;
- authentification forte pour les comptes privilégiés ;
- principe du moindre privilège ;
- validation de toutes les entrées côté serveur ;
- chiffrement des communications ;
- dépendances maintenues et analysées ;
- journalisation des événements de sécurité ;
- protection contre les abus et l'automatisation ;
- revue de code avant intégration ;
- tests de sécurité automatisés ;
- protection des données dès la conception.

## Données interdites dans les journaux

Les journaux ne doivent jamais contenir :

- des mots de passe ;
- des jetons d'authentification complets ;
- des clés API ;
- des cookies de session ;
- des documents d'identité ;
- des messages privés en clair ;
- des coordonnées GPS exactes ;
- des données bancaires complètes.

## Gestion des vulnérabilités

Toute vulnérabilité doit être :

1. enregistrée ;
2. évaluée ;
3. classifiée ;
4. corrigée ;
5. testée ;
6. documentée ;
7. clôturée après validation.

# Barrière qualité CI/CD de Mbolo

## Objectif

Le workflow `Mbolo CI` contrôle automatiquement chaque modification envoyée
sur `main` et chaque pull request visant `main`.

Il ne déploie rien et ne possède aucun droit d'écriture sur le dépôt. Son rôle
est uniquement de détecter une régression avant la préproduction.

## Contrôles réalisés

### Dépôt

- recherche de secrets et de fichiers locaux suivis par Git ;
- blocage des médias, sauvegardes, clés et fichiers d'environnement connus.

### Frontend

- installation reproductible avec `npm ci` ;
- contrôle TypeScript ;
- lint ;
- build Vite de production ;
- audit des vulnérabilités de niveau élevé ou critique dans les dépendances
  utilisées en production.

### Backend

- PostgreSQL isolé réservé à l'exécution CI ;
- Redis éphémère protégé par un mot de passe de test ;
- `manage.py check` ;
- détection des migrations oubliées ;
- compilation Python ;
- exécution des tests Django ;
- audit des dépendances Python avec `pip-audit`.

Les identifiants visibles dans le workflow sont exclusivement des valeurs
éphémères de test. Ils ne donnent accès à aucune base Mbolo réelle.

## Dependabot

Dependabot vérifie chaque semaine :

- les dépendances Python ;
- les dépendances npm ;
- les versions des actions GitHub.

Une proposition Dependabot n'est jamais une autorisation de fusionner
automatiquement. Il faut attendre la réussite de la CI et examiner les
changements incompatibles éventuels.

## Sécurité et conformité

Ce dispositif contribue notamment :

- à la gestion contrôlée des changements ;
- à la séparation entre test et production ;
- à la détection des vulnérabilités ;
- à la traçabilité des contrôles ;
- au principe du moindre privilège ;
- aux pratiques Secure by Design et Privacy by Design.

Il soutient une démarche ISO/IEC 27001 et RGPD, mais ne constitue pas à lui
seul une certification ni une preuve de conformité juridique complète.

## Lecture d'un résultat GitHub

- coche verte : tous les contrôles ont réussi ;
- croix rouge : au moins un contrôle a échoué ;
- point jaune : contrôles encore en cours ou en attente.

En cas d'échec, ouvrir l'exécution `Mbolo CI`, sélectionner le job rouge puis
la première étape en erreur. Ne jamais contourner un échec sans comprendre sa
cause.

## Retour arrière

Avant le commit, les nouveaux fichiers peuvent simplement ne pas être ajoutés.
Après un commit partagé, utiliser un nouveau commit de correction ou un
`git revert`. Ne jamais utiliser `git reset --hard` pour cette procédure.


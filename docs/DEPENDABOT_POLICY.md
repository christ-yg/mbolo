# Politique Dependabot de Mbolo

## Objectif

Dependabot surveille les dépendances Python, npm et GitHub Actions. Il propose
des modifications, mais ne possède aucune autorisation de fusion automatique.

Cette politique réduit le nombre de pull requests simultanées sans diminuer la
visibilité des mises à jour de sécurité.

## Organisation des mises à jour

### Modifications mineures et correctives

Les versions `minor` et `patch` sont regroupées par écosystème :

- backend Python ;
- dépendances frontend utilisées en production ;
- outils frontend de développement ;
- GitHub Actions.

Un groupe vert dans la CI reste une proposition. Il doit être relu puis testé
fonctionnellement avant fusion.

### Modifications majeures

Les versions `major` restent dans des pull requests séparées. Cette règle
concerne notamment :

- Django 5 vers Django 6 ;
- TypeScript 6 vers TypeScript 7 ;
- Redis 6 vers Redis 8 ;
- toute future migration majeure de React Router.

Une migration majeure peut modifier des API, les migrations, la sécurité ou le
comportement métier. Elle ne doit jamais être fusionnée avec un simple lot de
maintenance.

## Délai de stabilisation

Les mises à jour ordinaires attendent sept jours après leur publication avant
d'être proposées. Ce délai permet de détecter les versions retirées ou les
régressions rapportées par d'autres projets.

Les alertes de sécurité gardent leur priorité et ne doivent pas attendre ce
cycle de maintenance ordinaire.

## Exception React Router

La version `7.18.2` reste verrouillée pendant la dérogation documentée dans
`docs/CI_FAILURE_FIX_20260730.md`.

La plage `>=7.12.0 <8.3.0` n'est pas proposée automatiquement. Dès qu'une
version corrigée est publiée et compatible avec Mbolo, il faut :

1. créer une branche de migration ;
2. retirer la règle `ignore` ;
3. mettre à niveau React Router ;
4. exécuter le typecheck, le lint, le build et les tests fonctionnels ;
5. supprimer la dérogation de l'audit npm.

## Procédure de fusion

Avant chaque fusion Dependabot :

1. lire le changelog de la dépendance ;
2. vérifier que la CI Mbolo est verte ;
3. tester les parcours concernés ;
4. confirmer l'absence de migration ou de changement de configuration oublié ;
5. fusionner une seule catégorie de risque à la fois ;
6. surveiller la préproduction après reconstruction.

## Contribution ISO/IEC 27001 et RGPD

Cette organisation améliore :

- la gestion des vulnérabilités ;
- la maîtrise des changements ;
- la traçabilité des décisions ;
- la disponibilité et l'intégrité du service ;
- le principe de sécurité dès la conception.

Elle soutient le SMSI de Mbolo, mais ne remplace ni l'analyse de risque, ni les
tests, ni l'approbation humaine.

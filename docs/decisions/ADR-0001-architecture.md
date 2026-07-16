# ADR-0001 — Architecture initiale

## Statut

Acceptée provisoirement.

## Contexte

Mbolo doit fournir une application Web sécurisée, puis une application mobile,
tout en restant réalisable par une petite équipe pendant la phase initiale.

## Décision

Le projet commencera sous la forme d'un monolithe Django modulaire exposant
une API REST consommée par une interface React.

Les services de données locaux seront exécutés avec Docker Compose :

- PostgreSQL ;
- Redis.

## Justification

Cette architecture :

- limite la complexité opérationnelle ;
- réduit la surface d'attaque initiale ;
- facilite les transactions ;
- simplifie les tests et les audits ;
- permet une évolution future vers des services séparés.

## Conséquences

Une séparation stricte devra être maintenue entre les modules métier :

- comptes ;
- profils ;
- matching ;
- messagerie ;
- modération ;
- abonnements ;
- confidentialité ;
- audit.

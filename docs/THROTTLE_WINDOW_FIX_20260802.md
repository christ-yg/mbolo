# Stabilisation de la fenêtre anti-bruteforce

## Incident observé

La CI de la mise à jour Dependabot backend exécutait 329 tests. Un test de
journalisation attendait une réponse HTTP 429 après cinq échecs de connexion,
mais recevait parfois HTTP 400.

L'ancienne clé Redis contenait le numéro de la minute calculé à partir de
l'horloge système. Si les cinq premières tentatives avaient lieu juste avant
le changement de minute et la sixième juste après, une nouvelle clé était
créée et le compteur repartait à un.

## Correction

La clé contient désormais uniquement :

1. le préfixe fonctionnel du limiteur ;
2. le nom de la classe de limitation ;
3. une empreinte HMAC-SHA-256 de l'identifiant.

Redis démarre la durée de vie lors de la première tentative. La clé reste donc
stable pendant toute la fenêtre et expire automatiquement.

Les adresses e-mail et IP restent pseudonymisées : aucune valeur brute n'est
inscrite dans le nom de clé Redis.

## Tests ajoutés et renforcés

- vérification de la forme exacte de la clé HMAC, sans suffixe temporel ;
- vérification de l'absence de l'adresse e-mail brute ;
- namespace Redis unique pour chaque test de limitation ;
- namespace Redis unique pour chaque test de journalisation ;
- restauration des préfixes après chaque test.

## Sécurité, RGPD et ISO 27001

Cette correction soutient :

- la résistance aux tentatives de connexion automatisées ;
- la confidentialité des identifiants dans Redis par pseudonymisation HMAC ;
- l'intégrité et la reproductibilité des contrôles de sécurité ;
- la traçabilité par tests automatisés et historique Git ;
- la séparation entre données actives et base de tests temporaire.

Elle contribue aux mesures de sécurité attendues par l'article 32 du RGPD et
aux pratiques de gestion des changements, de journalisation et de contrôle
d'accès associées à ISO/IEC 27001. Elle ne constitue pas, à elle seule, une
certification ni une preuve complète de conformité.


# Mbolo — Lot 02 E-mails gratuits

## Objectif

Ce lot rend la configuration e-mail de Django compatible avec :

- la console locale historique ;
- Mailpit pour les tests SMTP entièrement locaux ;
- un futur fournisseur SMTP public sans modifier le code.

Aucun e-mail de test ne quitte le PC.

## Installation

Extraire l'archive depuis la racine `~/projects/mbolo`, puis rendre le script
exécutable :

```bash
chmod +x scripts/email-local-check.sh
```

## Validation

```bash
bash scripts/email-local-check.sh
```

Résultats attendus :

- `SMTP_DJANGO=OK` ;
- `EMAIL_MAILPIT=OK` ;
- une URL locale `http://127.0.0.1:8025`.

Ouvrir cette URL dans le navigateur permet de voir le message capturé. Mailpit
n'envoie rien vers Internet : il sert de boîte aux lettres de test.

## Utilisation avec les vrais parcours Mbolo

Lorsque le fichier Compose e-mail local est actif, les messages produits par
l'inscription, la vérification d'adresse, la récupération du mot de passe, les
alertes et la 2FA sont capturés par Mailpit.

## Future production

Sur le futur VPS, Mailpit ne sera pas lancé. Les variables
`DJANGO_EMAIL_*` du fichier secret de production recevront les paramètres du
fournisseur SMTP. `DJANGO_REQUIRE_SMTP_EMAIL=true` empêchera alors Django de
démarrer avec le backend console.

## Sécurité

- aucun identifiant SMTP réel n'est versionné ;
- l'interface Mailpit est liée à `127.0.0.1` ;
- TLS et SSL ne peuvent pas être activés simultanément ;
- un délai réseau de 10 secondes empêche un appel SMTP bloqué indéfiniment ;
- les futures clés resteront exclusivement dans `.env.production`.

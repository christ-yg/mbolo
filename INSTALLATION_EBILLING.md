# Intégration E-Billing — Mbolo Premium

## Objectif

Mbolo utilise E-Billing comme agrégateur de paiement Mobile Money pour
Airtel Money Gabon et Moov Money Gabon. Les secrets restent exclusivement
dans le backend Django. L'utilisateur valide le paiement dans le parcours
Mobile Money de son opérateur ; Mbolo ne collecte jamais son PIN.

## Configuration locale / sandbox

Dans le fichier `.env` local :

```env
MBOLO_PAYMENT_PROVIDER=ebilling
MBOLO_PAYMENT_TEST_MODE=false

EBILLING_ENV=lab
EBILLING_BASE_URL=https://lab.billing-easy.net
EBILLING_CLIENT_ID=<client-id-fourni-par-ebilling>
EBILLING_CLIENT_SECRET=<client-secret-fourni-par-ebilling>
EBILLING_HTTP_TIMEOUT_SECONDS=15
EBILLING_WEBHOOK_SIGNING_KEY=
```

Ne jamais committer les vraies valeurs de `EBILLING_CLIENT_ID`,
`EBILLING_CLIENT_SECRET` ou une clé de signature.

## Base de données

Après récupération de la branche :

```bash
cd ~/projects/mbolo/backend
python manage.py migrate
```

La migration `0005_ebilling_references` ajoute les identifiants de facture
et de push USSD E-Billing à la transaction locale.

## Endpoints Mbolo

- `POST /api/v1/premium/payments/checkout/`
  - authentifié ;
  - paramètres : `plan`, `method`, `payer_phone` ;
  - le montant est recalculé côté serveur.
- `POST /api/v1/premium/payments/refresh/`
  - authentifié ;
  - réinterroge E-Billing pour confirmer l'état réel du push.
- `POST /api/v1/premium/payments/ebilling/webhook/`
  - callback serveur ;
  - le contenu du webhook n'est jamais considéré comme preuve de paiement :
    Mbolo réinterroge E-Billing avant d'activer Premium.

## Flux

1. L'utilisateur choisit Mbolo Plus ou Prestige.
2. Il sélectionne Airtel Money ou Moov Money et saisit son numéro.
3. Django crée une transaction locale avec un montant déterminé par Mbolo.
4. Django s'authentifie auprès d'E-Billing via OAuth2 client credentials.
5. Django crée une facture E-Billing.
6. Django déclenche le push USSD Airtel ou Moov.
7. L'utilisateur confirme sur son téléphone avec son opérateur.
8. Le webhook E-Billing ou l'action « J'ai confirmé » déclenche une enquête
   serveur-vers-serveur.
9. Premium est activé uniquement si E-Billing retourne un état payé.

## Passage en production

Avant la production :

1. Faire valider le compte marchand/KYC par E-Billing.
2. Obtenir les identifiants de production.
3. Confirmer auprès d'E-Billing l'URL de base de production attribuée au compte
   marchand ; ne pas déduire cette URL depuis l'environnement lab.
4. Déployer le backend Mbolo derrière HTTPS.
5. Configurer chez E-Billing l'URL publique :
   `https://<domaine-mbolo>/api/v1/premium/payments/ebilling/webhook/`.
6. Si E-Billing fournit une clé et la spécification officielle de signature
   webhook, activer la vérification cryptographique en plus de la revalidation
   serveur déjà présente.
7. Effectuer des paiements réels de faible montant avec Airtel Money et Moov
   Money avant l'ouverture générale.

## Sécurité

- Le PIN Mobile Money n'est jamais demandé ni stocké par Mbolo.
- Les clés E-Billing ne sont jamais exposées à React ou Flutter.
- Le montant et l'offre sont décidés exclusivement côté serveur.
- Les références E-Billing sont journalisées dans la transaction.
- La confirmation est idempotente.
- Une notification webhook seule ne peut pas activer Premium.

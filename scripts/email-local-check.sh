#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."

ENV_FILE=".env.production"
BASE_COMPOSE="compose.production.yaml"
EMAIL_COMPOSE="compose.email-local.yaml"
MAILPIT_UI_PORT="${MBOLO_MAILPIT_UI_PORT:-8025}"
SUBJECT="Mbolo SMTP local check $(date +%s)"

if [[ ! -f "$ENV_FILE" ]]; then
  echo "❌ $ENV_FILE est absent."
  exit 1
fi

compose=(
  docker compose
  --env-file "$ENV_FILE"
  -f "$BASE_COMPOSE"
  -f "$EMAIL_COMPOSE"
)

echo "[1/5] Validation de la configuration Compose"
"${compose[@]}" config >/dev/null

echo "[2/5] Démarrage de Mailpit et reconstruction du backend"
"${compose[@]}" build backend
"${compose[@]}" up -d mailpit backend

echo "[3/5] Attente de l'interface Mailpit"
curl \
  --fail \
  --silent \
  --show-error \
  --retry 20 \
  --retry-delay 2 \
  --retry-all-errors \
  "http://127.0.0.1:${MAILPIT_UI_PORT}/api/v1/info" >/dev/null

echo "[4/5] Envoi d'un message par le backend SMTP Django"
"${compose[@]}" exec \
  -T \
  -e "MBOLO_EMAIL_TEST_SUBJECT=$SUBJECT" \
  backend \
  python manage.py shell -c '
import os
from django.conf import settings
from django.core.mail import send_mail

subject = os.environ["MBOLO_EMAIL_TEST_SUBJECT"]
sent = send_mail(
    subject=subject,
    message="Validation SMTP locale Mbolo. Aucun message externe.",
    from_email=settings.DEFAULT_FROM_EMAIL,
    recipient_list=["security-test@mbolo.local"],
    fail_silently=False,
)
assert sent == 1, f"Nombre de messages inattendu : {sent}"
print("SMTP_DJANGO=OK")
'

echo "[5/5] Vérification du message dans Mailpit"
messages="$(
  curl \
    --fail \
    --silent \
    --show-error \
    "http://127.0.0.1:${MAILPIT_UI_PORT}/api/v1/messages"
)"

if ! grep -Fq "$SUBJECT" <<<"$messages"; then
  echo "❌ Le message SMTP n'a pas été retrouvé dans Mailpit."
  exit 1
fi

echo "✅ EMAIL_MAILPIT=OK"
echo "✅ Message capturé : $SUBJECT"
echo "ℹ️  Interface locale : http://127.0.0.1:${MAILPIT_UI_PORT}"

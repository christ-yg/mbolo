from dataclasses import dataclass
from datetime import timedelta
from uuid import UUID

from django.conf import settings
from django.core import signing
from django.core.mail import send_mail
from django.urls import reverse

from .models import User


EMAIL_VERIFICATION_SALT = "mbolo.accounts.email-verification"
EMAIL_VERIFICATION_MAX_AGE = timedelta(minutes=30)


class InvalidEmailVerificationToken(Exception):
    """Le jeton est invalide, altéré ou mal formé."""


class ExpiredEmailVerificationToken(Exception):
    """Le jeton de vérification a dépassé sa durée de validité."""


@dataclass(frozen=True)
class EmailVerificationPayload:
    """
    Données validées extraites du jeton.

    Le jeton contient uniquement :
    - l'UUID utilisateur ;
    - l'adresse e-mail normalisée au moment de sa création.

    Il ne contient jamais :
    - de mot de passe ;
    - de cookie de session ;
    - de jeton CSRF ;
    - de permissions.
    """

    user_id: UUID
    email: str


def build_email_verification_token(user: User) -> str:
    """
    Crée un jeton signé et horodaté.

    Toute modification du contenu invalidera automatiquement
    la signature cryptographique.
    """

    payload = {
        "user_id": str(user.id),
        "email": user.email.strip().lower(),
    }

    return signing.dumps(
        payload,
        salt=EMAIL_VERIFICATION_SALT,
        compress=True,
    )


def read_email_verification_token(
    token: str,
) -> EmailVerificationPayload:
    """
    Vérifie la signature, l'âge et la structure du jeton.
    """

    try:
        payload = signing.loads(
            token,
            salt=EMAIL_VERIFICATION_SALT,
            max_age=EMAIL_VERIFICATION_MAX_AGE,
        )
    except signing.SignatureExpired as exc:
        raise ExpiredEmailVerificationToken(
            "Le jeton de vérification a expiré."
        ) from exc
    except signing.BadSignature as exc:
        raise InvalidEmailVerificationToken(
            "Le jeton de vérification est invalide."
        ) from exc

    if not isinstance(payload, dict):
        raise InvalidEmailVerificationToken(
            "Le contenu du jeton est invalide."
        )

    raw_user_id = payload.get("user_id")
    raw_email = payload.get("email")

    if not isinstance(raw_user_id, str):
        raise InvalidEmailVerificationToken(
            "L'identifiant du jeton est invalide."
        )

    if not isinstance(raw_email, str):
        raise InvalidEmailVerificationToken(
            "L'adresse du jeton est invalide."
        )

    try:
        user_id = UUID(raw_user_id)
    except ValueError as exc:
        raise InvalidEmailVerificationToken(
            "L'identifiant du jeton est invalide."
        ) from exc

    normalized_email = raw_email.strip().lower()

    if not normalized_email:
        raise InvalidEmailVerificationToken(
            "L'adresse du jeton est vide."
        )

    return EmailVerificationPayload(
        user_id=user_id,
        email=normalized_email,
    )


def send_email_verification_message(
    *,
    user: User,
) -> str:
    """
    Génère puis envoie le jeton de vérification.

    En développement, le backend console affiche le message
    directement dans le terminal Django.
    """

    token = build_email_verification_token(user)

    confirmation_path = reverse(
        "accounts:email-verification-confirm"
    )

    frontend_base_url = getattr(
        settings,
        "FRONTEND_BASE_URL",
        "http://localhost:5173",
    ).rstrip("/")

    verification_url = (
        f"{frontend_base_url}/verify-email"
        f"?token={token}"
    )

    subject = "Vérification de votre adresse e-mail Mbolo"

    message = (
        "Bienvenue sur Mbolo.\n\n"
        "Pour vérifier votre adresse e-mail, utilisez le lien suivant :\n"
        f"{verification_url}\n\n"
        "Le jeton est valable pendant 30 minutes.\n\n"
        "Endpoint API de confirmation :\n"
        f"{confirmation_path}\n\n"
        "Si vous n'avez pas créé ce compte, ignorez ce message."
    )

    send_mail(
        subject=subject,
        message=message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[user.email],
        fail_silently=False,
    )

    return token

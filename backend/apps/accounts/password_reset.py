from django.conf import settings
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import send_mail
from django.urls import reverse
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode

from .models import User


def send_password_reset_message(*, user: User) -> None:
    """Envoie un lien à usage unique sans journaliser le jeton."""
    uid = urlsafe_base64_encode(force_bytes(user.pk))
    token = default_token_generator.make_token(user)
    frontend_base_url = getattr(
        settings,
        "FRONTEND_BASE_URL",
        "http://localhost:5173",
    ).rstrip("/")
    reset_url = (
        f"{frontend_base_url}/reset-password"
        f"?uid={uid}&token={token}"
    )
    api_path = reverse("accounts:password-reset-confirm")
    timeout_minutes = max(
        1,
        int(getattr(settings, "PASSWORD_RESET_TIMEOUT", 1800)) // 60,
    )

    send_mail(
        subject="Réinitialisation de votre mot de passe Mbolo",
        message=(
            "Une réinitialisation du mot de passe Mbolo a été demandée.\n\n"
            f"Utilisez ce lien :\n{reset_url}\n\n"
            f"Le lien expire dans {timeout_minutes} minutes et devient "
            "inutilisable après le changement du mot de passe.\n\n"
            f"Endpoint API : {api_path}\n\n"
            "Si vous n'êtes pas à l'origine de cette demande, ignorez ce message."
        ),
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[user.email],
        fail_silently=False,
    )

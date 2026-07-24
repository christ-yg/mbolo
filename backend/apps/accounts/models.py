import uuid
from .managers import UserManager
from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """
    Utilisateur principal de Mbolo.

    Choix de sécurité et de conception :
    - UUID non séquentiel comme identifiant public ;
    - adresse e-mail unique ;
    - nom d'utilisateur Django supprimé ;
    - indicateurs de vérification séparés ;
    - dates de création et modification traçables.

    Les informations détaillées du profil de rencontre seront stockées
    dans une application distincte afin de séparer identité,
    authentification et données sociales.
    """
    objects = UserManager()

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )

    username = None

    email = models.EmailField(
        unique=True,
        db_index=True,
    )

    phone_number = models.CharField(
        max_length=32,
        blank=True,
        default="",
    )

    is_email_verified = models.BooleanField(
        default=False,
    )

    email_2fa_enabled = models.BooleanField(
        default=False,
        help_text=(
            "Exige un code temporaire envoyé par e-mail "
            "après la validation du mot de passe."
        ),
    )

    is_phone_verified = models.BooleanField(
        default=False,
    )

    is_suspended = models.BooleanField(
        default=False,
    )

    suspension_until = models.DateTimeField(
        null=True,
        blank=True,
        db_index=True,
        help_text=(
            "Date de fin d'une suspension temporaire. "
            "Une valeur vide avec is_suspended=True représente "
            "une suspension sans échéance."
        ),
    )

    terms_accepted_at = models.DateTimeField(
        null=True,
        blank=True,
        editable=False,
    )

    terms_version = models.CharField(
        max_length=20,
        blank=True,
        default="",
        editable=False,
    )

    privacy_version = models.CharField(
        max_length=20,
        blank=True,
        default="",
        editable=False,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS: list[str] = []

    class Meta:
        db_table = "accounts_user"
        ordering = ("-created_at",)

    def __str__(self) -> str:
        """
        Représentation administrative minimale.

        Ne jamais retourner ici un mot de passe, un jeton,
        un numéro de téléphone ou une autre donnée sensible.
        """
        return self.email


class LoginActivity(models.Model):
    """Trace minimale et pseudonymisée des connexions d'un membre."""

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="login_activities",
    )
    method = models.CharField(
        max_length=32,
        choices=(
            ("password", "Mot de passe"),
            ("email_2fa", "Double authentification e-mail"),
        ),
    )
    device = models.CharField(
        max_length=120,
        default="Appareil inconnu",
    )
    ip_fingerprint = models.CharField(
        max_length=16,
        blank=True,
        default="",
        help_text="Empreinte irréversible et tronquée, jamais l'adresse IP.",
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        db_index=True,
    )

    class Meta:
        ordering = ("-created_at",)
        indexes = [
            models.Index(
                fields=("user", "-created_at"),
                name="account_login_user_created_idx",
            ),
        ]

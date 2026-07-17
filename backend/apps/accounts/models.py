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

    is_phone_verified = models.BooleanField(
        default=False,
    )

    is_suspended = models.BooleanField(
        default=False,
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

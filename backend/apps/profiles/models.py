from datetime import date
from uuid import uuid4

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models


class Gender(models.TextChoices):
    """
    Valeurs initiales proposées pour le genre public.

    Nous stockons des codes techniques stables en base et
    affichons des libellés français dans l'interface.
    """

    MAN = "man", "Homme"
    WOMAN = "woman", "Femme"
    NON_BINARY = "non_binary", "Non binaire"
    PREFER_NOT_TO_SAY = "prefer_not_to_say", "Préfère ne pas préciser"


class DatingIntent(models.TextChoices):
    """
    Intention principale déclarée par l'utilisateur.
    """

    SERIOUS_RELATIONSHIP = (
        "serious_relationship",
        "Relation sérieuse",
    )
    FRIENDSHIP = "friendship", "Amitié"
    DISCUSSION = "discussion", "Discussion"
    MARRIAGE = "marriage", "Mariage"
    NOT_SURE = "not_sure", "Je ne sais pas encore"


class GabonCity(models.TextChoices):
    """
    Première liste normalisée de villes gabonaises.

    Cette liste pourra ensuite être remplacée par une table
    géographique plus complète avec provinces et coordonnées.
    """

    LIBREVILLE = "libreville", "Libreville"
    PORT_GENTIL = "port_gentil", "Port-Gentil"
    FRANCEVILLE = "franceville", "Franceville"
    OYEM = "oyem", "Oyem"
    MOANDA = "moanda", "Moanda"
    LAMBARENE = "lambarene", "Lambaréné"
    MOUILA = "mouila", "Mouila"
    TCHIBANGA = "tchibanga", "Tchibanga"
    KOULAMOUTOU = "koulamoutou", "Koulamoutou"
    MAKOKOU = "makokou", "Makokou"
    BITAM = "bitam", "Bitam"
    OTHER = "other", "Autre ville"


def calculate_age(
    birth_date: date,
    reference_date: date | None = None,
) -> int:
    """
    Calcule l'âge exact à une date de référence.

    La soustraction tient compte du fait que l'anniversaire
    ait déjà eu lieu ou non pendant l'année courante.
    """

    today = reference_date or date.today()

    return (
        today.year
        - birth_date.year
        - (
            (today.month, today.day)
            < (birth_date.month, birth_date.day)
        )
    )


def validate_adult_birth_date(
    value: date,
) -> None:
    """
    Refuse les utilisateurs de moins de 18 ans.

    Une application de rencontre ne doit pas permettre
    l'inscription ou l'exposition publique de mineurs.
    """

    if value > date.today():
        raise ValidationError(
            "La date de naissance ne peut pas être dans le futur."
        )

    if calculate_age(value) < 18:
        raise ValidationError(
            "Vous devez avoir au moins 18 ans."
        )


class Profile(models.Model):
    """
    Profil public de rencontre associé à un compte Mbolo.

    Le compte d'authentification contient les données techniques :
    - e-mail ;
    - mot de passe ;
    - permissions ;
    - statut du compte.

    Le profil contient les données sociales et publiques.
    Cette séparation réduit les risques de surexposition.
    """

    id = models.UUIDField(
        primary_key=True,
        default=uuid4,
        editable=False,
    )

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="profile",
    )

    display_name = models.CharField(
        max_length=50,
        blank=True,
        default="",
    )

    birth_date = models.DateField(
        null=True,
        blank=True,
        validators=[
            validate_adult_birth_date,
        ],
    )

    gender = models.CharField(
        max_length=32,
        choices=Gender.choices,
        blank=True,
        default="",
    )

    city = models.CharField(
        max_length=32,
        choices=GabonCity.choices,
        blank=True,
        default="",
    )

    biography = models.TextField(
        max_length=500,
        blank=True,
        default="",
    )

    dating_intent = models.CharField(
        max_length=32,
        choices=DatingIntent.choices,
        blank=True,
        default="",
    )

    is_discoverable = models.BooleanField(
        default=False,
        help_text=(
            "Autorise l'apparition du profil dans les résultats "
            "de découverte."
        ),
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    class Meta:
        db_table = "profiles_profile"
        ordering = ("-created_at",)

    def __str__(self) -> str:
        """
        Représentation administrative sans exposer l'e-mail.
        """

        return f"Profile<{self.id}>"

    @property
    def age(self) -> int | None:
        """
        Retourne l'âge calculé sans le stocker en base.

        L'âge évolue avec le temps ; le stocker directement
        créerait une donnée rapidement obsolète.
        """

        if self.birth_date is None:
            return None

        return calculate_age(
            self.birth_date
        )

    @property
    def is_complete(self) -> bool:
        """
        Indique si les informations minimales sont présentes.
        """

        return all(
            (
                self.display_name,
                self.birth_date,
                self.gender,
                self.city,
                self.dating_intent,
            )
        )

    def clean(self) -> None:
        """
        Applique les validations métier du modèle.
        """

        super().clean()

        if self.birth_date is not None:
            validate_adult_birth_date(
                self.birth_date
            )

        if self.is_discoverable and not self.is_complete:
            raise ValidationError(
                {
                    "is_discoverable": (
                        "Le profil doit être complété avant "
                        "d'être rendu visible."
                    )
                }
            )

        if (
            self.is_discoverable
            and not self.user.is_email_verified
        ):
            raise ValidationError(
                {
                    "is_discoverable": (
                        "L'adresse e-mail doit être vérifiée "
                        "avant de rendre le profil visible."
                    )
                }
            )

    def save(
        self,
        *args,
        **kwargs,
    ) -> None:
        """
        Valide le modèle avant chaque sauvegarde.

        Cela évite de dépendre uniquement du sérialiseur API :
        les règles restent actives dans l'administration,
        les scripts et les tâches asynchrones.
        """

        self.full_clean()

        super().save(
            *args,
            **kwargs,
        )

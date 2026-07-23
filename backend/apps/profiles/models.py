from datetime import date
from uuid import uuid4

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models


class Gender(models.TextChoices):
    """
    Valeurs techniques stables utilisées pour le genre public.
    """

    MAN = "man", "Homme"
    WOMAN = "woman", "Femme"
    NON_BINARY = "non_binary", "Non binaire"
    PREFER_NOT_TO_SAY = (
        "prefer_not_to_say",
        "Préfère ne pas préciser",
    )


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

class Interest(models.TextChoices):
    """
    Centres d'intérêt publics, normalisés et stables.
    """

    MUSIC = "music", "Musique"
    FOOTBALL = "football", "Football"
    FITNESS = "fitness", "Musculation et fitness"
    MARTIAL_ARTS = "martial_arts", "Arts martiaux"
    TECHNOLOGY = "technology", "Technologie"
    CYBERSECURITY = "cybersecurity", "Cybersécurité"
    TRAVEL = "travel", "Voyages"
    COOKING = "cooking", "Cuisine"
    CINEMA = "cinema", "Cinéma"
    READING = "reading", "Lecture"
    ENTREPRENEURSHIP = "entrepreneurship", "Entrepreneuriat"
    PERSONAL_GROWTH = "personal_growth", "Développement personnel"
    DANCE = "dance", "Danse"
    ART = "art", "Art"
    NATURE = "nature", "Nature"
    FAMILY = "family", "Famille"


def calculate_age(
    birth_date: date,
    reference_date: date | None = None,
) -> int:
    """
    Calcule l'âge exact à une date donnée.

    La formule tient compte du fait que l'anniversaire
    soit déjà passé ou non pendant l'année courante.
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
    Refuse les dates futures et les personnes de moins de 18 ans.
    """

    if value > date.today():
        raise ValidationError(
            "La date de naissance ne peut pas être dans le futur."
        )

    if calculate_age(value) < 18:
        raise ValidationError(
            "Vous devez avoir au moins 18 ans."
        )


def validate_choice_list(
    *,
    values,
    allowed_values: set[str],
    field_name: str,
) -> None:
    """
    Valide une liste stockée dans un JSONField.

    Contrôles :
    - la valeur doit être une liste ;
    - chaque élément doit être une chaîne ;
    - aucun doublon ;
    - toutes les valeurs doivent être autorisées.
    """

    if not isinstance(values, list):
        raise ValidationError(
            {
                field_name: (
                    "La valeur doit être une liste."
                )
            }
        )

    if any(
        not isinstance(value, str)
        for value in values
    ):
        raise ValidationError(
            {
                field_name: (
                    "Chaque élément doit être une chaîne."
                )
            }
        )

    if len(values) != len(set(values)):
        raise ValidationError(
            {
                field_name: (
                    "La liste ne doit pas contenir de doublons."
                )
            }
        )

    invalid_values = sorted(
        set(values) - allowed_values
    )

    if invalid_values:
        raise ValidationError(
            {
                field_name: (
                    "Valeurs non autorisées : "
                    + ", ".join(invalid_values)
                )
            }
        )


class Profile(models.Model):
    """
    Profil public de rencontre associé à un compte Mbolo.

    Les données publiques sont séparées des informations
    techniques d'authentification.
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

    interests = models.JSONField(
        default=list,
        blank=True,
    )

    is_discoverable = models.BooleanField(
        default=False,
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
        return f"Profile<{self.id}>"

    @property
    def age(self) -> int | None:
        """
        Calcule l'âge à la demande sans le stocker.
        """

        if self.birth_date is None:
            return None

        return calculate_age(
            self.birth_date
        )

    @property
    def is_complete(self) -> bool:
        """
        Vérifie la présence des informations minimales.
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
        Applique les principales règles métier.
        """

        super().clean()

        if self.birth_date is not None:
            validate_adult_birth_date(
                self.birth_date
            )

        validate_choice_list(
            values=self.interests,
            allowed_values=set(Interest.values),
            field_name="interests",
        )

        if len(self.interests) > 8:
            raise ValidationError(
                {
                    "interests": (
                        "Sélectionnez au maximum 8 centres d'intérêt."
                    )
                }
            )

        if (
            self.is_discoverable
            and not self.is_complete
        ):
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
        Exécute les validations avant chaque sauvegarde.
        """

        self.full_clean()

        super().save(
            *args,
            **kwargs,
        )


class SearchPreferences(models.Model):
    """
    Préférences privées utilisées par le moteur de découverte.

    Elles ne sont pas destinées à être visibles publiquement.

    JSONField est utilisé pour stocker plusieurs choix tout en
    conservant une architecture compatible avec PostgreSQL.
    """

    id = models.UUIDField(
        primary_key=True,
        default=uuid4,
        editable=False,
    )

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="search_preferences",
    )

    minimum_age = models.PositiveSmallIntegerField(
        default=18,
        validators=[
            MinValueValidator(18),
            MaxValueValidator(99),
        ],
    )

    maximum_age = models.PositiveSmallIntegerField(
        default=45,
        validators=[
            MinValueValidator(18),
            MaxValueValidator(99),
        ],
    )

    preferred_genders = models.JSONField(
        default=list,
        blank=True,
    )

    preferred_cities = models.JSONField(
        default=list,
        blank=True,
    )

    preferred_dating_intents = models.JSONField(
        default=list,
        blank=True,
    )

    maximum_distance_km = models.PositiveSmallIntegerField(
        default=50,
        validators=[
            MinValueValidator(1),
            MaxValueValidator(500),
        ],
    )

    only_verified_profiles = models.BooleanField(
        default=True,
    )

    only_profiles_with_photos = models.BooleanField(
        default=False,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    class Meta:
        db_table = "profiles_search_preferences"
        ordering = ("-created_at",)
        verbose_name = "Préférences de recherche"
        verbose_name_plural = "Préférences de recherche"

    def __str__(self) -> str:
        """
        Représentation administrative sans e-mail.
        """

        return f"SearchPreferences<{self.id}>"

    def clean(self) -> None:
        """
        Valide la cohérence des préférences.
        """

        super().clean()

        if self.minimum_age > self.maximum_age:
            raise ValidationError(
                {
                    "maximum_age": (
                        "L'âge maximum doit être supérieur "
                        "ou égal à l'âge minimum."
                    )
                }
            )

        validate_choice_list(
            values=self.preferred_genders,
            allowed_values={
                choice.value
                for choice in Gender
            },
            field_name="preferred_genders",
        )

        validate_choice_list(
            values=self.preferred_cities,
            allowed_values={
                choice.value
                for choice in GabonCity
            },
            field_name="preferred_cities",
        )

        validate_choice_list(
            values=self.preferred_dating_intents,
            allowed_values={
                choice.value
                for choice in DatingIntent
            },
            field_name="preferred_dating_intents",
        )

    def save(
        self,
        *args,
        **kwargs,
    ) -> None:
        """
        Valide systématiquement les préférences avant sauvegarde.
        """

        self.full_clean()

        super().save(
            *args,
            **kwargs,
        )

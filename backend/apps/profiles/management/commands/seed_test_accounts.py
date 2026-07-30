"""
Crée les comptes interactifs fictifs utilisés pour tester Mbolo.

Cette commande complète ``seed_demo_profiles`` :

- les profils de démonstration ordinaires restent non connectables ;
- Sarah et Audrey peuvent se connecter afin de tester les matchs,
  les messages et les notifications avec Kevin ;
- les mots de passe sont demandés silencieusement dans le terminal ;
- aucun mot de passe n'est écrit dans le code, les journaux ou la base
  de données en clair ;
- la commande est idempotente et ne crée jamais de doublon ;
- Kevin n'est jamais créé et son mot de passe n'est jamais modifié.

Exemple dans la préproduction Docker locale :

    python manage.py seed_test_accounts \
        --confirm-local-preproduction \
        --viewer-email kevin.test@mbolo.example

La commande est destinée uniquement à une base locale de test. Le drapeau
explicite est obligatoire même lorsque Django fonctionne avec DEBUG=True.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from getpass import getpass
from typing import Final

from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.core.management.base import (
    BaseCommand,
    CommandError,
    CommandParser,
)
from django.db import transaction

from apps.profiles.models import (
    DatingIntent,
    GabonCity,
    Gender,
    Interest,
    Profile,
    SearchPreferences,
)


TEST_EMAIL_DOMAIN: Final[str] = "mbolo.example"

ALL_GENDERS: Final[list[str]] = list(Gender.values)
ALL_CITIES: Final[list[str]] = list(GabonCity.values)
ALL_DATING_INTENTS: Final[list[str]] = list(DatingIntent.values)


@dataclass(frozen=True, slots=True)
class TestAccountDefinition:
    """Décrit uniquement les données fictives d'un compte de test."""

    email: str
    display_name: str
    birth_date: date
    gender: str
    city: str
    biography: str
    dating_intent: str
    interests: tuple[str, ...]


TEST_ACCOUNTS: Final[tuple[TestAccountDefinition, ...]] = (
    TestAccountDefinition(
        email=f"sarah.test@{TEST_EMAIL_DOMAIN}",
        display_name="Sarah",
        birth_date=date(1997, 9, 18),
        gender=Gender.WOMAN,
        city=GabonCity.LIBREVILLE,
        biography=(
            "Passionnée de voyages, de musique et de développement "
            "personnel. Je recherche une relation sérieuse fondée sur "
            "la confiance, le respect et une vraie complicité."
        ),
        dating_intent=DatingIntent.SERIOUS_RELATIONSHIP,
        interests=(
            Interest.MUSIC,
            Interest.TRAVEL,
            Interest.CINEMA,
            Interest.READING,
            Interest.PERSONAL_GROWTH,
            Interest.FAMILY,
        ),
    ),
    TestAccountDefinition(
        email=f"audrey.test@{TEST_EMAIL_DOMAIN}",
        display_name="Audrey",
        birth_date=date(1995, 4, 7),
        gender=Gender.WOMAN,
        city=GabonCity.PORT_GENTIL,
        biography=(
            "Entrepreneure, sportive et curieuse. J'apprécie les projets "
            "ambitieux, les conversations sincères et les personnes qui "
            "avancent avec discipline et bienveillance."
        ),
        dating_intent=DatingIntent.SERIOUS_RELATIONSHIP,
        interests=(
            Interest.FITNESS,
            Interest.ENTREPRENEURSHIP,
            Interest.TRAVEL,
            Interest.COOKING,
            Interest.TECHNOLOGY,
            Interest.PERSONAL_GROWTH,
        ),
    ),
)


class Command(BaseCommand):
    """Commande Django sécurisée de préparation des comptes interactifs."""

    help = (
        "Crée ou actualise Sarah et Audrey dans la base locale de test, "
        "avec des mots de passe saisis silencieusement."
    )

    def add_arguments(self, parser: CommandParser) -> None:
        """Déclare les confirmations et options non sensibles."""

        parser.add_argument(
            "--confirm-local-preproduction",
            action="store_true",
            help=(
                "Confirme explicitement que la base ciblée est une "
                "préproduction locale contenant uniquement des données "
                "de développement ou de test."
            ),
        )
        parser.add_argument(
            "--viewer-email",
            type=str,
            default=None,
            help=(
                "Compte existant dont les préférences de découverte "
                "seront élargies. Son mot de passe et son profil public "
                "ne seront jamais modifiés."
            ),
        )

    def handle(self, *args: object, **options: object) -> None:
        """Valide le contexte, collecte les secrets puis écrit les données."""

        if not options.get("confirm_local_preproduction"):
            raise CommandError(
                "Opération refusée. Ajoute "
                "--confirm-local-preproduction uniquement après avoir "
                "vérifié que la base est la préproduction locale."
            )

        viewer_email_option = options.get("viewer_email")
        viewer_email = (
            str(viewer_email_option).strip().lower()
            if viewer_email_option
            else None
        )

        passwords = {
            definition.email: self._prompt_valid_password(definition)
            for definition in TEST_ACCOUNTS
        }

        self._create_or_update_accounts(
            passwords=passwords,
            viewer_email=viewer_email,
        )

        self.stdout.write("")
        self.stdout.write(
            self.style.SUCCESS(
                "✅ Sarah et Audrey sont prêtes pour les tests Mbolo."
            )
        )
        self.stdout.write(
            "Les mots de passe n'ont été ni affichés ni journalisés."
        )

    def _prompt_valid_password(
        self,
        definition: TestAccountDefinition,
    ) -> str:
        """Demande deux fois un mot de passe conforme aux règles Django."""

        User = get_user_model()
        validation_user = User(email=definition.email)

        first_password = getpass(
            f"Mot de passe temporaire pour {definition.email} : "
        )
        confirmation = getpass(
            f"Confirme le mot de passe pour {definition.email} : "
        )

        if first_password != confirmation:
            raise CommandError(
                f"Les mots de passe de {definition.email} ne correspondent pas."
            )

        try:
            validate_password(
                first_password,
                user=validation_user,
            )
        except ValidationError as exc:
            messages = " ".join(exc.messages)
            raise CommandError(
                f"Mot de passe refusé pour {definition.email} : {messages}"
            ) from exc

        return first_password

    @transaction.atomic
    def _create_or_update_accounts(
        self,
        *,
        passwords: dict[str, str],
        viewer_email: str | None,
    ) -> None:
        """Crée ou actualise les comptes, profils et préférences atomiquement."""

        User = get_user_model()

        for definition in TEST_ACCOUNTS:
            user, created = User.objects.get_or_create(
                email=definition.email,
                defaults={
                    "is_active": True,
                    "is_email_verified": True,
                    "is_phone_verified": False,
                    "is_suspended": False,
                    "is_staff": False,
                    "is_superuser": False,
                },
            )

            # Les comptes de test restent des membres ordinaires.
            user.is_active = True
            user.is_email_verified = True
            user.is_phone_verified = False
            user.is_suspended = False
            user.suspension_until = None
            user.is_staff = False
            user.is_superuser = False
            user.set_password(passwords[definition.email])
            user.save()

            Profile.objects.update_or_create(
                user=user,
                defaults={
                    "display_name": definition.display_name,
                    "birth_date": definition.birth_date,
                    "gender": definition.gender,
                    "city": definition.city,
                    "biography": definition.biography,
                    "dating_intent": definition.dating_intent,
                    "interests": list(definition.interests),
                    "is_discoverable": True,
                },
            )

            SearchPreferences.objects.update_or_create(
                user=user,
                defaults={
                    "minimum_age": 18,
                    "maximum_age": 70,
                    "preferred_genders": ALL_GENDERS,
                    "preferred_cities": ALL_CITIES,
                    "preferred_dating_intents": ALL_DATING_INTENTS,
                    "maximum_distance_km": 500,
                    "only_verified_profiles": False,
                    "only_profiles_with_photos": False,
                },
            )

            action = "créé" if created else "actualisé"
            self.stdout.write(
                f"  [{action}] {definition.display_name} — {definition.email}"
            )

        if viewer_email is not None:
            self._configure_viewer(User=User, viewer_email=viewer_email)

    def _configure_viewer(self, *, User, viewer_email: str) -> None:
        """Élargit uniquement les préférences privées du compte spectateur."""

        try:
            viewer = User.objects.get(email__iexact=viewer_email)
        except User.DoesNotExist as exc:
            raise CommandError(
                f"Aucun compte spectateur trouvé : {viewer_email}"
            ) from exc

        if not hasattr(viewer, "profile"):
            raise CommandError(
                "Le compte spectateur ne possède pas encore de profil."
            )

        SearchPreferences.objects.update_or_create(
            user=viewer,
            defaults={
                "minimum_age": 18,
                "maximum_age": 70,
                "preferred_genders": ALL_GENDERS,
                "preferred_cities": ALL_CITIES,
                "preferred_dating_intents": ALL_DATING_INTENTS,
                "maximum_distance_km": 500,
                "only_verified_profiles": False,
                "only_profiles_with_photos": False,
            },
        )

        self.stdout.write(
            f"  [préférences élargies] {viewer.email}"
        )

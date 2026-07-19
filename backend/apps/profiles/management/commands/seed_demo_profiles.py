"""
Commande Django de création de profils fictifs pour Mbolo.

Cette commande est strictement destinée au développement local.

Utilisations principales
========================

Créer ou actualiser les profils de démonstration :

    python manage.py seed_demo_profiles

Créer les profils et élargir les préférences d'un compte de test :

    python manage.py seed_demo_profiles \
        --viewer-email frontendtest2026-04@example.com

Supprimer les comptes de démonstration :

    python manage.py seed_demo_profiles --delete

Principes de sécurité
=====================

- La commande refuse de fonctionner lorsque DEBUG=False.
- Les utilisateurs fictifs reçoivent des mots de passe inutilisables.
- Aucun mot de passe partagé ou prévisible n'est créé.
- Les adresses utilisent le domaine réservé example.com.
- La commande est idempotente : elle peut être relancée sans doublons.
- Les données de démonstration sont clairement identifiables.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Final

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.management.base import (
    BaseCommand,
    CommandError,
    CommandParser,
)
from django.db import transaction

from apps.profiles.models import Profile, SearchPreferences


# ---------------------------------------------------------------------------
# Constantes générales
# ---------------------------------------------------------------------------

DEMO_EMAIL_PREFIX: Final[str] = "mbolo.demo."
DEMO_EMAIL_DOMAIN: Final[str] = "example.com"

# Tous les genres actuellement autorisés par le modèle Profile.
ALL_GENDERS: Final[list[str]] = [
    "man",
    "woman",
    "non_binary",
    "prefer_not_to_say",
]

# Toutes les villes actuellement autorisées par le modèle Profile.
ALL_CITIES: Final[list[str]] = [
    "libreville",
    "port_gentil",
    "franceville",
    "oyem",
    "moanda",
    "lambarene",
    "mouila",
    "tchibanga",
    "koulamoutou",
    "makokou",
    "bitam",
    "other",
]

# Toutes les intentions relationnelles actuellement autorisées.
ALL_DATING_INTENTS: Final[list[str]] = [
    "serious_relationship",
    "friendship",
    "discussion",
    "marriage",
    "not_sure",
]


# ---------------------------------------------------------------------------
# Structure d'un profil de démonstration
# ---------------------------------------------------------------------------

@dataclass(frozen=True, slots=True)
class DemoProfileDefinition:
    """
    Décrit un utilisateur et son profil fictif.

    frozen=True :
        empêche une modification accidentelle après création.

    slots=True :
        réduit légèrement la mémoire utilisée et empêche l'ajout
        arbitraire de propriétés inconnues.
    """

    email_slug: str
    display_name: str
    birth_date: date
    gender: str
    city: str
    biography: str
    dating_intent: str


# ---------------------------------------------------------------------------
# Données fictives
# ---------------------------------------------------------------------------

DEMO_PROFILES: Final[tuple[DemoProfileDefinition, ...]] = (
    DemoProfileDefinition(
        email_slug="arielle",
        display_name="Arielle",
        birth_date=date(1997, 3, 14),
        gender="woman",
        city="libreville",
        biography=(
            "Passionnée de voyages, de culture et de projets ambitieux. "
            "J'apprécie les conversations sincères, l'élégance et les "
            "personnes qui savent où elles vont."
        ),
        dating_intent="serious_relationship",
    ),
    DemoProfileDefinition(
        email_slug="grace",
        display_name="Grâce",
        birth_date=date(1999, 8, 21),
        gender="woman",
        city="port_gentil",
        biography=(
            "Entrepreneure, sportive et attachée aux valeurs familiales. "
            "Je recherche une relation fondée sur le respect, la stabilité "
            "et une véritable complicité."
        ),
        dating_intent="marriage",
    ),
    DemoProfileDefinition(
        email_slug="melissa",
        display_name="Mélissa",
        birth_date=date(1995, 11, 7),
        gender="woman",
        city="franceville",
        biography=(
            "Créative, curieuse et toujours prête à découvrir de nouvelles "
            "choses. J'aime la musique, la gastronomie et les échanges qui "
            "font grandir."
        ),
        dating_intent="serious_relationship",
    ),
    DemoProfileDefinition(
        email_slug="nadia",
        display_name="Nadia",
        birth_date=date(2000, 1, 29),
        gender="woman",
        city="oyem",
        biography=(
            "Calme, ambitieuse et très proche de ma famille. Je crois aux "
            "relations construites avec patience, honnêteté et maturité."
        ),
        dating_intent="friendship",
    ),
    DemoProfileDefinition(
        email_slug="estelle",
        display_name="Estelle",
        birth_date=date(1996, 6, 18),
        gender="woman",
        city="libreville",
        biography=(
            "Professionnelle passionnée par la mode, le développement "
            "personnel et les voyages. Je souhaite rencontrer quelqu'un "
            "de positif, responsable et authentique."
        ),
        dating_intent="discussion",
    ),
    DemoProfileDefinition(
        email_slug="david",
        display_name="David",
        birth_date=date(1994, 9, 12),
        gender="man",
        city="libreville",
        biography=(
            "Ingénieur, amateur de sport et de lecture. Je valorise la "
            "discipline, l'humour et les projets construits à deux."
        ),
        dating_intent="serious_relationship",
    ),
    DemoProfileDefinition(
        email_slug="kevin",
        display_name="Kevin",
        birth_date=date(1998, 4, 3),
        gender="man",
        city="moanda",
        biography=(
            "Passionné de technologie, de football et d'entrepreneuriat. "
            "Je souhaite d'abord créer une belle connexion et laisser "
            "la relation évoluer naturellement."
        ),
        dating_intent="discussion",
    ),
    DemoProfileDefinition(
        email_slug="alex",
        display_name="Alex",
        birth_date=date(1997, 12, 5),
        gender="non_binary",
        city="lambarene",
        biography=(
            "Personne ouverte, respectueuse et passionnée par l'art. "
            "Je recherche des échanges bienveillants, intelligents et "
            "sans jugement."
        ),
        dating_intent="friendship",
    ),
)


class Command(BaseCommand):
    """
    Commande de gestion Django.

    Le nom du fichier détermine le nom de la commande :

        seed_demo_profiles.py
        devient
        python manage.py seed_demo_profiles
    """

    help = (
        "Crée, actualise ou supprime les profils fictifs "
        "de démonstration du projet Mbolo."
    )

    def add_arguments(self, parser: CommandParser) -> None:
        """
        Déclare les options acceptées par la commande.
        """

        parser.add_argument(
            "--delete",
            action="store_true",
            help=(
                "Supprime tous les utilisateurs dont l'adresse "
                "commence par mbolo.demo."
            ),
        )

        parser.add_argument(
            "--viewer-email",
            type=str,
            default=None,
            help=(
                "Adresse d'un compte local dont les préférences "
                "seront élargies pour afficher les profils de démonstration."
            ),
        )

    def handle(self, *args: object, **options: object) -> None:
        """
        Point d'entrée principal de la commande.
        """

        # Cette commande ne doit jamais injecter de fausses données
        # dans une base de production.
        if not settings.DEBUG:
            raise CommandError(
                "La commande seed_demo_profiles est interdite "
                "lorsque DEBUG=False."
            )

        should_delete = bool(options.get("delete"))
        viewer_email_option = options.get("viewer_email")

        viewer_email = (
            str(viewer_email_option).strip().lower()
            if viewer_email_option
            else None
        )

        if should_delete:
            self._delete_demo_users()
            return

        self._create_or_update_demo_profiles()

        if viewer_email:
            self._configure_viewer_preferences(viewer_email)

        self.stdout.write("")
        self.stdout.write(
            self.style.SUCCESS(
                "Les données de démonstration Mbolo sont prêtes."
            )
        )

        self.stdout.write(
            "Ouvre ensuite : http://127.0.0.1:5173/discovery"
        )

    @transaction.atomic
    def _create_or_update_demo_profiles(self) -> None:
        """
        Crée ou actualise les utilisateurs, profils et préférences.

        transaction.atomic garantit que l'opération est cohérente :
        en cas d'erreur, les modifications de cette méthode sont annulées.
        """

        User = get_user_model()

        created_users = 0
        updated_users = 0

        for definition in DEMO_PROFILES:
            email = (
                f"{DEMO_EMAIL_PREFIX}"
                f"{definition.email_slug}@"
                f"{DEMO_EMAIL_DOMAIN}"
            )

            # get_or_create évite de créer plusieurs comptes
            # portant la même adresse lors des exécutions suivantes.
            user, user_created = User.objects.get_or_create(
                email=email,
                defaults={
                    "is_active": True,
                    "is_email_verified": True,
                    "is_phone_verified": False,
                    "is_suspended": False,
                },
            )

            # Nous réappliquons ces valeurs afin que la commande
            # puisse aussi réparer un compte fictif précédemment modifié.
            user.is_active = True
            user.is_email_verified = True
            user.is_phone_verified = False
            user.is_suspended = False

            # Un compte fictif ne doit pas être utilisable pour
            # une connexion interactive.
            user.set_unusable_password()

            user.save(
                update_fields=[
                    "password",
                    "is_active",
                    "is_email_verified",
                    "is_phone_verified",
                    "is_suspended",
                    "updated_at",
                ]
            )

            # update_or_create rend également le profil idempotent.
            Profile.objects.update_or_create(
                user=user,
                defaults={
                    "display_name": definition.display_name,
                    "birth_date": definition.birth_date,
                    "gender": definition.gender,
                    "city": definition.city,
                    "biography": definition.biography,
                    "dating_intent": definition.dating_intent,
                    "is_discoverable": True,
                },
            )

            # Ces préférences permettent aux comptes fictifs
            # d'avoir une structure complète, même si la première
            # version du moteur n'impose pas encore la réciprocité.
            SearchPreferences.objects.update_or_create(
                user=user,
                defaults={
                    "minimum_age": 18,
                    "maximum_age": 70,
                    "preferred_genders": ALL_GENDERS,
                    "preferred_cities": ALL_CITIES,
                    "preferred_dating_intents": ALL_DATING_INTENTS,
                    "maximum_distance_km": 500,
                    "only_verified_profiles": True,
                },
            )

            if user_created:
                created_users += 1
                action_label = "créé"
            else:
                updated_users += 1
                action_label = "actualisé"

            self.stdout.write(
                f"  [{action_label}] "
                f"{definition.display_name} — {email}"
            )

        self.stdout.write("")
        self.stdout.write(
            self.style.SUCCESS(
                f"{created_users} utilisateur(s) créé(s), "
                f"{updated_users} utilisateur(s) actualisé(s)."
            )
        )

    @transaction.atomic
    def _configure_viewer_preferences(
        self,
        viewer_email: str,
    ) -> None:
        """
        Élargit les préférences du compte utilisé pour tester l'interface.

        Cette modification est exécutée uniquement lorsque l'option
        --viewer-email est explicitement fournie.
        """

        User = get_user_model()

        try:
            viewer = User.objects.get(email__iexact=viewer_email)
        except User.DoesNotExist as exc:
            raise CommandError(
                f"Aucun utilisateur trouvé avec l'adresse : {viewer_email}"
            ) from exc

        # Le compte doit posséder un profil pour utiliser le moteur.
        if not hasattr(viewer, "profile"):
            raise CommandError(
                "Le compte indiqué ne possède pas encore de profil."
            )

        preferences, created = SearchPreferences.objects.update_or_create(
            user=viewer,
            defaults={
                "minimum_age": 18,
                "maximum_age": 70,
                "preferred_genders": ALL_GENDERS,
                "preferred_cities": ALL_CITIES,
                "preferred_dating_intents": ALL_DATING_INTENTS,
                "maximum_distance_km": 500,
                "only_verified_profiles": True,
            },
        )

        action_label = "créées" if created else "actualisées"

        self.stdout.write("")
        self.stdout.write(
            self.style.SUCCESS(
                f"Préférences {action_label} pour {viewer.email}."
            )
        )

        self.stdout.write(
            "  Âges : "
            f"{preferences.minimum_age}–{preferences.maximum_age}"
        )
        self.stdout.write(
            f"  Genres acceptés : {preferences.preferred_genders}"
        )
        self.stdout.write(
            f"  Villes acceptées : {preferences.preferred_cities}"
        )

    @transaction.atomic
    def _delete_demo_users(self) -> None:
        """
        Supprime tous les comptes créés par cette commande.

        Les relations Profile et SearchPreferences seront supprimées
        selon les règles de cascade définies par leurs OneToOneField.
        """

        User = get_user_model()

        demo_users = User.objects.filter(
            email__startswith=DEMO_EMAIL_PREFIX,
            email__endswith=f"@{DEMO_EMAIL_DOMAIN}",
        )

        number_of_users = demo_users.count()

        demo_users.delete()

        self.stdout.write(
            self.style.SUCCESS(
                f"{number_of_users} compte(s) de démonstration supprimé(s)."
            )
        )

"""Create four ordinary, fictitious accounts in a confirmed local test database."""
from dataclasses import replace

from django.contrib.auth import get_user_model
from django.core.management.base import CommandError
from django.db import transaction

from apps.profiles.management.commands.seed_test_accounts import (
    ALL_CITIES, ALL_DATING_INTENTS, ALL_GENDERS,
    TEST_ACCOUNTS, Command as TestAccountsCommand,
)
from apps.profiles.models import Gender, Profile, SearchPreferences

ACCOUNTS = (
    replace(TEST_ACCOUNTS[0], email="beta.alex@mbolo.example", display_name="Alex Test", gender=Gender.MAN),
    replace(TEST_ACCOUNTS[0], email="beta.sarah@mbolo.example", display_name="Sarah Test"),
    replace(TEST_ACCOUNTS[1], email="beta.audrey@mbolo.example", display_name="Audrey Test"),
    replace(TEST_ACCOUNTS[1], email="beta.marc@mbolo.example", display_name="Marc Test", gender=Gender.MAN),
)


class Command(TestAccountsCommand):
    help = "Crée quatre nouveaux comptes fictifs locaux sans écraser les comptes existants."

    def add_arguments(self, parser):
        parser.add_argument("--confirm-local-preproduction", action="store_true")

    def handle(self, *args, **options):
        if not options.get("confirm_local_preproduction"):
            raise CommandError("Base locale de test uniquement : --confirm-local-preproduction requis.")
        User = get_user_model()
        if any(User.objects.filter(email__iexact=account.email).exists() for account in ACCOUNTS):
            raise CommandError("Un compte bêta existe déjà. Aucun compte ni mot de passe ne sera modifié.")
        passwords = {account.email: self._prompt_valid_password(account) for account in ACCOUNTS}
        self.create_accounts(passwords)
        self.stdout.write(self.style.SUCCESS("Quatre comptes fictifs créés. Aucun match ni message préfabriqué."))
        for account in ACCOUNTS:
            self.stdout.write(f"{account.display_name} : {account.email}")

    @transaction.atomic
    def create_accounts(self, passwords):
        User = get_user_model()
        for account in ACCOUNTS:
            if User.objects.filter(email__iexact=account.email).exists():
                raise CommandError("Compte déjà présent : création annulée intégralement.")
            user = User(email=account.email, is_active=True, is_email_verified=True,
                        is_staff=False, is_superuser=False, is_suspended=False)
            user.set_password(passwords[account.email])
            user.save(force_insert=True)
            Profile.objects.update_or_create(user=user, defaults={
                "display_name": account.display_name,
                "birth_date": account.birth_date,
                "gender": account.gender,
                "city": account.city,
                "biography": "Compte fictif pour la recette locale Web et Mobile de MBOLO.",
                "dating_intent": account.dating_intent,
                "interests": list(account.interests),
                "is_discoverable": True,
            })
            SearchPreferences.objects.update_or_create(user=user, defaults={
                "minimum_age": 18, "maximum_age": 70,
                "preferred_genders": ALL_GENDERS, "preferred_cities": ALL_CITIES,
                "preferred_dating_intents": ALL_DATING_INTENTS,
                "maximum_distance_km": 500, "only_verified_profiles": False,
                "only_profiles_with_photos": False,
            })

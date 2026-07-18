from datetime import date, timedelta

from django.contrib.auth import get_user_model
from django.db.models import QuerySet

from .models import (
    Profile,
    SearchPreferences,
)


# Nous récupérons le modèle User réellement configuré dans Django.
#
# Cette méthode est préférable à un import direct de accounts.User,
# car elle respecte la valeur AUTH_USER_MODEL de settings.py.
User = get_user_model()


def subtract_years(
    source_date: date,
    years: int,
) -> date:
    """
    Retire un nombre d'années à une date.

    Exemple :
        18 juillet 2026 - 18 ans = 18 juillet 2008

    Le cas du 29 février est traité séparément :
    certaines années ne possèdent pas de 29 février.
    Dans ce cas, nous utilisons le 28 février.
    """

    try:
        return source_date.replace(
            year=source_date.year - years,
        )
    except ValueError:
        return source_date.replace(
            year=source_date.year - years,
            month=2,
            day=28,
        )


def calculate_birth_date_bounds(
    *,
    minimum_age: int,
    maximum_age: int,
    reference_date: date | None = None,
) -> tuple[date, date]:
    """
    Calcule les limites de dates de naissance correspondant
    à une tranche d'âge inclusive.

    Exemple :

        minimum_age = 25
        maximum_age = 40

    Nous cherchons les personnes âgées de 25 à 40 ans,
    en incluant les deux limites.

    La valeur retournée contient :

        date_de_naissance_la_plus_ancienne
        date_de_naissance_la_plus_récente
    """

    today = reference_date or date.today()

    # Une personne ayant exactement minimum_age ans aujourd'hui
    # peut être née jusqu'à cette date incluse.
    latest_allowed_birth_date = subtract_years(
        today,
        minimum_age,
    )

    # Pour inclure toutes les personnes ayant maximum_age ans,
    # nous calculons d'abord la date correspondant à
    # maximum_age + 1 ans, puis nous ajoutons un jour.
    #
    # Ainsi, les personnes qui n'ont pas encore atteint
    # maximum_age + 1 ans restent incluses.
    earliest_allowed_birth_date = (
        subtract_years(
            today,
            maximum_age + 1,
        )
        + timedelta(days=1)
    )

    return (
        earliest_allowed_birth_date,
        latest_allowed_birth_date,
    )


def get_or_create_search_preferences(
    *,
    user: User,
) -> SearchPreferences:
    """
    Récupère les préférences privées de l'utilisateur.

    Si elles n'existent pas encore, Django crée automatiquement
    les valeurs par défaut :

        minimum_age = 18
        maximum_age = 45
        distance = 50 km
        profils vérifiés uniquement = True
    """

    preferences, _created = (
        SearchPreferences.objects.get_or_create(
            user=user,
        )
    )

    return preferences


def build_discovery_queryset(
    *,
    user: User,
) -> QuerySet[Profile]:
    """
    Construit la requête du moteur de découverte.

    Cette fonction ne retourne pas immédiatement une liste Python.
    Elle retourne un QuerySet Django.

    Un QuerySet représente une requête SQL qui sera réellement
    exécutée lorsque les résultats seront utilisés ou sérialisés.
    """

    preferences = get_or_create_search_preferences(
        user=user,
    )

    (
        earliest_birth_date,
        latest_birth_date,
    ) = calculate_birth_date_bounds(
        minimum_age=preferences.minimum_age,
        maximum_age=preferences.maximum_age,
    )

    queryset = (
        Profile.objects

        # select_related("user") demande à Django de récupérer
        # le profil et son utilisateur dans une seule requête SQL.
        #
        # Sans cela, accéder à profile.user pour chaque résultat
        # pourrait provoquer le problème N+1 :
        #
        # 1 requête pour les profils
        # + 1 requête supplémentaire par utilisateur.
        .select_related("user")

        # L'utilisateur ne doit jamais apparaître
        # dans ses propres résultats de découverte.
        .exclude(
            user=user,
        )

        # Un profil doit avoir volontairement activé sa visibilité.
        .filter(
            is_discoverable=True,
        )

        # Le compte associé doit être actif.
        .filter(
            user__is_active=True,
        )

        # Les comptes suspendus ne doivent jamais apparaître.
        .filter(
            user__is_suspended=False,
        )

        # Sur Mbolo, la vérification de l'e-mail est obligatoire
        # avant toute apparition dans la découverte.
        .filter(
            user__is_email_verified=True,
        )

        # Un profil incomplet ne doit pas apparaître.
        #
        # Les chaînes vides correspondent aux valeurs par défaut
        # de ces champs dans notre modèle Profile.
        .exclude(
            display_name="",
        )
        .exclude(
            birth_date=None,
        )
        .exclude(
            gender="",
        )
        .exclude(
            city="",
        )
        .exclude(
            dating_intent="",
        )

        # Filtrage de l'âge directement dans PostgreSQL.
        #
        # Cela évite de charger tous les profils en mémoire Python
        # uniquement pour calculer leur âge un par un.
        .filter(
            birth_date__range=(
                earliest_birth_date,
                latest_birth_date,
            )
        )
    )

    # Une liste vide signifie :
    # "Je n'applique aucun filtre sur le genre."
    if preferences.preferred_genders:
        queryset = queryset.filter(
            gender__in=(
                preferences.preferred_genders
            )
        )

    # Une liste vide signifie :
    # "Toutes les villes sont acceptées."
    if preferences.preferred_cities:
        queryset = queryset.filter(
            city__in=(
                preferences.preferred_cities
            )
        )

    # Une liste vide signifie :
    # "Toutes les intentions sont acceptées."
    if preferences.preferred_dating_intents:
        queryset = queryset.filter(
            dating_intent__in=(
                preferences.preferred_dating_intents
            )
        )

    # Nous utilisons un ordre stable.
    #
    # L'UUID permet de départager deux profils créés
    # exactement au même moment.
    return queryset.order_by(
        "-created_at",
        "id",
    )

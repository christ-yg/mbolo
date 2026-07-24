"""
Service de construction du moteur de découverte Mbolo.

Ce fichier contient la logique de filtrage des profils proposés
à l'utilisateur connecté.

La requête applique notamment les règles suivantes :

- exclure le propre profil de l'utilisateur ;
- exclure les profils invisibles ;
- exclure les comptes inactifs ;
- exclure les comptes suspendus ;
- exclure les comptes non vérifiés ;
- exclure les profils incomplets ;
- respecter les préférences d'âge ;
- respecter les préférences de genre ;
- respecter les préférences de ville ;
- respecter les intentions de rencontre ;
- exclure les blocages dans les deux directions.

La logique reste dans un service séparé afin de pouvoir être
réutilisée par :

- l'application web ;
- l'application mobile ;
- une future tâche de recommandation ;
- des tests unitaires ;
- un moteur de compatibilité plus avancé.
"""

from datetime import date, timedelta

from django.contrib.auth import get_user_model
from django.db.models import (
    Case,
    IntegerField,
    Q,
    QuerySet,
    Value,
    When,
    Exists,
    OuterRef,
)
from django.utils import timezone

from apps.safety.models import Block
from apps.subscriptions.services import get_subscription_state
from apps.subscriptions.models import ProfileBoost

from .models import (
    Profile,
    SearchPreferences,
)
from .locations import (
    GABON_CITY_CENTROIDS,
    approximate_city_distance_km,
)


# Récupère le modèle User réellement configuré dans Django.
#
# Cette méthode respecte AUTH_USER_MODEL et évite d'importer
# directement une classe utilisateur spécifique.
User = get_user_model()


def subtract_years(
    source_date: date,
    years: int,
) -> date:
    """
    Retire un nombre d'années à une date.

    Exemple :

        18 juillet 2026 - 18 ans
        = 18 juillet 2008

    Le cas du 29 février est traité séparément car certaines
    années ne possèdent pas de 29 février.
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
    Transforme une tranche d'âge en intervalle de dates de naissance.

    Exemple :

        minimum_age = 25
        maximum_age = 40

    La base de données filtrera les dates de naissance correspondant
    aux personnes ayant entre 25 et 40 ans inclusivement.

    Cette méthode évite de charger tous les profils en mémoire Python
    pour calculer leur âge un par un.
    """

    today = reference_date or date.today()

    # Date de naissance la plus récente autorisée.
    #
    # Une personne née après cette date serait trop jeune.
    latest_allowed_birth_date = subtract_years(
        today,
        minimum_age,
    )

    # Date de naissance la plus ancienne autorisée.
    #
    # Nous retirons maximum_age + 1 années, puis ajoutons un jour,
    # afin d'inclure toutes les personnes ayant exactement l'âge
    # maximum demandé.
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
    Retourne les préférences privées de l'utilisateur.

    Si elles n'existent pas, les préférences par défaut sont créées.
    """

    preferences, _created = (
        SearchPreferences.objects.get_or_create(
            user=user,
        )
    )

    return preferences


def get_blocked_user_ids(
    *,
    user: User,
) -> set:
    """
    Retourne les identifiants des utilisateurs bloqués dans les deux sens.

    Deux situations sont prises en compte :

    1. l'utilisateur connecté a bloqué une personne ;
    2. une autre personne a bloqué l'utilisateur connecté.

    Exemple :

        Christ bloque Marie
        → Marie est exclue de la découverte de Christ.

        Marie bloque Christ
        → Marie est également exclue de la découverte de Christ.

    Nous utilisons un set Python pour supprimer automatiquement
    les éventuels doublons.
    """

    # Utilisateurs bloqués directement par l'utilisateur courant.
    users_blocked_by_current_user = Block.objects.filter(
        blocker=user,
    ).values_list(
        "blocked_user_id",
        flat=True,
    )

    # Utilisateurs ayant bloqué l'utilisateur courant.
    users_who_blocked_current_user = Block.objects.filter(
        blocked_user=user,
    ).values_list(
        "blocker_id",
        flat=True,
    )

    return {
        *users_blocked_by_current_user,
        *users_who_blocked_current_user,
    }


def build_discovery_queryset(
    *,
    user: User,
) -> QuerySet[Profile]:
    """
    Construit le QuerySet sécurisé du moteur de découverte.

    Un QuerySet est une représentation paresseuse d'une requête SQL.

    La requête n'est généralement exécutée que lorsque les résultats
    sont réellement parcourus, paginés ou sérialisés.
    """

    preferences = get_or_create_search_preferences(
        user=user,
    )
    advanced_filters_enabled = bool(
        get_subscription_state(user)["entitlements"]["advanced_filters"]
    )

    (
        earliest_birth_date,
        latest_birth_date,
    ) = calculate_birth_date_bounds(
        minimum_age=preferences.minimum_age,
        maximum_age=preferences.maximum_age,
    )

    # Récupération des comptes qui doivent être totalement exclus
    # en raison d'un blocage dans l'un des deux sens.
    blocked_user_ids = get_blocked_user_ids(
        user=user,
    )

    queryset = (
        Profile.objects

        # Charge Profile et User dans une seule requête SQL.
        #
        # Cela évite le problème N+1 lorsque le sérialiseur accède
        # à profile.user pour chaque résultat.
        .select_related("user", "verification")

        # Un utilisateur ne doit jamais apparaître
        # dans sa propre découverte.
        .exclude(
            user=user,
        )

        # Exclusion bidirectionnelle des utilisateurs bloqués.
        #
        # Si le set est vide, cette exclusion reste parfaitement valide.
        .exclude(
            user_id__in=blocked_user_ids,
        )

        # Un profil déjà évalué ne doit pas revenir à chaque chargement.
        #
        # Le Rewind Premium supprime uniquement le dernier PASS autorisé :
        # ce profil redevient alors naturellement éligible à cette requête.
        .exclude(
            received_interactions__actor=user,
        )

        # Le propriétaire du profil doit avoir volontairement
        # rendu son profil découvrable.
        .filter(
            is_discoverable=True,
        )

        # Le compte doit être actif.
        .filter(
            user__is_active=True,
        )

        # Le compte ne doit pas être suspendu.
        .filter(
            user__is_suspended=False,
        )

        # L'adresse e-mail doit être vérifiée.
        .filter(
            user__is_email_verified=True,
        )

        # Exclusion des profils incomplets.
        #
        # Nos champs facultatifs utilisent une chaîne vide
        # comme valeur initiale.
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
        .filter(
            birth_date__range=(
                earliest_birth_date,
                latest_birth_date,
            )
        )
    )

    # Une liste vide signifie :
    # aucun filtre spécifique sur les genres.
    if preferences.preferred_genders:
        queryset = queryset.filter(
            gender__in=preferences.preferred_genders,
        )

    # Une liste vide signifie :
    # toutes les villes sont acceptées.
    if advanced_filters_enabled and preferences.preferred_cities:
        queryset = queryset.filter(
            city__in=preferences.preferred_cities,
        )

    # Proximité géographique approximative et respectueuse de la vie privée.
    #
    # Aucune latitude/longitude d'utilisateur n'est stockée. PostgreSQL reçoit
    # uniquement une table CASE contenant la distance arrondie entre la ville
    # déclarée du membre connecté et chaque ville connue.
    current_profile = getattr(user, "profile", None)
    current_city = getattr(current_profile, "city", "")
    if (
        advanced_filters_enabled
        and current_city in GABON_CITY_CENTROIDS
    ):
        distance_cases = [
            When(
                city=candidate_city,
                then=Value(
                    approximate_city_distance_km(
                        current_city,
                        candidate_city,
                    )
                ),
            )
            for candidate_city in GABON_CITY_CENTROIDS
        ]
        queryset = queryset.annotate(
            distance_km=Case(
                *distance_cases,
                default=Value(None),
                output_field=IntegerField(),
            )
        ).filter(
            distance_km__lte=preferences.maximum_distance_km,
        )
    else:
        # Le sérialiseur peut ainsi distinguer clairement une distance
        # indisponible d'une distance nulle.
        queryset = queryset.annotate(
            distance_km=Value(
                None,
                output_field=IntegerField(),
            )
        )

    if (
        advanced_filters_enabled
        and preferences.only_verified_profiles
    ):
        queryset = queryset.filter(
            verification__status="approved",
        )

    # Une liste vide signifie :
    # toutes les intentions de rencontre sont acceptées.
    if advanced_filters_enabled and preferences.preferred_dating_intents:
        queryset = queryset.filter(
            dating_intent__in=(
                preferences.preferred_dating_intents
            ),
        )

    # Priorité Prestige calculée par PostgreSQL.
    #
    # Un simple champ envoyé par React ne peut donc pas promouvoir un profil.
    # Seul un abonnement Prestige actif ou en essai, non expiré, reçoit le
    # rang prioritaire. Tous les contrôles de sécurité et préférences restent
    # appliqués avant ce classement.
    active_boosts = ProfileBoost.objects.filter(
        user_id=OuterRef("user_id"),
        starts_at__lte=timezone.now(),
        ends_at__gt=timezone.now(),
    )
    queryset = queryset.annotate(
        boost_priority=Case(
            When(Exists(active_boosts), then=Value(1)),
            default=Value(0),
            output_field=IntegerField(),
        ),
        premium_priority=Case(
            When(
                Q(user__subscription__plan="prestige")
                & Q(user__subscription__status__in=("active", "trial"))
                & (
                    Q(user__subscription__ends_at__isnull=True)
                    | Q(user__subscription__ends_at__gt=timezone.now())
                ),
                then=Value(1),
            ),
            default=Value(0),
            output_field=IntegerField(),
        )
    )

    # Ordre stable des résultats.
    #
    # L'UUID départage les profils qui auraient exactement
    # la même date de création.
    return queryset.order_by(
        "-boost_priority",
        "-premium_priority",
        "-created_at",
        "id",
    )

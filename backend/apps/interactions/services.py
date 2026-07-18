"""
Services métier du module des interactions.

Ce fichier centralise la logique sensible des likes, des passes
et des matchs.

Les principales protections utilisées sont :

- authentification vérifiée par les vues ;
- validation métier ;
- contrôle des comptes suspendus ;
- contrôle de la vérification d'e-mail ;
- contrôle des blocages bidirectionnels ;
- transactions atomiques ;
- verrouillage avec select_for_update() ;
- contraintes PostgreSQL ;
- ordre canonique des matchs ;
- messages génériques contre l'énumération.
"""

from dataclasses import dataclass
from uuid import UUID

from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction

from apps.profiles.models import Profile
from apps.safety.services import users_are_blocked

from .models import (
    Interaction,
    InteractionDecision,
    Match,
)


@dataclass(frozen=True)
class InteractionResult:
    """
    Résultat immuable d'une opération d'interaction.

    interaction
        Ligne LIKE ou PASS enregistrée.

    interaction_created
        True si une nouvelle ligne a été créée.
        False si une ligne existante a été modifiée.

    match
        Match créé ou retrouvé.
        None lorsqu'il n'existe aucun match.

    match_created
        True uniquement lorsqu'un nouveau match vient d'être créé.
    """

    interaction: Interaction
    interaction_created: bool
    match: Match | None
    match_created: bool


def canonical_profile_pair(
    *,
    first_profile: Profile,
    second_profile: Profile,
) -> tuple[Profile, Profile]:
    """
    Place deux profils dans un ordre stable.

    Cet ordre empêche la création de deux matchs équivalents :

        A / B
        B / A
    """

    if first_profile.id == second_profile.id:
        raise ValidationError(
            "Un profil ne peut pas être associé à lui-même."
        )

    if str(first_profile.id) < str(second_profile.id):
        return first_profile, second_profile

    return second_profile, first_profile


def validate_actor(
    *,
    actor,
) -> Profile:
    """
    Vérifie que l'utilisateur connecté peut effectuer une interaction.

    Conditions :

    - compte actif ;
    - compte non suspendu ;
    - adresse e-mail vérifiée ;
    - profil existant ;
    - profil complet ;
    - profil découvrable.
    """

    if not actor.is_active:
        raise ValidationError(
            "Ce compte ne peut pas effectuer cette action."
        )

    if actor.is_suspended:
        raise ValidationError(
            "Ce compte ne peut pas effectuer cette action."
        )

    if not actor.is_email_verified:
        raise ValidationError(
            "L'adresse e-mail doit être vérifiée."
        )

    try:
        actor_profile = (
            Profile.objects
            .select_for_update()
            .select_related("user")
            .get(
                user=actor,
            )
        )
    except Profile.DoesNotExist as exc:
        raise ValidationError(
            "Complétez votre profil avant d'interagir."
        ) from exc

    if not actor_profile.is_complete:
        raise ValidationError(
            "Complétez votre profil avant d'interagir."
        )

    if not actor_profile.is_discoverable:
        raise ValidationError(
            "Votre profil doit être visible avant d'interagir."
        )

    return actor_profile


def validate_target_profile(
    *,
    actor,
    target_profile_id: UUID,
) -> Profile:
    """
    Vérifie que le profil ciblé peut recevoir une interaction.

    Un message générique est utilisé lorsque le profil :

    - n'existe pas ;
    - est privé ;
    - appartient à un compte inactif ;
    - appartient à un compte suspendu ;
    - appartient à un compte non vérifié.

    Cela réduit les possibilités d'énumération des comptes.
    """

    try:
        target_profile = (
            Profile.objects
            .select_for_update()
            .select_related("user")
            .get(
                id=target_profile_id,
                is_discoverable=True,
                user__is_active=True,
                user__is_suspended=False,
                user__is_email_verified=True,
            )
        )
    except Profile.DoesNotExist as exc:
        raise ValidationError(
            "Le profil demandé n'est pas disponible."
        ) from exc

    if target_profile.user_id == actor.id:
        raise ValidationError(
            "Vous ne pouvez pas interagir "
            "avec votre propre profil."
        )

    if not target_profile.is_complete:
        raise ValidationError(
            "Le profil demandé n'est pas disponible."
        )

    # Contrôle de blocage bidirectionnel.
    #
    # Il suffit que l'un des deux utilisateurs ait bloqué l'autre
    # pour interdire totalement les interactions.
    if users_are_blocked(
        first_user=actor,
        second_user=target_profile.user,
    ):
        # Message volontairement générique.
        #
        # Nous ne révélons pas qui a bloqué qui.
        raise ValidationError(
            "Le profil demandé n'est pas disponible."
        )

    return target_profile


def find_reciprocal_like(
    *,
    actor_profile: Profile,
    target_profile: Profile,
) -> Interaction | None:
    """
    Recherche le like inverse.

    Exemple :

        A LIKE B

    Nous recherchons :

        B LIKE A
    """

    return (
        Interaction.objects
        .select_for_update()
        .filter(
            actor=target_profile.user,
            target_profile=actor_profile,
            decision=InteractionDecision.LIKE,
        )
        .first()
    )


def get_existing_match(
    *,
    first_profile: Profile,
    second_profile: Profile,
) -> Match | None:
    """
    Recherche un match entre deux profils.
    """

    profile_one, profile_two = canonical_profile_pair(
        first_profile=first_profile,
        second_profile=second_profile,
    )

    return (
        Match.objects
        .select_for_update()
        .filter(
            profile_one=profile_one,
            profile_two=profile_two,
        )
        .first()
    )


def create_or_get_match(
    *,
    actor_profile: Profile,
    target_profile: Profile,
) -> tuple[Match, bool]:
    """
    Crée ou récupère un match unique.

    Avant la création, nous vérifions encore l'absence de blocage.

    Cette vérification supplémentaire protège contre une situation
    de concurrence dans laquelle un blocage aurait été créé pendant
    le traitement de l'interaction.
    """

    if users_are_blocked(
        first_user=actor_profile.user,
        second_user=target_profile.user,
    ):
        raise ValidationError(
            "Le profil demandé n'est pas disponible."
        )

    profile_one, profile_two = canonical_profile_pair(
        first_profile=actor_profile,
        second_profile=target_profile,
    )

    existing_match = (
        Match.objects
        .select_for_update()
        .filter(
            profile_one=profile_one,
            profile_two=profile_two,
        )
        .first()
    )

    if existing_match is not None:
        if not existing_match.is_active:
            existing_match.is_active = True

            existing_match.save(
                update_fields=[
                    "is_active",
                    "updated_at",
                ]
            )

        return existing_match, False

    try:
        # Transaction imbriquée créant un savepoint.
        #
        # Une collision d'unicité n'endommagera pas la transaction
        # principale.
        with transaction.atomic():
            match = Match.objects.create(
                profile_one=profile_one,
                profile_two=profile_two,
                is_active=True,
            )

        return match, True

    except IntegrityError:
        # Une requête concurrente a probablement créé
        # la même paire avant nous.
        match = (
            Match.objects
            .select_for_update()
            .get(
                profile_one=profile_one,
                profile_two=profile_two,
            )
        )

        if not match.is_active:
            match.is_active = True

            match.save(
                update_fields=[
                    "is_active",
                    "updated_at",
                ]
            )

        return match, False


def deactivate_existing_match(
    *,
    actor_profile: Profile,
    target_profile: Profile,
) -> Match | None:
    """
    Désactive un match lorsqu'un participant remplace son like
    par un pass.
    """

    match = get_existing_match(
        first_profile=actor_profile,
        second_profile=target_profile,
    )

    if match is None:
        return None

    if match.is_active:
        match.is_active = False

        match.save(
            update_fields=[
                "is_active",
                "updated_at",
            ]
        )

    return match


def create_interaction_safely(
    *,
    actor,
    target_profile: Profile,
    decision: str,
) -> tuple[Interaction, bool]:
    """
    Crée une interaction en protégeant la transaction principale
    contre les collisions d'unicité.
    """

    try:
        with transaction.atomic():
            interaction = Interaction.objects.create(
                actor=actor,
                target_profile=target_profile,
                decision=decision,
            )

        return interaction, True

    except IntegrityError:
        interaction = (
            Interaction.objects
            .select_for_update()
            .get(
                actor=actor,
                target_profile=target_profile,
            )
        )

        interaction.decision = decision

        interaction.save(
            update_fields=[
                "decision",
                "updated_at",
            ]
        )

        return interaction, False


@transaction.atomic
def record_interaction(
    *,
    actor,
    target_profile_id: UUID,
    decision: str,
) -> InteractionResult:
    """
    Enregistre un LIKE ou un PASS de manière atomique.

    La transaction garantit le principe tout ou rien.

    En cas d'erreur :

    - aucune interaction partielle n'est conservée ;
    - aucun match partiel n'est créé ;
    - PostgreSQL effectue un rollback.
    """

    valid_decisions = {
        InteractionDecision.LIKE,
        InteractionDecision.PASS,
    }

    if decision not in valid_decisions:
        raise ValidationError(
            {
                "decision": (
                    "La décision doit être 'like' ou 'pass'."
                )
            }
        )

    actor_profile = validate_actor(
        actor=actor,
    )

    target_profile = validate_target_profile(
        actor=actor,
        target_profile_id=target_profile_id,
    )

    existing_interaction = (
        Interaction.objects
        .select_for_update()
        .filter(
            actor=actor,
            target_profile=target_profile,
        )
        .first()
    )

    if existing_interaction is None:
        interaction, interaction_created = (
            create_interaction_safely(
                actor=actor,
                target_profile=target_profile,
                decision=decision,
            )
        )
    else:
        interaction = existing_interaction

        # Évite une écriture inutile si la décision n'a pas changé.
        if interaction.decision != decision:
            interaction.decision = decision

            interaction.save(
                update_fields=[
                    "decision",
                    "updated_at",
                ]
            )

        interaction_created = False

    match = None
    match_created = False

    if decision == InteractionDecision.LIKE:
        reciprocal_like = find_reciprocal_like(
            actor_profile=actor_profile,
            target_profile=target_profile,
        )

        if reciprocal_like is not None:
            match, match_created = create_or_get_match(
                actor_profile=actor_profile,
                target_profile=target_profile,
            )

    else:
        # PASS signifie retrait de l'intérêt positif.
        deactivate_existing_match(
            actor_profile=actor_profile,
            target_profile=target_profile,
        )

    return InteractionResult(
        interaction=interaction,
        interaction_created=interaction_created,
        match=match,
        match_created=match_created,
    )

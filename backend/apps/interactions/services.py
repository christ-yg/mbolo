"""
Services métier du module des interactions.

Ce fichier contient la logique sensible qui ne doit pas être
placée directement dans les vues HTTP.

Séparer la logique métier des vues présente plusieurs avantages :

- réutilisation future par l'application mobile ;
- tests unitaires plus simples ;
- transactions centralisées ;
- réduction du risque de duplication de code ;
- meilleure lisibilité ;
- meilleure traçabilité des règles de sécurité.

Les opérations critiques utilisent :

- transaction.atomic() ;
- select_for_update() ;
- contraintes d'unicité PostgreSQL ;
- validation multicouche ;
- messages génériques contre l'énumération.
"""

from dataclasses import dataclass
from uuid import UUID

from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction

from apps.profiles.models import Profile

from .models import (
    Interaction,
    InteractionDecision,
    Match,
)


@dataclass(frozen=True)
class InteractionResult:
    """
    Résultat immuable d'une opération d'interaction.

    frozen=True empêche de modifier accidentellement les données
    après la création de l'objet.

    Attributs :

    interaction
        Interaction LIKE ou PASS enregistrée.

    interaction_created
        True si une nouvelle ligne a été créée.
        False si une interaction existante a été modifiée.

    match
        Match existant ou nouvellement créé.
        None lorsqu'aucun match n'existe.

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
    Retourne deux profils dans un ordre canonique et stable.

    Sans ordre canonique, les paires suivantes pourraient être
    considérées comme différentes :

        A / B
        B / A

    Avec l'ordre canonique, le profil ayant le plus petit UUID
    est toujours stocké dans profile_one.
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
    Vérifie que l'utilisateur connecté est autorisé à interagir.

    Conditions obligatoires :

    - compte actif ;
    - compte non suspendu ;
    - adresse e-mail vérifiée ;
    - profil existant ;
    - profil complet ;
    - profil visible dans la découverte.

    Un utilisateur qui refuse d'être visible ne doit pas pouvoir
    interagir anonymement avec les autres profils.
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
        # select_for_update() verrouille le profil jusqu'à la fin
        # de la transaction courante.
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

    Nous utilisons volontairement un message générique lorsque :

    - le profil n'existe pas ;
    - le profil est privé ;
    - le compte est suspendu ;
    - le compte est désactivé ;
    - l'e-mail n'est pas vérifié.

    Cette uniformité réduit le risque d'énumération des profils.
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

    return target_profile


def find_reciprocal_like(
    *,
    actor_profile: Profile,
    target_profile: Profile,
) -> Interaction | None:
    """
    Recherche un like dans le sens inverse.

    Situation actuelle :

        utilisateur A → LIKE → profil B

    Situation réciproque recherchée :

        utilisateur B → LIKE → profil A

    Si cette seconde interaction existe, un match peut être créé.
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

    L'ordre canonique est appliqué avant la requête afin de
    rechercher systématiquement la même paire.
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

    Protections utilisées :

    1. ordre canonique des profils ;
    2. contrainte UniqueConstraint PostgreSQL ;
    3. transaction imbriquée autour de l'INSERT ;
    4. récupération du match si une requête concurrente
       l'a créé quelques millisecondes auparavant.
    """

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
        # Transaction imbriquée / savepoint.
        #
        # Si PostgreSQL déclenche IntegrityError, seule cette petite
        # transaction est annulée. La transaction principale reste
        # utilisable.
        with transaction.atomic():
            match = Match.objects.create(
                profile_one=profile_one,
                profile_two=profile_two,
                is_active=True,
            )

        return match, True

    except IntegrityError:
        # Une autre requête concurrente a probablement créé
        # exactement la même paire.
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
    Désactive un match lorsqu'un participant retire son like.

    Exemple :

        A LIKE B
        B LIKE A
        => match actif

        A remplace ensuite LIKE par PASS
        => match désactivé

    Nous conservons la ligne en base pour la traçabilité,
    mais elle ne sera plus visible dans l'endpoint des matchs actifs.
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
    Crée une interaction en résistant aux requêtes concurrentes.

    Une transaction imbriquée protège la transaction principale
    lorsqu'une contrainte d'unicité est déclenchée.
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
        # Une autre transaction a créé la même interaction.
        # Nous récupérons la ligne protégée par verrou.
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
    Enregistre un LIKE ou un PASS dans une transaction atomique.

    Une transaction atomique garantit le principe :

        tout ou rien

    Si une erreur non gérée survient :

    - aucune interaction partielle n'est conservée ;
    - aucun match incomplet n'est créé ;
    - PostgreSQL effectue un rollback.
    """

    # Défense supplémentaire pour les appels directs au service.
    #
    # L'API contrôle déjà ce champ avec ChoiceField, mais le service
    # pourrait plus tard être appelé par Celery ou une commande Django.
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

        # Nous évitons une écriture SQL inutile si la décision
        # demandée est déjà enregistrée.
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
        # Un PASS retire l'intérêt positif.
        #
        # S'il existait déjà un match, il devient inactif.
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

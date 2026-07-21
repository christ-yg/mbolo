"""
Services métier de la messagerie privée Mbolo.

Ce module contient la logique de sécurité indépendante
des vues HTTP.
"""

from dataclasses import dataclass
from uuid import UUID

from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone

from apps.interactions.models import Match

from .models import Conversation, Message


@dataclass(frozen=True)
class ConversationResult:
    """
    Résultat de l'ouverture d'une conversation.
    """

    conversation: Conversation
    created: bool


@dataclass(frozen=True)
class MarkConversationReadResult:
    """
    Résultat du marquage d'une conversation comme lue.
    """

    conversation: Conversation
    marked_count: int
    read_at: object


def get_actor_profile(actor):
    """
    Retourne le profil du compte authentifié.
    """

    if not getattr(actor, "is_authenticated", False):
        raise ValidationError(
            "Une authentification est requise."
        )

    try:
        return actor.profile
    except AttributeError as exc:
        raise ValidationError(
            "Complétez votre profil avant d'accéder "
            "à la messagerie."
        ) from exc


@transaction.atomic
def get_or_create_conversation(
    *,
    actor,
    match_id: UUID,
) -> ConversationResult:
    """
    Retourne ou crée la conversation d'un match actif.

    Contrôles :

    - compte authentifié ;
    - profil existant ;
    - match actif ;
    - acteur participant au match ;
    - une seule conversation par match.
    """

    actor_profile = get_actor_profile(actor)

    try:
        match = (
            Match.objects
            .select_for_update()
            .select_related(
                "profile_one",
                "profile_one__user",
                "profile_two",
                "profile_two__user",
            )
            .get(
                id=match_id,
                is_active=True,
            )
        )
    except Match.DoesNotExist as exc:
        raise ValidationError(
            "Ce match actif est introuvable."
        ) from exc

    if not match.includes_profile(actor_profile):
        raise ValidationError(
            "Vous ne participez pas à ce match."
        )

    conversation, created = (
        Conversation.objects.get_or_create(
            match=match,
        )
    )

    return ConversationResult(
        conversation=conversation,
        created=created,
    )


def get_conversation_for_actor(
    *,
    actor,
    conversation_id: UUID,
) -> Conversation:
    """
    Récupère une conversation appartenant à l'acteur.

    Une conversation liée à un match inactif n'est pas accessible.
    """

    get_actor_profile(actor)

    try:
        conversation = (
            Conversation.objects
            .select_related(
                "match",
                "match__profile_one",
                "match__profile_one__user",
                "match__profile_two",
                "match__profile_two__user",
            )
            .get(
                id=conversation_id,
                match__is_active=True,
            )
        )
    except Conversation.DoesNotExist as exc:
        raise ValidationError(
            "Cette conversation active est introuvable."
        ) from exc

    if not conversation.includes_user(actor):
        raise ValidationError(
            "Vous ne participez pas à cette conversation."
        )

    return conversation


@transaction.atomic
def send_message(
    *,
    actor,
    conversation_id: UUID,
    body: str,
) -> Message:
    """
    Envoie un message dans une conversation active.

    L'expéditeur est toujours actor, donc request.user.
    """

    conversation = get_conversation_for_actor(
        actor=actor,
        conversation_id=conversation_id,
    )

    normalized_body = (body or "").strip()

    if not normalized_body:
        raise ValidationError(
            {
                "body": [
                    "Le message ne peut pas être vide."
                ]
            }
        )

    if len(normalized_body) > Message.MAX_BODY_LENGTH:
        raise ValidationError(
            {
                "body": [
                    "Le message ne peut pas dépasser "
                    f"{Message.MAX_BODY_LENGTH} caractères."
                ]
            }
        )

    message = Message.objects.create(
        conversation=conversation,
        sender=actor,
        body=normalized_body,
    )

    Conversation.objects.filter(
        id=conversation.id,
    ).update(
        updated_at=timezone.now(),
    )

    return message


@transaction.atomic
def mark_conversation_as_read(
    *,
    actor,
    conversation_id: UUID,
) -> MarkConversationReadResult:
    """
    Marque comme lus tous les messages reçus dans une conversation.

    Les messages envoyés par actor ne sont jamais modifiés.

    L'opération est idempotente :
    la relancer ne modifie pas les messages déjà lus.
    """

    conversation = get_conversation_for_actor(
        actor=actor,
        conversation_id=conversation_id,
    )

    read_at = timezone.now()

    marked_count = (
        Message.objects
        .filter(
            conversation=conversation,
            read_at__isnull=True,
        )
        .exclude(
            sender=actor,
        )
        .update(
            read_at=read_at,
        )
    )

    return MarkConversationReadResult(
        conversation=conversation,
        marked_count=marked_count,
        read_at=read_at,
    )


def get_total_unread_count(
    *,
    actor,
) -> int:
    """
    Retourne le nombre total de messages non lus du compte.

    Seuls les messages appartenant à des matchs actifs sont comptés.
    """

    actor_profile = get_actor_profile(actor)

    return (
        Message.objects
        .filter(
            conversation__match__is_active=True,
            read_at__isnull=True,
        )
        .filter(
            conversation__match__profile_one=actor_profile,
        )
        .exclude(
            sender=actor,
        )
        .count()
        +
        Message.objects
        .filter(
            conversation__match__is_active=True,
            read_at__isnull=True,
            conversation__match__profile_two=actor_profile,
        )
        .exclude(
            sender=actor,
        )
        .count()
    )

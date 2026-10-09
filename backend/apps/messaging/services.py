"""
Services métier de la messagerie privée Mbolo.

Ce module contient la logique de sécurité indépendante
des vues HTTP.
"""

from dataclasses import dataclass
from datetime import timedelta
from uuid import UUID

from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone

from apps.interactions.models import Match
from apps.photos.image_processing import process_profile_photo

from .models import Conversation, Message, MessageReaction


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
    image=None,
    reply_to_id: UUID | None = None,
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

    if not normalized_body and image is None:
        raise ValidationError(
            {
                "body": [
                    "Ajoutez un texte ou une image."
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

    processed = process_profile_photo(image) if image is not None else None
    reply_to = None
    if reply_to_id is not None:
        try:
            reply_to = Message.objects.get(
                id=reply_to_id,
                conversation=conversation,
            )
        except Message.DoesNotExist as exc:
            raise ValidationError(
                {"reply_to_id": ["Le message cité est introuvable."]}
            ) from exc
    message = Message(
        conversation=conversation,
        sender=actor,
        body=normalized_body,
        reply_to=reply_to,
    )
    if processed is not None:
        message.image.save(processed.filename, processed.content, save=False)
    message.save()

    Conversation.objects.filter(
        id=conversation.id,
    ).update(
        updated_at=timezone.now(),
    )

    return message


@transaction.atomic
def set_message_reaction(*, actor, conversation_id: UUID, message_id: UUID, emoji: str):
    """Ajoute, remplace ou retire la réaction de l'acteur."""
    conversation = get_conversation_for_actor(
        actor=actor,
        conversation_id=conversation_id,
    )
    try:
        message = Message.objects.get(id=message_id, conversation=conversation)
    except Message.DoesNotExist as exc:
        raise ValidationError("Ce message est introuvable.") from exc

    if message.deleted_at is not None:
        raise ValidationError("Un message supprimé ne peut plus recevoir de réaction.")

    reaction = MessageReaction.objects.filter(message=message, user=actor).first()
    if not emoji:
        if reaction is not None:
            reaction.delete()
        return message
    if emoji not in MessageReaction.ALLOWED_EMOJIS:
        raise ValidationError({"emoji": ["Cette réaction n'est pas autorisée."]})
    MessageReaction.objects.update_or_create(
        message=message,
        user=actor,
        defaults={"emoji": emoji},
    )
    return message


@transaction.atomic
def delete_message_for_everyone(*, actor, conversation_id: UUID, message_id: UUID):
    """Masque définitivement le contenu d'un message appartenant à l'acteur."""
    conversation = get_conversation_for_actor(
        actor=actor,
        conversation_id=conversation_id,
    )
    try:
        message = (
            Message.objects.select_for_update(of=("self",))
            .select_related("sender", "reply_to", "reply_to__sender__profile")
            .get(id=message_id, conversation=conversation)
        )
    except Message.DoesNotExist as exc:
        raise ValidationError("Ce message est introuvable.") from exc

    if message.sender_id != actor.id:
        raise ValidationError("Seul l'expéditeur peut supprimer ce message.")
    if message.deleted_at is not None:
        return message

    image_name = message.image.name if message.image else None
    image_storage = message.image.storage if message.image else None
    message.body = ""
    message.image = None
    message.deleted_at = timezone.now()
    message.save(update_fields=("body", "image", "deleted_at"))
    message.reactions.all().delete()
    if image_name and image_storage:
        transaction.on_commit(lambda: image_storage.delete(image_name))
    return message


@transaction.atomic
def edit_message(*, actor, conversation_id: UUID, message_id: UUID, body: str):
    """Modifie le texte d'un message récent appartenant à l'acteur."""
    conversation = get_conversation_for_actor(
        actor=actor,
        conversation_id=conversation_id,
    )
    try:
        message = Message.objects.select_for_update().get(
            id=message_id,
            conversation=conversation,
        )
    except Message.DoesNotExist as exc:
        raise ValidationError("Ce message est introuvable.") from exc

    if message.sender_id != actor.id:
        raise ValidationError("Seul l'expéditeur peut modifier ce message.")
    if message.deleted_at is not None:
        raise ValidationError("Un message supprimé ne peut pas être modifié.")
    if timezone.now() - message.created_at > timedelta(minutes=15):
        raise ValidationError("Le délai de modification de 15 minutes est dépassé.")

    normalized_body = (body or "").strip()
    if not normalized_body:
        raise ValidationError({"body": ["Le texte du message est requis."]})
    if len(normalized_body) > Message.MAX_BODY_LENGTH:
        raise ValidationError({"body": ["Le message est trop long."]})

    message.body = normalized_body
    message.edited_at = timezone.now()
    message.save(update_fields=("body", "edited_at"))
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

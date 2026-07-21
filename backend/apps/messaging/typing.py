"""
Gestion éphémère de l'indicateur de saisie Mbolo.

L'état est stocké dans Redis via le cache Django. Aucun texte saisi
n'est conservé et aucune écriture SQL n'est réalisée.
"""

from django.core.cache import cache

from .services import get_conversation_for_actor


TYPING_TTL_SECONDS = 8


def _typing_cache_key(conversation_id, user_id) -> str:
    return f"mbolo:typing:{conversation_id}:{user_id}"


def set_typing_status(*, actor, conversation_id, is_typing: bool) -> dict[str, object]:
    """Enregistre ou supprime l'état de saisie du participant authentifié."""
    conversation = get_conversation_for_actor(
        actor=actor,
        conversation_id=conversation_id,
    )

    key = _typing_cache_key(conversation.id, actor.id)

    if is_typing:
        cache.set(key, True, timeout=TYPING_TTL_SECONDS)
    else:
        cache.delete(key)

    return {
        "conversation_id": conversation.id,
        "is_typing": bool(is_typing),
        "expires_in_seconds": TYPING_TTL_SECONDS if is_typing else 0,
    }


def get_other_typing_status(*, actor, conversation_id) -> dict[str, object]:
    """Retourne uniquement l'état de saisie de l'autre participant."""
    conversation = get_conversation_for_actor(
        actor=actor,
        conversation_id=conversation_id,
    )

    other_profile = conversation.other_profile_for_user(actor)
    is_typing = bool(
        cache.get(
            _typing_cache_key(
                conversation.id,
                other_profile.user_id,
            )
        )
    )

    return {
        "conversation_id": conversation.id,
        "other_is_typing": is_typing,
    }

"""
Outils de diffusion temps réel de la messagerie Mbolo.

Ce module centralise les noms de groupes Channels et les appels
``group_send`` utilisés par les vues HTTP et les consumers WebSocket.
"""

from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer


def conversation_group_name(conversation_id) -> str:
    """Construit un nom de groupe stable et compatible avec Channels."""
    return f"conversation.{str(conversation_id).replace('-', '')}"


def broadcast_conversation_event(*, conversation_id, event: dict) -> None:
    """
    Diffuse un événement à tous les WebSockets d'une conversation.

    Le champ interne ``type`` indique à Channels quelle méthode du
    consumer doit exécuter. Le champ public ``event`` est envoyé au client.
    """
    channel_layer = get_channel_layer()
    if channel_layer is None:
        return

    async_to_sync(channel_layer.group_send)(
        conversation_group_name(conversation_id),
        {
            "type": "conversation.event",
            "payload": event,
        },
    )

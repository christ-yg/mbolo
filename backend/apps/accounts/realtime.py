"""Diffusion temps réel privée au niveau d'un compte Mbolo."""

from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer


def account_group_name(user_id) -> str:
    """Retourne le groupe Channels privé d'un compte authentifié."""
    return f"account.{str(user_id).replace('-', '')}"


def broadcast_account_event(*, user_id, event: dict) -> None:
    """Diffuse un événement à toutes les sessions WebSocket d'un compte."""
    channel_layer = get_channel_layer()
    if channel_layer is None:
        return

    async_to_sync(channel_layer.group_send)(
        account_group_name(user_id),
        {
            "type": "account.event",
            "payload": event,
        },
    )

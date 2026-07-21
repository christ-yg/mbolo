"""Routes WebSocket de la messagerie privée Mbolo."""

from django.urls import re_path

from .consumers import ConversationConsumer


websocket_urlpatterns = [
    re_path(
        r"^ws/conversations/(?P<conversation_id>[0-9a-fA-F-]{36})/$",
        ConversationConsumer.as_asgi(),
    ),
]

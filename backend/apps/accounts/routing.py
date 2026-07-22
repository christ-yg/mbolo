"""Routes WebSocket globales du compte Mbolo."""

from django.urls import path

from .consumers import AccountConsumer

websocket_urlpatterns = [
    path("ws/account/", AccountConsumer.as_asgi()),
]

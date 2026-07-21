"""
Configuration ASGI de Mbolo.

Cette application accepte à la fois :

- les requêtes HTTP classiques de Django/DRF ;
- les connexions WebSocket authentifiées de la messagerie.
"""

import os

from channels.auth import AuthMiddlewareStack
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.security.websocket import AllowedHostsOriginValidator
from django.core.asgi import get_asgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

# Initialiser Django avant d'importer le routing métier.
django_asgi_application = get_asgi_application()

from apps.messaging.routing import websocket_urlpatterns  # noqa: E402

application = ProtocolTypeRouter(
    {
        "http": django_asgi_application,
        "websocket": AllowedHostsOriginValidator(
            AuthMiddlewareStack(
                URLRouter(websocket_urlpatterns)
            )
        ),
    }
)

"""Configuration ASGI HTTP et WebSocket de Mbolo."""

import os

from channels.auth import AuthMiddlewareStack
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.security.websocket import AllowedHostsOriginValidator
from django.core.asgi import get_asgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

django_asgi_application = get_asgi_application()

from apps.accounts.routing import websocket_urlpatterns as account_patterns  # noqa: E402
from apps.messaging.routing import websocket_urlpatterns as messaging_patterns  # noqa: E402

application = ProtocolTypeRouter(
    {
        "http": django_asgi_application,
        "websocket": AllowedHostsOriginValidator(
            AuthMiddlewareStack(
                URLRouter([*account_patterns, *messaging_patterns])
            )
        ),
    }
)

"""
Tests du canal WebSocket global du compte Mbolo.

Ces tests vérifient principalement deux règles de sécurité :

1. un utilisateur anonyme ne peut pas ouvrir le canal personnel ;
2. un utilisateur authentifié reçoit bien l'événement initial.

Le canal testé est :

    /ws/account/

L'identité n'est jamais fournie dans l'URL. Elle provient uniquement
de la session Django disponible dans scope["user"].
"""

from asgiref.sync import sync_to_async
from channels.routing import URLRouter
from channels.testing import WebsocketCommunicator
from django.contrib.auth.models import AnonymousUser
from django.test import TransactionTestCase, override_settings
from django.urls import path

from apps.accounts.consumers import AccountConsumer
from apps.accounts.models import User


@override_settings(
    CHANNEL_LAYERS={
        "default": {
            "BACKEND": "channels.layers.InMemoryChannelLayer",
        }
    }
)
class AccountConsumerTests(TransactionTestCase):
    """
    Tests d'intégration du consumer WebSocket personnel.
    """

    async def test_anonymous_connection_is_rejected(self):
        """
        Un visiteur non authentifié doit être refusé.

        Le code 4401 est utilisé comme équivalent WebSocket
        d'une erreur d'authentification HTTP 401.
        """

        communicator = WebsocketCommunicator(
            URLRouter(
                [
                    path(
                        "ws/account/",
                        AccountConsumer.as_asgi(),
                    ),
                ]
            ),
            "/ws/account/",
        )

        communicator.scope["user"] = AnonymousUser()

        connected, close_code = await communicator.connect()

        self.assertFalse(connected)
        self.assertEqual(close_code, 4401)

    async def test_authenticated_connection_is_accepted(self):
        """
        Un utilisateur authentifié doit pouvoir ouvrir son canal.

        Le manager User possède une méthode synchrone create_user().
        Comme le test est asynchrone, nous utilisons sync_to_async()
        afin d'exécuter proprement cette opération ORM.
        """

        user = await sync_to_async(
            User.objects.create_user,
            thread_sensitive=True,
        )(
            email="realtime@example.com",
            password="A-secure-password-2026!",
        )

        communicator = WebsocketCommunicator(
            URLRouter(
                [
                    path(
                        "ws/account/",
                        AccountConsumer.as_asgi(),
                    ),
                ]
            ),
            "/ws/account/",
        )

        communicator.scope["user"] = user

        connected, close_code = await communicator.connect()

        self.assertTrue(
            connected,
            msg=(
                "Le consumer devrait accepter "
                f"l'utilisateur authentifié. Code reçu : {close_code}"
            ),
        )

        payload = await communicator.receive_json_from()

        self.assertEqual(
            payload["event"],
            "account.connection.ready",
        )

        self.assertIn(
            "unread_count",
            payload,
        )

        await communicator.disconnect()

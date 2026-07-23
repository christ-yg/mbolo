"""
Consumer WebSocket sécurisé d'une conversation Mbolo.

La connexion est refusée si la session Django n'est pas authentifiée ou si
le compte ne participe pas à la conversation active demandée.
"""

from uuid import UUID

from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncJsonWebsocketConsumer
from django.core.exceptions import ValidationError

from apps.accounts.presence import touch_user_presence
from apps.subscriptions.services import get_subscription_state

from .realtime import conversation_group_name
from .services import (
    get_conversation_for_actor,
    mark_conversation_as_read,
)
from .typing import set_typing_status


class ConversationConsumer(AsyncJsonWebsocketConsumer):
    """Connexion temps réel d'un participant à une conversation privée."""

    conversation_id: UUID
    group_name: str

    async def connect(self) -> None:
        user = self.scope.get("user")

        if user is None or not user.is_authenticated:
            await self.close(code=4401)
            return

        raw_conversation_id = self.scope["url_route"]["kwargs"].get(
            "conversation_id"
        )

        try:
            self.conversation_id = UUID(str(raw_conversation_id))
            await self._authorize_conversation()
        except (TypeError, ValueError, ValidationError):
            await self.close(code=4403)
            return

        self.group_name = conversation_group_name(self.conversation_id)

        await self.channel_layer.group_add(
            self.group_name,
            self.channel_name,
        )
        await self.accept()
        await self._touch_presence()

        await self.send_json(
            {
                "event": "connection.ready",
                "conversation_id": str(self.conversation_id),
            }
        )

    async def disconnect(self, close_code: int) -> None:
        if hasattr(self, "group_name"):
            try:
                await self._set_typing(False)
            except ValidationError:
                pass

            await self.channel_layer.group_discard(
                self.group_name,
                self.channel_name,
            )

    async def receive_json(self, content: dict, **kwargs) -> None:
        event_name = content.get("event")

        if event_name == "ping":
            await self._touch_presence()
            await self.send_json({"event": "pong"})
            return

        if event_name == "typing.set":
            is_typing = content.get("is_typing")
            if not isinstance(is_typing, bool):
                await self._send_error("invalid_typing_state")
                return

            await self._set_typing(is_typing)
            await self.channel_layer.group_send(
                self.group_name,
                {
                    "type": "conversation.event",
                    "payload": {
                        "event": "typing.updated",
                        "actor_id": str(self.scope["user"].id),
                        "is_typing": is_typing,
                    },
                },
            )
            return

        if event_name == "conversation.read":
            try:
                result = await self._mark_read()
            except ValidationError:
                await self._send_error("conversation_unavailable")
                return

            await self.channel_layer.group_send(
                self.group_name,
                {
                    "type": "conversation.event",
                    "payload": {
                        "event": "conversation.read",
                        "reader_id": str(self.scope["user"].id),
                        "marked_count": result.marked_count,
                        "read_at": result.read_at.isoformat(),
                    },
                },
            )
            return

        await self._send_error("unsupported_event")

    async def conversation_event(self, event: dict) -> None:
        """Adapte un événement de groupe au point de vue du client courant."""
        payload = dict(event.get("payload") or {})
        current_user_id = str(self.scope["user"].id)

        actor_id = payload.pop("actor_id", None)
        sender_id = payload.pop("sender_id", None)
        reader_id = payload.pop("reader_id", None)

        if payload.get("event") == "typing.updated":
            if actor_id == current_user_id:
                return
            payload["other_is_typing"] = bool(payload.pop("is_typing", False))

        if payload.get("event") == "message.created":
            message = dict(payload.get("message") or {})
            message["is_mine"] = sender_id == current_user_id
            payload["message"] = message

        if payload.get("event") == "conversation.read":
            payload["read_by_other"] = reader_id != current_user_id

            # Un événement temps réel ne doit pas contourner le masquage
            # appliqué par le sérialiseur HTTP. Le lecteur conserve son
            # fonctionnement normal, mais seul un auteur Plus/Prestige
            # reçoit l'accusé de lecture de l'autre personne.
            if (
                payload["read_by_other"]
                and not await self._has_read_receipts()
            ):
                return

        await self.send_json(payload)

    async def _send_error(self, code: str) -> None:
        await self.send_json(
            {
                "event": "error",
                "code": code,
            }
        )

    @database_sync_to_async
    def _authorize_conversation(self):
        return get_conversation_for_actor(
            actor=self.scope["user"],
            conversation_id=self.conversation_id,
        )

    @database_sync_to_async
    def _touch_presence(self):
        return touch_user_presence(self.scope["user"])

    @database_sync_to_async
    def _has_read_receipts(self) -> bool:
        state = get_subscription_state(self.scope["user"])
        return bool(state["entitlements"]["read_receipts"])

    @database_sync_to_async
    def _set_typing(self, is_typing: bool):
        return set_typing_status(
            actor=self.scope["user"],
            conversation_id=self.conversation_id,
            is_typing=is_typing,
        )

    @database_sync_to_async
    def _mark_read(self):
        return mark_conversation_as_read(
            actor=self.scope["user"],
            conversation_id=self.conversation_id,
        )

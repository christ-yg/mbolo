"""Consumer WebSocket global et sécurisé du compte Mbolo."""

from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncJsonWebsocketConsumer

from apps.messaging.services import get_total_unread_count

from .presence import touch_user_presence
from .realtime import account_group_name


class AccountConsumer(AsyncJsonWebsocketConsumer):
    """Canal privé ouvert pendant toute la session authentifiée."""

    group_name: str

    async def connect(self) -> None:
        user = self.scope.get("user")

        if user is None or not user.is_authenticated:
            await self.close(code=4401)
            return

        if not user.is_active or user.is_suspended:
            await self.close(code=4403)
            return

        self.group_name = account_group_name(user.id)

        await self.channel_layer.group_add(
            self.group_name,
            self.channel_name,
        )
        await self.accept()
        await self._touch_presence()

        await self.send_json(
            {
                "event": "account.connection.ready",
                "unread_count": await self._get_unread_count(),
            }
        )

    async def disconnect(self, close_code: int) -> None:
        if hasattr(self, "group_name"):
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

        if event_name == "unread.refresh":
            await self.send_json(
                {
                    "event": "unread.count.changed",
                    "unread_count": await self._get_unread_count(),
                }
            )
            return

        await self.send_json(
            {
                "event": "error",
                "code": "unsupported_event",
            }
        )

    async def account_event(self, event: dict) -> None:
        payload = dict(event.get("payload") or {})
        await self.send_json(payload)

    @database_sync_to_async
    def _touch_presence(self):
        return touch_user_presence(self.scope["user"])

    @database_sync_to_async
    def _get_unread_count(self) -> int:
        try:
            return get_total_unread_count(actor=self.scope["user"])
        except Exception:
            return 0


"""
API du centre de notifications Mbolo.

Toutes les requêtes sont limitées au compte authentifié.
Un UUID valide appartenant à un autre compte retourne 404.
"""

from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts.realtime import broadcast_account_event

from .models import Notification
from .pagination import NotificationPagination
from .serializers import (
    MarkAllNotificationsReadSerializer,
    NotificationSerializer,
    NotificationUnreadCountSerializer,
)
from .services import (
    delete_notification,
    get_unread_notification_count,
    mark_all_notifications_as_read,
    mark_notification_as_read,
)


def broadcast_notification_count(actor) -> int:
    unread_count = get_unread_notification_count(actor=actor)

    broadcast_account_event(
        user_id=actor.id,
        event={
            "event": "notification.unread.changed",
            "notification_unread_count": unread_count,
        },
    )

    return unread_count


class NotificationListView(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request: Request) -> Response:
        queryset = (
            Notification.objects
            .filter(recipient=request.user)
            .order_by("-created_at", "-id")
        )

        paginator = NotificationPagination()
        page = paginator.paginate_queryset(
            queryset,
            request,
            view=self,
        )

        serializer = NotificationSerializer(
            page,
            many=True,
        )

        return paginator.get_paginated_response(serializer.data)


class NotificationUnreadCountView(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request: Request) -> Response:
        serializer = NotificationUnreadCountSerializer(
            {
                "unread_count": get_unread_notification_count(
                    actor=request.user,
                )
            }
        )
        return Response(serializer.data)


class NotificationMarkReadView(APIView):
    permission_classes = (IsAuthenticated,)

    def post(
        self,
        request: Request,
        notification_id,
    ) -> Response:
        notification = mark_notification_as_read(
            actor=request.user,
            notification_id=notification_id,
        )

        if notification is None:
            return Response(
                {"detail": "Notification introuvable."},
                status=status.HTTP_404_NOT_FOUND,
            )

        broadcast_notification_count(request.user)

        return Response(
            NotificationSerializer(notification).data,
            status=status.HTTP_200_OK,
        )


class NotificationMarkAllReadView(APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request: Request) -> Response:
        marked_count, read_at = mark_all_notifications_as_read(
            actor=request.user,
        )

        broadcast_notification_count(request.user)

        serializer = MarkAllNotificationsReadSerializer(
            {
                "marked_count": marked_count,
                "read_at": read_at,
            }
        )

        return Response(serializer.data)


class NotificationDeleteView(APIView):
    permission_classes = (IsAuthenticated,)

    def delete(
        self,
        request: Request,
        notification_id,
    ) -> Response:
        deleted = delete_notification(
            actor=request.user,
            notification_id=notification_id,
        )

        if not deleted:
            return Response(
                {"detail": "Notification introuvable."},
                status=status.HTTP_404_NOT_FOUND,
            )

        broadcast_notification_count(request.user)

        return Response(status=status.HTTP_204_NO_CONTENT)

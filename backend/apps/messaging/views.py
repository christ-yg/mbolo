"""
Vues API de la messagerie privée Mbolo.
"""

from django.core.exceptions import (
    ValidationError as DjangoValidationError,
)
from django.db.models import Q
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.core.security_logging import (
    log_security_event,
)

from .models import Conversation, Message
from .realtime import broadcast_conversation_event
from .pagination import (
    ConversationPagination,
    MessagePagination,
)
from .serializers import (
    ConversationCreateSerializer,
    ConversationSerializer,
    MarkConversationReadSerializer,
    MessageCreateSerializer,
    MessageSerializer,
    UnreadCountSerializer,
    OtherTypingStatusSerializer,
    TypingStatusInputSerializer,
    TypingStatusSerializer,
)
from .services import (
    get_conversation_for_actor,
    get_or_create_conversation,
    get_total_unread_count,
    mark_conversation_as_read,
    send_message,
)
from .typing import (
    get_other_typing_status,
    set_typing_status,
)


def validation_error_response(
    exc: DjangoValidationError,
) -> Response:
    """
    Convertit une ValidationError Django en réponse API 400.
    """

    if hasattr(exc, "message_dict"):
        detail = exc.message_dict
    else:
        detail = {
            "detail": exc.messages,
        }

    return Response(
        detail,
        status=status.HTTP_400_BAD_REQUEST,
    )


class ConversationListCreateView(APIView):
    """
    GET  /api/v1/conversations/
    POST /api/v1/conversations/
    """

    permission_classes = (
        IsAuthenticated,
    )

    def get(self, request: Request) -> Response:
        """
        Retourne uniquement les conversations du compte connecté.
        """

        try:
            profile = request.user.profile
        except AttributeError:
            queryset = Conversation.objects.none()
        else:
            queryset = (
                Conversation.objects
                .select_related(
                    "match",
                    "match__profile_one",
                    "match__profile_one__user",
                    "match__profile_two",
                    "match__profile_two__user",
                )
                .filter(
                    Q(match__profile_one=profile)
                    | Q(match__profile_two=profile),
                    match__is_active=True,
                )
                .order_by("-updated_at")
            )

        paginator = ConversationPagination()

        page = paginator.paginate_queryset(
            queryset,
            request,
            view=self,
        )

        serializer = ConversationSerializer(
            page,
            many=True,
            context={
                "request": request,
            },
        )

        return paginator.get_paginated_response(
            serializer.data
        )

    def post(self, request: Request) -> Response:
        """
        Crée ou retourne la conversation d'un match actif.
        """

        input_serializer = (
            ConversationCreateSerializer(
                data=request.data,
            )
        )

        input_serializer.is_valid(
            raise_exception=True,
        )

        try:
            result = get_or_create_conversation(
                actor=request.user,
                match_id=(
                    input_serializer.validated_data[
                        "match_id"
                    ]
                ),
            )
        except DjangoValidationError as exc:
            return validation_error_response(exc)

        log_security_event(
            request=request,
            event="conversation.open",
            outcome="success",
            reason=(
                "created"
                if result.created
                else "existing"
            ),
            user=request.user,
            email=request.user.email,
        )

        output_serializer = ConversationSerializer(
            result.conversation,
            context={
                "request": request,
            },
        )

        return Response(
            output_serializer.data,
            status=(
                status.HTTP_201_CREATED
                if result.created
                else status.HTTP_200_OK
            ),
        )


class ConversationMessageListCreateView(
    APIView
):
    """
    GET  /api/v1/conversations/<uuid>/messages/
    POST /api/v1/conversations/<uuid>/messages/
    """

    permission_classes = (
        IsAuthenticated,
    )

    def get(
        self,
        request: Request,
        conversation_id,
    ) -> Response:
        """
        Retourne les messages d'une conversation autorisée.
        """

        try:
            conversation = (
                get_conversation_for_actor(
                    actor=request.user,
                    conversation_id=conversation_id,
                )
            )
        except DjangoValidationError as exc:
            return validation_error_response(exc)

        queryset = (
            Message.objects
            .filter(
                conversation=conversation,
            )
            .select_related(
                "sender",
            )
            .order_by("created_at")
        )

        paginator = MessagePagination()

        page = paginator.paginate_queryset(
            queryset,
            request,
            view=self,
        )

        serializer = MessageSerializer(
            page,
            many=True,
            context={
                "request": request,
            },
        )

        return paginator.get_paginated_response(
            serializer.data
        )

    def post(
        self,
        request: Request,
        conversation_id,
    ) -> Response:
        """
        Envoie un message au nom du compte connecté.
        """

        input_serializer = (
            MessageCreateSerializer(
                data=request.data,
            )
        )

        input_serializer.is_valid(
            raise_exception=True,
        )

        try:
            message = send_message(
                actor=request.user,
                conversation_id=conversation_id,
                body=(
                    input_serializer.validated_data[
                        "body"
                    ]
                ),
            )
        except DjangoValidationError as exc:
            return validation_error_response(exc)

        log_security_event(
            request=request,
            event="message.send",
            outcome="success",
            reason="created",
            user=request.user,
            email=request.user.email,
        )

        output_serializer = MessageSerializer(
            message,
            context={
                "request": request,
            },
        )

        broadcast_conversation_event(
            conversation_id=message.conversation_id,
            event={
                "event": "message.created",
                "sender_id": str(request.user.id),
                "message": output_serializer.data,
            },
        )

        return Response(
            output_serializer.data,
            status=status.HTTP_201_CREATED,
        )


class ConversationMarkReadView(APIView):
    """
    POST /api/v1/conversations/<uuid>/read/

    Marque comme lus tous les messages reçus.
    """

    permission_classes = (
        IsAuthenticated,
    )

    def post(
        self,
        request: Request,
        conversation_id,
    ) -> Response:
        try:
            result = mark_conversation_as_read(
                actor=request.user,
                conversation_id=conversation_id,
            )
        except DjangoValidationError as exc:
            return validation_error_response(exc)

        log_security_event(
            request=request,
            event="conversation.read",
            outcome="success",
            reason=f"marked:{result.marked_count}",
            user=request.user,
            email=request.user.email,
        )

        serializer = MarkConversationReadSerializer(
            {
                "conversation_id": (
                    result.conversation.id
                ),
                "marked_count": result.marked_count,
                "read_at": result.read_at,
            }
        )

        broadcast_conversation_event(
            conversation_id=result.conversation.id,
            event={
                "event": "conversation.read",
                "reader_id": str(request.user.id),
                "marked_count": result.marked_count,
                "read_at": result.read_at.isoformat(),
            },
        )

        return Response(
            serializer.data,
            status=status.HTTP_200_OK,
        )


class UnreadMessageCountView(APIView):
    """
    GET /api/v1/messages/unread-count/

    Retourne le nombre total de messages reçus et non lus.
    """

    permission_classes = (
        IsAuthenticated,
    )

    def get(self, request: Request) -> Response:
        try:
            unread_count = get_total_unread_count(
                actor=request.user,
            )
        except DjangoValidationError as exc:
            return validation_error_response(exc)

        serializer = UnreadCountSerializer(
            {
                "unread_count": unread_count,
            }
        )

        return Response(
            serializer.data,
            status=status.HTTP_200_OK,
        )


class ConversationTypingView(APIView):
    """
    GET  /api/v1/conversations/<uuid>/typing/
    POST /api/v1/conversations/<uuid>/typing/
    """

    permission_classes = (IsAuthenticated,)

    def get(self, request: Request, conversation_id) -> Response:
        try:
            result = get_other_typing_status(
                actor=request.user,
                conversation_id=conversation_id,
            )
        except DjangoValidationError as exc:
            return validation_error_response(exc)

        serializer = OtherTypingStatusSerializer(result)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request: Request, conversation_id) -> Response:
        input_serializer = TypingStatusInputSerializer(data=request.data)
        input_serializer.is_valid(raise_exception=True)

        try:
            result = set_typing_status(
                actor=request.user,
                conversation_id=conversation_id,
                is_typing=input_serializer.validated_data["is_typing"],
            )
        except DjangoValidationError as exc:
            return validation_error_response(exc)

        serializer = TypingStatusSerializer(result)

        broadcast_conversation_event(
            conversation_id=result["conversation_id"],
            event={
                "event": "typing.updated",
                "actor_id": str(request.user.id),
                "is_typing": result["is_typing"],
            },
        )

        return Response(serializer.data, status=status.HTTP_200_OK)

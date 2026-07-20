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
from .pagination import (
    ConversationPagination,
    MessagePagination,
)
from .serializers import (
    ConversationCreateSerializer,
    ConversationSerializer,
    MessageCreateSerializer,
    MessageSerializer,
)
from .services import (
    get_conversation_for_actor,
    get_or_create_conversation,
    send_message,
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
    Liste et création des conversations.

    Endpoints :

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
    Liste et création des messages d'une conversation.

    Endpoints :

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

        return Response(
            output_serializer.data,
            status=status.HTTP_201_CREATED,
        )

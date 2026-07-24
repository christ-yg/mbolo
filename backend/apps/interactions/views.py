from django.core.exceptions import ValidationError as DjangoValidationError
from django.db.models import Q
from rest_framework import status
from rest_framework.generics import ListAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.core.security_logging import log_security_event
from apps.notifications.services import (
    broadcast_notification_created,
    create_like_notification,
    create_match_notification,
)

from .models import Match
from .pagination import MatchPagination
from .pagination_received_likes import ReceivedLikePagination
from .serializers import (
    InteractionCreateSerializer,
    InteractionResponseSerializer,
    RewindResponseSerializer,
    RewindStateSerializer,
    SuperLikeStateSerializer,
    MatchSerializer,
    UnmatchResponseSerializer,
    ReceivedLikeActionResultSerializer,
    ReceivedLikeResponseSerializer,
    ReceivedLikeSerializer,
)
from .services import (
    deactivate_match,
    get_pending_received_likes,
    record_interaction,
    get_rewind_state,
    rewind_last_pass,
    respond_to_received_like,
    get_super_like_state,
)


def publish_interaction_notifications(*, result) -> None:
    """
    Crée et diffuse les notifications liées à une interaction.

    Règles :

    - PASS : aucune notification ;
    - LIKE non réciproque : notification anonyme pour la cible ;
    - nouveau MATCH : notification nominative pour les deux comptes ;
    - interaction répétée sans changement : aucune duplication.
    """

    if (
        result.interaction.decision != "like"
        or not result.decision_changed
    ):
        return

    actor_user = result.interaction.actor
    actor_profile = actor_user.profile
    target_profile = result.interaction.target_profile
    target_user = target_profile.user

    if result.match_created and result.match is not None:
        actor_result = create_match_notification(
            recipient=actor_user,
            other_display_name=target_profile.display_name,
            match_id=result.match.id,
        )

        target_result = create_match_notification(
            recipient=target_user,
            other_display_name=actor_profile.display_name,
            match_id=result.match.id,
        )

        if actor_result.created:
            broadcast_notification_created(
                notification=actor_result.notification,
                event_name="match.notification",
                extra_payload={
                    "match_id": str(result.match.id),
                    "other_display_name": (
                        target_profile.display_name
                    ),
                },
            )

        if target_result.created:
            broadcast_notification_created(
                notification=target_result.notification,
                event_name="match.notification",
                extra_payload={
                    "match_id": str(result.match.id),
                    "other_display_name": (
                        actor_profile.display_name
                    ),
                },
            )

        return

    like_result = create_like_notification(
        recipient=target_user,
        interaction_id=result.interaction.id,
        is_super_like=result.interaction.is_super_like,
    )

    if like_result.created:
        broadcast_notification_created(
            notification=like_result.notification,
            event_name="like.notification",
        )


class InteractionCreateView(APIView):
    """
    Crée ou modifie une interaction vers un profil.

    Endpoint :

        POST /api/v1/interactions/

    Exemple de corps JSON :

        {
            "target_profile_id": "uuid-du-profil",
            "decision": "like"
        }
    """

    permission_classes = (
        IsAuthenticated,
    )

    def post(
        self,
        request: Request,
    ) -> Response:
        """
        Valide la requête puis appelle le service transactionnel.
        """

        serializer = InteractionCreateSerializer(
            data=request.data,
        )

        serializer.is_valid(
            raise_exception=True,
        )

        try:
            result = record_interaction(
                actor=request.user,
                target_profile_id=(
                    serializer.validated_data[
                        "target_profile_id"
                    ]
                ),
                decision=(
                    serializer.validated_data[
                        "decision"
                    ]
                ),
                is_super_like=serializer.validated_data["is_super_like"],
            )
        except DjangoValidationError as exc:
            # Le service utilise les ValidationError Django,
            # car il est indépendant de Django REST Framework.
            #
            # Nous convertissons ici l'erreur en réponse API 400.
            if hasattr(exc, "message_dict"):
                detail = exc.message_dict
            else:
                detail = {
                    "detail": exc.messages
                }

            return Response(
                detail,
                status=status.HTTP_400_BAD_REQUEST,
            )

        log_security_event(
            request=request,
            event="interaction.record",
            outcome="success",
            reason=result.interaction.decision,
            user=request.user,
            email=request.user.email,
        )

        publish_interaction_notifications(
            result=result,
        )

        if result.match_created:
            log_security_event(
                request=request,
                event="match.create",
                outcome="success",
                reason="mutual_like",
                user=request.user,
                email=request.user.email,
            )

        response_serializer = (
            InteractionResponseSerializer(
                {
                    "interaction_id": (
                        result.interaction.id
                    ),
                    "decision": (
                        result.interaction.decision
                    ),
                    "is_super_like": result.interaction.is_super_like,
                    "interaction_created": (
                        result.interaction_created
                    ),
                    "matched": (
                        result.match is not None
                    ),
                    "match_created": (
                        result.match_created
                    ),
                    "match_id": (
                        result.match.id
                        if result.match is not None
                        else None
                    ),
                }
            )
        )

        response_status = (
            status.HTTP_201_CREATED
            if result.interaction_created
            else status.HTTP_200_OK
        )

        return Response(
            response_serializer.data,
            status=response_status,
        )


class SuperLikeStateView(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request: Request) -> Response:
        return Response(
            SuperLikeStateSerializer(
                get_super_like_state(actor=request.user)
            ).data
        )


class InteractionRewindView(APIView):
    """
    Consulte ou exécute le retour sur le dernier PASS.

    Aucun UUID n'est accepté : le serveur choisit lui-même la seule
    interaction pouvant être annulée, ce qui évite les attaques IDOR.
    """

    permission_classes = (IsAuthenticated,)

    def get(self, request: Request) -> Response:
        serializer = RewindStateSerializer(
            get_rewind_state(actor=request.user)
        )
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request: Request) -> Response:
        try:
            profile = rewind_last_pass(actor=request.user)
        except PermissionError as exc:
            log_security_event(
                request=request,
                event="interaction.rewind",
                outcome="failure",
                reason="premium_required",
                user=request.user,
                email=request.user.email,
            )
            return Response(
                {"detail": str(exc)},
                status=status.HTTP_403_FORBIDDEN,
            )
        except DjangoValidationError as exc:
            detail = (
                exc.message_dict
                if hasattr(exc, "message_dict")
                else {"detail": exc.messages}
            )
            return Response(detail, status=status.HTTP_400_BAD_REQUEST)

        log_security_event(
            request=request,
            event="interaction.rewind",
            outcome="success",
            reason="last_pass_restored",
            user=request.user,
            email=request.user.email,
        )

        serializer = RewindResponseSerializer(
            {"rewound": True, "profile": profile},
            context={"request": request},
        )
        return Response(serializer.data, status=status.HTTP_200_OK)


class MatchListView(ListAPIView):
    """
    Retourne uniquement les matchs de l'utilisateur connecté.

    Endpoint :

        GET /api/v1/matches/

    Aucun identifiant utilisateur n'est accepté en paramètre.
    Le filtrage repose exclusivement sur request.user.
    """

    serializer_class = MatchSerializer

    permission_classes = (
        IsAuthenticated,
    )

    pagination_class = MatchPagination

    def get_queryset(self):
        """
        Retourne les matchs actifs contenant le profil courant.

        select_related récupère les profils et leurs comptes
        associés dans une requête SQL optimisée.
        """

        try:
            current_profile = self.request.user.profile
        except AttributeError:
            return Match.objects.none()

        return (
            Match.objects
            .select_related(
                "profile_one",
                "profile_one__user",
                "profile_two",
                "profile_two__user",
            )
            .filter(
                Q(profile_one=current_profile)
                | Q(profile_two=current_profile),
                is_active=True,
            )
            .order_by(
                "-created_at",
                "id",
            )
        )

    def list(
        self,
        request,
        *args,
        **kwargs,
    ):
        """
        Journalise la consultation sans enregistrer
        la liste des participants.
        """

        log_security_event(
            request=request,
            event="match.list",
            outcome="success",
            reason="matches_requested",
            user=request.user,
            email=request.user.email,
        )

        return super().list(
            request,
            *args,
            **kwargs,
        )



class ReceivedLikeListView(ListAPIView):
    """
    Liste masquée des likes reçus en attente de réponse.

    Endpoint :

        GET /api/v1/likes-received/

    L’identité de l’auteur n’est jamais exposée dans la version
    gratuite.
    """

    permission_classes = (
        IsAuthenticated,
    )

    serializer_class = ReceivedLikeSerializer
    pagination_class = ReceivedLikePagination

    def get_queryset(self):
        try:
            return get_pending_received_likes(
                actor=self.request.user,
            )
        except DjangoValidationError:
            return Match.objects.none()

    def list(
        self,
        request,
        *args,
        **kwargs,
    ):
        log_security_event(
            request=request,
            event="received_like.list",
            outcome="success",
            reason="likes_requested_entitlement_applied",
            user=request.user,
            email=request.user.email,
        )

        return super().list(
            request,
            *args,
            **kwargs,
        )


class ReceivedLikeRespondView(APIView):
    """
    Accepte ou refuse un like reçu sans révéler son auteur avant match.

    Endpoint :

        POST /api/v1/likes-received/<uuid>/respond/
    """

    permission_classes = (
        IsAuthenticated,
    )

    def post(
        self,
        request: Request,
        interaction_id,
    ) -> Response:
        serializer = ReceivedLikeResponseSerializer(
            data=request.data,
        )
        serializer.is_valid(
            raise_exception=True,
        )

        try:
            result = respond_to_received_like(
                actor=request.user,
                received_interaction_id=interaction_id,
                decision=(
                    serializer.validated_data["decision"]
                ),
            )
        except DjangoValidationError as exc:
            detail = (
                exc.message_dict
                if hasattr(exc, "message_dict")
                else {"detail": exc.messages}
            )

            return Response(
                detail,
                status=status.HTTP_400_BAD_REQUEST,
            )

        publish_interaction_notifications(
            result=result,
        )

        revealed_profile = None

        if result.match is not None:
            revealed_profile = (
                result.interaction.target_profile
            )

        response_serializer = (
            ReceivedLikeActionResultSerializer(
                {
                    "decision": (
                        result.interaction.decision
                    ),
                    "matched": (
                        result.match is not None
                    ),
                    "match_created": (
                        result.match_created
                    ),
                    "match_id": (
                        result.match.id
                        if result.match is not None
                        else None
                    ),
                    "revealed_profile": (
                        revealed_profile
                    ),
                },
                context={
                    "request": request,
                },
            )
        )

        log_security_event(
            request=request,
            event="received_like.respond",
            outcome="success",
            reason=result.interaction.decision,
            user=request.user,
            email=request.user.email,
        )

        return Response(
            response_serializer.data,
            status=status.HTTP_200_OK,
        )



class MatchDeactivateView(APIView):
    """
    Supprime logiquement un match.

    Endpoint :

        DELETE /api/v1/matches/<uuid:match_id>/

    L'historique de conversation reste conservé en base mais devient
    inaccessible dès que le match est inactif.
    """

    permission_classes = (
        IsAuthenticated,
    )

    def delete(
        self,
        request: Request,
        match_id,
    ) -> Response:
        try:
            result = deactivate_match(
                actor=request.user,
                match_id=match_id,
            )
        except DjangoValidationError as exc:
            detail = (
                exc.message_dict
                if hasattr(exc, "message_dict")
                else {"detail": exc.messages}
            )

            return Response(
                detail,
                status=status.HTTP_400_BAD_REQUEST,
            )

        log_security_event(
            request=request,
            event="match.deactivate",
            outcome="success",
            reason="user_requested_unmatch",
            user=request.user,
            email=request.user.email,
        )

        serializer = UnmatchResponseSerializer(
            {
                "match_id": result.match.id,
                "conversation_id": (
                    result.conversation_id
                ),
                "deactivated": result.deactivated,
                "message": (
                    "Le match a été supprimé. "
                    "La conversation est maintenant fermée."
                ),
            }
        )

        return Response(
            serializer.data,
            status=status.HTTP_200_OK,
        )

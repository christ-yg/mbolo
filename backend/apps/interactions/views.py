from django.core.exceptions import ValidationError as DjangoValidationError
from django.db.models import Q
from rest_framework import status
from rest_framework.generics import ListAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.core.security_logging import log_security_event

from .models import Match
from .pagination import MatchPagination
from .serializers import (
    InteractionCreateSerializer,
    InteractionResponseSerializer,
    MatchSerializer,
)
from .services import record_interaction


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

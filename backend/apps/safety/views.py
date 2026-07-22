"""
Vues API du module Safety.

Endpoints :

    POST   /api/v1/safety/blocks/
    GET    /api/v1/safety/blocks/
    DELETE /api/v1/safety/blocks/<uuid>/

Toutes les routes exigent une session authentifiée.
Les requêtes POST et DELETE utilisant une session Django restent
protégées par le mécanisme CSRF.
"""

from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import status
from rest_framework.generics import ListAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.core.security_logging import log_security_event

from .models import Block
from .pagination import BlockPagination
from .serializers import (
    BlockCreateResponseSerializer,
    BlockCreateSerializer,
    BlockSerializer,
    ProfileBlockCreateSerializer,
    ProfileReportCreateSerializer,
    ProfileSafetyActionResponseSerializer,
)
from .services import (
    create_block,
    create_profile_block,
    create_profile_report,
    delete_block,
)


def validation_error_response(
    exception: DjangoValidationError,
) -> Response:
    """
    Convertit une ValidationError Django en réponse HTTP 400.

    Le service métier reste ainsi indépendant de Django REST Framework.
    """

    if hasattr(exception, "message_dict"):
        detail = exception.message_dict
    else:
        detail = {
            "detail": exception.messages,
        }

    return Response(
        detail,
        status=status.HTTP_400_BAD_REQUEST,
    )


class BlockListCreateView(ListAPIView):
    """
    Liste les blocages créés par l'utilisateur connecté.

    La méthode POST est ajoutée manuellement afin de conserver
    l'utilisation de notre service transactionnel.
    """

    serializer_class = BlockSerializer

    permission_classes = (
        IsAuthenticated,
    )

    pagination_class = BlockPagination

    def get_queryset(self):
        """
        Retourne uniquement les blocages appartenant à request.user.

        Cette règle empêche un utilisateur de consulter les blocages
        créés par une autre personne.
        """

        return (
            Block.objects
            .select_related(
                "blocked_user",
            )
            .filter(
                blocker=self.request.user,
            )
            .order_by(
                "-created_at",
                "id",
            )
        )

    def post(
        self,
        request: Request,
        *args,
        **kwargs,
    ) -> Response:
        """
        Crée un blocage ou retourne le blocage existant.
        """

        input_serializer = BlockCreateSerializer(
            data=request.data,
        )

        input_serializer.is_valid(
            raise_exception=True,
        )

        try:
            result = create_block(
                blocker=request.user,
                blocked_user_id=(
                    input_serializer.validated_data[
                        "blocked_user_id"
                    ]
                ),
            )
        except DjangoValidationError as exc:
            return validation_error_response(
                exc
            )

        log_security_event(
            request=request,
            event="safety.block.create",
            outcome="success",
            reason=(
                "block_created"
                if result.created
                else "block_already_exists"
            ),
            user=request.user,
            email=request.user.email,
        )

        output_serializer = BlockCreateResponseSerializer(
            {
                "id": result.block.id,
                "created": result.created,
                "deactivated_matches": (
                    result.deactivated_matches
                ),
                "message": (
                    "Utilisateur bloqué."
                    if result.created
                    else "Cet utilisateur est déjà bloqué."
                ),
            }
        )

        response_status = (
            status.HTTP_201_CREATED
            if result.created
            else status.HTTP_200_OK
        )

        return Response(
            output_serializer.data,
            status=response_status,
        )


class BlockDeleteView(APIView):
    """
    Supprime uniquement un blocage créé par l'utilisateur connecté.

    L'UUID seul ne suffit pas : le service vérifie aussi blocker=request.user.
    Cette double vérification protège contre les IDOR.
    """

    permission_classes = (
        IsAuthenticated,
    )

    def delete(
        self,
        request: Request,
        block_id,
    ) -> Response:
        """
        Supprime le blocage et retourne HTTP 204.
        """

        try:
            delete_block(
                blocker=request.user,
                block_id=block_id,
            )
        except DjangoValidationError as exc:
            return validation_error_response(
                exc
            )

        log_security_event(
            request=request,
            event="safety.block.delete",
            outcome="success",
            reason="block_deleted",
            user=request.user,
            email=request.user.email,
        )

        return Response(
            status=status.HTTP_204_NO_CONTENT,
        )



class ProfileBlockCreateView(APIView):
    """
    Bloque un profil depuis sa page détaillée.

    Endpoint :
        POST /api/v1/safety/profiles/<uuid>/block/
    """

    permission_classes = (
        IsAuthenticated,
    )

    def post(
        self,
        request: Request,
        profile_id,
    ) -> Response:
        input_serializer = ProfileBlockCreateSerializer(
            data=request.data,
        )
        input_serializer.is_valid(
            raise_exception=True,
        )

        try:
            result = create_profile_block(
                blocker=request.user,
                profile_id=profile_id,
            )
        except DjangoValidationError as exc:
            return validation_error_response(exc)

        log_security_event(
            request=request,
            event="safety.profile.block",
            outcome="success",
            reason=(
                "block_created"
                if result.created
                else "block_already_exists"
            ),
            user=request.user,
            email=request.user.email,
        )

        output_serializer = (
            ProfileSafetyActionResponseSerializer(
                {
                    "created": result.created,
                    "deactivated_matches": (
                        result.deactivated_matches
                    ),
                    "message": (
                        "Ce profil a été bloqué."
                        if result.created
                        else "Ce profil est déjà bloqué."
                    ),
                }
            )
        )

        return Response(
            output_serializer.data,
            status=(
                status.HTTP_201_CREATED
                if result.created
                else status.HTTP_200_OK
            ),
        )


class ProfileReportCreateView(APIView):
    """
    Signale un profil depuis sa page détaillée.

    Endpoint :
        POST /api/v1/safety/profiles/<uuid>/report/
    """

    permission_classes = (
        IsAuthenticated,
    )

    def post(
        self,
        request: Request,
        profile_id,
    ) -> Response:
        input_serializer = ProfileReportCreateSerializer(
            data=request.data,
        )
        input_serializer.is_valid(
            raise_exception=True,
        )

        try:
            result = create_profile_report(
                reporter=request.user,
                profile_id=profile_id,
                reason=(
                    input_serializer.validated_data["reason"]
                ),
                description=(
                    input_serializer.validated_data[
                        "description"
                    ]
                ),
            )
        except DjangoValidationError as exc:
            return validation_error_response(exc)

        log_security_event(
            request=request,
            event="safety.profile.report",
            outcome="success",
            reason=(
                "report_created"
                if result.created
                else "active_report_already_exists"
            ),
            user=request.user,
            email=request.user.email,
        )

        output_serializer = (
            ProfileSafetyActionResponseSerializer(
                {
                    "created": result.created,
                    "message": (
                        "Le signalement a été transmis à la modération."
                        if result.created
                        else (
                            "Un signalement actif existe déjà "
                            "pour ce motif."
                        )
                    ),
                }
            )
        )

        return Response(
            output_serializer.data,
            status=(
                status.HTTP_201_CREATED
                if result.created
                else status.HTTP_200_OK
            ),
        )

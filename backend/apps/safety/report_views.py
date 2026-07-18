"""
Vues publiques des signalements utilisateurs.

Endpoints :

    GET  /api/v1/safety/reports/
    POST /api/v1/safety/reports/

Règles :

- authentification obligatoire ;
- CSRF obligatoire pour POST avec SessionAuthentication ;
- limitation anti-spam ;
- isolation stricte des données ;
- aucune information interne de modération exposée.
"""

from django.core.exceptions import (
    ValidationError as DjangoValidationError,
)
from rest_framework import status
from rest_framework.generics import ListAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response

from apps.core.security_logging import (
    log_security_event,
)

from .models import Report
from .pagination import BlockPagination
from .report_serializers import (
    ReportCreateSerializer,
    ReportListSerializer,
)
from .report_services import create_report
from .report_throttles import ReportCreateThrottle


def report_validation_error_response(
    exception: DjangoValidationError,
) -> Response:
    """
    Transforme une ValidationError Django en réponse API HTTP 400.
    """

    if hasattr(exception, "message_dict"):
        response_data = exception.message_dict
    else:
        response_data = {
            "detail": exception.messages,
        }

    return Response(
        response_data,
        status=status.HTTP_400_BAD_REQUEST,
    )


class ReportListCreateView(ListAPIView):
    """
    Liste et crée les signalements de l'utilisateur connecté.

    Un utilisateur ne peut consulter que les signalements
    qu'il a lui-même déposés.
    """

    permission_classes = (
        IsAuthenticated,
    )

    serializer_class = ReportListSerializer

    # La pagination existante peut être réutilisée :
    #
    # 20 éléments par défaut ;
    # 50 éléments maximum.
    pagination_class = BlockPagination

    def get_queryset(self):
        """
        Retourne uniquement les signalements appartenant au déclarant.

        Cette condition empêche une exposition horizontale
        des signalements d'un autre utilisateur.
        """

        return (
            Report.objects
            .select_related(
                "reported_user",
            )
            .filter(
                reporter=self.request.user,
            )
            .order_by(
                "-created_at",
                "id",
            )
        )

    def get_throttles(self):
        """
        Applique la limitation uniquement aux créations POST.

        La consultation GET de ses propres signalements
        n'incrémente pas le compteur anti-spam.
        """

        if self.request.method == "POST":
            return [
                ReportCreateThrottle()
            ]

        return []

    def post(
        self,
        request: Request,
        *args,
        **kwargs,
    ) -> Response:
        """
        Valide puis crée un signalement.
        """

        input_serializer = ReportCreateSerializer(
            data=request.data,
        )

        input_serializer.is_valid(
            raise_exception=True,
        )

        validated_data = (
            input_serializer.validated_data
        )

        try:
            result = create_report(
                reporter=request.user,
                reported_user_id=(
                    validated_data[
                        "reported_user_id"
                    ]
                ),
                reason=validated_data["reason"],
                description=validated_data.get(
                    "description",
                    "",
                ),
            )
        except DjangoValidationError as exc:
            log_security_event(
                request=request,
                event="safety.report.create",
                outcome="failure",
                reason="report_rejected",
                user=request.user,
                email=request.user.email,
            )

            return report_validation_error_response(
                exc
            )

        # La description n'est volontairement pas écrite
        # dans le journal de sécurité.
        #
        # Elle peut contenir des informations sensibles,
        # des accusations ou des données personnelles.
        log_security_event(
            request=request,
            event="safety.report.create",
            outcome="success",
            reason="report_created",
            user=request.user,
            email=request.user.email,
        )

        output_serializer = ReportListSerializer(
            result.report,
            context={
                "request": request,
            },
        )

        return Response(
            {
                "data": output_serializer.data,
                "message": (
                    "Signalement enregistré. "
                    "Il sera examiné par la modération."
                ),
            },
            status=status.HTTP_201_CREATED,
        )

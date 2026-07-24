"""API publique et strictement limitée de contestation d'une sanction."""

from django.contrib.auth import authenticate
from django.db import IntegrityError, models, transaction
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_protect
from rest_framework import serializers, status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.throttling import AnonRateThrottle
from rest_framework.views import APIView

from apps.accounts.models import User
from apps.core.security_logging import log_security_event

from .models import (
    ModerationSanction,
    ModerationSanctionType,
    SanctionAppeal,
)


class SanctionAppealThrottle(AnonRateThrottle):
    """Trois soumissions maximales par jour et par adresse IP."""

    rate = "3/day"


class SanctionAppealSerializer(serializers.Serializer):
    """Valide les identifiants sans créer de session Django."""

    email = serializers.EmailField(max_length=254, write_only=True)
    password = serializers.CharField(
        max_length=128,
        trim_whitespace=False,
        write_only=True,
    )
    message = serializers.CharField(
        min_length=30,
        max_length=2000,
        trim_whitespace=True,
    )

    def validate(self, attrs):
        email = User.objects.normalize_email(attrs["email"]).strip().lower()
        user = authenticate(
            request=self.context["request"],
            email=email,
            password=attrs["password"],
        )
        if user is None or not user.is_active:
            raise serializers.ValidationError(
                {"detail": "Les informations fournies ne permettent pas cette demande."}
            )

        now = timezone.now()
        sanction = (
            ModerationSanction.objects.filter(
                user=user,
                sanction_type__in=(
                    ModerationSanctionType.SUSPENSION_7_DAYS,
                    ModerationSanctionType.SUSPENSION_30_DAYS,
                    ModerationSanctionType.PERMANENT_SUSPENSION,
                ),
            )
            .filter(
                models.Q(expires_at__isnull=True) |
                models.Q(expires_at__gt=now)
            )
            .order_by("-created_at")
            .first()
        )
        if sanction is None or not user.is_suspended:
            raise serializers.ValidationError(
                {"detail": "Aucune sanction contestable n’a été trouvée."}
            )
        if SanctionAppeal.objects.filter(sanction=sanction).exists():
            raise serializers.ValidationError(
                {"detail": "Une contestation existe déjà pour cette sanction."}
            )

        attrs["email"] = email
        attrs["user"] = user
        attrs["sanction"] = sanction
        return attrs

    def create(self, validated_data):
        try:
            with transaction.atomic():
                return SanctionAppeal.objects.create(
                    sanction=validated_data["sanction"],
                    user=validated_data["user"],
                    message=validated_data["message"],
                )
        except IntegrityError as exc:
            raise serializers.ValidationError(
                {"detail": "Une contestation existe déjà pour cette sanction."}
            ) from exc


@method_decorator(csrf_protect, name="dispatch")
class SanctionAppealCreateView(APIView):
    authentication_classes = ()
    permission_classes = (AllowAny,)
    throttle_classes = (SanctionAppealThrottle,)

    def post(self, request):
        serializer = SanctionAppealSerializer(
            data=request.data,
            context={"request": request},
        )
        serializer.is_valid(raise_exception=True)
        appeal = serializer.save()
        log_security_event(
            request=request,
            event="moderation.appeal.create",
            outcome="success",
            reason="appeal_created",
            user=appeal.user,
            email=appeal.user.email,
        )
        return Response(
            {
                "data": {"id": str(appeal.id), "status": appeal.status},
                "message": "Ta contestation a été transmise à la modération.",
            },
            status=status.HTTP_201_CREATED,
        )

"""
API de l'historique de sécurité visible par le membre.
"""

from rest_framework import serializers
from rest_framework.generics import ListAPIView
from rest_framework.permissions import IsAuthenticated

from .models import AccountSecurityEvent


class AccountSecurityEventSerializer(serializers.ModelSerializer):
    createdAt = serializers.DateTimeField(
        source="created_at",
        read_only=True,
    )

    class Meta:
        model = AccountSecurityEvent
        fields = (
            "id",
            "event",
            "outcome",
            "reason",
            "createdAt",
        )
        read_only_fields = fields


class AccountSecurityEventListView(ListAPIView):
    """
    Retourne uniquement les événements du membre authentifié.

    La limite de 100 correspond aussi à la rétention appliquée lors de
    l'enregistrement.
    """

    permission_classes = (IsAuthenticated,)
    serializer_class = AccountSecurityEventSerializer
    pagination_class = None

    def get_queryset(self):
        return AccountSecurityEvent.objects.filter(
            user=self.request.user,
        )[:100]

from django.db import transaction
from rest_framework.generics import RetrieveUpdateAPIView
from rest_framework.permissions import IsAuthenticated

from apps.core.security_logging import log_security_event

from .models import (
    Profile,
    SearchPreferences,
)
from .serializers import (
    ProfileSerializer,
    SearchPreferencesSerializer,
)


class CurrentProfileView(RetrieveUpdateAPIView):
    """
    Consulte ou modifie uniquement le profil connecté.

    L'absence d'UUID dans l'URL réduit le risque d'IDOR.
    """

    serializer_class = ProfileSerializer

    permission_classes = (
        IsAuthenticated,
    )

    @transaction.atomic
    def get_object(self) -> Profile:
        profile, _created = (
            Profile.objects.select_for_update()
            .get_or_create(
                user=self.request.user,
            )
        )

        return profile

    def perform_update(
        self,
        serializer: ProfileSerializer,
    ) -> None:
        profile = serializer.save()

        log_security_event(
            request=self.request,
            event="profile.update",
            outcome="success",
            reason="profile_updated",
            user=self.request.user,
            email=self.request.user.email,
        )

        serializer.instance = profile


class CurrentSearchPreferencesView(
    RetrieveUpdateAPIView
):
    """
    Consulte ou modifie uniquement les préférences
    de recherche de l'utilisateur connecté.

    Ces préférences restent privées et ne sont jamais
    exposées sur le profil public.
    """

    serializer_class = SearchPreferencesSerializer

    permission_classes = (
        IsAuthenticated,
    )

    @transaction.atomic
    def get_object(
        self,
    ) -> SearchPreferences:
        """
        Crée automatiquement les préférences par défaut
        lors du premier accès.
        """

        preferences, _created = (
            SearchPreferences.objects.select_for_update()
            .get_or_create(
                user=self.request.user,
            )
        )

        return preferences

    def perform_update(
        self,
        serializer: SearchPreferencesSerializer,
    ) -> None:
        """
        Sauvegarde et journalise la modification
        sans enregistrer les valeurs privées.
        """

        preferences = serializer.save()

        log_security_event(
            request=self.request,
            event="profile.preferences_update",
            outcome="success",
            reason="preferences_updated",
            user=self.request.user,
            email=self.request.user.email,
        )

        serializer.instance = preferences

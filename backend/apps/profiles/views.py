from django.db import transaction
from rest_framework.generics import RetrieveUpdateAPIView
from rest_framework.permissions import IsAuthenticated

from apps.core.security_logging import log_security_event

from .models import Profile
from .serializers import ProfileSerializer


class CurrentProfileView(RetrieveUpdateAPIView):
    """
    Consulte ou modifie uniquement le profil de l'utilisateur connecté.

    Aucun identifiant de profil n'est accepté dans l'URL.
    Cette conception réduit les risques d'IDOR :
    l'utilisateur ne peut pas demander le profil d'une autre personne
    en modifiant simplement un UUID.
    """

    serializer_class = ProfileSerializer
    permission_classes = (
        IsAuthenticated,
    )

    @transaction.atomic
    def get_object(self) -> Profile:
        """
        Récupère ou crée automatiquement le profil personnel.
        """

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
        """
        Sauvegarde le profil et journalise la modification.
        """

        profile = serializer.save()

        log_security_event(
            request=self.request,
            event="profile.update",
            outcome="success",
            reason="profile_updated",
            user=self.request.user,
            email=self.request.user.email,
        )

        # Le profil reste disponible via serializer.instance.
        serializer.instance = profile

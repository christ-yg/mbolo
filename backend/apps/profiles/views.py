from django.db import transaction
from django.db.models import Q
from django.core.exceptions import ValidationError as DjangoValidationError
from django.http import Http404
from django.utils import timezone
from rest_framework.generics import (
    ListAPIView,
    RetrieveAPIView,
    RetrieveUpdateAPIView,
)
from rest_framework.permissions import IsAuthenticated
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.response import Response
from rest_framework import status
from rest_framework.views import APIView

from apps.core.security_logging import log_security_event
from apps.interactions.models import Match
from apps.photos.image_processing import process_profile_photo
from apps.safety.services import users_are_blocked
from apps.subscriptions.services import get_subscription_state

from .discovery import build_discovery_queryset
from .models import (
    Profile,
    ProfileVerification,
    SearchPreferences,
)
from .pagination import DiscoveryPagination
from .serializers import (
    DiscoveryProfileSerializer,
    PublicProfileDetailSerializer,
    ProfileSerializer,
    ProfileVerificationSerializer,
    SearchPreferencesSerializer,
)


class CurrentProfileView(RetrieveUpdateAPIView):
    """
    Consulte ou modifie uniquement le profil
    de l'utilisateur connecté.

    L'URL ne contient aucun UUID modifiable :

        /api/v1/profiles/me/

    Cette architecture réduit fortement le risque d'IDOR.
    """

    serializer_class = ProfileSerializer

    permission_classes = (
        IsAuthenticated,
    )

    @transaction.atomic
    def get_object(self) -> Profile:
        """
        Récupère ou crée automatiquement le profil personnel.

        select_for_update() verrouille temporairement la ligne
        pendant la transaction lorsqu'elle existe.

        Cela évite certaines conditions de concurrence lorsque
        deux requêtes tentent de modifier le même profil.
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
        Sauvegarde et journalise la modification du profil.
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

        serializer.instance = profile


class CurrentProfileVerificationView(APIView):
    """
    Consulte ou soumet la vérification du profil connecté.

    GET ne retourne que le statut. POST accepte un selfie récent, le traite
    avec la même chaîne de sécurité que les photos publiques, puis le range
    dans un stockage privé. Le client ne choisit jamais le profil concerné.
    """

    permission_classes = (IsAuthenticated,)
    parser_classes = (MultiPartParser, FormParser)

    @staticmethod
    def _get_profile(request) -> Profile:
        profile, _created = Profile.objects.get_or_create(
            user=request.user,
        )
        return profile

    @staticmethod
    def _get_verification(profile) -> ProfileVerification:
        verification, _created = (
            ProfileVerification.objects.get_or_create(
                profile=profile,
            )
        )
        return verification

    def get(self, request):
        profile = self._get_profile(request)
        verification = self._get_verification(profile)
        return Response(
            ProfileVerificationSerializer(verification).data,
        )

    @transaction.atomic
    def post(self, request):
        profile = (
            Profile.objects.select_for_update()
            .filter(user=request.user)
            .first()
        )

        if profile is None or not profile.is_complete:
            return Response(
                {
                    "detail": (
                        "Complète d'abord les informations obligatoires "
                        "de ton profil."
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        if not request.user.is_email_verified:
            return Response(
                {
                    "detail": (
                        "Vérifie d'abord ton adresse e-mail."
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        if not profile.photos.filter(is_primary=True).exists():
            return Response(
                {
                    "detail": (
                        "Ajoute d'abord une photo principale publique."
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        verification, _created = (
            ProfileVerification.objects.select_for_update()
            .get_or_create(profile=profile)
        )

        if verification.status == ProfileVerification.Status.PENDING:
            return Response(
                {"detail": "Ta demande est déjà en cours d'examen."},
                status=status.HTTP_409_CONFLICT,
            )

        if verification.status == ProfileVerification.Status.APPROVED:
            return Response(
                {"detail": "Ton profil est déjà vérifié."},
                status=status.HTTP_409_CONFLICT,
            )

        uploaded_selfie = request.FILES.get("selfie")
        if uploaded_selfie is None:
            return Response(
                {"selfie": ["Ajoute un selfie récent et net."]},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            processed = process_profile_photo(uploaded_selfie)
        except DjangoValidationError as exc:
            detail = (
                exc.message_dict
                if hasattr(exc, "message_dict")
                else {"selfie": list(exc.messages)}
            )
            if "image" in detail:
                detail["selfie"] = detail.pop("image")
            return Response(
                detail,
                status=status.HTTP_400_BAD_REQUEST,
            )

        old_selfie_name = (
            verification.selfie.name
            if verification.selfie
            else ""
        )

        verification.selfie.save(
            processed.filename,
            processed.content,
            save=False,
        )
        verification.status = ProfileVerification.Status.PENDING
        verification.rejection_reason = ""
        verification.submitted_at = timezone.now()
        verification.reviewed_at = None
        verification.save()

        if (
            old_selfie_name
            and old_selfie_name != verification.selfie.name
        ):
            verification.selfie.storage.delete(old_selfie_name)

        log_security_event(
            request=request,
            event="profile.verification_submit",
            outcome="success",
            reason="verification_pending",
            user=request.user,
            email=request.user.email,
        )

        return Response(
            ProfileVerificationSerializer(verification).data,
            status=status.HTTP_201_CREATED,
        )


class CurrentSearchPreferencesView(
    RetrieveUpdateAPIView
):
    """
    Consulte ou modifie uniquement les préférences privées
    de l'utilisateur connecté.
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
        Crée automatiquement des préférences par défaut
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
        Sauvegarde les préférences et journalise l'action.

        Les valeurs privées ne sont pas inscrites
        directement dans les journaux.
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


class DiscoveryProfileListView(ListAPIView):
    """
    Retourne les profils compatibles avec les préférences
    de l'utilisateur connecté.

    Cette première version applique des filtres stricts.

    Une version future ajoutera notamment :

    - la compatibilité réciproque ;
    - le score de matching ;
    - les intérêts communs ;
    - la proximité géographique réelle ;
    - la détection des profils déjà vus ;
    - les blocages et signalements ;
    - le mélange contrôlé des résultats.
    """

    serializer_class = DiscoveryProfileSerializer

    permission_classes = (
        IsAuthenticated,
    )

    pagination_class = DiscoveryPagination

    def get_queryset(self):
        """
        Construit dynamiquement le QuerySet pour l'utilisateur courant.

        Il est important de ne pas définir un QuerySet global fixe,
        car les préférences diffèrent selon chaque utilisateur.
        """

        queryset = build_discovery_queryset(
            user=self.request.user,
        )

        preferences, _created = (
            SearchPreferences.objects.get_or_create(
                user=self.request.user,
            )
        )

        advanced_filters_enabled = bool(
            get_subscription_state(self.request.user)["entitlements"][
                "advanced_filters"
            ]
        )

        if (
            advanced_filters_enabled
            and preferences.only_profiles_with_photos
        ):
            queryset = queryset.filter(
                photos__isnull=False,
            ).distinct()

        # Les photos sont préchargées en une seule requête supplémentaire.
        # Cela évite une requête SQL par profil pendant la sérialisation.
        return queryset.prefetch_related(
            "photos",
        )

    def list(
        self,
        request,
        *args,
        **kwargs,
    ):
        """
        Journalise l'accès au moteur de découverte.

        Nous n'enregistrons pas la liste des profils retournés,
        afin d'éviter une journalisation excessive de données.
        """

        log_security_event(
            request=request,
            event="profile.discovery",
            outcome="success",
            reason="discovery_requested",
            user=request.user,
            email=request.user.email,
        )

        return super().list(
            request,
            *args,
            **kwargs,
        )



class PublicProfileDetailView(RetrieveAPIView):
    """
    Retourne le détail public d'un profil lorsque l'accès est légitime.

    Accès autorisé :
    - profil actuellement visible dans la découverte ;
    - profil lié à un match actif.

    Accès refusé avec 404 :
    - propre profil ;
    - compte suspendu/inactif/non vérifié ;
    - blocage dans un sens ou dans l'autre ;
    - profil non visible sans match actif ;
    - UUID inexistant.

    Le même 404 limite l'énumération des profils.
    """

    serializer_class = PublicProfileDetailSerializer
    permission_classes = (IsAuthenticated,)
    lookup_url_kwarg = "profile_id"

    def get_object(self) -> Profile:
        actor = self.request.user
        actor_profile = getattr(actor, "profile", None)

        if actor_profile is None:
            raise Http404

        profile_id = self.kwargs.get(self.lookup_url_kwarg)

        target = (
            Profile.objects
            .select_related("user", "verification")
            .prefetch_related("photos")
            .filter(
                id=profile_id,
                user__is_active=True,
                user__is_suspended=False,
                user__is_email_verified=True,
            )
            .exclude(id=actor_profile.id)
            .first()
        )

        if target is None:
            raise Http404

        if users_are_blocked(
            first_user=actor,
            second_user=target.user,
        ):
            raise Http404

        has_active_match = Match.objects.filter(
            is_active=True,
        ).filter(
            Q(
                profile_one=actor_profile,
                profile_two=target,
            )
            | Q(
                profile_one=target,
                profile_two=actor_profile,
            )
        ).exists()

        is_publicly_visible = bool(
            target.is_discoverable
            and target.is_complete
        )

        if not has_active_match and not is_publicly_visible:
            raise Http404

        log_security_event(
            request=self.request,
            event="profile.public_detail",
            outcome="success",
            reason=(
                "active_match"
                if has_active_match
                else "discoverable_profile"
            ),
            user=actor,
            email=actor.email,
        )

        self.check_object_permissions(
            self.request,
            target,
        )

        return target

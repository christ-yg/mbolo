"""
Vues API des photos de profil.

Les requêtes d'écriture utilisent SessionAuthentication et restent
donc protégées par le mécanisme CSRF de Django.
"""

from django.core.exceptions import (
    ValidationError as DjangoValidationError,
)
from rest_framework import status
from rest_framework.parsers import (
    FormParser,
    MultiPartParser,
)
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.core.security_logging import log_security_event

from .models import ProfilePhoto
from .serializers import (
    ProfilePhotoSerializer,
    ProfilePhotoUpdateSerializer,
    ProfilePhotoUploadSerializer,
)
from .services import (
    create_profile_photo,
    delete_profile_photo,
    get_owned_photo,
    update_profile_photo,
)


def photo_validation_error_response(
    exception: DjangoValidationError,
) -> Response:
    """
    Convertit une ValidationError Django en HTTP 400.
    """

    if hasattr(exception, "message_dict"):
        data = exception.message_dict
    else:
        data = {
            "detail": exception.messages,
        }

    return Response(
        data,
        status=status.HTTP_400_BAD_REQUEST,
    )


class ProfilePhotoListCreateView(APIView):
    """
    Liste les photos du profil connecté ou ajoute une photo.
    """

    permission_classes = (
        IsAuthenticated,
    )

    parser_classes = (
        MultiPartParser,
        FormParser,
    )

    def get(
        self,
        request: Request,
    ) -> Response:
        """
        Retourne uniquement les photos appartenant au compte connecté.
        """

        photos = (
            ProfilePhoto.objects
            .select_related("profile")
            .filter(
                profile__user=request.user,
            )
            .order_by(
                "position",
                "created_at",
            )
        )

        serializer = ProfilePhotoSerializer(
            photos,
            many=True,
            context={
                "request": request,
            },
        )

        return Response(
            {
                "results": serializer.data,
                "count": len(serializer.data),
            },
            status=status.HTTP_200_OK,
        )

    def post(
        self,
        request: Request,
    ) -> Response:
        """
        Traite puis enregistre une nouvelle photo.
        """

        serializer = ProfilePhotoUploadSerializer(
            data=request.data,
        )

        serializer.is_valid(
            raise_exception=True
        )

        validated_data = serializer.validated_data

        try:
            result = create_profile_photo(
                user=request.user,
                uploaded_file=validated_data["image"],
                position=validated_data.get(
                    "position"
                ),
                is_primary=validated_data.get(
                    "is_primary",
                    False,
                ),
            )
        except DjangoValidationError as exc:
            return photo_validation_error_response(
                exc
            )

        log_security_event(
            request=request,
            event="profile.photo.create",
            outcome="success",
            reason="photo_created",
            user=request.user,
            email=request.user.email,
        )

        output_serializer = ProfilePhotoSerializer(
            result.photo,
            context={
                "request": request,
            },
        )

        return Response(
            {
                "data": output_serializer.data,
                "processing": {
                    "width": result.processed_width,
                    "height": result.processed_height,
                    "format": "webp",
                },
                "message": "Photo ajoutée avec succès.",
            },
            status=status.HTTP_201_CREATED,
        )


class ProfilePhotoDetailView(APIView):
    """
    Modifie ou supprime une photo appartenant au compte connecté.
    """

    permission_classes = (
        IsAuthenticated,
    )

    def patch(
        self,
        request: Request,
        photo_id,
    ) -> Response:
        """
        Modifie la position ou le statut principal.
        """

        serializer = ProfilePhotoUpdateSerializer(
            data=request.data,
            partial=True,
        )

        serializer.is_valid(
            raise_exception=True
        )

        validated_data = serializer.validated_data

        try:
            photo = update_profile_photo(
                user=request.user,
                photo_id=photo_id,
                position=validated_data.get(
                    "position"
                ),
                is_primary=validated_data.get(
                    "is_primary"
                ),
            )
        except DjangoValidationError as exc:
            return photo_validation_error_response(
                exc
            )

        log_security_event(
            request=request,
            event="profile.photo.update",
            outcome="success",
            reason="photo_updated",
            user=request.user,
            email=request.user.email,
        )

        output_serializer = ProfilePhotoSerializer(
            photo,
            context={
                "request": request,
            },
        )

        return Response(
            {
                "data": output_serializer.data,
                "message": "Photo mise à jour.",
            },
            status=status.HTTP_200_OK,
        )

    def delete(
        self,
        request: Request,
        photo_id,
    ) -> Response:
        """
        Supprime une photo appartenant au compte connecté.
        """

        try:
            delete_profile_photo(
                user=request.user,
                photo_id=photo_id,
            )
        except DjangoValidationError as exc:
            return photo_validation_error_response(
                exc
            )

        log_security_event(
            request=request,
            event="profile.photo.delete",
            outcome="success",
            reason="photo_deleted",
            user=request.user,
            email=request.user.email,
        )

        return Response(
            status=status.HTTP_204_NO_CONTENT,
        )

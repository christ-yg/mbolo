"""
Sérialiseurs publics des photos de profil.

Les sérialiseurs séparent :

- les données acceptées lors d'un téléversement ;
- les données acceptées lors d'une modification ;
- les informations retournées au frontend.
"""

from rest_framework import serializers

from .models import ProfilePhoto


class ProfilePhotoUploadSerializer(
    serializers.Serializer
):
    """
    Données acceptées lors de l'ajout d'une photo.
    """

    image = serializers.ImageField(
        required=True,
        allow_empty_file=False,
        use_url=False,
    )

    position = serializers.IntegerField(
        required=False,
        min_value=0,
        max_value=5,
    )

    is_primary = serializers.BooleanField(
        required=False,
        default=False,
    )


class ProfilePhotoUpdateSerializer(
    serializers.Serializer
):
    """
    Champs modifiables après la création.

    Le fichier image n'est pas remplaçable via PATCH.
    Pour changer une image, le client doit supprimer l'ancienne
    puis en envoyer une nouvelle.
    """

    position = serializers.IntegerField(
        required=False,
        min_value=0,
        max_value=5,
    )

    is_primary = serializers.BooleanField(
        required=False,
    )

    def validate(self, attrs):
        """
        Exige au moins un champ à modifier.
        """

        if not attrs:
            raise serializers.ValidationError(
                "Aucune modification n'a été fournie."
            )

        return attrs


class ProfilePhotoSerializer(
    serializers.ModelSerializer
):
    """
    Représentation publique d'une photo.
    """

    image_url = serializers.SerializerMethodField()

    class Meta:
        model = ProfilePhoto

        fields = (
            "id",
            "image_url",
            "position",
            "is_primary",
            "created_at",
            "updated_at",
        )

        read_only_fields = fields

    def get_image_url(
        self,
        photo: ProfilePhoto,
    ) -> str | None:
        """
        Construit une URL absolue lorsque la requête est disponible.
        """

        if not photo.image:
            return None

        image_url = photo.image.url

        request = self.context.get(
            "request"
        )

        if request is None:
            return image_url

        return request.build_absolute_uri(
            image_url
        )

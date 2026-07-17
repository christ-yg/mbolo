from rest_framework import serializers

from .models import User


class CurrentUserSerializer(serializers.ModelSerializer):
    """
    Sérialiseur minimal de l'utilisateur connecté.

    Les champs sensibles ou internes ne sont jamais exposés :
    - mot de passe ;
    - permissions internes ;
    - statut de superutilisateur ;
    - numéro de téléphone ;
    - jetons ;
    - groupes administratifs.
    """

    class Meta:
        model = User

        fields = (
            "id",
            "email",
            "is_email_verified",
            "is_phone_verified",
            "created_at",
        )

        read_only_fields = fields

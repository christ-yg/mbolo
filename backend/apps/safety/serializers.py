"""
Sérialiseurs du module Safety.

Les sérialiseurs contrôlent précisément :

- les champs acceptés en entrée ;
- leur type ;
- les champs exposés en sortie ;
- l'impossibilité de choisir le propriétaire du blocage.
"""

from rest_framework import serializers

from apps.profiles.models import Profile
from apps.profiles.serializers import DiscoveryProfileSerializer

from .models import Block


class BlockCreateSerializer(serializers.Serializer):
    """
    Valide la création d'un blocage.

    Le client transmet uniquement l'UUID de l'utilisateur ciblé.

    L'utilisateur qui effectue le blocage est toujours request.user.
    """

    blocked_user_id = serializers.UUIDField(
        required=True,
    )


class BlockSerializer(serializers.ModelSerializer):
    """
    Représentation sécurisée d'un blocage.

    Nous affichons éventuellement le profil public minimal de la cible,
    mais jamais :

    - son adresse e-mail ;
    - son numéro de téléphone ;
    - sa date de naissance exacte ;
    - ses permissions ;
    - ses informations administratives.
    """

    blocked_profile = serializers.SerializerMethodField()

    class Meta:
        model = Block

        fields = (
            "id",
            "blocked_profile",
            "created_at",
        )

        read_only_fields = fields

    def get_blocked_profile(
        self,
        block: Block,
    ):
        """
        Retourne le profil public minimal de l'utilisateur bloqué.

        Si aucun profil n'existe, nous retournons None.
        Le blocage reste valide au niveau du compte.
        """

        try:
            profile = Profile.objects.select_related(
                "user"
            ).get(
                user=block.blocked_user,
            )
        except Profile.DoesNotExist:
            return None

        return DiscoveryProfileSerializer(
            profile,
            context=self.context,
        ).data


class BlockCreateResponseSerializer(serializers.Serializer):
    """
    Structure de la réponse après création d'un blocage.
    """

    id = serializers.UUIDField(
        read_only=True,
    )

    created = serializers.BooleanField(
        read_only=True,
    )

    deactivated_matches = serializers.IntegerField(
        read_only=True,
    )

    message = serializers.CharField(
        read_only=True,
    )

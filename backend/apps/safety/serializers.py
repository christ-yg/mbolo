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

from .models import Block, ReportReason


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



class ProfileBlockCreateSerializer(serializers.Serializer):
    """
    Création d'un blocage à partir de l'UUID public d'un profil.

    Le frontend ne transmet jamais l'UUID du compte utilisateur.
    La résolution profil -> compte reste exclusivement côté serveur.
    """

    confirm = serializers.BooleanField(
        required=True,
    )

    def validate_confirm(self, value: bool) -> bool:
        if value is not True:
            raise serializers.ValidationError(
                "La confirmation du blocage est obligatoire."
            )

        return value


class ProfileReportCreateSerializer(serializers.Serializer):
    """
    Signalement d'un profil depuis sa page publique.

    Le motif est limité aux valeurs du modèle ReportReason.
    La description reste facultative mais bornée.
    """

    reason = serializers.ChoiceField(
        choices=ReportReason.choices,
        required=True,
    )

    description = serializers.CharField(
        required=False,
        allow_blank=True,
        default="",
        trim_whitespace=True,
        max_length=2000,
    )


class ProfileSafetyActionResponseSerializer(serializers.Serializer):
    """
    Réponse commune aux actions Bloquer et Signaler.
    """

    created = serializers.BooleanField(
        read_only=True,
    )

    message = serializers.CharField(
        read_only=True,
    )

    deactivated_matches = serializers.IntegerField(
        read_only=True,
        required=False,
    )

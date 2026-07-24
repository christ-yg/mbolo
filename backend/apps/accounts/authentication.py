"""
Authentification par session renforcée de Mbolo.

La classe standard de Django REST Framework valide la session, mais elle ne
refuse pas automatiquement un compte suspendu après sa connexion. Cette couche
réalise donc le contrôle à chaque requête authentifiée.
"""

from django.utils import timezone
from rest_framework.authentication import SessionAuthentication
from rest_framework.exceptions import AuthenticationFailed


class ActiveAccountSessionAuthentication(SessionAuthentication):
    """
    Refuse immédiatement les sessions d'un compte suspendu ou désactivé.

    Une suspension temporaire expirée est levée atomiquement lors de la
    prochaine requête ou tentative de connexion. Le message reste générique
    afin de ne pas divulguer de détails internes de modération.
    """

    def authenticate(self, request):
        result = super().authenticate(request)

        if result is None:
            return None

        user, auth = result
        now = timezone.now()

        if (
            user.is_suspended
            and user.suspension_until is not None
            and user.suspension_until <= now
        ):
            # request.user est souvent enveloppé dans SimpleLazyObject.
            # user._meta.model désigne toujours le véritable modèle User,
            # contrairement à type(user), qui désignerait l'enveloppe.
            user._meta.model.objects.filter(
                pk=user.pk,
                is_suspended=True,
                suspension_until__lte=now,
            ).update(
                is_suspended=False,
                suspension_until=None,
            )
            user.is_suspended = False
            user.suspension_until = None

        if not user.is_active or user.is_suspended:
            raise AuthenticationFailed(
                "Ce compte ne peut pas être utilisé."
            )

        return user, auth

from rest_framework.generics import RetrieveAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request

from .models import User
from .serializers import CurrentUserSerializer


class CurrentUserView(RetrieveAPIView):
    """
    Retourne les informations minimales de l'utilisateur connecté.

    L'accès exige une session Django authentifiée.
    Un utilisateur ne peut obtenir que ses propres informations.
    """

    serializer_class = CurrentUserSerializer
    permission_classes = (IsAuthenticated,)

    def get_object(self) -> User:
        """
        Retourne exclusivement l'utilisateur associé à la requête.

        Aucun identifiant utilisateur n'est accepté dans l'URL,
        ce qui réduit le risque d'accès horizontal non autorisé.
        """

        request: Request = self.request

        return request.user

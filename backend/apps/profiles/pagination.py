from rest_framework.pagination import PageNumberPagination


class DiscoveryPagination(PageNumberPagination):
    """
    Pagination du moteur de découverte.

    Exemple :

        /api/v1/profiles/discovery/?page=2

    Le frontend peut demander une taille différente :

        /api/v1/profiles/discovery/?page_size=10

    Mais il ne pourra jamais dépasser 50 résultats par requête.
    """

    # Nombre de profils retournés par défaut.
    page_size = 20

    # Nom du paramètre permettant au frontend
    # de demander une taille personnalisée.
    page_size_query_param = "page_size"

    # Protection contre les demandes excessives comme :
    #
    # ?page_size=100000
    max_page_size = 50

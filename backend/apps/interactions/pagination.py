from rest_framework.pagination import PageNumberPagination


class MatchPagination(PageNumberPagination):
    """
    Pagination des matchs de l'utilisateur.

    Par défaut :

        20 matchs par page

    Maximum :

        50 matchs par requête
    """

    page_size = 20

    page_size_query_param = "page_size"

    max_page_size = 50

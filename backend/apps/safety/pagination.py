from rest_framework.pagination import PageNumberPagination


class BlockPagination(PageNumberPagination):
    """
    Pagination de la liste des utilisateurs bloqués.

    Par défaut :
        20 éléments par page.

    Maximum :
        50 éléments par requête.
    """

    page_size = 20

    page_size_query_param = "page_size"

    max_page_size = 50

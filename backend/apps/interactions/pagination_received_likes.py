
from rest_framework.pagination import PageNumberPagination


class ReceivedLikePagination(PageNumberPagination):
    """
    Pagination bornée de la page « Qui m’a liké ».

    La limite empêche un client de demander un volume excessif
    de données en une seule requête.
    """

    page_size = 12
    page_size_query_param = "page_size"
    max_page_size = 30

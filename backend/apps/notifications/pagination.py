
from rest_framework.pagination import PageNumberPagination


class NotificationPagination(PageNumberPagination):
    """
    Pagination bornée du centre de notifications.

    Le client peut demander page_size, mais jamais plus de 50 éléments.
    """

    page_size = 20
    page_size_query_param = "page_size"
    max_page_size = 50

from rest_framework.pagination import PageNumberPagination


class ConversationPagination(PageNumberPagination):
    """
    Pagination de la liste des conversations.
    """

    page_size = 20
    page_size_query_param = "page_size"
    max_page_size = 50


class MessagePagination(PageNumberPagination):
    """
    Pagination de l'historique des messages.
    """

    page_size = 50
    page_size_query_param = "page_size"
    max_page_size = 100

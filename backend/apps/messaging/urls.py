from django.urls import path

from .views import (
    ConversationListCreateView,
    ConversationMessageListCreateView,
)


app_name = "messaging"


urlpatterns = [
    path(
        "conversations/",
        ConversationListCreateView.as_view(),
        name="conversation-list-create",
    ),
    path(
        (
            "conversations/"
            "<uuid:conversation_id>/"
            "messages/"
        ),
        ConversationMessageListCreateView.as_view(),
        name="conversation-message-list-create",
    ),
]

"""
Routes de la messagerie privée Mbolo.
"""

from django.urls import path

from .views import (
    ConversationListCreateView,
    ConversationMarkReadView,
    ConversationMessageListCreateView,
    UnreadMessageCountView,
    ConversationTypingView,
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
    path(
        (
            "conversations/"
            "<uuid:conversation_id>/"
            "read/"
        ),
        ConversationMarkReadView.as_view(),
        name="conversation-mark-read",
    ),
    path(
        (
            "conversations/"
            "<uuid:conversation_id>/"
            "typing/"
        ),
        ConversationTypingView.as_view(),
        name="conversation-typing",
    ),
    path(
        "messages/unread-count/",
        UnreadMessageCountView.as_view(),
        name="message-unread-count",
    ),
]

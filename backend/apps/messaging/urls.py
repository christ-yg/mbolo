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
    MessageReactionView,
    MessageDetailView,
    MessageReportView,
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
        "conversations/<uuid:conversation_id>/messages/<uuid:message_id>/reaction/",
        MessageReactionView.as_view(),
        name="message-reaction",
    ),
    path(
        "conversations/<uuid:conversation_id>/messages/<uuid:message_id>/",
        MessageDetailView.as_view(),
        name="message-detail",
    ),
    path(
        "conversations/<uuid:conversation_id>/messages/<uuid:message_id>/report/",
        MessageReportView.as_view(),
        name="message-report",
    ),
    path(
        "messages/unread-count/",
        UnreadMessageCountView.as_view(),
        name="message-unread-count",
    ),
]

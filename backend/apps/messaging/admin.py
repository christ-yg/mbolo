from django.contrib import admin

from .models import Conversation, Message


@admin.register(Conversation)
class ConversationAdmin(admin.ModelAdmin):
    """
    Administration des conversations.
    """

    list_display = (
        "id",
        "match",
        "match_is_active",
        "created_at",
        "updated_at",
    )

    readonly_fields = (
        "id",
        "created_at",
        "updated_at",
    )

    search_fields = (
        "id",
        "match__id",
    )

    ordering = (
        "-updated_at",
    )

    @admin.display(
        boolean=True,
        description="Match actif",
    )
    def match_is_active(
        self,
        conversation: Conversation,
    ) -> bool:
        return conversation.match.is_active


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    """
    Administration des messages.
    """

    list_display = (
        "id",
        "conversation",
        "sender",
        "created_at",
    )

    readonly_fields = (
        "id",
        "created_at",
    )

    search_fields = (
        "id",
        "conversation__id",
        "sender__email",
        "body",
    )

    list_filter = (
        "created_at",
    )

    ordering = (
        "-created_at",
    )

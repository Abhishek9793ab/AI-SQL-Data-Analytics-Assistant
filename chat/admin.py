from django.contrib import admin

from .models import Conversation, Message


@admin.register(Conversation)
class ConversationAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "user",
        "dataset",
        "title",
        "created_at",
        "updated_at",
    )

    list_filter = (
        "dataset",
        "created_at",
        "updated_at",
    )

    search_fields = (
        "title",
        "user__username",
        "dataset__name",
    )


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "conversation",
        "role",
        "created_at",
    )

    list_filter = (
        "role",
        "created_at",
    )

    search_fields = (
        "content",
        "sql",
    )
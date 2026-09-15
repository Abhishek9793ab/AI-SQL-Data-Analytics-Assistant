from django.conf import settings
from django.db import models


class Conversation(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="analytics_conversations",
    )

    dataset = models.ForeignKey(
        "datasets.Dataset",
        on_delete=models.CASCADE,
        related_name="conversations",
    )

    title = models.CharField(
        max_length=200,
        default="New Analysis",
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    class Meta:
        ordering = ["-updated_at"]

    def __str__(self):
        return (
            f"{self.title} - "
            f"{self.dataset.name}"
        )


class Message(models.Model):

    USER = "user"
    ASSISTANT = "assistant"

    ROLE_CHOICES = [
        (USER, "User"),
        (ASSISTANT, "Assistant"),
    ]

    conversation = models.ForeignKey(
        Conversation,
        on_delete=models.CASCADE,
        related_name="messages",
    )

    role = models.CharField(
        max_length=20,
        choices=ROLE_CHOICES,
    )

    content = models.TextField()

    sql = models.TextField(
        blank=True,
        default="",
    )

    result_json = models.JSONField(
        default=dict,
        blank=True,
    )

    metadata_json = models.JSONField(
        default=dict,
        blank=True,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    class Meta:
        ordering = ["created_at"]

    def __str__(self):
        return (
            f"{self.role}: "
            f"{self.content[:60]}"
        )
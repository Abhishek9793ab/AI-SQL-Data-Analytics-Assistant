from django.contrib.auth.models import User
from django.db import models


class Dataset(models.Model):

    STATUS_CHOICES = [
        ("processing", "Processing"),
        ("ready", "Ready"),
        ("failed", "Failed"),
    ]

    FILE_TYPE_CHOICES = [
        ("csv", "CSV"),
        ("xlsx", "Excel"),
        ("json", "JSON"),
    ]

    owner = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="datasets",
    )

    name = models.CharField(
        max_length=255
    )

    original_filename = models.CharField(
        max_length=255
    )

    file = models.FileField(
        upload_to="datasets/%Y/%m/"
    )

    file_type = models.CharField(
        max_length=20,
        choices=FILE_TYPE_CHOICES,
    )

    database_table = models.CharField(
        max_length=128,
        unique=True,
    )

    rows = models.PositiveBigIntegerField(
        default=0
    )

    columns = models.PositiveIntegerField(
        default=0
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="processing",
    )

    error_message = models.TextField(
        blank=True,
        default="",
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    updated_at = models.DateTimeField(
        auto_now=True
    )

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.name} - {self.owner.username}"


class DatasetColumn(models.Model):

    DATA_TYPE_CHOICES = [
        ("integer", "Integer"),
        ("float", "Float"),
        ("boolean", "Boolean"),
        ("date", "Date"),
        ("datetime", "DateTime"),
        ("text", "Text"),
    ]

    dataset = models.ForeignKey(
        Dataset,
        on_delete=models.CASCADE,
        related_name="columns_info",
    )

    original_name = models.CharField(
        max_length=255
    )

    database_name = models.CharField(
        max_length=128
    )

    data_type = models.CharField(
        max_length=20,
        choices=DATA_TYPE_CHOICES,
    )

    position = models.PositiveIntegerField(
        default=0
    )

    nullable = models.BooleanField(
        default=True
    )

    unique_values = models.PositiveBigIntegerField(
        default=0
    )

    null_count = models.PositiveBigIntegerField(
        default=0
    )

    sample_values = models.JSONField(
        default=list,
        blank=True,
    )

    class Meta:
        ordering = ["position"]
        constraints = [
            models.UniqueConstraint(
                fields=["dataset", "database_name"],
                name="unique_dataset_column_name",
            )
        ]

    def __str__(self):
        return f"{self.dataset.name} → {self.original_name}"


class DatasetProfile(models.Model):

    dataset = models.OneToOneField(
        Dataset,
        on_delete=models.CASCADE,
        related_name="profile",
    )

    missing_cells = models.PositiveBigIntegerField(
        default=0
    )

    duplicate_rows = models.PositiveBigIntegerField(
        default=0
    )

    numeric_columns = models.PositiveIntegerField(
        default=0
    )

    categorical_columns = models.PositiveIntegerField(
        default=0
    )

    date_columns = models.PositiveIntegerField(
        default=0
    )

    memory_usage_bytes = models.PositiveBigIntegerField(
        default=0
    )

    profile_json = models.JSONField(
        default=dict,
        blank=True,
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    updated_at = models.DateTimeField(
        auto_now=True
    )

    def __str__(self):
        return f"Profile: {self.dataset.name}"
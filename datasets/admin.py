from django.contrib import admin

from .models import (
    Dataset,
    DatasetColumn,
    DatasetProfile,
)


@admin.register(Dataset)
class DatasetAdmin(admin.ModelAdmin):

    list_display = (
        "id",
        "name",
        "owner",
        "file_type",
        "rows",
        "columns",
        "status",
        "created_at",
    )

    list_filter = (
        "status",
        "file_type",
    )

    search_fields = (
        "name",
        "original_filename",
        "owner__username",
    )


@admin.register(DatasetColumn)
class DatasetColumnAdmin(admin.ModelAdmin):

    list_display = (
        "dataset",
        "original_name",
        "database_name",
        "data_type",
        "position",
    )

    list_filter = (
        "data_type",
    )


@admin.register(DatasetProfile)
class DatasetProfileAdmin(admin.ModelAdmin):

    list_display = (
        "dataset",
        "missing_cells",
        "duplicate_rows",
        "numeric_columns",
        "categorical_columns",
        "date_columns",
    )
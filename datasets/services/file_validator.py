from pathlib import Path

from django.conf import settings
from django.core.exceptions import ValidationError


ALLOWED_EXTENSIONS = {
    ".csv": "csv",
    ".xlsx": "xlsx",
    ".json": "json",
}


def validate_dataset_file(uploaded_file):

    if not uploaded_file:
        raise ValidationError("Please select a dataset file.")

    extension = Path(
        uploaded_file.name
    ).suffix.lower()

    if extension not in ALLOWED_EXTENSIONS:
        raise ValidationError(
            "Unsupported file format. "
            "Only CSV, XLSX and JSON files are allowed."
        )

    max_size = (
        settings.MAX_UPLOAD_SIZE_MB
        * 1024
        * 1024
    )

    if uploaded_file.size > max_size:
        raise ValidationError(
            f"File size cannot exceed "
            f"{settings.MAX_UPLOAD_SIZE_MB} MB."
        )

    return ALLOWED_EXTENSIONS[extension]
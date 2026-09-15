from django import forms

from .services.file_validator import (
    validate_dataset_file,
)


class DatasetUploadForm(forms.Form):

    file = forms.FileField(
        widget=forms.ClearableFileInput(
            attrs={
                "accept": ".csv,.xlsx,.json",
                "class": "dataset-file-input",
            }
        )
    )

    def clean_file(self):

        uploaded_file = (
            self.cleaned_data["file"]
        )

        validate_dataset_file(
            uploaded_file
        )

        return uploaded_file
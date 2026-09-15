from django.shortcuts import render

# Create your views here.
import uuid

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.shortcuts import (
    get_object_or_404,
    redirect,
    render,
)

from .forms import DatasetUploadForm
from .models import (
    Dataset,
    DatasetColumn,
    DatasetProfile,
)

from .services.dataset_loader import (
    DatasetLoadError,
    load_dataset,
)

from .services.database_loader import (
    create_dataset_table,
    insert_dataframe,
)

from .services.profiler import (
    profile_dataset,
    detect_column_type,
)

from .services.schema_builder import (
    build_database_columns,
)


@login_required
def dashboard(request):

    datasets = Dataset.objects.filter(
        owner=request.user
    ).order_by("-updated_at")

    total_datasets = datasets.count()

    ready_datasets = datasets.filter(
        status="ready"
    ).count()

    processing_datasets = datasets.filter(
        status="processing"
    ).count()

    failed_datasets = datasets.filter(
        status="failed"
    ).count()

    total_rows = 0
    total_columns = 0

    for dataset in datasets:
        total_rows += dataset.rows or 0
        total_columns += dataset.columns or 0

    recent_datasets = datasets[:5]

    context = {
        "datasets": datasets,
        "recent_datasets": recent_datasets,

        "total_datasets": total_datasets,
        "ready_datasets": ready_datasets,
        "processing_datasets": processing_datasets,
        "failed_datasets": failed_datasets,

        "total_rows": total_rows,
        "total_columns": total_columns,
    }

    return render(
        request,
        "dashboard/dashboard.html",
        context,
    )


@login_required
def upload_dataset(request):

    if request.method == "POST":

        form = DatasetUploadForm(
            request.POST,
            request.FILES,
        )

        if form.is_valid():

            uploaded_file = (
                form.cleaned_data["file"]
            )

            dataset = None

            try:

                with transaction.atomic():

                    file_type = (
                        uploaded_file
                        .name
                        .rsplit(
                            ".",
                            1
                        )[-1]
                        .lower()
                    )

                    dataset = Dataset.objects.create(
                        owner=request.user,
                        name=(
                            uploaded_file.name
                            .rsplit(
                                ".",
                                1
                            )[0]
                        ),
                        original_filename=(
                            uploaded_file.name
                        ),
                        file=uploaded_file,
                        file_type=file_type,
                        database_table=(
                            f"dataset_"
                            f"{uuid.uuid4().hex[:16]}"
                        ),
                        status="processing",
                    )

                    # FileField has now saved the file
                    file_path = (
                        dataset.file.path
                    )

                    df = load_dataset(
                        file_path,
                        file_type,
                    )

                    profile = profile_dataset(
                        df
                    )

                    database_columns = (
                        build_database_columns(
                            df.columns
                        )
                    )

                    for item in database_columns:

                        original_name = item[
                            "original_name"
                        ]

                        item["data_type"] = (
                            detect_column_type(
                                df[
                                    original_name
                                ]
                            )
                        )

                    create_dataset_table(
                        dataset.database_table,
                        database_columns,
                    )

                    insert_dataframe(
                        dataset.database_table,
                        df,
                        database_columns,
                    )

                    dataset.rows = len(df)
                    dataset.columns = len(
                        df.columns
                    )
                    dataset.status = "ready"

                    dataset.save(
                        update_fields=[
                            "rows",
                            "columns",
                            "status",
                            "updated_at",
                        ]
                    )

                    for position, item in enumerate(
                        database_columns
                    ):

                        column_df = df[
                            item["original_name"]
                        ]

                        DatasetColumn.objects.create(
                            dataset=dataset,
                            original_name=item[
                                "original_name"
                            ],
                            database_name=item[
                                "database_name"
                            ],
                            data_type=item[
                                "data_type"
                            ],
                            position=position,
                            nullable=bool(
                                column_df.isna().any()
                            ),
                            unique_values=int(
                                column_df.nunique(
                                    dropna=True
                                )
                            ),
                            null_count=int(
                                column_df.isna().sum()
                            ),
                            sample_values=(
                                profile[
                                    "columns"
                                ][position][
                                    "sample_values"
                                ]
                            ),
                        )

                    DatasetProfile.objects.create(
                        dataset=dataset,
                        missing_cells=profile[
                            "missing_cells"
                        ],
                        duplicate_rows=profile[
                            "duplicate_rows"
                        ],
                        numeric_columns=profile[
                            "numeric_columns"
                        ],
                        categorical_columns=profile[
                            "categorical_columns"
                        ],
                        date_columns=profile[
                            "date_columns"
                        ],
                        memory_usage_bytes=profile[
                            "memory_usage_bytes"
                        ],
                        profile_json=profile,
                    )

                messages.success(
                    request,
                    "Dataset uploaded successfully.",
                )

                return redirect(
                    "dataset_detail",
                    dataset_id=dataset.id,
                )

            except Exception as exc:

                if dataset:

                    dataset.status = "failed"

                    dataset.error_message = str(
                        exc
                    )

                    dataset.save(
                        update_fields=[
                            "status",
                            "error_message",
                            "updated_at",
                        ]
                    )

                messages.error(
                    request,
                    f"Dataset processing failed: {exc}",
                )

    else:

        form = DatasetUploadForm()

    return render(
        request,
        "datasets/upload.html",
        {
            "form": form,
        },
    )


@login_required
def dataset_detail(
    request,
    dataset_id,
):

    dataset = get_object_or_404(
        Dataset,
        id=dataset_id,
        owner=request.user,
    )

    columns = dataset.columns_info.all()

    profile = getattr(
        dataset,
        "profile",
        None,
    )

    return render(
        request,
        "datasets/detail.html",
        {
            "dataset": dataset,
            "columns": columns,
            "profile": profile,
        },
    )
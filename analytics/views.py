from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, render

from datasets.models import Dataset, DatasetColumn


@login_required
def analyst_view(request, dataset_id):
    """
    AI SQL Analyst page for a ready dataset.
    """

    # =========================================================
    # 1. GET DATASET
    # =========================================================

    dataset = get_object_or_404(
        Dataset,
        id=dataset_id,
        owner=request.user,
        status="ready",
    )

    # =========================================================
    # 2. GET ACTUAL COLUMN RECORDS
    # =========================================================

    columns = (
        DatasetColumn.objects
        .filter(dataset=dataset)
        .order_by("position")
    )

    # =========================================================
    # 3. RENDER ANALYST PAGE
    # =========================================================

    return render(
        request,
        "analytics/analyst.html",
        {
            "dataset": dataset,
            "columns": columns,
        },
    )
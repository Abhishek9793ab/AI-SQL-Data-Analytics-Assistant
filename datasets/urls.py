from django.urls import path

from . import views


urlpatterns = [

    path(
        "",
        views.dashboard,
        name="dashboard",
    ),

    path(
        "dashboard/",
        views.dashboard,
        name="dashboard",
    ),

    path(
        "datasets/upload/",
        views.upload_dataset,
        name="upload_dataset",
    ),

    path(
        "datasets/<int:dataset_id>/",
        views.dataset_detail,
        name="dataset_detail",
    ),
]
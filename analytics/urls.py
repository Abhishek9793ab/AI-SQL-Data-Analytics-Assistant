from django.urls import path

from . import views


app_name = "analytics"


urlpatterns = [
    path(
        "<int:dataset_id>/",
        views.analyst_view,
        name="analyst",
    ),
]
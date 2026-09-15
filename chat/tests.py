from django.urls import path
from . import views

app_name = "chat"

urlpatterns = [
    path(
        "<int:dataset_id>/ask/",
        views.ask_question,
        name="ask_question",
    ),
]
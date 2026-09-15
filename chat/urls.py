from django.urls import path

from . import views


app_name = "chat"


urlpatterns = [
    path(
        "<int:conversation_id>/export/",
        views.export_conversation,
        name="export_conversation",
    ),

    path(
        "<int:dataset_id>/ask/",
        views.ask_question,
        name="ask_question",
    ),

    path(
        "<int:dataset_id>/history/",
        views.conversation_history,
        name="conversation_history",
    ),
]
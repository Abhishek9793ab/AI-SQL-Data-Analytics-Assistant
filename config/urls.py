from django.contrib import admin
from django.urls import include, path

from django.conf import settings
from django.conf.urls.static import static


urlpatterns = [
    # Django Admin
    path(
        "admin/",
        admin.site.urls,
    ),

    # Authentication
    path(
        "accounts/",
        include("accounts.urls"),
    ),

    # Dataset application
    path(
        "",
        include("datasets.urls"),
    ),

    # AI Analytics
    path(
        "analytics/",
        include(
            ("analytics.urls", "analytics"),
            namespace="analytics",
        ),
    ),

    # AI Chat / Question API
    path(
        "chat/",
        include(
            ("chat.urls", "chat"),
            namespace="chat",
        ),
    ),
]


if settings.DEBUG:
    urlpatterns += static(
        settings.MEDIA_URL,
        document_root=settings.MEDIA_ROOT,
    )
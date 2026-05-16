from django.contrib import admin
from django.urls import include, path, register_converter

from apps.core import views
from apps.core.converters import UnicodeSlugConverter

register_converter(UnicodeSlugConverter, "uslug")

handler404 = "apps.core.views.custom_404"

urlpatterns = [
    path("", views.home, name="home"),
    path("docs/", views.docs_index, name="docs_index"),
    path("docs/<uslug:workspace_slug>/", views.docs_workspace, name="docs_workspace"),
    path("search", views.public_search, name="public_search"),
    path("django-admin/", admin.site.urls),
    path("", include("apps.accounts.urls")),
    path("", include("apps.documents.urls")),
    path("", include("apps.editor.urls")),
    path("", include("apps.publishing.urls")),
    path("", include("apps.workspaces.urls")),
    path("", include("apps.skills.urls")),
]

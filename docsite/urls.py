from django.contrib import admin
from django.urls import include, path

from apps.core import views

handler404 = "apps.core.views.custom_404"

urlpatterns = [
    path("", views.home, name="home"),
    path("django-admin/", admin.site.urls),
    path("", include("apps.accounts.urls")),
    path("", include("apps.documents.urls")),
    path("", include("apps.editor.urls")),
]

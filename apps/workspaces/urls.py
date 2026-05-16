from django.urls import path

from .views import workspace_home, workspace_trash

urlpatterns = [
    path("w/<slug:workspace_slug>/", workspace_home, name="workspace_home"),
    path("w/<slug:workspace_slug>/trash/", workspace_trash, name="workspace_trash"),
]

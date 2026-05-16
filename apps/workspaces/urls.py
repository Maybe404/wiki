from django.urls import path

from .views import (
    workspace_create,
    workspace_delete,
    workspace_home,
    workspace_trash,
    workspace_update,
)

urlpatterns = [
    path("admin/workspaces/new/", workspace_create, name="workspace_create"),
    path(
        "admin/workspaces/<uslug:workspace_slug>/edit/", workspace_update, name="workspace_update"
    ),
    path(
        "admin/workspaces/<uslug:workspace_slug>/delete/",
        workspace_delete,
        name="workspace_delete",
    ),
    path("w/<uslug:workspace_slug>/", workspace_home, name="workspace_home"),
    path("w/<uslug:workspace_slug>/trash/", workspace_trash, name="workspace_trash"),
]

from django.contrib.auth.decorators import login_required
from django.http import Http404, HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, render

from apps.documents.models import Document
from apps.documents.utils import build_nested_tree

from .models import Workspace
from .permissions import is_admin, require_workspace_access


@login_required
def workspace_home(request: HttpRequest, workspace_slug: str) -> HttpResponse:
    """GET /w/<workspace-slug>/ — workspace 内目录与文档列表（登录后可见）。"""
    ws = get_object_or_404(Workspace, slug=workspace_slug, is_deleted=False)
    require_workspace_access(request.user, ws)  # ty: ignore[unresolved-attribute]

    qs = Document.get_tree().filter(workspace=ws, is_deleted=False).select_related("workspace")
    tree_data = build_nested_tree(qs)

    return render(
        request,
        "workspaces/workspace_home.html",
        {
            "workspace": ws,
            "tree_data": tree_data,
            "current_workspace": ws,
        },
    )


@login_required
def workspace_trash(request: HttpRequest, workspace_slug: str) -> HttpResponse:
    """GET /w/<workspace-slug>/trash/ — 回收站，仅管理员可见。"""
    if not is_admin(request.user):  # ty: ignore[unresolved-attribute]
        raise Http404

    ws = get_object_or_404(Workspace, slug=workspace_slug, is_deleted=False)
    deleted_nodes = (
        Document.objects.filter(workspace=ws, is_deleted=True)
        .select_related("owner", "workspace")
        .order_by("-deleted_at", "-updated_at")
    )

    return render(
        request,
        "workspaces/workspace_trash.html",
        {
            "workspace": ws,
            "deleted_nodes": deleted_nodes,
            "current_workspace": ws,
        },
    )

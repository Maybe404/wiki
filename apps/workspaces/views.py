import secrets

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import Http404, HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.text import slugify
from django.views.decorators.http import require_POST

from apps.documents.models import Document
from apps.documents.utils import build_nested_tree

from .models import Workspace
from .permissions import is_admin, require_workspace_access


def _generate_workspace_slug(name: str) -> str:
    """根据名称生成唯一 workspace slug。"""
    base = slugify(name, allow_unicode=True)[:50] or "workspace"
    if not Workspace.objects.filter(slug=base).exists():  # ty: ignore[unresolved-attribute]
        return base
    for _ in range(10):
        candidate = f"{base}-{secrets.token_hex(3)}"
        if not Workspace.objects.filter(slug=candidate).exists():  # ty: ignore[unresolved-attribute]
            return candidate
    return f"workspace-{secrets.token_hex(6)}"


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


@login_required
@require_POST
def workspace_create(request: HttpRequest) -> HttpResponse:
    """POST /admin/workspaces/new/ — 创建工作空间（仅管理员）。"""
    if not is_admin(request.user):  # ty: ignore[unresolved-attribute]
        raise Http404

    name = request.POST.get("name", "").strip()[:100]
    if not name:
        messages.error(request, "空间名称不能为空。")
        return redirect("admin_dashboard")

    Workspace.objects.create(  # ty: ignore[unresolved-attribute]
        name=name,
        slug=_generate_workspace_slug(name),
        description=request.POST.get("description", "").strip(),
        created_by=request.user,  # ty: ignore[unresolved-attribute]
    )
    messages.success(request, f"工作空间「{name}」已创建。")
    return redirect("admin_dashboard")


@login_required
@require_POST
def workspace_update(request: HttpRequest, workspace_slug: str) -> HttpResponse:
    """POST /admin/workspaces/<slug>/edit/ — 重命名/改描述（仅管理员）。"""
    if not is_admin(request.user):  # ty: ignore[unresolved-attribute]
        raise Http404

    ws = get_object_or_404(Workspace, slug=workspace_slug, is_deleted=False)
    name = request.POST.get("name", "").strip()[:100]
    if not name:
        messages.error(request, "空间名称不能为空。")
        return redirect("admin_dashboard")

    ws.name = name
    ws.description = request.POST.get("description", "").strip()
    ws.save(update_fields=["name", "description", "updated_at"])
    messages.success(request, f"工作空间「{name}」已更新。")
    return redirect("admin_dashboard")


@login_required
@require_POST
def workspace_delete(request: HttpRequest, workspace_slug: str) -> HttpResponse:
    """POST /admin/workspaces/<slug>/delete/ — 软删除空间（仅管理员）。"""
    if not is_admin(request.user):  # ty: ignore[unresolved-attribute]
        raise Http404

    ws = get_object_or_404(Workspace, slug=workspace_slug, is_deleted=False)
    if ws.nodes.filter(is_deleted=False).exists():
        messages.error(request, f"工作空间「{ws.name}」下仍有文档，无法删除。")
        return redirect("admin_dashboard")

    ws.is_deleted = True
    ws.save(update_fields=["is_deleted", "updated_at"])
    messages.success(request, f"工作空间「{ws.name}」已删除。")
    return redirect("admin_dashboard")

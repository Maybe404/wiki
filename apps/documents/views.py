import json
import secrets
import uuid
from typing import cast

from django.contrib.auth.decorators import login_required
from django.http import Http404, HttpRequest, HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.utils.text import slugify
from django.views.decorators.http import require_POST
from django.views.generic import DetailView

from apps.workspaces.models import Workspace
from apps.workspaces.permissions import (
    can_copy_document,
    can_read_document,
    can_view_doc_in_admin,
    is_admin,
)

from .fts import search_documents
from .models import AuditLog, Document, DocumentVersion, SlugAlias
from .utils import build_admin_workspace_tree, build_published_workspace_tree, extract_toc

DOCUMENT_CONTENT_CSP = (
    "default-src 'none'; "
    "script-src 'unsafe-inline' 'unsafe-eval' "
    "https://cdn.jsdelivr.net https://unpkg.com https://cdnjs.cloudflare.com; "
    "style-src 'unsafe-inline' "
    "https://fonts.googleapis.com https://cdn.jsdelivr.net https://unpkg.com "
    "https://cdnjs.cloudflare.com; "
    "font-src https://fonts.gstatic.com https://cdn.jsdelivr.net https://unpkg.com data:; "
    "img-src https: data: blob:; "
    "media-src https: data: blob:; "
    "connect-src https:; "
    "frame-src https:;"
)


def _current_version(doc: Document) -> DocumentVersion | None:
    """Return the current content snapshot for a document."""
    return doc.versions.filter(is_auto=False).first() or doc.versions.first()  # ty: ignore[unresolved-attribute]


def _document_content_response(html: str) -> HttpResponse:
    """Serve the imported full-page HTML verbatim; the iframe owns its own scroll."""
    response = HttpResponse(
        html,
        content_type="text/html; charset=utf-8",
    )
    response["Content-Security-Policy"] = DOCUMENT_CONTENT_CSP
    response["X-Frame-Options"] = "SAMEORIGIN"
    return response


class DocumentDetailView(DetailView):
    """公开阅读页 /d/<slug>/，草稿返回 404，旧 slug 301 跳转。"""

    model = Document
    template_name = "doc/detail.html"
    context_object_name = "document"

    def get(self, request: HttpRequest, *args, **kwargs) -> HttpResponse:
        slug = self.kwargs["slug"]

        alias = SlugAlias.objects.filter(old_slug=slug).select_related("document").first()  # ty: ignore[unresolved-attribute]
        if alias is not None:
            return redirect("doc_detail", slug=alias.document.slug, permanent=True)

        return super().get(request, *args, **kwargs)

    def get_object(self, queryset=None):  # type: ignore[override]
        slug = self.kwargs["slug"]
        doc = get_object_or_404(
            Document.objects.select_related("workspace"),
            slug=slug,
            node_type=Document.NodeType.DOCUMENT,
            status=Document.Status.PUBLISHED,
            is_deleted=False,
        )
        if not can_read_document(self.request.user, doc):
            raise Http404
        return doc

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        doc: Document = self.object  # type: ignore[assignment]
        version = _current_version(doc)
        raw_html: str = str(version.html) if version else ""
        is_full_page = bool(version and version.is_full_page)
        if is_full_page:
            content_html, toc_items = raw_html, []
            ctx["content_url"] = reverse("doc_content", kwargs={"slug": doc.slug})
        else:
            content_html, toc_items = extract_toc(raw_html)
            ctx["content_url"] = ""
        ctx["version"] = version
        ctx["content_html"] = content_html
        ctx["is_full_page"] = is_full_page
        ctx["toc_items"] = toc_items
        ctx["tree_data"] = build_published_workspace_tree(self.request.user)
        return ctx


def document_content(request: HttpRequest, slug: str) -> HttpResponse:
    """Public iframe content endpoint for published full-page HTML."""
    alias = SlugAlias.objects.filter(old_slug=slug).select_related("document").first()  # ty: ignore[unresolved-attribute]
    if alias is not None:
        return redirect("doc_content", slug=alias.document.slug, permanent=True)

    doc = get_object_or_404(
        Document.objects.select_related("workspace"),
        slug=slug,
        node_type=Document.NodeType.DOCUMENT,
        status=Document.Status.PUBLISHED,
        is_deleted=False,
    )
    if not can_read_document(request.user, doc):  # ty: ignore[unresolved-attribute]
        raise Http404
    version = _current_version(doc)
    return _document_content_response(str(version.html) if version else "")


@login_required
def admin_doc_detail(request: HttpRequest, pk: uuid.UUID) -> HttpResponse:
    """管理端文档详情页 /admin/doc/<pk>/，含编辑入口。"""
    doc = get_object_or_404(
        Document.objects.select_related("workspace"),
        pk=pk,
        node_type=Document.NodeType.DOCUMENT,
        is_deleted=False,
    )
    if not can_view_doc_in_admin(request.user, doc):  # ty: ignore[unresolved-attribute]
        raise Http404

    # 优先取最新命名版本，没有就取最新自动版本
    version = _current_version(doc)
    content_html = version.html if version else ""
    is_full_page = bool(version and version.is_full_page)

    user = request.user  # ty: ignore[unresolved-attribute]
    workspace = cast(Workspace | None, doc.workspace if doc.workspace_id else None)
    tree_data = build_admin_workspace_tree(user, workspace)

    # 面包屑：取祖先中 node_type=folder 的节点
    breadcrumbs = list(doc.get_ancestors())

    return render(
        request,
        "admin_ui/doc_detail.html",
        {
            "document": doc,
            "version": version,
            "content_html": content_html,
            "is_full_page": is_full_page,
            "content_url": reverse("admin_doc_content", kwargs={"pk": doc.pk})
            if is_full_page
            else "",
            "tree_data": tree_data,
            "current_workspace": doc.workspace,
            "breadcrumbs": breadcrumbs,
        },
    )


@login_required
def admin_doc_content(request: HttpRequest, pk: uuid.UUID) -> HttpResponse:
    """Authenticated iframe content endpoint for admin previews, including drafts."""
    doc = get_object_or_404(
        Document.objects.select_related("workspace"),
        pk=pk,
        node_type=Document.NodeType.DOCUMENT,
        is_deleted=False,
    )
    if not can_view_doc_in_admin(request.user, doc):  # ty: ignore[unresolved-attribute]
        raise Http404
    version = _current_version(doc)
    return _document_content_response(str(version.html) if version else "")


@login_required
@require_POST
def tree_reorder(request: HttpRequest) -> JsonResponse:
    """拖拽排序：接收 {node_id, new_parent_id, prev_sibling_id}，用 treebeard move() 持久化。"""
    try:
        data = json.loads(request.body)
        node_id: str = data["node_id"]
        new_parent_id: str = data.get("new_parent_id") or ""
        prev_sibling_id: str = data.get("prev_sibling_id") or ""
    except (json.JSONDecodeError, KeyError):
        return JsonResponse({"error": "invalid payload"}, status=400)

    try:
        node = Document.objects.get(pk=node_id, is_deleted=False)
    except Document.DoesNotExist:  # ty: ignore[unresolved-attribute]
        return JsonResponse({"error": "node not found"}, status=404)

    try:
        if prev_sibling_id:
            if new_parent_id:
                parent = Document.objects.get(pk=new_parent_id, is_deleted=False)
                if parent.node_type != Document.NodeType.FOLDER:
                    return JsonResponse({"error": "documents cannot contain children"}, status=400)
            # 放在某个兄弟节点之后
            prev = Document.objects.get(pk=prev_sibling_id, is_deleted=False)
            node.move(prev, "right")
        elif new_parent_id:
            # 移入某父节点且作为第一个子节点
            parent = Document.objects.get(pk=new_parent_id, is_deleted=False)
            if parent.node_type != Document.NodeType.FOLDER:
                return JsonResponse({"error": "documents cannot contain children"}, status=400)
            node.move(parent, "first-child")
        else:
            # 移到根级别第一位
            roots = list(Document.get_root_nodes().filter(is_deleted=False).exclude(pk=node.pk))
            if roots:
                node.move(roots[0], "left")
    except Document.DoesNotExist:  # ty: ignore[unresolved-attribute]
        return JsonResponse({"error": "reference node not found"}, status=404)
    except Exception as exc:
        return JsonResponse({"error": str(exc)}, status=500)

    return JsonResponse({"ok": True})


def _generate_folder_slug(title: str) -> str:
    base = slugify(title, allow_unicode=True)[:40] or "folder"
    for _ in range(10):
        candidate = f"folder-{base}-{secrets.token_hex(3)}"
        if not Document.objects.filter(slug=candidate, is_deleted=False).exists():
            return candidate
    return f"folder-{secrets.token_hex(6)}"


def _resolve_folder_workspace(parent: Document | None) -> Workspace | None:
    if parent is not None and parent.workspace_id is not None:  # ty: ignore[unresolved-attribute]
        return parent.workspace  # ty: ignore[invalid-return-type]
    return Workspace.objects.filter(slug="default", is_deleted=False).first()  # ty: ignore[unresolved-attribute]


@login_required
@require_POST
def folder_create(request: HttpRequest) -> HttpResponse:
    """POST /admin/folder/new/ — 创建目录节点，可作为根级或子级。"""
    title = request.POST.get("title", "").strip()[:200] or "未命名文件夹"
    parent_id = request.POST.get("parent_id", "").strip()
    slug = _generate_folder_slug(title)

    folder_parent: Document | None = None
    if parent_id:
        folder_parent = get_object_or_404(
            Document.objects.select_related("workspace"), pk=parent_id, is_deleted=False
        )
        if folder_parent.node_type != Document.NodeType.FOLDER:
            return HttpResponse("只能在文件夹中创建子文件夹", status=400)

    ws = _resolve_folder_workspace(folder_parent)
    node_kwargs = {
        "title": title,
        "slug": slug,
        "node_type": Document.NodeType.FOLDER,
        "status": Document.Status.DRAFT,
        "owner": request.user,  # ty: ignore[unresolved-attribute]
        "workspace": ws,
    }
    folder = (
        folder_parent.add_child(**node_kwargs)
        if folder_parent is not None
        else Document.add_root(**node_kwargs)
    )

    AuditLog.objects.create(  # ty: ignore[unresolved-attribute]
        actor=request.user,  # ty: ignore[unresolved-attribute]
        action=AuditLog.Action.CREATE,
        target_type="folder",
        target_id=str(folder.pk),
        payload={"title": title, "parent_id": parent_id or None},
    )
    return redirect("admin_dashboard")


@login_required
@require_POST
def tree_node_delete(request: HttpRequest, pk: uuid.UUID) -> JsonResponse:
    """软删除文档或文件夹。删除文件夹时一并隐藏其全部子节点。"""
    node = get_object_or_404(Document, pk=pk, is_deleted=False)
    descendants = list(node.get_descendants().filter(is_deleted=False))
    ids = [node.pk, *(child.pk for child in descendants)]
    now = timezone.now()

    Document.objects.filter(pk__in=ids).update(is_deleted=True, deleted_at=now, updated_at=now)
    AuditLog.objects.create(  # ty: ignore[unresolved-attribute]
        actor=request.user,  # ty: ignore[unresolved-attribute]
        action=AuditLog.Action.DELETE,
        target_type=node.node_type,
        target_id=str(node.pk),
        payload={"title": node.title, "descendants": len(descendants)},
    )

    return JsonResponse({"ok": True, "deleted": len(ids), "redirect": "/admin/"})


@login_required
@require_POST
def node_move(request: HttpRequest, pk: uuid.UUID) -> JsonResponse:
    """POST /admin/tree/node/<pk>/move/ — 把节点移动到指定文件夹（或根级）。

    与 tree_reorder 不同：这是「右键菜单 → 移动」走的显式确认路径，
    会同步更新节点及其子树的 workspace，确保移动后路径稳定持久。
    """
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({"error": "invalid payload"}, status=400)

    node = get_object_or_404(Document, pk=pk, is_deleted=False)
    parent_id = str(data.get("parent_id") or "").strip()

    parent: Document | None = None
    if parent_id:
        parent = get_object_or_404(Document, pk=parent_id, is_deleted=False)
        if parent.node_type != Document.NodeType.FOLDER:
            return JsonResponse({"error": "目标必须是文件夹"}, status=400)
        if parent.pk == node.pk or parent.is_descendant_of(node):
            return JsonResponse({"error": "不能移动到自身或其子目录"}, status=400)

    try:
        if parent is not None:
            node.move(parent, "sorted-child")
        else:
            first_root = Document.get_first_root_node()
            if first_root is not None and first_root.pk != node.pk:
                node.move(first_root, "sorted-sibling")
    except Exception as exc:  # noqa: BLE001
        return JsonResponse({"error": str(exc)}, status=500)

    # 同步 workspace：节点及其子树归到目标父级所在空间
    node.refresh_from_db()
    target_ws_id = parent.workspace_id if parent is not None else node.workspace_id
    ids = [node.pk, *(c.pk for c in node.get_descendants())]
    Document.objects.filter(pk__in=ids).update(workspace_id=target_ws_id, updated_at=timezone.now())

    AuditLog.objects.create(  # ty: ignore[unresolved-attribute]
        actor=request.user,  # ty: ignore[unresolved-attribute]
        action=AuditLog.Action.UPDATE,
        target_type=node.node_type,
        target_id=str(node.pk),
        payload={"action": "move", "parent_id": parent_id or None},
    )
    return JsonResponse({"ok": True})


@login_required
def search_api(request: HttpRequest) -> JsonResponse:
    """GET /admin/search?q=xxx — FTS5 全文搜索，返回分组 JSON。"""
    q = request.GET.get("q", "").strip()
    if not q:
        return JsonResponse({"groups": []})
    result = search_documents(q)
    return JsonResponse(result)


def _generate_copy_slug(original_slug: str) -> str:
    base = f"{original_slug}-copy"
    if not Document.objects.filter(slug=base, is_deleted=False).exists():
        return base
    for i in range(2, 20):
        candidate = f"{original_slug}-copy-{i}"
        if not Document.objects.filter(slug=candidate, is_deleted=False).exists():
            return candidate
    return f"{original_slug}-copy-{secrets.token_hex(3)}"


@login_required
@require_POST
def doc_copy(request: HttpRequest, pk: uuid.UUID) -> HttpResponse:
    """POST /admin/doc/<pk>/copy/ — 复制文档为草稿（同 workspace、同目录）。"""
    doc = get_object_or_404(
        Document.objects.select_related("workspace"),
        pk=pk,
        node_type=Document.NodeType.DOCUMENT,
        is_deleted=False,
    )
    if not can_copy_document(request.user, doc):  # ty: ignore[unresolved-attribute]
        raise Http404

    version = _current_version(doc)
    new_slug = _generate_copy_slug(doc.slug)
    parent = doc.get_parent()

    new_doc_kwargs = {
        "title": f"{doc.title}（副本）",
        "slug": new_slug,
        "node_type": Document.NodeType.DOCUMENT,
        "status": Document.Status.DRAFT,
        "owner": request.user,  # ty: ignore[unresolved-attribute]
        "workspace": doc.workspace,
        "visibility": doc.visibility,
    }

    if parent is not None:
        new_doc = parent.add_child(**new_doc_kwargs)
    else:
        new_doc = Document.add_root(**new_doc_kwargs)

    if version:
        DocumentVersion.objects.create(  # ty: ignore[unresolved-attribute]
            document=new_doc,
            html=version.html,
            editable_blocks=version.editable_blocks,
            is_full_page=version.is_full_page,
            author=request.user,  # ty: ignore[unresolved-attribute]
            note=f"复制自「{doc.title}」",
        )

    AuditLog.objects.create(  # ty: ignore[unresolved-attribute]
        actor=request.user,  # ty: ignore[unresolved-attribute]
        action=AuditLog.Action.CREATE,
        target_type="document",
        target_id=str(new_doc.pk),
        payload={"source_id": str(doc.pk), "source_title": doc.title},
    )

    return redirect("admin_doc_detail", pk=new_doc.pk)


@login_required
@require_POST
def tree_node_restore(request: HttpRequest, pk: uuid.UUID) -> HttpResponse:
    """POST /admin/tree/node/<pk>/restore/ — 从回收站恢复（管理员）。"""
    if not is_admin(request.user):  # ty: ignore[unresolved-attribute]
        raise Http404

    node = get_object_or_404(Document, pk=pk, is_deleted=True)
    workspace = node.workspace
    now = timezone.now()
    Document.objects.filter(pk=node.pk).update(is_deleted=False, deleted_at=None, updated_at=now)
    AuditLog.objects.create(  # ty: ignore[unresolved-attribute]
        actor=request.user,  # ty: ignore[unresolved-attribute]
        action=AuditLog.Action.UPDATE,
        target_type=node.node_type,
        target_id=str(node.pk),
        payload={"action": "restore", "title": node.title},
    )
    if workspace is not None:
        return redirect("workspace_trash", workspace_slug=workspace.slug)
    return redirect("admin_dashboard")


@login_required
@require_POST
def tree_node_purge(request: HttpRequest, pk: uuid.UUID) -> HttpResponse:
    """POST /admin/tree/node/<pk>/purge/ — 永久删除（管理员，不可恢复）。"""
    if not is_admin(request.user):  # ty: ignore[unresolved-attribute]
        raise Http404

    node = get_object_or_404(Document, pk=pk, is_deleted=True)
    workspace = node.workspace
    title = node.title
    node_type = node.node_type
    AuditLog.objects.create(  # ty: ignore[unresolved-attribute]
        actor=request.user,  # ty: ignore[unresolved-attribute]
        action=AuditLog.Action.DELETE,
        target_type=node_type,
        target_id=str(pk),
        payload={"action": "purge", "title": title},
    )
    node.delete()
    if workspace is not None:
        return redirect("workspace_trash", workspace_slug=workspace.slug)
    return redirect("admin_dashboard")

import json
import secrets
import uuid

from django.contrib.auth.decorators import login_required
from django.http import HttpRequest, HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.utils.text import slugify
from django.views.decorators.http import require_POST
from django.views.generic import DetailView

from .fts import search_documents
from .models import AuditLog, Document, DocumentVersion, SlugAlias
from .utils import build_nested_tree, build_published_tree, extract_toc


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
            Document,
            slug=slug,
            node_type=Document.NodeType.DOCUMENT,
            status=Document.Status.PUBLISHED,
            is_deleted=False,
        )
        return doc

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        doc: Document = self.object  # type: ignore[assignment]
        version: DocumentVersion | None = (
            doc.versions.filter(is_auto=False).first()  # ty: ignore[unresolved-attribute]
            or doc.versions.first()  # ty: ignore[unresolved-attribute]
        )
        raw_html: str = str(version.html) if version else ""
        is_full_page = bool(version and version.is_full_page)
        if is_full_page:
            content_html, toc_items = raw_html, []
        else:
            content_html, toc_items = extract_toc(raw_html)
        ctx["version"] = version
        ctx["content_html"] = content_html
        ctx["is_full_page"] = is_full_page
        ctx["toc_items"] = toc_items
        ctx["tree_data"] = build_published_tree()
        return ctx


@login_required
def admin_doc_detail(request: HttpRequest, pk: uuid.UUID) -> HttpResponse:
    """管理端文档详情页 /admin/doc/<pk>/，含编辑入口。"""
    doc = get_object_or_404(
        Document,
        pk=pk,
        node_type=Document.NodeType.DOCUMENT,
        is_deleted=False,
    )

    # 优先取最新命名版本，没有就取最新自动版本
    version: DocumentVersion | None = (
        doc.versions.filter(is_auto=False).first()  # type: ignore[unresolved-attribute]
        or doc.versions.first()  # type: ignore[unresolved-attribute]
    )
    content_html = version.html if version else ""
    is_full_page = bool(version and version.is_full_page)

    # 侧边栏目录树
    qs = Document.get_tree().filter(is_deleted=False)
    tree_data = build_nested_tree(qs)

    return render(
        request,
        "admin_ui/doc_detail.html",
        {
            "document": doc,
            "version": version,
            "content_html": content_html,
            "is_full_page": is_full_page,
            "tree_data": tree_data,
        },
    )


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


@login_required
@require_POST
def folder_create(request: HttpRequest) -> HttpResponse:
    """POST /admin/folder/new/ — 创建目录节点，可作为根级或子级。"""
    title = request.POST.get("title", "").strip()[:200] or "未命名文件夹"
    parent_id = request.POST.get("parent_id", "").strip()
    slug = _generate_folder_slug(title)

    if parent_id:
        parent = get_object_or_404(Document, pk=parent_id, is_deleted=False)
        if parent.node_type != Document.NodeType.FOLDER:
            return HttpResponse("只能在文件夹中创建子文件夹", status=400)
        folder = parent.add_child(
            title=title,
            slug=slug,
            node_type=Document.NodeType.FOLDER,
            status=Document.Status.DRAFT,
            owner=request.user,  # ty: ignore[unresolved-attribute]
        )
    else:
        folder = Document.add_root(
            title=title,
            slug=slug,
            node_type=Document.NodeType.FOLDER,
            status=Document.Status.DRAFT,
            owner=request.user,  # ty: ignore[unresolved-attribute]
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

    Document.objects.filter(pk__in=ids).update(is_deleted=True, updated_at=now)
    AuditLog.objects.create(  # ty: ignore[unresolved-attribute]
        actor=request.user,  # ty: ignore[unresolved-attribute]
        action=AuditLog.Action.DELETE,
        target_type=node.node_type,
        target_id=str(node.pk),
        payload={"title": node.title, "descendants": len(descendants)},
    )

    return JsonResponse({"ok": True, "deleted": len(ids), "redirect": "/admin/"})


@login_required
def search_api(request: HttpRequest) -> JsonResponse:
    """GET /admin/search?q=xxx — FTS5 全文搜索，返回分组 JSON。"""
    q = request.GET.get("q", "").strip()
    if not q:
        return JsonResponse({"groups": []})
    result = search_documents(q)
    return JsonResponse(result)

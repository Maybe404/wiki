import json

from django.contrib.auth.decorators import login_required
from django.http import HttpRequest, HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect
from django.views.decorators.http import require_POST
from django.views.generic import DetailView

from .models import Document, DocumentVersion, SlugAlias


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
        ctx["version"] = version
        ctx["content_html"] = version.html if version else ""
        return ctx


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
            # 放在某个兄弟节点之后
            prev = Document.objects.get(pk=prev_sibling_id, is_deleted=False)
            node.move(prev, "right")
        elif new_parent_id:
            # 移入某父节点且作为第一个子节点
            parent = Document.objects.get(pk=new_parent_id, is_deleted=False)
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

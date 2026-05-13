from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, redirect
from django.views.generic import DetailView

from .models import Document, DocumentVersion, SlugAlias


class DocumentDetailView(DetailView):
    """公开阅读页 /d/<slug>/，草稿返回 404，旧 slug 301 跳转。"""

    model = Document
    template_name = "doc/detail.html"
    context_object_name = "document"

    def get(self, request: HttpRequest, *args, **kwargs) -> HttpResponse:
        slug = self.kwargs["slug"]

        # 先检查是否是旧 slug（301 重定向）
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
        # 取最新命名版本，没有则取最新自动版本
        version: DocumentVersion | None = (
            doc.versions.filter(is_auto=False).first()  # ty: ignore[unresolved-attribute]
            or doc.versions.first()  # ty: ignore[unresolved-attribute]
        )
        ctx["version"] = version
        ctx["content_html"] = version.html if version else ""
        return ctx

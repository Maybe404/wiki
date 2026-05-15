from django.http import HttpRequest, HttpResponse, JsonResponse
from django.shortcuts import render

from apps.documents.fts import search_documents
from apps.documents.models import Document
from apps.documents.utils import build_published_tree


def home(request: HttpRequest) -> HttpResponse:
    """公开首页：系统介绍 + 特性展示（非文档列表）。"""
    toc_items = [
        {"id": "intro", "text": "概览"},
        {"id": "why-html", "text": "为什么不是 Markdown"},
        {"id": "showcase", "text": "HTML 能呈现什么"},
        {"id": "workflow", "text": "团队工作流"},
        {"id": "start", "text": "开始阅读"},
    ]
    return render(request, "landing.html", {"toc_items": toc_items})


def docs_index(request: HttpRequest) -> HttpResponse:
    """公开文档索引：左侧目录树、中央最近发布与全部文档。"""
    tree_data = build_published_tree()

    recent = list(
        Document.objects.filter(status=Document.Status.PUBLISHED, is_deleted=False).order_by(
            "-published_at", "-updated_at"
        )[:6]
    )

    all_published = list(
        Document.objects.filter(status=Document.Status.PUBLISHED, is_deleted=False).order_by(
            "-published_at", "-updated_at"
        )
    )

    toc_items = [
        {"id": "recent", "text": "最近发布"},
        {"id": "all", "text": "全部文档"},
    ]

    return render(
        request,
        "docs_index.html",
        {
            "tree_data": tree_data,
            "recent": recent,
            "all_published": all_published,
            "toc_items": toc_items,
            "total_count": len(all_published),
        },
    )


def public_search(request: HttpRequest) -> JsonResponse:
    """公开搜索：未登录只搜已发布；登录后搜全部。"""
    q = request.GET.get("q", "").strip()
    if not q:
        return JsonResponse({"groups": []})

    result = search_documents(q)
    is_auth = request.user.is_authenticated

    filtered_groups = []
    for group in result.get("groups", []):
        items = []
        for item in group.get("items", []):
            status = item.get("status")
            if not is_auth and status != Document.Status.PUBLISHED:
                continue
            new_item = dict(item)
            if status == Document.Status.PUBLISHED:
                slug = _slug_for_doc(item["doc_id"])
                if slug:
                    new_item["url"] = f"/d/{slug}/"
            elif not is_auth:
                continue
            items.append(new_item)
        if items:
            filtered_groups.append({**group, "items": items})

    return JsonResponse({"groups": filtered_groups})


def _slug_for_doc(doc_id: str) -> str | None:
    try:
        return Document.objects.only("slug").get(id=doc_id).slug
    except Document.DoesNotExist:
        return None


def custom_404(request: HttpRequest, exception=None) -> HttpResponse:
    return render(request, "404.html", status=404)

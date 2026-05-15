from django.http import HttpRequest, HttpResponse
from django.shortcuts import render

from apps.documents.models import Document
from apps.documents.utils import build_published_tree


def home(request: HttpRequest) -> HttpResponse:
    """公开首页：左侧目录、中央 hero + 已发布列表、右侧页内 TOC。"""
    tree_data = build_published_tree()

    recent = list(
        Document.objects.filter(
            status=Document.Status.PUBLISHED, is_deleted=False
        ).order_by("-published_at", "-updated_at")[:6]
    )

    all_published = list(
        Document.objects.filter(
            status=Document.Status.PUBLISHED, is_deleted=False
        ).order_by("-published_at", "-updated_at")
    )

    toc_items = [
        {"id": "intro", "text": "概览", "level": 2},
        {"id": "recent", "text": "最近发布", "level": 2},
        {"id": "all", "text": "全部文档", "level": 2},
    ]

    return render(
        request,
        "home.html",
        {
            "tree_data": tree_data,
            "recent": recent,
            "all_published": all_published,
            "toc_items": toc_items,
            "total_count": len(all_published),
        },
    )


def custom_404(request: HttpRequest, exception=None) -> HttpResponse:
    return render(request, "404.html", status=404)

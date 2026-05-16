from django.http import Http404, HttpRequest, HttpResponse, JsonResponse
from django.shortcuts import render

from apps.documents.fts import search_documents
from apps.documents.models import Document
from apps.documents.utils import (
    build_published_tree,
    published_documents_for_user,
    workspace_queryset_for_user,
)
from apps.workspaces.models import Workspace
from apps.workspaces.permissions import can_access_workspace, can_read_document


def home(request: HttpRequest) -> HttpResponse:
    """公开首页：系统介绍 + 完整公开目录。"""
    user = request.user  # ty: ignore[unresolved-attribute]
    toc_items = [
        {"id": "intro", "text": "概览"},
        {"id": "why-html", "text": "为什么不是 Markdown"},
        {"id": "showcase", "text": "HTML 能呈现什么"},
        {"id": "workflow", "text": "团队工作流"},
        {"id": "start", "text": "开始阅读"},
    ]
    return render(
        request,
        "landing.html",
        {
            "toc_items": toc_items,
            "tree_data": build_published_tree(user),
            "public_workspaces": workspace_queryset_for_user(user),
            "current_public_workspace": None,
            "route_name": "home",
        },
    )


def docs_index(request: HttpRequest) -> HttpResponse:
    """公开文档索引：左侧空间目录、中央最近发布与目录总览。"""
    return _render_docs_home(request, route_name="docs_index")


def docs_workspace(request: HttpRequest, workspace_slug: str) -> HttpResponse:
    """公开空间浏览页：按路径进入某个可观看空间。"""
    user = request.user  # ty: ignore[unresolved-attribute]
    workspace = Workspace.objects.filter(slug=workspace_slug, is_deleted=False).first()  # ty: ignore[unresolved-attribute]
    if workspace is None:
        raise Http404
    if not can_access_workspace(user, workspace):
        # 游客不能进入空间本身，但可看到该空间中 link_shared 文档的目录。
        visible_has_docs = published_documents_for_user(user, workspace).exists()
        if not visible_has_docs:
            raise Http404
    return _render_docs_home(request, route_name="docs_workspace", current_workspace=workspace)


def _render_docs_home(
    request: HttpRequest,
    route_name: str,
    current_workspace: Workspace | None = None,
) -> HttpResponse:
    user = request.user  # ty: ignore[unresolved-attribute]
    tree_data = build_published_tree(user, current_workspace)
    readable_docs = published_documents_for_user(user, current_workspace).order_by(
        "-published_at", "-updated_at"
    )

    recent = list(readable_docs[:6])
    all_published = list(readable_docs)
    workspaces = workspace_queryset_for_user(user)

    title = current_workspace.name if current_workspace else "全部已发布文档"
    lead = (
        current_workspace.description
        if current_workspace and current_workspace.description
        else "所有你有权限阅读的内容都收在这里。按空间进入目录，或直接搜索标题与正文。"
    )

    return render(
        request,
        "docs_index.html",
        {
            "tree_data": tree_data,
            "recent": recent,
            "all_published": all_published,
            "total_count": len(all_published),
            "public_workspaces": workspaces,
            "current_public_workspace": current_workspace,
            "route_name": route_name,
            "page_title": title,
            "page_lead": lead,
        },
    )


def public_search(request: HttpRequest) -> JsonResponse:
    """公开搜索：只返回当前用户可阅读的已发布文档。"""
    user = request.user  # ty: ignore[unresolved-attribute]
    q = request.GET.get("q", "").strip()
    if not q:
        return JsonResponse({"groups": []})

    result = search_documents(q)
    filtered_groups = []
    for group in result.get("groups", []):
        items = []
        for item in group.get("items", []):
            status = item.get("status")
            if status != Document.Status.PUBLISHED:
                continue
            doc = _doc_for_search(item["doc_id"])
            if doc is None or not can_read_document(user, doc):
                continue
            new_item = dict(item)
            new_item["url"] = f"/d/{doc.slug}/"
            items.append(new_item)
        if items:
            filtered_groups.append({**group, "items": items})

    return JsonResponse({"groups": filtered_groups})


def _doc_for_search(doc_id: str) -> Document | None:
    try:
        return Document.objects.select_related("workspace", "owner").get(id=doc_id)
    except Document.DoesNotExist:  # ty: ignore[unresolved-attribute]
        return None


def custom_404(request: HttpRequest, exception=None) -> HttpResponse:
    return render(request, "404.html", status=404)

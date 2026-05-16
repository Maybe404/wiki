from __future__ import annotations

import re
import unicodedata

from bs4 import BeautifulSoup
from django.db.models import Q

from apps.workspaces.models import Workspace
from apps.workspaces.permissions import is_admin

from .models import Document


def build_nested_tree(queryset) -> list[dict]:
    """将 treebeard get_tree() 返回的扁平列表转为嵌套 dict 列表。

    每项结构: {'node': Document, 'children': [...]}
    """
    nodes = list(queryset)
    result: list[dict] = []
    stack: list[tuple[int, list]] = []

    for node in nodes:
        depth = node.get_depth()
        item: dict = {"node": node, "children": []}

        while stack and stack[-1][0] >= depth:
            stack.pop()

        if stack:
            stack[-1][1].append(item)
        else:
            result.append(item)

        stack.append((depth, item["children"]))

    return result


def folder_options_for_user(request) -> dict:
    """登录态 admin 页面注入 folder_options（新建/导入选目录用）。"""
    user = getattr(request, "user", None)
    path = getattr(request, "path", "")
    if not user or not user.is_authenticated or not path.startswith("/admin"):
        return {"folder_options": []}
    qs = (
        Document.get_tree()
        .filter(is_deleted=False, node_type=Document.NodeType.FOLDER)
        .select_related("workspace")
        .only("id", "title", "depth", "workspace_id", "workspace__name")
    )
    stack: list[tuple[int, str]] = []
    options = []
    for f in qs:
        while stack and stack[-1][0] >= f.depth:
            stack.pop()
        parts = [title for _, title in stack] + [f.title]
        if f.workspace_id:
            parts.insert(0, f.workspace.name)
        options.append(
            {
                "id": str(f.pk),
                "title": " / ".join(parts),
                "indent": "",
            }
        )
        stack.append((f.depth, f.title))
    return {"folder_options": options}


def workspace_queryset_for_user(user) -> list[Workspace]:
    """Return workspaces the current user may see in navigation."""
    objects = Workspace.objects.filter(is_deleted=False)  # ty: ignore[unresolved-attribute]
    if is_admin(user):
        return list(objects.order_by("name"))
    link_shared_workspace_ids = (
        Document.objects.filter(
            is_deleted=False,
            node_type=Document.NodeType.DOCUMENT,
            status=Document.Status.PUBLISHED,
            visibility=Document.Visibility.LINK_SHARED,
            workspace__isnull=False,
        )
        .values_list("workspace_id", flat=True)
        .distinct()
    )
    if getattr(user, "is_authenticated", False):
        return list(
            objects.filter(Q(members__user=user) | Q(id__in=link_shared_workspace_ids))
            .distinct()
            .order_by("name")
        )
    return list(objects.filter(id__in=link_shared_workspace_ids).order_by("name"))


def published_documents_for_user(user, workspace: Workspace | None = None):
    """Published document queryset filtered by the visibility matrix."""
    qs = Document.objects.filter(
        is_deleted=False,
        node_type=Document.NodeType.DOCUMENT,
        status=Document.Status.PUBLISHED,
    ).select_related("workspace", "owner")
    if workspace is not None:
        qs = qs.filter(workspace=workspace)

    if is_admin(user):
        return qs
    if getattr(user, "is_authenticated", False):
        member_workspace_ids = Workspace.objects.filter(  # ty: ignore[unresolved-attribute]
            members__user=user,
            is_deleted=False,
        ).values_list("id", flat=True)
        return qs.filter(
            Q(visibility=Document.Visibility.LINK_SHARED)
            | Q(visibility=Document.Visibility.WORKSPACE, workspace_id__in=member_workspace_ids)
            | Q(visibility=Document.Visibility.PRIVATE, owner=user)
        )
    return qs.filter(visibility=Document.Visibility.LINK_SHARED)


def build_published_tree(user=None, workspace: Workspace | None = None) -> list[dict]:
    """公开端目录树：只含当前用户可阅读的已发布文档及其可见祖先目录。"""
    visible_docs = published_documents_for_user(user, workspace)
    visible_doc_ids = set(visible_docs.values_list("pk", flat=True))

    all_nodes = (
        Document.get_tree()
        .filter(is_deleted=False)
        .select_related("workspace")
        .only(
            "id",
            "title",
            "slug",
            "node_type",
            "status",
            "path",
            "depth",
            "updated_at",
            "published_at",
            "workspace_id",
        )
    )
    if workspace is not None:
        all_nodes = all_nodes.filter(workspace=workspace)
    elif not is_admin(user):
        workspace_ids = [ws.pk for ws in workspace_queryset_for_user(user)]
        all_nodes = all_nodes.filter(workspace_id__in=workspace_ids)

    def prune(items: list[dict]) -> list[dict]:
        pruned = []
        for item in items:
            node = item["node"]
            children = prune(item.get("children", []))
            is_visible_doc = (
                node.node_type == Document.NodeType.DOCUMENT and node.pk in visible_doc_ids
            )
            if is_visible_doc or children:
                pruned.append({"node": node, "children": children})
        return pruned

    return prune(build_nested_tree(all_nodes))


def build_admin_workspace_tree(user, current_workspace: Workspace | None = None) -> list[dict]:
    """Sidebar tree grouped as 全部空间 / <workspace> / folders and docs."""
    workspaces = workspace_queryset_for_user(user)
    if current_workspace is not None:
        workspaces = [ws for ws in workspaces if ws.pk == current_workspace.pk]

    workspace_items = []
    for ws in workspaces:
        qs = Document.get_tree().filter(workspace=ws, is_deleted=False).select_related("workspace")
        workspace_items.append(
            {
                "kind": "workspace",
                "workspace": ws,
                "children": build_nested_tree(qs),
                "is_active": current_workspace is not None and ws.pk == current_workspace.pk,
            }
        )

    return [
        {
            "kind": "all_workspaces",
            "children": workspace_items,
            "is_active": current_workspace is None,
        }
    ]


# ── TOC 抽取 ───────────────────────────────────────────────────────────────

_SLUG_STRIP = re.compile(r"[^\w一-鿿\-]+", re.UNICODE)


def _slugify_heading(text: str, used: set[str]) -> str:
    """生成稳定的锚点 id，支持中英文，重名追加 -2、-3。"""
    base = unicodedata.normalize("NFKC", text).strip().lower()
    base = base.replace(" ", "-")
    base = _SLUG_STRIP.sub("", base) or "section"
    candidate = base
    i = 2
    while candidate in used:
        candidate = f"{base}-{i}"
        i += 1
    used.add(candidate)
    return candidate


def extract_toc(html: str) -> tuple[str, list[dict]]:
    """从 HTML 抽取 h2/h3 生成 TOC，并给标题补 id 锚点。

    返回 (修改后的 html, [{'level': 2|3, 'id': str, 'text': str}, ...])
    """
    if not html:
        return html, []

    soup = BeautifulSoup(html, "html.parser")
    items: list[dict] = []
    used: set[str] = set()

    for tag in soup.find_all(["h2", "h3"]):
        text = tag.get_text(strip=True)
        if not text:
            continue
        raw_id = tag.get("id")
        existing_id = str(raw_id) if isinstance(raw_id, str) and raw_id else ""
        if existing_id:
            anchor_id = existing_id
            used.add(existing_id)
        else:
            anchor_id = _slugify_heading(text, used)
            tag["id"] = anchor_id
        items.append({"level": int(tag.name[1]), "id": anchor_id, "text": text})

    return str(soup), items

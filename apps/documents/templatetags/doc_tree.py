from django import template
from django.utils import timezone
from django.utils.html import escape, mark_safe

register = template.Library()

# ---------- SVG 图标 ----------

_ICON_EDIT = (
    '<svg width="14" height="14" viewBox="0 0 14 14" fill="none" '
    'stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">'
    '<path d="M9.5 2.5l2 2L4 12H2v-2l7.5-7.5z"/>'
    "</svg>"
)

_ICON_MORE = (
    '<svg width="14" height="14" viewBox="0 0 14 14" fill="currentColor">'
    '<circle cx="7" cy="3.5" r="1.1"/>'
    '<circle cx="7" cy="7" r="1.1"/>'
    '<circle cx="7" cy="10.5" r="1.1"/>'
    "</svg>"
)

_ICON_CHEVRON = (
    '<svg class="toggle-chevron" width="10" height="10" viewBox="0 0 10 10" fill="none" '
    'stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">'
    '<path d="M3 4l2 2 2-2"/>'
    "</svg>"
)

_ICON_FOLDER = (
    '<svg width="14" height="14" viewBox="0 0 14 14" fill="none" '
    'stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">'
    '<path d="M2 4.5V11a1 1 0 0 0 1 1h8a1 1 0 0 0 1-1V5.5'
    'a1 1 0 0 0-1-1H7L5.7 3.2A1 1 0 0 0 5 3H3a1 1 0 0 0-1 1.5z"/>'
    "</svg>"
)


def _render_synthetic_node(item: dict, active_id: str = "") -> str:
    """Render a workspace as a top-level tree node holding its folders and documents."""
    if item.get("kind") != "workspace":
        return ""

    workspace = item["workspace"]
    children: list = item.get("children", [])
    node_id = f"workspace-{escape(str(workspace.pk))}"
    ws_id = escape(str(workspace.pk))
    title = escape(workspace.name)
    url = f"/w/{escape(workspace.slug)}/"
    active_class = " is-active" if item.get("is_active") else ""

    inner = "".join(_render_node(child, active_id) for child in children)

    return (
        f'<li class="tree-node tree-node--folder tree-node--workspace" data-id="{node_id}"'
        f' data-node-type="workspace" data-node-title="{title}">'
        f'<div class="tree-node-row tree-node-row--folder tree-node-row--workspace{active_class}"'
        f' tabindex="0" role="treeitem" aria-label="{title}" data-node-type="workspace"'
        f' data-node-id="{node_id}" data-node-title="{title}" data-doc-url="{url}">'
        f'<button type="button" class="tree-toggle" aria-label="展开/收起">{_ICON_CHEVRON}</button>'
        f'<span class="folder-mark" aria-hidden="true">{_ICON_FOLDER}</span>'
        f'<span class="node-title">{title}</span>'
        f"</div>"
        f'<ul class="tree-children sortable-list" data-parent-id=""'
        f' data-workspace-id="{ws_id}">{inner}</ul>'
        f"</li>"
    )


def _render_node(item: dict, active_id: str = "") -> str:
    node = item["node"]
    children: list = item.get("children", [])
    node_id = escape(str(node.pk))
    status = escape(node.status)
    title = escape(node.title)
    node_type = escape(node.node_type)
    is_folder = node.node_type == node.NodeType.FOLDER

    # 文件夹始终显示展开箭头并渲染子列表（即使为空），以便：
    #   1) 下三角随时可点，符合常理（bug #3）
    #   2) 空文件夹也是合法的拖放目标（bug #4）
    show_toggle = is_folder or bool(children)
    toggle = (
        f'<button type="button" class="tree-toggle" aria-label="展开/收起">{_ICON_CHEVRON}</button>'
        if show_toggle
        else '<span class="tree-toggle-placeholder"></span>'
    )

    children_html = ""
    if is_folder or children:
        inner = "".join(_render_node(c, active_id) for c in children)
        ws_attr = (
            f' data-workspace-id="{escape(str(node.workspace_id))}"' if node.workspace_id else ""
        )
        children_html = (
            f'<ul class="tree-children sortable-list" data-parent-id="{node_id}"'
            f"{ws_attr}>{inner}</ul>"
        )

    row_class = "tree-node-row tree-node-row--folder" if is_folder else "tree-node-row"
    if not is_folder and active_id and node_id == active_id:
        row_class += " is-active"
    doc_url_attr = "" if is_folder else f' data-doc-url="/admin/doc/{node_id}/"'
    leading = (
        f'<span class="folder-mark" aria-hidden="true">{_ICON_FOLDER}</span>'
        if is_folder
        else f'<span class="status-dot status-dot--{status}" title="{status}"></span>'
    )
    edit_button = (
        ""
        if is_folder
        else (
            '<button class="node-action node-action--edit" aria-label="编辑" title="编辑"'
            f' data-doc-url="/admin/doc/{node_id}/">{_ICON_EDIT}</button>'
        )
    )
    return (
        f'<li class="tree-node tree-node--{node_type}" data-id="{node_id}"'
        f' data-node-type="{node_type}" data-node-title="{title}"'
        f' @contextmenu.prevent="ctxMenu.open=true;'
        f" ctxMenu.x=$event.clientX; ctxMenu.y=$event.clientY; ctxMenu.nodeId='{node_id}';"
        f" ctxMenu.nodeTitle='{title}'; ctxMenu.nodeType='{node_type}'\">"
        f'<div class="{row_class}"'
        f' tabindex="0" role="treeitem" aria-label="{title}" data-node-type="{node_type}"'
        f' data-node-id="{node_id}" data-node-title="{title}"'
        f"{doc_url_attr}>"
        f"{toggle}"
        f"{leading}"
        f'<span class="node-title">{title}</span>'
        f'<div class="node-actions">'
        f"{edit_button}"
        f'<button class="node-action node-action--more" aria-label="更多" title="更多"'
        f' data-id="{node_id}" data-node-type="{node_type}" data-node-title="{title}">'
        f"{_ICON_MORE}</button>"
        f"</div>"
        f"</div>"
        f"{children_html}"
        f"</li>"
    )


@register.simple_tag
def render_admin_tree(tree_data: list, active_id: str = "") -> str:
    """渲染文档目录树为嵌套 HTML。顶层是各工作空间节点，工作空间不可拖拽排序。

    active_id 为当前正在查看的文档主键，命中的节点会标记为 is-active。
    """
    active = str(active_id) if active_id else ""
    inner = "".join(
        _render_synthetic_node(item, active) if item.get("kind") else _render_node(item, active)
        for item in tree_data
    )
    return mark_safe(f'<ul class="tree-root" data-parent-id="">{inner}</ul>')


# ---------- 公开端目录树（只读，无操作按钮，无状态点）----------


_ICON_PUB_CHEVRON = (
    '<svg class="pub-tree-chevron" width="10" height="10" viewBox="0 0 10 10" fill="none" '
    'stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" '
    'aria-hidden="true"><path d="M3 4l2 2 2-2"/></svg>'
)


def _render_public_node(item: dict, active_slug: str) -> str:
    node = item["node"]
    children: list = item.get("children", [])
    node_id = escape(str(node.pk))
    title = escape(node.title)
    slug = escape(node.slug)
    is_folder = node.node_type == node.NodeType.FOLDER

    children_html = ""
    if children:
        inner = "".join(_render_public_node(c, active_slug) for c in children)
        children_html = f'<ul class="pub-tree-children">{inner}</ul>'

    toggle = (
        f'<button type="button" class="pub-tree-toggle" aria-label="展开/收起">'
        f"{_ICON_PUB_CHEVRON}</button>"
        if children
        else '<span class="pub-tree-toggle-spacer" aria-hidden="true"></span>'
    )

    if is_folder:
        label = f'<span class="pub-side-link pub-side-link--folder"><span>{title}</span></span>'
    else:
        active = " is-active" if str(node.slug) == active_slug else ""
        label = f'<a class="pub-side-link{active}" href="/d/{slug}/"><span>{title}</span></a>'

    node_class = "pub-tree-node pub-tree-node--folder" if is_folder else "pub-tree-node"
    return (
        f'<li class="{node_class}" data-id="{node_id}">'
        f'<div class="pub-tree-row">{toggle}{label}</div>'
        f"{children_html}"
        f"</li>"
    )


def _render_public_workspace(item: dict, active_slug: str) -> str:
    workspace = item["workspace"]
    children: list = item.get("children", [])
    node_id = f"ws-{escape(str(workspace.pk))}"
    title = escape(workspace.name)
    inner = "".join(_render_public_node(c, active_slug) for c in children)
    return (
        f'<li class="pub-tree-node pub-tree-node--folder pub-tree-node--space" data-id="{node_id}">'
        f'<div class="pub-tree-row">'
        f'<button type="button" class="pub-tree-toggle" aria-label="展开/收起">'
        f"{_ICON_PUB_CHEVRON}</button>"
        f'<span class="pub-side-link pub-side-link--folder pub-side-link--space">'
        f"<span>{title}</span></span>"
        f"</div>"
        f'<ul class="pub-tree-children">{inner}</ul>'
        f"</li>"
    )


@register.simple_tag
def render_public_tree(tree_data: list, active_slug: str = "") -> str:
    """渲染公开端目录树。支持「空间 → 文件夹 → 文档」层级，可折叠，只读无编辑入口。"""
    inner = "".join(
        _render_public_workspace(item, active_slug)
        if item.get("kind") == "workspace"
        else _render_public_node(item, active_slug)
        for item in tree_data
    )
    return mark_safe(f'<ul class="pub-tree-root">{inner}</ul>')


@register.simple_tag
def render_public_workspace_nav(workspaces: list, current_workspace=None) -> str:
    """渲染公开端可访问空间导航。"""
    rows = []
    for ws in workspaces:
        active = (
            " is-active"
            if current_workspace is not None and str(ws.pk) == str(current_workspace.pk)
            else ""
        )
        rows.append(
            f'<li class="pub-tree-node">'
            f'<a class="pub-side-link{active}" href="/docs/{escape(ws.slug)}/">'
            f"<span>{escape(ws.name)}</span>"
            f"</a>"
            f"</li>"
        )
    return mark_safe(f'<ul class="pub-tree-root pub-tree-root--spaces">{"".join(rows)}</ul>')


def _format_public_date(node) -> str:
    dt = node.published_at or node.updated_at
    if not dt:
        return ""
    return timezone.localtime(dt).strftime("%Y-%m-%d")


def _render_public_catalog_node(item: dict, index: int) -> str:
    node = item["node"]
    children: list = item.get("children", [])
    title = escape(node.title)
    slug = escape(node.slug)
    is_folder = node.node_type == node.NodeType.FOLDER
    date_label = escape(_format_public_date(node))
    number = f"{index:02d}"

    children_html = ""
    if children:
        inner = "".join(
            _render_public_catalog_node(child, i) for i, child in enumerate(children, 1)
        )
        children_html = f'<ol class="pub-catalog-children">{inner}</ol>'

    meta = (
        f'<span class="pub-catalog-meta">发布于 {date_label}</span>'
        if date_label and not is_folder
        else ""
    )
    child_count = f'<span class="pub-catalog-count">{len(children)} 项</span>' if children else ""
    tag = "div" if is_folder else "a"
    href = "" if is_folder else f' href="/d/{slug}/"'
    folder_class = " pub-catalog-link--folder" if is_folder else ""

    return (
        '<li class="pub-catalog-node">'
        f'<{tag} class="pub-catalog-link{folder_class}"{href}>'
        f'<span class="pub-catalog-index">{number}</span>'
        '<span class="pub-catalog-copy">'
        f'<span class="pub-catalog-title">{title}</span>'
        f'<span class="pub-catalog-row">{meta}{child_count}</span>'
        "</span>"
        f"</{tag}>"
        f"{children_html}"
        "</li>"
    )


@register.simple_tag
def render_public_catalog(tree_data: list) -> str:
    """渲染公开文档库主目录。比侧栏更适合浏览，保留文档层级。"""
    inner = "".join(
        _render_public_catalog_node(item, index) for index, item in enumerate(tree_data, 1)
    )
    return mark_safe(f'<ol class="pub-catalog-list">{inner}</ol>')

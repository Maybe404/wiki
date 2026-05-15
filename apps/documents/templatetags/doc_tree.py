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

_ICON_LINK = (
    '<svg width="14" height="14" viewBox="0 0 14 14" fill="none" '
    'stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">'
    '<path d="M5.5 8.5a3 3 0 0 0 4.2.3l1.3-1.3a3 3 0 0 0-4.2-4.2l-.8.7"/>'
    '<path d="M8.5 5.5a3 3 0 0 0-4.2-.3L3 6.5a3 3 0 0 0 4.2 4.2l.8-.7"/>'
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


def _render_node(item: dict) -> str:
    node = item["node"]
    children: list = item.get("children", [])
    node_id = escape(str(node.pk))
    status = escape(node.status)
    title = escape(node.title)
    slug = escape(node.slug)
    node_type = escape(node.node_type)
    is_folder = node.node_type == node.NodeType.FOLDER

    toggle = (
        f'<button class="tree-toggle" aria-label="展开/收起">{_ICON_CHEVRON}</button>'
        if children
        else '<span class="tree-toggle-placeholder"></span>'
    )

    children_html = ""
    if children:
        inner = "".join(_render_node(c) for c in children)
        children_html = (
            f'<ul class="tree-children sortable-list" data-parent-id="{node_id}">{inner}</ul>'
        )

    row_class = "tree-node-row tree-node-row--folder" if is_folder else "tree-node-row"
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
    copy_button = (
        ""
        if is_folder
        else (
            '<button class="node-action node-action--copy" aria-label="复制链接" title="复制链接"'
            f' data-slug="{slug}">{_ICON_LINK}</button>'
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
        f"{copy_button}"
        f'<button class="node-action node-action--more" aria-label="更多" title="更多"'
        f' data-id="{node_id}" data-node-type="{node_type}" data-node-title="{title}">'
        f"{_ICON_MORE}</button>"
        f"</div>"
        f"</div>"
        f"{children_html}"
        f"</li>"
    )


@register.simple_tag
def render_admin_tree(tree_data: list) -> str:
    """渲染文档目录树为嵌套 HTML。接收 build_nested_tree() 的返回值。"""
    inner = "".join(_render_node(item) for item in tree_data)
    return mark_safe(f'<ul class="tree-root sortable-list" data-parent-id="">{inner}</ul>')


# ---------- 公开端目录树（只读，无操作按钮，无状态点）----------


def _render_public_node(item: dict, active_slug: str) -> str:
    node = item["node"]
    children: list = item.get("children", [])
    title = escape(node.title)
    slug = escape(node.slug)
    is_active = " is-active" if str(node.slug) == active_slug else ""

    children_html = ""
    if children:
        inner = "".join(_render_public_node(c, active_slug) for c in children)
        children_html = f'<ul class="pub-tree-children">{inner}</ul>'

    return (
        f'<li class="pub-tree-node">'
        f'<a class="pub-side-link{is_active}" href="/d/{slug}/">'
        f"<span>{title}</span>"
        f"</a>"
        f"{children_html}"
        f"</li>"
    )


@register.simple_tag
def render_public_tree(tree_data: list, active_slug: str = "") -> str:
    """渲染公开端目录树为嵌套 HTML。只列已发布文档，无任何编辑入口。"""
    inner = "".join(_render_public_node(item, active_slug) for item in tree_data)
    return mark_safe(f'<ul class="pub-tree-root">{inner}</ul>')


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
    date_label = escape(_format_public_date(node))
    number = f"{index:02d}"

    children_html = ""
    if children:
        inner = "".join(
            _render_public_catalog_node(child, i) for i, child in enumerate(children, 1)
        )
        children_html = f'<ol class="pub-catalog-children">{inner}</ol>'

    meta = f'<span class="pub-catalog-meta">发布于 {date_label}</span>' if date_label else ""
    child_count = (
        f'<span class="pub-catalog-count">{len(children)} 个子文档</span>' if children else ""
    )

    return (
        '<li class="pub-catalog-node">'
        f'<a class="pub-catalog-link" href="/d/{slug}/">'
        f'<span class="pub-catalog-index">{number}</span>'
        '<span class="pub-catalog-copy">'
        f'<span class="pub-catalog-title">{title}</span>'
        f'<span class="pub-catalog-row">{meta}{child_count}</span>'
        "</span>"
        "</a>"
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

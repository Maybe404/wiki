from django import template
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


def _render_node(item: dict) -> str:
    node = item["node"]
    children: list = item.get("children", [])
    node_id = escape(str(node.pk))
    status = escape(node.status)
    title = escape(node.title)
    slug = escape(node.slug)

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

    return (
        f'<li class="tree-node" data-id="{node_id}"'
        f' @contextmenu.prevent="ctxMenu.open=true;'
        f" ctxMenu.x=$event.clientX; ctxMenu.y=$event.clientY; ctxMenu.nodeId='{node_id}'\">"
        f'<div class="tree-node-row" tabindex="0" role="treeitem" aria-label="{title}"'
        f' data-doc-url="/admin/doc/{node_id}/">'
        f"{toggle}"
        f'<span class="status-dot status-dot--{status}" title="{status}"></span>'
        f'<span class="node-title">{title}</span>'
        f'<div class="node-actions">'
        f'<button class="node-action" aria-label="编辑" title="编辑"'
        f' data-id="{node_id}">{_ICON_EDIT}</button>'
        f'<button class="node-action node-action--copy" aria-label="复制链接" title="复制链接"'
        f' data-slug="{slug}">{_ICON_LINK}</button>'
        f'<button class="node-action" aria-label="更多" title="更多"'
        f' data-id="{node_id}">{_ICON_MORE}</button>'
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

"""HTML 清洗：行内编辑专用白名单，比导入时的白名单更严。"""

import bleach

# 行内编辑只允许加粗、斜体、链接——其他结构标签由 AI 模板决定，编辑者不能改。
_ALLOWED_TAGS: list[str] = ["strong", "em", "a"]
_ALLOWED_ATTRS: dict[str, list[str]] = {
    "a": ["href", "rel", "title"],
}
_ALLOWED_PROTOCOLS: list[str] = ["http", "https", "mailto"]


def sanitize_inline(html: str) -> str:
    """清洗行内 HTML：只保留 <strong>、<em>、<a href>，剥离其余标签（保留文本）。"""
    return bleach.clean(
        html,
        tags=_ALLOWED_TAGS,
        attributes=_ALLOWED_ATTRS,
        protocols=_ALLOWED_PROTOCOLS,
        strip=True,
    )

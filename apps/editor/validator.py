"""HTML 导入校验器与清洗器。

流程：
1. validate_import_html(html) → (errors, cleaned_html, editable_blocks)
2. 有错误 → cleaned_html 和 editable_blocks 为空，不应继续入库
3. 无错误 → cleaned_html 经过 bleach 清洗，editable_blocks 是 {id: inner_html}
"""

from __future__ import annotations

import re
from dataclasses import dataclass

import bleach
from bs4 import BeautifulSoup, Tag

# ── Import-level bleach whitelist (wider than inline editing) ─────────────────

IMPORT_ALLOWED_TAGS: list[str] = [
    "h1",
    "h2",
    "h3",
    "h4",
    "p",
    "br",
    "strong",
    "em",
    "a",
    "ul",
    "ol",
    "li",
    "blockquote",
    "code",
    "pre",
    "div",
    "span",
    "section",
    "article",
    "table",
    "thead",
    "tbody",
    "tr",
    "th",
    "td",
    "img",
]

IMPORT_ALLOWED_ATTRS: dict[str, list[str]] = {
    "*": ["class", "id", "data-editable", "data-editable-id"],
    "a": ["href", "title", "rel"],
    "img": ["src", "alt", "width", "height"],
}

IMPORT_ALLOWED_PROTOCOLS: list[str] = ["http", "https", "mailto"]

# 禁止的 class 中不做白名单限制（AI 可使用系统 class），只禁止危险属性和标签


@dataclass
class ValidationError:
    line: int | None
    reason: str
    suggestion: str


def _get_line(tag: Tag) -> int | None:
    """BeautifulSoup html.parser 为每个 Tag 附加 sourceline（1-based）。"""
    v = getattr(tag, "sourceline", None)
    return int(v) if v is not None else None


def validate_import_html(
    raw_html: str,
) -> tuple[list[ValidationError], str, dict[str, str]]:
    """校验并清洗导入 HTML。

    有任何 error → cleaned_html = ""，editable_blocks = {}。
    全部通过 → 执行 bleach 清洗，提取 editable_blocks。
    """
    errors: list[ValidationError] = []

    html = _unwrap_body(raw_html)
    soup = BeautifulSoup(html, "html.parser")

    # ── 1. 禁止标签 ────────────────────────────────────────────────────────────
    for tag_name in ("script", "iframe", "style", "object", "embed"):
        for tag in soup.find_all(tag_name):
            if not isinstance(tag, Tag):
                continue
            errors.append(
                ValidationError(
                    line=_get_line(tag),
                    reason=f"禁止使用 <{tag_name}> 标签",
                    suggestion=f"删除所有 <{tag_name}> 标签及其内容",
                )
            )

    # ── 2. 禁止 <link> 标签（外部 CSS / 字体） ─────────────────────────────────
    for tag in soup.find_all("link"):
        if not isinstance(tag, Tag):
            continue
        errors.append(
            ValidationError(
                line=_get_line(tag),
                reason="禁止使用 <link> 标签引入外部资源",
                suggestion="删除所有 <link> 标签；系统样式由页面框架统一提供，无需外部引入",
            )
        )

    # ── 3. 禁止内联 style 属性 ─────────────────────────────────────────────────
    for tag in soup.find_all(True):
        if not isinstance(tag, Tag):
            continue
        if tag.get("style"):
            style_preview = str(tag["style"])[:50]
            errors.append(
                ValidationError(
                    line=_get_line(tag),
                    reason=f'<{tag.name}> 含有内联 style 属性（"{style_preview}…"）',
                    suggestion="删除 style 属性；使用系统提供的 class 控制样式",
                )
            )

    # ── 4. 禁止 on* 事件属性 ───────────────────────────────────────────────────
    _ON_ATTR_RE = re.compile(r"^on[a-z]+$")
    for tag in soup.find_all(True):
        if not isinstance(tag, Tag):
            continue
        for attr in list(tag.attrs.keys()):
            if _ON_ATTR_RE.match(attr.lower()):
                errors.append(
                    ValidationError(
                        line=_get_line(tag),
                        reason=f"<{tag.name}> 含有事件属性 {attr}",
                        suggestion=f"删除 {attr} 属性；系统不允许内联事件处理器",
                    )
                )

    # ── 5. 禁止 javascript: 协议（href / src / action） ───────────────────────
    _JS_PROTO_RE = re.compile(r"javascript\s*:", re.IGNORECASE)
    for attr_name in ("href", "src", "action"):
        for tag in soup.find_all(attrs={attr_name: True}):
            if not isinstance(tag, Tag):
                continue
            val = str(tag.get(attr_name, ""))
            if _JS_PROTO_RE.match(val):
                errors.append(
                    ValidationError(
                        line=_get_line(tag),
                        reason=f"<{tag.name}> 的 {attr_name} 使用了 javascript: 协议",
                        suggestion=(
                            f"将 {attr_name} 改为合法的 http:// 或 https:// 链接，或删除该属性"
                        ),
                    )
                )

    # ── 6. 必须有 data-editable 区域 ──────────────────────────────────────────
    editable_tags = [
        t for t in soup.find_all(attrs={"data-editable": "true"}) if isinstance(t, Tag)
    ]
    if not editable_tags:
        errors.append(
            ValidationError(
                line=None,
                reason='HTML 中没有找到任何 data-editable="true" 元素',
                suggestion=(
                    '在需要编辑的文字区域添加 data-editable="true" 和唯一的 data-editable-id 属性，'
                    '例如：<p data-editable="true" data-editable-id="para-1">内容</p>'
                ),
            )
        )
    else:
        # ── 7. 每个 data-editable 元素必须有唯一 data-editable-id ──────────────
        seen_ids: set[str] = set()
        for tag in editable_tags:
            eid = str(tag.get("data-editable-id", "")).strip()
            if not eid:
                errors.append(
                    ValidationError(
                        line=_get_line(tag),
                        reason=f'<{tag.name} data-editable="true"> 缺少 data-editable-id 属性',
                        suggestion='添加唯一标识符，例如 data-editable-id="section-1-body"',
                    )
                )
            elif eid in seen_ids:
                errors.append(
                    ValidationError(
                        line=_get_line(tag),
                        reason=f'data-editable-id="{eid}" 重复（前面已出现过）',
                        suggestion=f'将此元素的 data-editable-id 改为一个唯一值，例如 "{eid}-2"',
                    )
                )
            else:
                seen_ids.add(eid)

    if errors:
        return errors, "", {}

    # ── 无错误：bleach 清洗 ────────────────────────────────────────────────────
    cleaned = bleach.clean(
        html,
        tags=IMPORT_ALLOWED_TAGS,
        attributes=IMPORT_ALLOWED_ATTRS,
        protocols=IMPORT_ALLOWED_PROTOCOLS,
        strip=True,
    )

    editable_blocks = _extract_editable_blocks(cleaned)
    return [], cleaned, editable_blocks


def _unwrap_body(html: str) -> str:
    """如果输入是完整 HTML 文档，提取 <body> 内容；否则原样返回。"""
    stripped = html.strip().lower()
    if "<html" in stripped or "<body" in stripped:
        soup = BeautifulSoup(html, "html.parser")
        body = soup.find("body")
        if isinstance(body, Tag):
            return body.decode_contents()
    return html


def _extract_editable_blocks(cleaned_html: str) -> dict[str, str]:
    """从清洗后的 HTML 中提取所有 data-editable 区域的 inner HTML。"""
    soup = BeautifulSoup(cleaned_html, "html.parser")
    blocks: dict[str, str] = {}
    for tag in soup.find_all(attrs={"data-editable": "true"}):
        if not isinstance(tag, Tag):
            continue
        eid = str(tag.get("data-editable-id", "")).strip()
        if eid:
            blocks[eid] = tag.decode_contents()
    return blocks


def extract_title(html: str) -> str:
    """从 HTML 中提取第一个标题元素的文本，作为文档标题建议。"""
    soup = BeautifulSoup(html, "html.parser")
    for tag_name in ("h1", "h2", "h3"):
        tag = soup.find(tag_name)
        if isinstance(tag, Tag):
            text = tag.get_text(strip=True)
            if text:
                return text[:200]
    return ""

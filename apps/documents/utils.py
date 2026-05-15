from __future__ import annotations

import re
import unicodedata

from bs4 import BeautifulSoup

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


def build_published_tree() -> list[dict]:
    """公开端目录树：只含已发布且未软删除的节点。

    若已发布节点的祖先为草稿/归档，节点会被提升为根级（弱化层级而不丢节点）。
    """
    qs = (
        Document.get_tree()
        .filter(status=Document.Status.PUBLISHED, is_deleted=False)
        .only("id", "title", "slug", "status", "path", "depth")
    )
    return build_nested_tree(qs)


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

"""FTS5 同步工具：在文档版本保存后更新 plain_text 字段。"""

import logging
import re
import uuid as _uuid

from bs4 import BeautifulSoup
from django.db import connection

logger = logging.getLogger(__name__)


def _strip_tags(html: str) -> str:
    return BeautifulSoup(html, "html.parser").get_text(" ", strip=True)


def _escape_fts_query(q: str) -> str:
    """转义 FTS5 查询字符串，用双引号包围做短语搜索。"""
    # 去除控制字符，把双引号转义为两个双引号
    q = re.sub(r"[\x00-\x1f]", " ", q)
    q = q.replace('"', '""')
    return f'"{q}"'


def update_fts_for_document(doc_rowid: int, plain_text: str) -> None:
    """更新指定文档的 FTS plain_text（应用层维护，触发器只同步 title）。"""
    try:
        with connection.cursor() as cur:
            cur.execute(
                "UPDATE documents_fts SET plain_text = %s WHERE rowid = %s",
                [plain_text, doc_rowid],
            )
    except Exception:
        logger.exception("FTS update failed for doc rowid=%s", doc_rowid)


def get_document_rowid(doc_id: str) -> int | None:
    """通过 UUID id 查询 documents_document 表的 SQLite rowid。

    Django 将 UUID 以无连字符格式存入 SQLite，需先去除连字符再查询。
    """
    doc_id_clean = str(doc_id).replace("-", "")
    with connection.cursor() as cur:
        cur.execute("SELECT rowid FROM documents_document WHERE id = %s", [doc_id_clean])
        row = cur.fetchone()
    return int(row[0]) if row else None


def sync_fts_plain_text(doc_id: str, html: str) -> None:
    """从 html 提取纯文本并同步到 FTS5 表。供版本保存/还原时调用。"""
    rowid = get_document_rowid(str(doc_id))
    if rowid is None:
        logger.warning("sync_fts_plain_text: doc %s not found", doc_id)
        return
    plain_text = _strip_tags(html)
    update_fts_for_document(rowid, plain_text)


def _search_by_like(q: str, limit: int = 10) -> dict:
    """短查询（< 3字符）时降级为标题 LIKE 搜索。"""
    pattern = f"%{q}%"
    with connection.cursor() as cur:
        cur.execute(
            """
            SELECT id, title, slug, status
            FROM documents_document
            WHERE title LIKE %s AND is_deleted = 0
              AND node_type = 'document'
            ORDER BY updated_at DESC
            LIMIT %s
            """,
            [pattern, limit],
        )
        items = [
            {
                "doc_id": str(_uuid.UUID(str(row[0]))),
                "title": row[1],
                "snippet": row[1],
                "url": f"/admin/doc/{_uuid.UUID(str(row[0]))}/",
                "status": row[3],
            }
            for row in cur.fetchall()
        ]
    if not items:
        return {"groups": []}
    return {"groups": [{"type": "title", "label": "标题匹配", "items": items}]}


def search_documents(q: str, limit: int = 20) -> dict:
    """执行 FTS5 搜索，返回分组结果 {groups: [{type, items}]}。

    items 格式：{doc_id, title, snippet, url, status}
    snippet 含 <mark> 高亮标签，来自 FTS5 snippet()。
    """
    q = q.strip()
    if len(q) < 1:
        return {"groups": []}

    # trigram 最少需要 3 个字符；短查询降级为 LIKE
    if len(q) < 3:
        return _search_by_like(q, limit=10)

    escaped = _escape_fts_query(q)

    title_items: list[dict] = []
    body_items: list[dict] = []
    title_ids: set[str] = set()

    title_match_expr = f"title: {escaped}"
    body_match_expr = f"plain_text: {escaped}"
    title_limit = limit // 2 + 5

    with connection.cursor() as cur:
        # 标题匹配
        cur.execute(
            """
            SELECT
                d.id,
                snippet(documents_fts, 0, '<mark>', '</mark>', '…', 12) AS snip,
                d.title,
                d.slug,
                d.status
            FROM documents_fts
            JOIN documents_document d ON documents_fts.rowid = d.rowid
            WHERE documents_fts MATCH %s
              AND d.is_deleted = 0
              AND d.node_type = 'document'
            ORDER BY rank
            LIMIT %s
            """,
            [title_match_expr, title_limit],
        )
        for row in cur.fetchall():
            doc_id_raw, snip, title, slug, status = row
            doc_id = str(_uuid.UUID(str(doc_id_raw)))
            title_items.append(
                {
                    "doc_id": doc_id,
                    "title": title,
                    "snippet": snip or title,
                    "url": f"/admin/doc/{doc_id}/",
                    "status": status,
                }
            )
            title_ids.add(doc_id)

        # 正文匹配（排除已在标题匹配中的文档）
        cur.execute(
            """
            SELECT
                d.id,
                snippet(documents_fts, 1, '<mark>', '</mark>', '…', 24) AS snip,
                d.title,
                d.slug,
                d.status
            FROM documents_fts
            JOIN documents_document d ON documents_fts.rowid = d.rowid
            WHERE documents_fts MATCH %s
              AND d.is_deleted = 0
              AND d.node_type = 'document'
            ORDER BY rank
            LIMIT %s
            """,
            [body_match_expr, limit],
        )
        for row in cur.fetchall():
            doc_id_raw, snip, title, slug, status = row
            doc_id = str(_uuid.UUID(str(doc_id_raw)))
            if doc_id in title_ids:
                continue
            body_items.append(
                {
                    "doc_id": doc_id,
                    "title": title,
                    "snippet": snip or "",
                    "url": f"/admin/doc/{doc_id}/",
                    "status": status,
                }
            )

    groups = []
    if title_items:
        groups.append({"type": "title", "label": "标题匹配", "items": title_items})
    if body_items:
        groups.append({"type": "body", "label": "正文匹配", "items": body_items[:10]})

    return {"groups": groups}

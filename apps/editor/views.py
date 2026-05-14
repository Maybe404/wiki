import json
import logging
import uuid

from bs4 import BeautifulSoup, Tag
from django.contrib.auth.decorators import login_required
from django.http import HttpRequest, JsonResponse
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.views.decorators.http import require_POST

from apps.documents.models import AuditLog, Document, DocumentVersion

from .sanitizer import sanitize_inline

logger = logging.getLogger(__name__)

_AUTO_SAVE_KEEP = 5  # 自动版本最多保留条数


def _reconstruct_html(base_html: str, editable_blocks: dict[str, str]) -> str:
    """将前端提交的 editable_blocks 合并回原 HTML 模板。

    用 BeautifulSoup 定位各 data-editable-id 元素，替换其 innerHTML，
    其余 DOM 结构保持原样。
    """
    # 用已知根 div 包裹，避免 BS4 自动补全 html/head/body 标签
    wrapped = f'<div id="__root__">{base_html}</div>'
    soup = BeautifulSoup(wrapped, "html.parser")
    root = soup.find("div", id="__root__")

    if not isinstance(root, Tag):
        return base_html

    for editable_id, new_content in editable_blocks.items():
        el = root.find(attrs={"data-editable-id": editable_id})
        if not isinstance(el, Tag):
            logger.warning("save_document: editable-id '%s' not found in base HTML", editable_id)
            continue

        clean = sanitize_inline(new_content)
        el.clear()
        # 将 clean HTML 解析为片段再移入，避免 BS4 树节点归属问题
        fragment_soup = BeautifulSoup(f"<x>{clean}</x>", "html.parser")
        fragment = fragment_soup.find("x")
        if isinstance(fragment, Tag):
            for child in list(fragment.children):
                el.append(child)

    return root.decode_contents()  # innerHTML of __root__，去掉包装 div


@login_required
@require_POST
def save_document(request: HttpRequest, pk: uuid.UUID) -> JsonResponse:
    """POST /admin/doc/<pk>/save/ — 接收 editable_blocks，重组 HTML，写入新版本。"""
    doc = get_object_or_404(Document, pk=pk, is_deleted=False)

    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({"error": "invalid JSON"}, status=400)

    editable_blocks: dict[str, str] = data.get("editable_blocks", {})
    note: str = str(data.get("note", ""))[:200]
    is_auto: bool = bool(data.get("is_auto", False))

    if not isinstance(editable_blocks, dict):
        return JsonResponse({"error": "editable_blocks must be an object"}, status=400)

    # 基础 HTML 取最新版本（不区分 is_auto）
    latest: DocumentVersion | None = doc.versions.first()
    if latest is None:
        return JsonResponse({"error": "no base version found"}, status=400)

    new_html = _reconstruct_html(str(latest.html), editable_blocks)

    # 自动版本数量管控：超出上限的旧自动版本先删掉
    if is_auto:
        old_auto_ids = list(
            doc.versions.filter(is_auto=True)
            .order_by("-created_at")
            .values_list("pk", flat=True)[_AUTO_SAVE_KEEP:]
        )
        if old_auto_ids:
            DocumentVersion.objects.filter(pk__in=old_auto_ids).delete()  # ty: ignore[unresolved-attribute]

    version = DocumentVersion.objects.create(  # ty: ignore[unresolved-attribute]
        document=doc,
        html=new_html,
        editable_blocks=editable_blocks,
        author=request.user,  # ty: ignore[unresolved-attribute]
        is_auto=is_auto,
        note=note,
    )

    # 更新文档 updated_at
    Document.objects.filter(pk=doc.pk).update(updated_at=timezone.now())

    AuditLog.objects.create(  # ty: ignore[unresolved-attribute]
        actor=request.user,  # ty: ignore[unresolved-attribute]
        action=AuditLog.Action.UPDATE,
        target_type="document",
        target_id=str(doc.pk),
        payload={"version_id": str(version.pk), "is_auto": is_auto, "note": note},
    )

    logger.info(
        "Document %s saved (is_auto=%s, blocks=%d, user=%s), bleach applied",
        doc.pk,
        is_auto,
        len(editable_blocks),
        request.user.username,  # ty: ignore[unresolved-attribute]
    )

    saved_at = timezone.localtime(version.created_at).strftime("%H:%M")
    return JsonResponse({"ok": True, "saved_at": saved_at, "version_id": str(version.pk)})

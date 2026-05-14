import html as _html
import json
import logging
import secrets
import uuid
from typing import cast

from bs4 import BeautifulSoup, Tag
from diff_match_patch import diff_match_patch
from django.contrib.auth.decorators import login_required
from django.http import HttpRequest, HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.utils.text import slugify
from django.views.decorators.http import require_POST

from apps.documents.models import AuditLog, Document, DocumentVersion
from apps.documents.utils import build_nested_tree

from .sanitizer import sanitize_inline
from .validator import ValidationError, extract_title, validate_import_html

logger = logging.getLogger(__name__)

_AUTO_SAVE_KEEP = 5  # 自动版本最多保留条数
_dmp = diff_match_patch()


# ── HTML 注入工具 ─────────────────────────────────────────────────────────────


def _inject_html_blocks(
    base_html: str,
    blocks: dict[str, str],
    *,
    sanitize: bool = True,
    warn_missing: bool = True,
) -> str:
    """将 blocks 注入 base_html 中对应的 data-editable-id 元素。

    sanitize=True 时对内容执行 sanitize_inline（用户输入路径，必须开启）。
    sanitize=False 仅限内部调用：调用方必须保证 blocks 中每段文本已经过
    html.escape()，绝对不可将用户直接提交的内容以 sanitize=False 注入。
    """
    wrapped = f'<div id="__root__">{base_html}</div>'
    soup = BeautifulSoup(wrapped, "html.parser")
    root = soup.find("div", id="__root__")
    if not isinstance(root, Tag):
        return base_html

    for bid, content in blocks.items():
        el = root.find(attrs={"data-editable-id": bid})
        if not isinstance(el, Tag):
            if warn_missing:
                logger.warning("save_document: editable-id '%s' not found in base HTML", bid)
            continue

        clean = sanitize_inline(content) if sanitize else content
        el.clear()
        frag_soup = BeautifulSoup(f"<x>{clean}</x>", "html.parser")
        frag = frag_soup.find("x")
        if isinstance(frag, Tag):
            for child in list(frag.children):
                el.append(child)

    return root.decode_contents()


def _reconstruct_html(base_html: str, editable_blocks: dict[str, str]) -> str:
    """将前端提交的 editable_blocks 合并回原 HTML 模板（内容经 bleach 清洗）。"""
    return _inject_html_blocks(base_html, editable_blocks)


# ── Diff 工具（版本对比用，内容经 html.escape 而非 bleach）──────────────────


def _strip_tags(html_str: str) -> str:
    """提取 HTML 中的纯文本。"""
    return BeautifulSoup(html_str, "html.parser").get_text()


def _compute_char_delta(old_text: str, new_text: str) -> tuple[int, int]:
    """返回 (chars_added, chars_removed)，基于 diff-match-patch 字符级对比。"""
    diffs = _dmp.diff_main(old_text, new_text)
    added = sum(len(t) for op, t in diffs if op == diff_match_patch.DIFF_INSERT)
    removed = sum(len(t) for op, t in diffs if op == diff_match_patch.DIFF_DELETE)
    return added, removed


def _patch_html_raw(base_html: str, patches: dict[str, str]) -> str:
    """将预渲染的 diff span HTML 注入对应 editable-id 元素（不经 bleach）。"""
    return _inject_html_blocks(base_html, patches, sanitize=False, warn_missing=False)


def _compute_diff_columns(
    current_ver: DocumentVersion,
    historical_ver: DocumentVersion,
) -> tuple[str, str]:
    """计算左右双栏 diff HTML。

    左栏 = 当前版本，新增文字标绿；右栏 = 历史版本，删除文字标红+删除线。
    对 editable_blocks 中每个块做字符级 diff；无 blocks 时降级为整体纯文本对比。
    """
    curr_blocks = cast(dict[str, str], current_ver.editable_blocks or {})
    hist_blocks = cast(dict[str, str], historical_ver.editable_blocks or {})

    left_patches: dict[str, str] = {}
    right_patches: dict[str, str] = {}

    for bid in set(curr_blocks) | set(hist_blocks):
        curr_text = _strip_tags(curr_blocks.get(bid, ""))
        hist_text = _strip_tags(hist_blocks.get(bid, ""))

        diffs = _dmp.diff_main(hist_text, curr_text)
        _dmp.diff_cleanupSemantic(diffs)

        left_parts: list[str] = []
        right_parts: list[str] = []

        for op, text in diffs:
            esc = _html.escape(text)
            if op == diff_match_patch.DIFF_EQUAL:
                left_parts.append(esc)
                right_parts.append(esc)
            elif op == diff_match_patch.DIFF_INSERT:
                left_parts.append(f'<span class="diff-add">{esc}</span>')
            elif op == diff_match_patch.DIFF_DELETE:
                right_parts.append(f'<span class="diff-del">{esc}</span>')

        left_patches[bid] = "".join(left_parts)
        right_patches[bid] = "".join(right_parts)

    left_html = _patch_html_raw(str(current_ver.html), left_patches)
    right_html = _patch_html_raw(str(historical_ver.html), right_patches)
    return left_html, right_html


# ── 视图 ─────────────────────────────────────────────────────────────────────


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

    latest: DocumentVersion | None = doc.versions.first()
    if latest is None:
        return JsonResponse({"error": "no base version found"}, status=400)

    new_html = _reconstruct_html(str(latest.html), editable_blocks)

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


@login_required
def version_list_api(request: HttpRequest, pk: uuid.UUID) -> JsonResponse:
    """GET /admin/doc/<pk>/versions/ → JSON 版本列表（含 +X/-Y 字符增减）。"""
    doc = get_object_or_404(Document, pk=pk, is_deleted=False)
    versions = list(doc.versions.select_related("author").order_by("-created_at"))

    result = []
    for i, v in enumerate(versions):
        prev = versions[i + 1] if i + 1 < len(versions) else None
        if prev and v.html and prev.html:
            added, removed = _compute_char_delta(
                _strip_tags(str(prev.html)), _strip_tags(str(v.html))
            )
        else:
            added, removed = 0, 0

        author = v.author
        author_name: str = (author.get_full_name() or author.get_username()) if author else "—"
        local_dt = timezone.localtime(v.created_at)

        result.append(
            {
                "id": str(v.pk),
                "is_auto": v.is_auto,
                "note": v.note,
                "author": author_name,
                "created_at": local_dt.strftime("%Y-%m-%d %H:%M"),
                "created_at_time": local_dt.strftime("%H:%M"),
                "added": added,
                "removed": removed,
            }
        )

    return JsonResponse({"versions": result})


@login_required
def version_diff_api(request: HttpRequest, pk: uuid.UUID, vid: int) -> JsonResponse:
    """GET /admin/doc/<pk>/versions/<vid>/diff/ → JSON {left_html, right_html}。"""
    doc = get_object_or_404(Document, pk=pk, is_deleted=False)
    historical = get_object_or_404(DocumentVersion, pk=vid, document=doc)

    current: DocumentVersion | None = (
        doc.versions.filter(is_auto=False).first() or doc.versions.first()
    )
    if current is None:
        return JsonResponse({"error": "no current version"}, status=400)

    local_dt = timezone.localtime(historical.created_at).strftime("%Y-%m-%d %H:%M")
    shared = {
        "version_note": historical.note or "手动保存",
        "version_date": local_dt,
        "version_id": str(historical.pk),
    }

    if str(current.pk) == str(vid):
        return JsonResponse(
            {
                **shared,
                "left_html": str(current.html),
                "right_html": str(historical.html),
                "is_same": True,
            }
        )

    left_html, right_html = _compute_diff_columns(current, historical)
    return JsonResponse(
        {
            **shared,
            "left_html": left_html,
            "right_html": right_html,
            "is_same": False,
        }
    )


@login_required
@require_POST
def version_restore(request: HttpRequest, pk: uuid.UUID, vid: int) -> JsonResponse:
    """POST /admin/doc/<pk>/versions/<vid>/restore/ → 基于历史版本创建新版本。"""
    doc = get_object_or_404(Document, pk=pk, is_deleted=False)
    historical = get_object_or_404(DocumentVersion, pk=vid, document=doc)

    local_dt = timezone.localtime(historical.created_at).strftime("%Y-%m-%d %H:%M")
    new_version = DocumentVersion.objects.create(  # ty: ignore[unresolved-attribute]
        document=doc,
        html=historical.html,
        editable_blocks=historical.editable_blocks,
        author=request.user,  # ty: ignore[unresolved-attribute]
        is_auto=False,
        note=f"还原自 {local_dt}",
    )

    AuditLog.objects.create(  # ty: ignore[unresolved-attribute]
        actor=request.user,  # ty: ignore[unresolved-attribute]
        action=AuditLog.Action.RESTORE,
        target_type="document",
        target_id=str(doc.pk),
        payload={
            "restored_from_version": str(vid),
            "new_version": str(new_version.pk),
        },
    )

    username = request.user.get_username()  # ty: ignore[unresolved-attribute]
    logger.info("Document %s restored from version %s by %s", doc.pk, vid, username)

    saved_at = timezone.localtime(new_version.created_at).strftime("%H:%M")
    return JsonResponse({"ok": True, "new_version_id": str(new_version.pk), "saved_at": saved_at})


# ── HTML 导入 ─────────────────────────────────────────────────────────────────


def _generate_unique_slug(title: str) -> str:
    """从标题生成带随机后缀的唯一 slug。"""
    base = slugify(title, allow_unicode=True)[:40] or "doc"
    for _ in range(10):
        candidate = f"{base}-{secrets.token_hex(3)}"
        if not Document.objects.filter(slug=candidate, is_deleted=False).exists():
            return candidate
    return f"doc-{secrets.token_hex(6)}"


@login_required
def import_document_page(request: HttpRequest) -> HttpResponse:
    """GET /admin/import/ — 显示 AI HTML 导入页面。"""
    qs = Document.get_tree().filter(is_deleted=False)
    tree_data = build_nested_tree(qs)
    return render(request, "admin_ui/import.html", {"tree_data": tree_data})


@login_required
@require_POST
def import_validate(request: HttpRequest) -> HttpResponse:
    """POST /admin/import/validate/ (HTMX) — 校验 HTML，返回错误列表或预览片段。"""
    raw_html: str = request.POST.get("raw_html", "").strip()

    if not raw_html:
        empty_error = ValidationError(
            line=None,
            reason="请粘贴 HTML 内容",
            suggestion="将 AI 生成的 HTML 粘贴到文本框后再点击解析",
        )
        return render(
            request,
            "admin_ui/import_result.html",
            {
                "errors": [empty_error],
                "cleaned_html": "",
                "editable_blocks": {},
                "raw_html": raw_html,
                "suggested_title": "",
                "suggested_slug": "",
            },
        )

    errors, cleaned_html, editable_blocks = validate_import_html(raw_html)

    suggested_title = ""
    suggested_slug = ""
    if not errors:
        suggested_title = extract_title(cleaned_html)
        suggested_slug = _generate_unique_slug(suggested_title)

    return render(
        request,
        "admin_ui/import_result.html",
        {
            "errors": errors,
            "cleaned_html": cleaned_html,
            "editable_blocks": editable_blocks,
            "raw_html": raw_html,
            "suggested_title": suggested_title,
            "suggested_slug": suggested_slug,
        },
    )


@login_required
@require_POST
def import_confirm(request: HttpRequest) -> HttpResponse:
    """POST /admin/import/confirm/ — 服务端再校验，入库，跳转到文档详情页。"""
    raw_html: str = request.POST.get("raw_html", "").strip()
    title: str = request.POST.get("title", "").strip()[:200] or "未命名文档"
    slug: str = request.POST.get("slug", "").strip()

    if not raw_html:
        return redirect("admin_import")

    # 服务端再次校验（幂等安全兜底，不信任前端）
    errors, cleaned_html, editable_blocks = validate_import_html(raw_html)

    if errors:
        qs = Document.get_tree().filter(is_deleted=False)
        tree_data = build_nested_tree(qs)
        return render(
            request,
            "admin_ui/import.html",
            {
                "tree_data": tree_data,
                "page_error": "HTML 内容校验失败，请重新粘贴并解析。",
            },
        )

    slug = slugify(slug, allow_unicode=True)[:60]
    if not slug or Document.objects.filter(slug=slug, is_deleted=False).exists():
        slug = _generate_unique_slug(title)

    doc = Document.add_root(
        title=title,
        slug=slug,
        status=Document.Status.DRAFT,
        owner=request.user,  # ty: ignore[unresolved-attribute]
    )

    DocumentVersion.objects.create(  # ty: ignore[unresolved-attribute]
        document=doc,
        html=cleaned_html,
        editable_blocks=editable_blocks,
        author=request.user,  # ty: ignore[unresolved-attribute]
        is_auto=False,
        note="从 HTML 导入",
    )

    AuditLog.objects.create(  # ty: ignore[unresolved-attribute]
        actor=request.user,  # ty: ignore[unresolved-attribute]
        action=AuditLog.Action.CREATE,
        target_type="document",
        target_id=str(doc.pk),
        payload={"source": "html_import", "slug": slug, "title": title},
    )

    username = request.user.get_username()  # ty: ignore[unresolved-attribute]
    logger.info("Document %s created via HTML import by %s (slug=%s)", doc.pk, username, slug)

    return redirect("admin_doc_detail", pk=doc.pk)

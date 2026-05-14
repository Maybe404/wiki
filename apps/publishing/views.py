import json
import logging
import re
import uuid

from django.contrib.auth.decorators import login_required
from django.http import HttpRequest, JsonResponse
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.views.decorators.http import require_POST

from apps.documents.models import AuditLog, Document, DocumentVersion, SlugAlias

logger = logging.getLogger(__name__)

# Unicode word chars + hyphen — consistent with Django's validate_unicode_slug
_SLUG_RE = re.compile(r"^[-\w]+$")


def _validate_slug(slug: str, exclude_pk: uuid.UUID) -> str | None:
    """slug 合法性校验，返回错误消息或 None（通过）。"""
    if not slug:
        return "slug 不能为空"
    if not _SLUG_RE.match(slug):
        return "slug 只能包含字母、数字、连字符和下划线"
    if Document.objects.filter(slug=slug, is_deleted=False).exclude(pk=exclude_pk).exists():
        return f'slug "{slug}" 已被其他文档占用'
    # 防止与其他文档的历史别名冲突（会导致 301 路由劫持）
    if SlugAlias.objects.exclude(document__pk=exclude_pk).filter(old_slug=slug).exists():  # ty: ignore[unresolved-attribute]
        return f'slug "{slug}" 已作为其他文档的历史别名，无法使用'
    return None


@login_required
@require_POST
def publish_document(request: HttpRequest, pk: uuid.UUID) -> JsonResponse:
    """POST /admin/doc/<pk>/publish/ — 发布文档，支持同时更改 slug。"""
    doc = get_object_or_404(Document, pk=pk, is_deleted=False)

    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({"error": "invalid JSON"}, status=400)

    new_slug: str = str(data.get("slug", doc.slug)).strip()

    error = _validate_slug(new_slug, exclude_pk=doc.pk)
    if error:
        return JsonResponse({"error": error}, status=400)

    if not doc.versions.exists():
        return JsonResponse({"error": "文档尚无内容，请先添加版本后再发布"}, status=400)

    old_slug = str(doc.slug)
    now = timezone.now()

    # slug 变更：将旧 slug 写入别名表，确保旧链接 301 跳转
    if new_slug != old_slug:
        # 若新 slug 恰好已是本文档的旧别名（如改回去），先删除避免自身循环
        SlugAlias.objects.filter(old_slug=new_slug, document=doc).delete()  # ty: ignore[unresolved-attribute]
        SlugAlias.objects.get_or_create(  # ty: ignore[unresolved-attribute]
            old_slug=old_slug,
            defaults={"document": doc},
        )

    published_at = doc.published_at if doc.published_at else now

    # 使用 .update() 绕过 treebeard 的 save() 覆盖，精确更新字段
    Document.objects.filter(pk=doc.pk).update(
        status=Document.Status.PUBLISHED,
        slug=new_slug,
        published_at=published_at,
        updated_at=now,
    )

    # 重新取 doc 以获取最新版本（slug 已变，但 pk 不变）
    latest: DocumentVersion = doc.versions.first()  # type: ignore[assignment]

    DocumentVersion.objects.create(  # ty: ignore[unresolved-attribute]
        document=doc,
        html=latest.html,
        editable_blocks=latest.editable_blocks,
        author=request.user,  # ty: ignore[unresolved-attribute]
        is_auto=False,
        note=f"发布于 {now.strftime('%Y-%m-%d')}",
    )

    AuditLog.objects.create(  # ty: ignore[unresolved-attribute]
        actor=request.user,  # ty: ignore[unresolved-attribute]
        action=AuditLog.Action.PUBLISH,
        target_type="document",
        target_id=str(doc.pk),
        payload={"new_slug": new_slug, "old_slug": old_slug},
    )

    username = request.user.get_username()  # ty: ignore[unresolved-attribute]
    logger.info("Document %s published as /d/%s/ by %s", doc.pk, new_slug, username)

    return JsonResponse({"ok": True, "public_url": f"/d/{new_slug}/"})


@login_required
@require_POST
def unpublish_document(request: HttpRequest, pk: uuid.UUID) -> JsonResponse:
    """POST /admin/doc/<pk>/unpublish/ — 撤回发布，状态回到 draft，published_at 保留。"""
    doc = get_object_or_404(Document, pk=pk, is_deleted=False)

    if doc.status != Document.Status.PUBLISHED:
        return JsonResponse({"error": "文档当前未发布"}, status=400)

    now = timezone.now()
    Document.objects.filter(pk=doc.pk).update(
        status=Document.Status.DRAFT,
        updated_at=now,
    )

    AuditLog.objects.create(  # ty: ignore[unresolved-attribute]
        actor=request.user,  # ty: ignore[unresolved-attribute]
        action=AuditLog.Action.UNPUBLISH,
        target_type="document",
        target_id=str(doc.pk),
        payload={"slug": str(doc.slug)},
    )

    username = request.user.get_username()  # ty: ignore[unresolved-attribute]
    logger.info("Document %s unpublished by %s", doc.pk, username)

    return JsonResponse({"ok": True})

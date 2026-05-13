import uuid

from django.contrib.auth import get_user_model
from django.db import models
from treebeard.mp_tree import MP_Node

User = get_user_model()


class Document(MP_Node):
    """一篇文档的元信息，使用 MP_Node 实现树形结构。"""

    class Status(models.TextChoices):
        DRAFT = "draft", "草稿"
        PUBLISHED = "published", "已发布"
        ARCHIVED = "archived", "已归档"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=200, verbose_name="标题")
    slug = models.SlugField(unique=True, allow_unicode=True, verbose_name="Slug")
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.DRAFT,
        verbose_name="状态",
    )
    owner = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name="documents",
        verbose_name="所有者",
    )
    is_deleted = models.BooleanField(default=False, verbose_name="软删除")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="更新时间")
    published_at = models.DateTimeField(null=True, blank=True, verbose_name="发布时间")

    # treebeard 要求的排序字段名
    node_order_by = ["title"]

    class Meta:
        verbose_name = "文档"
        verbose_name_plural = "文档"

    def __str__(self) -> str:
        return str(self.title)


class DocumentVersion(models.Model):
    """每次保存形成一条版本记录。"""

    document = models.ForeignKey(
        Document,
        on_delete=models.CASCADE,
        related_name="versions",
        verbose_name="文档",
    )
    html = models.TextField(verbose_name="HTML 内容")
    editable_blocks = models.JSONField(default=dict, verbose_name="可编辑区块")
    author = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name="document_versions",
        verbose_name="作者",
    )
    is_auto = models.BooleanField(default=False, verbose_name="自动保存")
    note = models.CharField(max_length=200, blank=True, verbose_name="版本说明")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")

    class Meta:
        verbose_name = "文档版本"
        verbose_name_plural = "文档版本"
        ordering = ["-created_at"]

    def __str__(self) -> str:
        kind = "自动" if self.is_auto else "命名"
        doc_title = str(self.document.title)  # ty: ignore[unresolved-attribute]
        return f"{doc_title} [{kind}] {self.created_at:%Y-%m-%d %H:%M}"


class SlugAlias(models.Model):
    """slug 改名时的 301 跳转映射。"""

    old_slug = models.SlugField(unique=True, allow_unicode=True, verbose_name="旧 Slug")
    document = models.ForeignKey(
        Document,
        on_delete=models.CASCADE,
        related_name="slug_aliases",
        verbose_name="文档",
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")

    class Meta:
        verbose_name = "Slug 别名"
        verbose_name_plural = "Slug 别名"

    def __str__(self) -> str:
        doc_slug = str(self.document.slug)  # ty: ignore[unresolved-attribute]
        return f"{self.old_slug} → {doc_slug}"


class AuditLog(models.Model):
    """操作审计日志：谁、何时、对什么做了什么。"""

    class Action(models.TextChoices):
        CREATE = "create", "创建"
        UPDATE = "update", "更新"
        PUBLISH = "publish", "发布"
        UNPUBLISH = "unpublish", "撤回"
        DELETE = "delete", "删除"
        RESTORE = "restore", "还原版本"

    actor = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name="audit_logs",
        verbose_name="操作人",
    )
    action = models.CharField(max_length=40, choices=Action.choices, verbose_name="操作")
    target_type = models.CharField(max_length=40, verbose_name="目标类型")
    target_id = models.CharField(max_length=64, verbose_name="目标 ID")
    payload = models.JSONField(default=dict, verbose_name="详情")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="操作时间")

    class Meta:
        verbose_name = "审计日志"
        verbose_name_plural = "审计日志"
        ordering = ["-created_at"]

    def __str__(self) -> str:
        action_display = self.get_action_display()  # ty: ignore[unresolved-attribute]
        return f"{self.actor} {action_display} {self.target_type}#{self.target_id}"

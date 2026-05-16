import uuid

from django.contrib.auth import get_user_model
from django.db import models

User = get_user_model()


class Workspace(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100, verbose_name="名称")
    slug = models.SlugField(max_length=60, unique=True, allow_unicode=True, verbose_name="Slug")
    description = models.TextField(blank=True, verbose_name="描述")
    created_by = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name="created_workspaces",
        verbose_name="创建人",
    )
    is_deleted = models.BooleanField(default=False, verbose_name="软删除")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="更新时间")

    class Meta:
        verbose_name = "工作空间"
        verbose_name_plural = "工作空间"

    def __str__(self) -> str:
        return str(self.name)


class WorkspaceMember(models.Model):
    workspace = models.ForeignKey(
        Workspace,
        on_delete=models.CASCADE,
        related_name="members",
        verbose_name="工作空间",
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="workspace_memberships",
        verbose_name="用户",
    )
    can_edit = models.BooleanField(default=True, verbose_name="可编辑")
    joined_at = models.DateTimeField(auto_now_add=True, verbose_name="加入时间")

    class Meta:
        verbose_name = "工作空间成员"
        verbose_name_plural = "工作空间成员"
        constraints = [
            models.UniqueConstraint(
                fields=["workspace", "user"],
                name="unique_workspace_member",
            )
        ]

    def __str__(self) -> str:
        return f"{self.user} @ {self.workspace}"

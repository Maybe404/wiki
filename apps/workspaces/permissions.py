"""权限检查工具。

规则（来自执行计划 §2.2 + §7）：
  - 管理员：is_superuser 或 is_staff → 隐式拥有全部 workspace 权限
  - 成员：存在 WorkspaceMember 记录的登录用户
  - 游客：未登录，仅能访问 link_shared 已发布文档

None workspace：不允许非管理员访问（fail-close）。
"""

from __future__ import annotations

from django.http import Http404

from apps.documents.models import Document

from .models import Workspace, WorkspaceMember


def is_admin(user: object) -> bool:
    return bool(
        getattr(user, "is_authenticated", False)
        and (getattr(user, "is_superuser", False) or getattr(user, "is_staff", False))
    )


def is_workspace_member(user: object, workspace: Workspace) -> bool:
    if not getattr(user, "is_authenticated", False):
        return False
    return WorkspaceMember.objects.filter(workspace=workspace, user=user).exists()  # ty: ignore[unresolved-attribute]


def can_access_workspace(user: object, workspace: Workspace | None) -> bool:
    """用户是否有权进入此 workspace（管理员或成员）。"""
    if workspace is None:
        return is_admin(user)
    return is_admin(user) or is_workspace_member(user, workspace)


def can_read_document(user: object, doc: Document) -> bool:
    """用户是否能阅读此文档（visibility 矩阵）。

    文档必须已是 status=PUBLISHED 且 is_deleted=False；此函数只判断 visibility。
    """
    if doc.visibility == Document.Visibility.LINK_SHARED:
        return True

    if not getattr(user, "is_authenticated", False):
        return False

    if is_admin(user):
        return True

    if doc.visibility == Document.Visibility.WORKSPACE:
        if doc.workspace_id is None:  # ty: ignore[unresolved-attribute]
            return False  # 无 workspace 的文档对非管理员不可见
        return is_workspace_member(user, doc.workspace)  # ty: ignore[invalid-argument-type]

    if doc.visibility == Document.Visibility.PRIVATE:
        return doc.owner_id == getattr(user, "pk", None)  # ty: ignore[unresolved-attribute]

    return False


def can_view_doc_in_admin(user: object, doc: Document) -> bool:
    """后台文档详情：管理员或所在 workspace 成员可访问（含草稿）。"""
    if is_admin(user):
        return True
    if not getattr(user, "is_authenticated", False):
        return False
    return can_access_workspace(user, doc.workspace)  # ty: ignore[invalid-argument-type]


def require_workspace_access(user: object, workspace: Workspace) -> None:
    """若用户无权访问 workspace，raise Http404（不泄露存在性）。"""
    if not can_access_workspace(user, workspace):
        raise Http404

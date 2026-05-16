"""模板上下文处理器：向后台页面注入空间列表，供侧边栏空间切换器使用。"""

from .models import Workspace
from .permissions import is_admin


def sidebar_workspaces(request) -> dict:
    """注入 `sidebar_workspaces`：当前用户可访问的工作空间列表。"""
    user = getattr(request, "user", None)
    path = getattr(request, "path", "")
    if (
        not user
        or not user.is_authenticated
        or not (path.startswith("/admin") or path.startswith("/w/"))
    ):
        return {"sidebar_workspaces": []}

    objects = Workspace.objects  # ty: ignore[unresolved-attribute]
    if is_admin(user):
        qs = objects.filter(is_deleted=False)
    else:
        qs = objects.filter(is_deleted=False, members__user=user)
    return {"sidebar_workspaces": list(qs.order_by("name"))}

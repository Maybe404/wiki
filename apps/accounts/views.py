from axes.handlers.proxy import AxesProxyHandler
from django.contrib import messages
from django.contrib.auth import authenticate, get_user_model, login
from django.contrib.auth import logout as auth_logout
from django.contrib.auth.decorators import login_required
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import require_POST

from apps.documents.utils import build_admin_workspace_tree
from apps.workspaces.models import Workspace, WorkspaceMember
from apps.workspaces.permissions import is_admin

from .forms import LoginForm

User = get_user_model()


def _safe_next(request) -> str:
    next_url = request.GET.get("next") or "/admin/"
    if url_has_allowed_host_and_scheme(next_url, allowed_hosts={request.get_host()}):
        return next_url
    return "/admin/"


def login_view(request):
    if request.user.is_authenticated:
        return redirect("admin_dashboard")

    error: str | None = None
    form = LoginForm()

    if request.method == "POST":
        form = LoginForm(request.POST)
        if form.is_valid():
            credentials = {
                "username": form.cleaned_data["username"],
                "password": form.cleaned_data["password"],
            }
            if AxesProxyHandler.is_locked(request, credentials):
                error = "登录尝试次数过多，请 15 分钟后再试。"
            else:
                user = authenticate(request, **credentials)
                if user is not None:
                    login(request, user)
                    return redirect(_safe_next(request))
                else:
                    if AxesProxyHandler.is_locked(request, credentials):
                        error = "登录尝试次数过多，请 15 分钟后再试。"
                    else:
                        error = "账号或密码错误，请重试。"

    return render(request, "accounts/login.html", {"form": form, "error": error})


def logout_view(request):
    auth_logout(request)
    return redirect("login")


@login_required
def admin_dashboard(request):
    tree_data = build_admin_workspace_tree(request.user)

    if is_admin(request.user):
        workspaces = Workspace.objects.filter(is_deleted=False).order_by("name")  # ty: ignore[unresolved-attribute]
    else:
        workspaces = Workspace.objects.filter(  # ty: ignore[unresolved-attribute]
            is_deleted=False,
            members__user=request.user,
        ).order_by("name")

    return render(
        request,
        "admin_ui/dashboard.html",
        {"tree_data": tree_data, "workspaces": workspaces},
    )


# ── 用户管理（仅管理员）────────────────────────────────────────────────────


def _require_admin(request) -> None:
    if not is_admin(request.user):
        raise Http404


@login_required
def user_list(request):
    """GET /admin/users/ — 用户与空间成员管理页（仅管理员）。"""
    _require_admin(request)

    users = list(User.objects.order_by("-is_superuser", "-is_staff", "username"))
    memberships = WorkspaceMember.objects.select_related("workspace", "user")  # ty: ignore[unresolved-attribute]
    by_user: dict[int, list] = {}
    for m in memberships:
        by_user.setdefault(m.user_id, []).append(m)

    rows = []
    for u in users:
        if u.is_superuser:
            role = "超级管理员"
        elif u.is_staff:
            role = "管理员"
        else:
            role = "成员"
        rows.append({"user": u, "role": role, "memberships": by_user.get(u.id, [])})

    workspaces = Workspace.objects.filter(is_deleted=False).order_by("name")  # ty: ignore[unresolved-attribute]
    return render(
        request,
        "admin_ui/users.html",
        {"rows": rows, "workspaces": workspaces, "tree_data": []},
    )


@login_required
@require_POST
def user_create(request):
    """POST /admin/users/new/ — 新建用户。"""
    _require_admin(request)

    username = request.POST.get("username", "").strip()
    password = request.POST.get("password", "")
    if not username or not password:
        messages.error(request, "用户名和密码不能为空。")
        return redirect("user_list")
    if User.objects.filter(username=username).exists():
        messages.error(request, f"用户名「{username}」已存在。")
        return redirect("user_list")

    user = User.objects.create_user(username=username, password=password)
    user.is_staff = request.POST.get("is_staff") == "on"
    user.save(update_fields=["is_staff"])
    messages.success(request, f"用户「{username}」已创建。")
    return redirect("user_list")


@login_required
@require_POST
def user_update(request, pk: int):
    """POST /admin/users/<pk>/update/ — 用户操作（启停/管理员/改密/成员）。"""
    _require_admin(request)

    target = get_object_or_404(User, pk=pk)
    action = request.POST.get("action", "")

    if action == "toggle_active":
        if target.pk == request.user.pk:
            messages.error(request, "不能停用自己的账号。")
        else:
            target.is_active = not target.is_active
            target.save(update_fields=["is_active"])
            messages.success(
                request, f"用户「{target.username}」已{'启用' if target.is_active else '停用'}。"
            )
    elif action == "toggle_staff":
        if target.pk == request.user.pk:
            messages.error(request, "不能修改自己的管理员权限。")
        elif target.is_superuser:
            messages.error(request, "超级管理员权限请在 Django admin 调整。")
        else:
            target.is_staff = not target.is_staff
            target.save(update_fields=["is_staff"])
            messages.success(request, f"用户「{target.username}」管理员权限已更新。")
    elif action == "set_password":
        password = request.POST.get("password", "")
        if not password:
            messages.error(request, "新密码不能为空。")
        else:
            target.set_password(password)
            target.save(update_fields=["password"])
            messages.success(request, f"用户「{target.username}」密码已重置。")
    elif action == "add_member":
        ws = get_object_or_404(Workspace, pk=request.POST.get("workspace_id"), is_deleted=False)
        WorkspaceMember.objects.update_or_create(  # ty: ignore[unresolved-attribute]
            workspace=ws,
            user=target,
            defaults={"can_edit": request.POST.get("can_edit") == "on"},
        )
        messages.success(request, f"已将「{target.username}」加入空间「{ws.name}」。")
    elif action == "remove_member":
        WorkspaceMember.objects.filter(  # ty: ignore[unresolved-attribute]
            user=target, workspace_id=request.POST.get("workspace_id")
        ).delete()
        messages.success(request, f"已将「{target.username}」移出该空间。")
    else:
        messages.error(request, "未知操作。")

    return redirect("user_list")

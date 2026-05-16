from axes.handlers.proxy import AxesProxyHandler
from django.contrib.auth import authenticate, login
from django.contrib.auth import logout as auth_logout
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render
from django.utils.http import url_has_allowed_host_and_scheme

from apps.documents.models import Document
from apps.documents.utils import build_nested_tree
from apps.workspaces.models import Workspace
from apps.workspaces.permissions import is_admin

from .forms import LoginForm


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
    qs = Document.get_tree().filter(is_deleted=False)
    tree_data = build_nested_tree(qs)

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

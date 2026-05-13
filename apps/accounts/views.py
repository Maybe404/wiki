from axes.handlers.proxy import AxesProxyHandler
from django.contrib.auth import authenticate, login
from django.contrib.auth import logout as auth_logout
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render
from django.utils.http import url_has_allowed_host_and_scheme

from .forms import LoginForm


def _safe_next(request) -> str:
    """校验 next 参数，防止开放重定向——只接受同源相对路径。"""
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
            # 先检查是否已被锁定（axes 双重检查，防止暴破）
            if AxesProxyHandler.is_locked(request, credentials):
                error = "登录尝试次数过多，请 15 分钟后再试。"
            else:
                user = authenticate(request, **credentials)
                if user is not None:
                    login(request, user)
                    return redirect(_safe_next(request))
                else:
                    # 验证失败后再查一次，区分"密码错"和"刚到达锁定阈值"
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
    return render(request, "admin_ui/dashboard.html")

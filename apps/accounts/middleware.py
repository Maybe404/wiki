from django.conf import settings
from django.shortcuts import redirect


class AdminLoginRequiredMiddleware:
    """粗筛：/admin/* 路径未登录时跳 /login，视图层仍有 @login_required 二次校验。"""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.path.startswith("/admin/") and not request.user.is_authenticated:
            return redirect(f"{settings.LOGIN_URL}?next={request.path}")
        return self.get_response(request)

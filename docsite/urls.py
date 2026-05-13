from django.contrib import admin
from django.urls import include, path

from apps.core import views

urlpatterns = [
    path("", views.home, name="home"),
    # Django 内置 admin 挪到非冲突路径
    path("django-admin/", admin.site.urls),
    # 鉴权：/login、/logout、/admin/
    path("", include("apps.accounts.urls")),
]

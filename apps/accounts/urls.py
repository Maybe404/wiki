from django.urls import path

from . import views

urlpatterns = [
    path("login", views.login_view, name="login"),
    path("logout", views.logout_view, name="logout"),
    path("admin/", views.admin_dashboard, name="admin_dashboard"),
    path("admin/users/", views.user_list, name="user_list"),
    path("admin/users/new/", views.user_create, name="user_create"),
    path("admin/users/<int:pk>/update/", views.user_update, name="user_update"),
]

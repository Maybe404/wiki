from django.urls import path

from .views import (
    skill_activate,
    skill_download_current,
    skill_download_version,
    skill_list,
    skill_upload,
)

urlpatterns = [
    path("skill/current.md", skill_download_current, name="skill_download_current"),
    path("skill/<str:version>.md", skill_download_version, name="skill_download_version"),
    path("admin/skills/", skill_list, name="skill_list"),
    path("admin/skills/upload/", skill_upload, name="skill_upload"),
    path("admin/skills/<int:pk>/activate/", skill_activate, name="skill_activate"),
]

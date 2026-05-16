from __future__ import annotations

from django.contrib.auth.decorators import login_required
from django.http import Http404, HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from apps.workspaces.permissions import is_admin

from .models import SkillVersion


def _markdown_response(sv: SkillVersion) -> HttpResponse:
    response = HttpResponse(sv.content, content_type="text/markdown; charset=utf-8")
    response["Content-Disposition"] = f'attachment; filename="skill-{sv.version}.md"'
    return response


def skill_download_current(request: HttpRequest) -> HttpResponse:
    """GET /skill/current.md — 公开下载当前激活 skill（无需登录）。"""
    sv = SkillVersion.objects.filter(is_active=True).first()  # ty: ignore[unresolved-attribute]
    if sv is None:
        raise Http404
    return _markdown_response(sv)


def skill_download_version(request: HttpRequest, version: str) -> HttpResponse:
    """GET /skill/<version>.md — 公开下载指定版本。"""
    sv = get_object_or_404(SkillVersion, version=version)
    return _markdown_response(sv)


@login_required
def skill_list(request: HttpRequest) -> HttpResponse:
    """GET /admin/skills/ — 管理员查看所有 skill 版本。"""
    if not is_admin(request.user):  # ty: ignore[unresolved-attribute]
        raise Http404
    versions = SkillVersion.objects.all()  # ty: ignore[unresolved-attribute]
    return render(request, "skills/skill_list.html", {"versions": versions})


@login_required
@require_POST
def skill_upload(request: HttpRequest) -> HttpResponse:
    """POST /admin/skills/upload/ — 上传新版本 skill。"""
    if not is_admin(request.user):  # ty: ignore[unresolved-attribute]
        raise Http404

    version = request.POST.get("version", "").strip()
    notes = request.POST.get("notes", "").strip()
    content = ""

    uploaded_file = request.FILES.get("skill_file")
    if uploaded_file:
        content = uploaded_file.read().decode("utf-8", errors="replace")
    else:
        content = request.POST.get("content", "").strip()

    errors = []
    if not version:
        errors.append("版本号不能为空")
    if SkillVersion.objects.filter(version=version).exists():  # ty: ignore[unresolved-attribute]
        errors.append(f"版本 {version} 已存在")
    if not content:
        errors.append("内容不能为空")

    if errors:
        versions = SkillVersion.objects.all()  # ty: ignore[unresolved-attribute]
        return render(
            request,
            "skills/skill_list.html",
            {"versions": versions, "errors": errors, "form_version": version, "form_notes": notes},
            status=400,
        )

    SkillVersion.objects.create(  # ty: ignore[unresolved-attribute]
        version=version,
        content=content,
        notes=notes,
        is_active=False,
        created_by=request.user,  # ty: ignore[unresolved-attribute]
    )
    return redirect("skill_list")


@login_required
@require_POST
def skill_activate(request: HttpRequest, pk: int) -> HttpResponse:
    """POST /admin/skills/<pk>/activate/ — 激活某个历史版本。"""
    if not is_admin(request.user):  # ty: ignore[unresolved-attribute]
        raise Http404

    sv = get_object_or_404(SkillVersion, pk=pk)
    SkillVersion.objects.filter(is_active=True).update(is_active=False)  # ty: ignore[unresolved-attribute]
    sv.is_active = True
    sv.save(update_fields=["is_active"])
    return redirect("skill_list")

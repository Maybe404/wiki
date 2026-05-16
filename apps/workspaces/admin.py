from django.contrib import admin

from .models import Workspace, WorkspaceMember


class WorkspaceMemberInline(admin.TabularInline):
    model = WorkspaceMember
    extra = 0
    fields = ("user", "can_edit", "joined_at")
    readonly_fields = ("joined_at",)


@admin.register(Workspace)
class WorkspaceAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "created_by", "is_deleted", "created_at")
    list_filter = ("is_deleted",)
    search_fields = ("name", "slug")
    readonly_fields = ("id", "created_at", "updated_at")
    inlines = [WorkspaceMemberInline]


@admin.register(WorkspaceMember)
class WorkspaceMemberAdmin(admin.ModelAdmin):
    list_display = ("user", "workspace", "can_edit", "joined_at")
    list_filter = ("can_edit", "workspace")
    search_fields = ("user__username", "workspace__name")

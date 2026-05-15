from django.contrib import admin
from treebeard.admin import TreeAdmin
from treebeard.forms import movenodeform_factory

from .models import AuditLog, Document, DocumentVersion, SlugAlias


@admin.register(Document)
class DocumentAdmin(TreeAdmin):
    form = movenodeform_factory(Document)
    list_display = [
        "title",
        "slug",
        "node_type",
        "status",
        "owner",
        "is_deleted",
        "created_at",
        "updated_at",
    ]
    list_filter = ["node_type", "status", "is_deleted", "owner"]
    search_fields = ["title", "slug"]
    readonly_fields = ["id", "created_at", "updated_at", "published_at"]
    ordering = ["path"]


@admin.register(DocumentVersion)
class DocumentVersionAdmin(admin.ModelAdmin):
    list_display = ["document", "author", "is_auto", "note", "created_at"]
    list_filter = ["is_auto", "author"]
    search_fields = ["document__title", "note"]
    readonly_fields = ["created_at"]
    raw_id_fields = ["document", "author"]


@admin.register(SlugAlias)
class SlugAliasAdmin(admin.ModelAdmin):
    list_display = ["old_slug", "document", "created_at"]
    search_fields = ["old_slug", "document__slug"]
    readonly_fields = ["created_at"]
    raw_id_fields = ["document"]


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ["actor", "action", "target_type", "target_id", "created_at"]
    list_filter = ["action", "target_type", "actor"]
    search_fields = ["actor__username", "target_id"]
    readonly_fields = ["actor", "action", "target_type", "target_id", "payload", "created_at"]

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

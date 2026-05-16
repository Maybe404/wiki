"""数据迁移：创建"默认空间"并将所有现有文档归入其中。

如果数据库中没有任何用户，跳过创建并打印警告；文档的 workspace 字段保持
null，等管理员建好第一个 Workspace 后手动关联。
"""

from __future__ import annotations

import uuid

from django.db import migrations


def seed_default_workspace(apps, schema_editor):
    Workspace = apps.get_model("workspaces", "Workspace")
    Document = apps.get_model("documents", "Document")
    User = apps.get_model("auth", "User")

    # 优先取 superuser，否则取任意第一个用户
    creator = (
        User.objects.filter(is_superuser=True).order_by("date_joined").first()
        or User.objects.order_by("date_joined").first()
    )

    if creator is None:
        print(
            "\n[WARNING] 没有找到任何用户，跳过默认空间创建。"
            "请手动创建 Workspace 并将已有文档关联到该空间。"
        )
        return

    ws, created = Workspace.objects.get_or_create(
        slug="default",
        defaults={
            "id": uuid.uuid4(),
            "name": "默认空间",
            "description": "系统自动创建的默认工作空间，存放迁移前的所有文档。",
            "created_by": creator,
        },
    )

    if created:
        print(f"\n[INFO] 默认空间已创建（id={ws.id}，creator={creator.username}）")

    updated = Document.objects.filter(workspace__isnull=True).update(workspace=ws)
    if updated:
        print(f"[INFO] 已将 {updated} 个节点归入默认空间。")


def remove_default_workspace(apps, schema_editor):
    """回滚：只清除 document.workspace 关联，不删除 Workspace 记录（避免误删数据）。"""
    Workspace = apps.get_model("workspaces", "Workspace")
    Document = apps.get_model("documents", "Document")
    ws = Workspace.objects.filter(slug="default").first()
    if ws:
        Document.objects.filter(workspace=ws).update(workspace=None)


class Migration(migrations.Migration):
    dependencies = [
        ("documents", "0006_document_workspace_fields"),
        ("workspaces", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(seed_default_workspace, remove_default_workspace),
    ]

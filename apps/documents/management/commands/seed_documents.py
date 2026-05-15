"""seed_documents: 创建 3 篇示例文档（含树形父子结构）用于开发验证。"""

from typing import Any

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.utils import timezone

from apps.documents.models import Document, DocumentVersion

User = get_user_model()

SAMPLE_HTML = """<article class="doc-section">
  <h1 data-editable="true" data-editable-id="title-1">{title}</h1>
  <p data-editable="true" data-editable-id="body-1">{body}</p>
</article>"""

SAMPLES: list[dict[str, Any]] = [
    {
        "title": "产品设计规范",
        "slug": "design-spec",
        "status": "published",
        "body": "本文档描述产品整体设计规范，包括配色、字体与组件标准。",
        "children": [
            {
                "title": "配色系统",
                "slug": "design-spec-colors",
                "status": "published",
                "body": "主色调为暖米色 #F5F3EE，强调色为深森林绿 #2C4A3A。",
            },
            {
                "title": "字体规范",
                "slug": "design-spec-typography",
                "status": "draft",
                "body": "标题使用 DM Serif Display，正文使用 Noto Sans SC（字重 300）。",
            },
        ],
    },
    {
        "title": "API 接口文档",
        "slug": "api-docs",
        "status": "draft",
        "body": "本文档描述系统对外暴露的 HTTP API 接口，供集成方参考。",
        "children": [],
    },
]


class Command(BaseCommand):
    help = "创建 3 篇示例文档（含树形结构），用于开发环境验证"

    def handle(self, *args, **options) -> None:
        # 取第一个超级用户，没有就用第一个用户
        user = User.objects.filter(is_superuser=True).first() or User.objects.first()
        if user is None:
            self.stderr.write("没有找到任何用户，请先运行 createsuperuser。")
            return

        created = 0
        for sample in SAMPLES:
            doc, is_new = self._get_or_create_root(sample, user)
            if is_new:
                created += 1
            for child_data in sample.get("children", []):
                _, is_new_child = self._get_or_create_child(child_data, doc, user)
                if is_new_child:
                    created += 1

        self.stdout.write(self.style.SUCCESS(f"完成：新建 {created} 篇文档。"))

    def _get_or_create_root(self, data: dict[str, Any], user: User) -> tuple["Document", bool]:
        if Document.objects.filter(slug=data["slug"]).exists():
            doc = Document.objects.get(slug=data["slug"])
            return doc, False

        doc = Document.add_root(
            title=data["title"],
            slug=data["slug"],
            node_type=Document.NodeType.DOCUMENT,
            status=data["status"],
            owner=user,
            published_at=timezone.now() if data["status"] == "published" else None,
        )
        self._add_version(doc, data["body"], user)
        return doc, True

    def _get_or_create_child(
        self, data: dict[str, Any], parent: "Document", user: User
    ) -> tuple["Document", bool]:
        if Document.objects.filter(slug=data["slug"]).exists():
            doc = Document.objects.get(slug=data["slug"])
            return doc, False

        doc = parent.add_child(
            title=data["title"],
            slug=data["slug"],
            node_type=Document.NodeType.DOCUMENT,
            status=data["status"],
            owner=user,
            published_at=timezone.now() if data["status"] == "published" else None,
        )
        self._add_version(doc, data["body"], user)
        return doc, True

    def _add_version(self, doc: "Document", body: str, user: User) -> None:
        html = SAMPLE_HTML.format(title=doc.title, body=body)
        DocumentVersion.objects.create(  # ty: ignore[unresolved-attribute]
            document=doc,
            html=html,
            editable_blocks={
                "title-1": doc.title,
                "body-1": body,
            },
            author=user,
            is_auto=False,
            note="初始版本（seed）",
        )
        # 同步 FTS plain_text（contentless 表：DELETE 旧行再 INSERT 新行）
        from django.db import connection

        plain_text = f"{doc.title} {body}"
        with connection.cursor() as cursor:
            # Django 在 SQLite 里以不含连字符的形式存储 UUID
            cursor.execute(
                "SELECT rowid FROM documents_document WHERE id = %s",
                [str(doc.pk).replace("-", "")],
            )
            row = cursor.fetchone()
            if row:
                rowid = row[0]
                cursor.execute("DELETE FROM documents_fts WHERE rowid = %s", [rowid])
                cursor.execute(
                    "INSERT INTO documents_fts(rowid, title, plain_text) VALUES (%s, %s, %s)",
                    [rowid, doc.title, plain_text],
                )

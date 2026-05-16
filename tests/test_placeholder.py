import pytest


def test_project_imports():
    import django  # noqa: F401

    assert django.VERSION >= (5, 0)


def _pad_full_html(html: str) -> str:
    """Make import fixtures look like complete generated HTML pages."""
    return html.replace("</body>", f"<!-- {'x' * 1100} --></body>")


def test_full_page_import_validation_preserves_scripts_and_styles():
    from apps.editor.validator import extract_title, validate_full_page_import

    raw_html = """
    <!DOCTYPE html>
    <html lang="zh-CN">
      <head>
        <title>原子能力优化建议</title>
        <link rel="stylesheet" href="https://example.com/font.css">
        <style>.secret { color: red; }</style>
      </head>
      <body>
        <div id="progress"></div>
        <header class="reveal">
          <h1>原子能力优化建议</h1>
          <p>从业务知识深度与工程规范出发。</p>
        </header>
        <section>
          <h2>现状诊断</h2>
          <div class="p-title">业务领域知识太浅</div>
          <div class="p-body">输出内容浮在表面、缺乏深度。</div>
        </section>
        <script>window.__should_not_import = true;</script>
      </body>
    </html>
    """

    errors, plain_text = validate_full_page_import(raw_html)

    assert errors == []
    assert "原子能力优化建议" in plain_text
    assert "业务领域知识太浅" in plain_text
    assert extract_title(raw_html) == "原子能力优化建议"


@pytest.mark.django_db
def test_import_validate_accepts_full_page_html(client, django_user_model):
    user = django_user_model.objects.create_user(
        username="import-editor",
        password="not-used-in-force-login",
    )
    client.force_login(user)

    raw_html = _pad_full_html(
        """
        <!DOCTYPE html>
        <html>
          <head><style>body { color: red; }</style></head>
          <body>
            <h1>原子能力优化建议</h1>
            <p>系统性重建路线。</p>
            <script>alert("blocked")</script>
          </body>
        </html>
        """
    )

    response = client.post(
        "/admin/import/validate/",
        {"raw_html": raw_html},
        HTTP_HOST="127.0.0.1",
    )

    assert response.status_code == 200
    body = response.content.decode()
    assert "校验通过" in body
    # 完整 HTML 页面：保留原版式，不再拆成 editable blocks
    assert "完整 HTML 页面" in body
    assert "禁止使用" not in body
    # 导入结果页只展示转义摘要，不在父页面执行导入 HTML。
    assert "&lt;script&gt;alert(&quot;blocked&quot;)&lt;/script&gt;" in body
    assert "&lt;style&gt;body { color: red; }&lt;/style&gt;" in body


@pytest.mark.django_db
def test_import_confirm_full_page_into_folder(client, django_user_model):
    from apps.documents.models import Document, DocumentVersion

    user = django_user_model.objects.create_user(
        username="full-page-editor",
        password="not-used",
    )
    client.force_login(user)
    folder = Document.add_root(
        title="设计文档",
        slug="folder-design",
        node_type=Document.NodeType.FOLDER,
        owner=user,
    )

    raw_html = _pad_full_html(
        "<!DOCTYPE html><html><head><style>h1 { color: blue; }</style></head>"
        "<body><h1>原子能力优化建议</h1></body></html>"
    )
    response = client.post(
        "/admin/import/confirm/",
        {
            "raw_html": raw_html,
            "title": "原子能力优化建议",
            "slug": "atomic-opt",
            "parent_id": str(folder.pk),
        },
        HTTP_HOST="127.0.0.1",
    )

    assert response.status_code == 302
    doc = Document.objects.get(slug="atomic-opt")
    assert doc.get_parent() == folder
    version: DocumentVersion = doc.versions.get()
    assert version.is_full_page is True
    assert version.editable_blocks == {}
    assert "<style>" in version.html
    assert "<script" not in version.html
    assert "原子能力优化建议" in version.html


@pytest.mark.django_db
def test_full_page_import_preserves_scripts_on_confirm(client, django_user_model):
    from apps.documents.models import Document

    user = django_user_model.objects.create_user(
        username="script-page-editor",
        password="not-used",
    )
    client.force_login(user)

    raw_html = _pad_full_html(
        '<!DOCTYPE html><html><head><title>动效页面</title><style id="stage-css">'
        "body { color: blue; }</style></head><body><h1>动效页面</h1>"
        "<script>window.__stageOneAnimation = true;</script></body></html>"
    )
    response = client.post(
        "/admin/import/confirm/",
        {
            "raw_html": raw_html,
            "title": "动效页面",
            "slug": "animated-doc",
        },
        HTTP_HOST="127.0.0.1",
    )

    assert response.status_code == 302
    doc = Document.objects.get(slug="animated-doc")
    version = doc.versions.get()
    assert version.is_full_page is True
    assert '<style id="stage-css">' in version.html
    assert "window.__stageOneAnimation = true;" in version.html


@pytest.mark.django_db
def test_public_detail_uses_content_iframe_sandbox(client, django_user_model):
    from apps.documents.models import Document, DocumentVersion

    user = django_user_model.objects.create_user(username="publisher", password="not-used")
    doc = Document.add_root(
        title="隔离页面",
        slug="isolated-page",
        node_type=Document.NodeType.DOCUMENT,
        status=Document.Status.PUBLISHED,
        owner=user,
    )
    DocumentVersion.objects.create(  # ty: ignore[unresolved-attribute]
        document=doc,
        html="<html><body><h1>隔离页面</h1></body></html>",
        editable_blocks={},
        is_full_page=True,
        author=user,
        note="full page",
    )

    response = client.get("/d/isolated-page/", HTTP_HOST="127.0.0.1")

    assert response.status_code == 200
    body = response.content.decode()
    assert 'src="/d/isolated-page/content/"' in body
    assert 'sandbox="allow-scripts allow-downloads allow-popups"' in body
    assert 'referrerpolicy="no-referrer"' in body
    assert "srcdoc=" not in body


@pytest.mark.django_db
def test_public_content_endpoint_has_csp_and_resize_script(client, django_user_model):
    from apps.documents.models import Document, DocumentVersion

    user = django_user_model.objects.create_user(username="content-publisher", password="not-used")
    doc = Document.add_root(
        title="内容端点",
        slug="content-endpoint",
        node_type=Document.NodeType.DOCUMENT,
        status=Document.Status.PUBLISHED,
        owner=user,
    )
    DocumentVersion.objects.create(  # ty: ignore[unresolved-attribute]
        document=doc,
        html=(
            "<!doctype html><html><head><style>body{color:red}</style></head>"
            "<body><h1>内容端点</h1><script>window.demo = true;</script></body></html>"
        ),
        editable_blocks={},
        is_full_page=True,
        author=user,
        note="full page",
    )

    response = client.get("/d/content-endpoint/content/", HTTP_HOST="127.0.0.1")

    assert response.status_code == 200
    assert response["X-Frame-Options"] == "SAMEORIGIN"
    assert "default-src 'none'" in response["Content-Security-Policy"]
    body = response.content.decode()
    assert "<script>window.demo = true;</script>" in body
    assert "atlas-doc-resize" in body
    assert body.index("atlas-doc-resize") < body.lower().index("</body>")


@pytest.mark.django_db
def test_admin_can_create_blank_document(client, django_user_model):
    from apps.documents.models import Document

    user = django_user_model.objects.create_user(
        username="editor",
        password="not-used-in-force-login",
    )
    client.force_login(user)

    response = client.post(
        "/admin/doc/new/",
        {"title": "项目复盘", "slug": "project-review"},
        HTTP_HOST="127.0.0.1",
    )

    assert response.status_code == 302
    doc = Document.objects.get(slug="project-review")
    assert doc.title == "项目复盘"
    assert doc.node_type == Document.NodeType.DOCUMENT
    assert doc.status == Document.Status.DRAFT

    version = doc.versions.get()
    assert version.note == "新建草稿"
    assert 'data-editable-id="section-1-title"' in version.html
    assert version.editable_blocks["body-1"] == "从这里开始编写正文。"


@pytest.mark.django_db
def test_admin_can_create_and_delete_folder(client, django_user_model):
    from apps.documents.models import Document

    user = django_user_model.objects.create_user(
        username="folder-editor",
        password="not-used-in-force-login",
    )
    client.force_login(user)

    response = client.post(
        "/admin/folder/new/",
        {"title": "产品规范"},
        HTTP_HOST="127.0.0.1",
    )

    assert response.status_code == 302
    folder = Document.objects.get(title="产品规范")
    assert folder.node_type == Document.NodeType.FOLDER
    assert folder.versions.count() == 0

    delete_response = client.post(
        f"/admin/tree/node/{folder.pk}/delete/",
        HTTP_HOST="127.0.0.1",
    )

    assert delete_response.status_code == 200
    folder.refresh_from_db()
    assert folder.is_deleted is True


@pytest.mark.django_db
def test_admin_can_create_document_inside_folder(client, django_user_model):
    from apps.documents.models import Document

    user = django_user_model.objects.create_user(
        username="nested-editor",
        password="not-used-in-force-login",
    )
    client.force_login(user)
    folder = Document.add_root(
        title="产品规范",
        slug="folder-product-spec",
        node_type=Document.NodeType.FOLDER,
        owner=user,
    )

    response = client.post(
        "/admin/doc/new/",
        {"title": "配色系统", "slug": "color-system", "parent_id": str(folder.pk)},
        HTTP_HOST="127.0.0.1",
    )

    assert response.status_code == 302
    doc = Document.objects.get(slug="color-system")
    assert doc.node_type == Document.NodeType.DOCUMENT
    assert doc.get_parent() == folder


@pytest.mark.django_db
def test_admin_cannot_create_children_inside_document(client, django_user_model):
    from apps.documents.models import Document

    user = django_user_model.objects.create_user(
        username="strict-editor",
        password="not-used-in-force-login",
    )
    client.force_login(user)
    doc = Document.add_root(
        title="已有文章",
        slug="existing-doc",
        node_type=Document.NodeType.DOCUMENT,
        owner=user,
    )

    child_doc_response = client.post(
        "/admin/doc/new/",
        {"title": "子文章", "slug": "child-doc", "parent_id": str(doc.pk)},
        HTTP_HOST="127.0.0.1",
    )
    child_folder_response = client.post(
        "/admin/folder/new/",
        {"title": "子文件夹", "parent_id": str(doc.pk)},
        HTTP_HOST="127.0.0.1",
    )

    assert child_doc_response.status_code == 400
    assert child_folder_response.status_code == 400
    assert Document.objects.filter(slug="child-doc").exists() is False
    assert Document.objects.filter(title="子文件夹").exists() is False

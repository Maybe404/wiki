import pytest


def test_project_imports():
    import django  # noqa: F401

    assert django.VERSION >= (5, 0)


def test_import_accepts_full_html_and_auto_marks_editable_blocks():
    from apps.editor.validator import validate_import_html

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

    errors, cleaned_html, editable_blocks = validate_import_html(raw_html)

    assert errors == []
    assert "<script" not in cleaned_html
    assert "<style" not in cleaned_html
    assert "<link" not in cleaned_html
    assert "should_not_import" not in cleaned_html
    assert 'data-editable="true"' in cleaned_html
    assert any("原子能力优化建议" in block for block in editable_blocks.values())
    assert any("业务领域知识太浅" in block for block in editable_blocks.values())


@pytest.mark.django_db
def test_import_validate_accepts_full_page_html(client, django_user_model):
    user = django_user_model.objects.create_user(
        username="import-editor",
        password="not-used-in-force-login",
    )
    client.force_login(user)

    response = client.post(
        "/admin/import/validate/",
        {
            "raw_html": """
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
        },
        HTTP_HOST="127.0.0.1",
    )

    assert response.status_code == 200
    body = response.content.decode()
    assert "校验通过" in body
    # 完整 HTML 页面：保留原版式，不再拆成 editable blocks
    assert "完整 HTML 页面" in body
    assert "禁止使用" not in body
    # script 被剥离，style 原样保留
    assert "alert(" not in body
    assert "<style>body { color: red; }</style>" in body


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

    raw_html = (
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
    assert "<style>" in version.html
    assert "原子能力优化建议" in version.html


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

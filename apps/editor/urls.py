from django.urls import path

from .views import (
    create_blank_document,
    import_confirm,
    import_document_page,
    import_validate,
    save_document,
    version_diff_api,
    version_list_api,
    version_restore,
)

urlpatterns = [
    path("admin/doc/new/", create_blank_document, name="admin_doc_create"),
    path("admin/doc/<uuid:pk>/save/", save_document, name="admin_doc_save"),
    path("admin/doc/<uuid:pk>/versions/", version_list_api, name="admin_doc_versions"),
    path(
        "admin/doc/<uuid:pk>/versions/<int:vid>/diff/",
        version_diff_api,
        name="admin_doc_version_diff",
    ),
    path(
        "admin/doc/<uuid:pk>/versions/<int:vid>/restore/",
        version_restore,
        name="admin_doc_version_restore",
    ),
    path("admin/import/", import_document_page, name="admin_import"),
    path("admin/import/validate/", import_validate, name="admin_import_validate"),
    path("admin/import/confirm/", import_confirm, name="admin_import_confirm"),
]

from django.urls import path

from .views import (
    DocumentDetailView,
    admin_doc_content,
    admin_doc_detail,
    doc_copy,
    document_content,
    folder_create,
    node_move,
    search_api,
    tree_node_delete,
    tree_node_purge,
    tree_node_restore,
    tree_reorder,
)

urlpatterns = [
    path("d/<uslug:slug>/", DocumentDetailView.as_view(), name="doc_detail"),
    path("d/<uslug:slug>/content/", document_content, name="doc_content"),
    path("admin/doc/<uuid:pk>/", admin_doc_detail, name="admin_doc_detail"),
    path("admin/doc/<uuid:pk>/content/", admin_doc_content, name="admin_doc_content"),
    path("admin/doc/<uuid:pk>/copy/", doc_copy, name="admin_doc_copy"),
    path("admin/folder/new/", folder_create, name="admin_folder_create"),
    path("admin/tree/node/<uuid:pk>/delete/", tree_node_delete, name="admin_tree_node_delete"),
    path("admin/tree/node/<uuid:pk>/move/", node_move, name="admin_tree_node_move"),
    path("admin/tree/node/<uuid:pk>/restore/", tree_node_restore, name="admin_tree_node_restore"),
    path("admin/tree/node/<uuid:pk>/purge/", tree_node_purge, name="admin_tree_node_purge"),
    path("admin/tree/reorder", tree_reorder, name="admin_tree_reorder"),
    path("admin/search", search_api, name="admin_search"),
]

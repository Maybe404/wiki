from django.urls import path

from .views import DocumentDetailView, admin_doc_detail, search_api, tree_reorder

urlpatterns = [
    path("d/<slug:slug>/", DocumentDetailView.as_view(), name="doc_detail"),
    path("admin/doc/<uuid:pk>/", admin_doc_detail, name="admin_doc_detail"),
    path("admin/tree/reorder", tree_reorder, name="admin_tree_reorder"),
    path("admin/search", search_api, name="admin_search"),
]

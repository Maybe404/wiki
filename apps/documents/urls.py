from django.urls import path

from .views import DocumentDetailView, tree_reorder

urlpatterns = [
    path("d/<slug:slug>/", DocumentDetailView.as_view(), name="doc_detail"),
    path("admin/tree/reorder", tree_reorder, name="admin_tree_reorder"),
]

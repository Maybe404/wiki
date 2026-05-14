from django.urls import path

from .views import save_document

urlpatterns = [
    path("admin/doc/<uuid:pk>/save/", save_document, name="admin_doc_save"),
]

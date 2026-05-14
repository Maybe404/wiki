from django.urls import path

from .views import publish_document, unpublish_document

urlpatterns = [
    path("admin/doc/<uuid:pk>/publish/", publish_document, name="admin_doc_publish"),
    path("admin/doc/<uuid:pk>/unpublish/", unpublish_document, name="admin_doc_unpublish"),
]

from django.urls import path

from .views import DocumentDetailView

urlpatterns = [
    path("d/<slug:slug>/", DocumentDetailView.as_view(), name="doc_detail"),
]

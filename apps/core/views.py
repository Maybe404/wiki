from django.http import HttpRequest, HttpResponse
from django.shortcuts import render


def home(request: HttpRequest) -> HttpResponse:
    return render(request, "home.html")


def custom_404(request: HttpRequest, exception=None) -> HttpResponse:
    return render(request, "404.html", status=404)

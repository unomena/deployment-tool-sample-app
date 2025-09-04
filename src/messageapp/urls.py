"""
URL configuration for the messages app.
"""

from django.urls import path, include
from . import views

urlpatterns = [
    path("", views.home, name="home"),
    path("status/", views.status, name="status"),
    path("api/", include("messageapp.api.urls")),
    path("", include("messageapp.health.urls")),
]

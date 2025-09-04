"""
API URL configuration for messageapp.
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import MessageViewSet, TaskLogViewSet

# Create a router and register our viewsets
router = DefaultRouter()
router.register(r"messages", MessageViewSet)
router.register(r"task-logs", TaskLogViewSet)

urlpatterns = [
    path("", include(router.urls)),
]

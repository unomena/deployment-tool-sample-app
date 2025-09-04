"""
Admin configuration for the messages app.
"""

from django.contrib import admin
from .models import Message, TaskLog


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    """Admin interface for Message model."""

    list_display = ("content_preview", "created_at", "processed_at", "task_id")
    list_filter = ("created_at", "processed_at")
    search_fields = ("content",)
    readonly_fields = ("created_at", "processed_at", "task_id")

    def content_preview(self, obj):
        """Show a preview of the message content."""
        return obj.content[:100] + "..." if len(obj.content) > 100 else obj.content

    content_preview.short_description = "Message Content"


@admin.register(TaskLog)
class TaskLogAdmin(admin.ModelAdmin):
    """Admin interface for TaskLog model."""

    list_display = ("task_name", "status", "started_at", "completed_at")
    list_filter = ("status", "task_name", "started_at")
    search_fields = ("task_name", "task_id", "result")
    readonly_fields = ("task_id", "started_at", "completed_at")

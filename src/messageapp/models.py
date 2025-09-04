"""
Models for the messages app.
"""

from django.db import models
from django.utils import timezone


class Message(models.Model):
    """Model to store user messages with timestamps."""

    content = models.TextField(help_text="The message content submitted by the user")
    created_at = models.DateTimeField(default=timezone.now, help_text="When the message was created")
    processed_at = models.DateTimeField(
        null=True, blank=True, help_text="When the message was processed by Celery task"
    )
    task_id = models.CharField(
        max_length=255, null=True, blank=True, help_text="Celery task ID that processed this message"
    )

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Message"
        verbose_name_plural = "Messages"

    def __str__(self):
        return f"Message: {self.content[:50]}... ({self.created_at})"


class TaskLog(models.Model):
    """Model to log Celery task executions."""

    task_name = models.CharField(max_length=255, help_text="Name of the Celery task")
    task_id = models.CharField(max_length=255, unique=True, help_text="Celery task ID")
    status = models.CharField(
        max_length=50,
        choices=[
            ("PENDING", "Pending"),
            ("STARTED", "Started"),
            ("SUCCESS", "Success"),
            ("FAILURE", "Failure"),
            ("RETRY", "Retry"),
        ],
        default="PENDING",
    )
    result = models.TextField(null=True, blank=True, help_text="Task result or error message")
    started_at = models.DateTimeField(default=timezone.now, help_text="When the task was started")
    completed_at = models.DateTimeField(null=True, blank=True, help_text="When the task was completed")

    class Meta:
        ordering = ["-started_at"]
        verbose_name = "Task Log"
        verbose_name_plural = "Task Logs"

    def __str__(self):
        return f"{self.task_name} ({self.status}) - {self.started_at}"

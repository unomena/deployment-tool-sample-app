"""
API serializers for the messageapp.
"""

from rest_framework import serializers
from .models import Message, TaskLog


class MessageSerializer(serializers.ModelSerializer):
    """Serializer for Message model."""

    class Meta:
        model = Message
        fields = ["id", "content", "created_at", "processed_at", "task_id"]
        read_only_fields = ["id", "created_at", "processed_at", "task_id"]


class MessageCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating new messages."""

    class Meta:
        model = Message
        fields = ["content"]


class TaskLogSerializer(serializers.ModelSerializer):
    """Serializer for TaskLog model."""

    class Meta:
        model = TaskLog
        fields = ["id", "task_name", "task_id", "status", "result", "started_at", "completed_at"]
        read_only_fields = ["id", "started_at", "completed_at"]

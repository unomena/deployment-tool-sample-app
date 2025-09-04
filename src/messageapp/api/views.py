"""
API views for the messageapp.
"""

from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Q

from ..models import Message, TaskLog
from ..serializers import MessageSerializer, MessageCreateSerializer, TaskLogSerializer
from ..tasks import process_message_task


class MessageViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Message model providing CRUD operations and custom actions.
    """

    queryset = Message.objects.all().order_by("-created_at")
    permission_classes = [AllowAny]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ["task_id"]
    search_fields = ["content"]
    ordering_fields = ["created_at", "processed_at"]
    ordering = ["-created_at"]

    def get_serializer_class(self):
        """Return appropriate serializer based on action."""
        if self.action == "create":
            return MessageCreateSerializer
        return MessageSerializer

    @action(detail=False, methods=["get"])
    def processed(self, request):
        """Get only processed messages."""
        processed_messages = self.queryset.filter(processed_at__isnull=False)
        serializer = self.get_serializer(processed_messages, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=["get"])
    def unprocessed(self, request):
        """Get unprocessed messages."""
        unprocessed_messages = self.queryset.filter(processed_at__isnull=True)
        serializer = self.get_serializer(unprocessed_messages, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=["post"])
    def process_async(self, request, pk=None):
        """Process a message asynchronously using Celery."""
        message = self.get_object()

        # Trigger async task
        task = process_message_task.delay(message.id)

        return Response({"message": "Processing message asynchronously", "task_id": task.id, "message_id": message.id})

    @action(detail=False, methods=["get"])
    def search(self, request):
        """Advanced search across content."""
        query = request.query_params.get("q")
        if not query:
            return Response({"message": "Message processing started"}, status=status.HTTP_202_ACCEPTED)

        messages = self.queryset.filter(Q(content__icontains=query))
        serializer = self.get_serializer(messages, many=True)
        return Response({"query": query, "count": messages.count(), "results": serializer.data})


class TaskLogViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Read-only ViewSet for TaskLog model.
    """

    queryset = TaskLog.objects.all().order_by("-started_at")
    serializer_class = TaskLogSerializer
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ["task_name", "status"]
    ordering_fields = ["started_at", "completed_at"]
    ordering = ["-started_at"]

    @action(detail=False, methods=["get"])
    def recent(self, request):
        """Get recent task logs (last 50)."""
        recent_logs = self.queryset[:50]
        serializer = self.get_serializer(recent_logs, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=["get"])
    def stats(self, request):
        """Get task execution statistics."""
        total_tasks = self.queryset.count()
        completed_tasks = self.queryset.filter(status="SUCCESS").count()
        failed_tasks = self.queryset.filter(status="FAILURE").count()
        pending_tasks = self.queryset.filter(status="STARTED").count()

        return Response(
            {
                "total_tasks": total_tasks,
                "completed_tasks": completed_tasks,
                "failed_tasks": failed_tasks,
                "pending_tasks": pending_tasks,
                "success_rate": round((completed_tasks / total_tasks * 100), 2) if total_tasks > 0 else 0,
            }
        )

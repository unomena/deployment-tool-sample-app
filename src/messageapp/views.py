"""
Views for the messages app.
"""

from django.shortcuts import render, redirect
from django.contrib import messages as django_messages
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from .models import Message, TaskLog
from .tasks import process_message_task
from .forms import MessageForm


def home(request):
    """
    Home page view that displays the message form and all messages.
    """
    if request.method == "POST":
        form = MessageForm(request.POST)
        if form.is_valid():
            # Create the message
            message = form.save()

            # Kick off the Celery task to process it
            task = process_message_task.delay(message.id)

            django_messages.success(request, f"Message submitted! Task {task.id} is processing your message.")
            return redirect("home")
    else:
        form = MessageForm()

    # Get all messages ordered by creation date (newest first)
    all_messages = Message.objects.all()

    # Get recent task logs for display
    recent_tasks = TaskLog.objects.all()[:10]

    context = {
        "form": form,
        "messages": all_messages,
        "recent_tasks": recent_tasks,
        "total_messages": all_messages.count(),
        "processed_messages": all_messages.filter(processed_at__isnull=False).count(),
    }

    return render(request, "messages/home.html", context)


@require_http_methods(["GET"])
def status(request):
    """
    API endpoint to get current status of messages and tasks.
    """
    total_messages = Message.objects.count()
    processed_messages = Message.objects.filter(processed_at__isnull=False).count()
    pending_messages = total_messages - processed_messages

    recent_tasks = TaskLog.objects.all()[:5]

    return JsonResponse(
        {
            "total_messages": total_messages,
            "processed_messages": processed_messages,
            "pending_messages": pending_messages,
            "recent_tasks": [
                {
                    "task_name": task.task_name,
                    "status": task.status,
                    "started_at": task.started_at.isoformat(),
                    "result": task.result[:100] if task.result else None,
                }
                for task in recent_tasks
            ],
        }
    )

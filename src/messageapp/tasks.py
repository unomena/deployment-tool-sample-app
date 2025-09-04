"""
Celery tasks for the messages app.
"""

from celery import shared_task
from django.utils import timezone
from .models import Message, TaskLog
import logging

logger = logging.getLogger(__name__)


@shared_task
def process_message_task(message_id):
    """
    Process a message by updating its processed_at timestamp.
    This simulates some background processing work.
    """
    task_id = getattr(process_message_task.request, "id", None) or f"test-{timezone.now().timestamp()}"

    # Log task start
    task_log = TaskLog.objects.create(task_name="process_message_task", task_id=task_id, status="STARTED")

    try:
        # Get the message
        message = Message.objects.get(id=message_id)

        # Simulate some processing time
        import time

        time.sleep(2)

        # Update the message
        message.processed_at = timezone.now()
        message.task_id = task_id
        message.save()

        # Update task log
        task_log.status = "SUCCESS"
        task_log.result = f"Successfully processed message: {message.content[:50]}"
        task_log.completed_at = timezone.now()
        task_log.save()

        logger.info(f"Successfully processed message {message_id}")
        return f"Message {message_id} processed successfully"

    except Message.DoesNotExist:
        error_msg = f"Message with id {message_id} not found"
        task_log.status = "FAILURE"
        task_log.result = error_msg
        task_log.completed_at = timezone.now()
        task_log.save()

        logger.error(error_msg)
        raise Exception(error_msg)

    except Exception as e:
        error_msg = f"Error processing message {message_id}: {str(e)}"
        task_log.status = "FAILURE"
        task_log.result = error_msg
        task_log.completed_at = timezone.now()
        task_log.save()

        logger.error(error_msg)
        raise


@shared_task
def periodic_message_task():
    """
    Periodic task that runs via Celery Beat.
    Creates a system message every minute.
    """
    task_id = getattr(periodic_message_task.request, "id", None) or f"test-{timezone.now().timestamp()}"

    # Log task start
    task_log = TaskLog.objects.create(task_name="periodic_message_task", task_id=task_id, status="STARTED")

    try:
        # Create a periodic system message
        message = Message.objects.create(
            content=f"System message created by periodic task at {timezone.now()}",
            processed_at=timezone.now(),
            task_id=task_id,
        )

        # Update task log
        task_log.status = "SUCCESS"
        task_log.result = f"Created periodic message: {message.id}"
        task_log.completed_at = timezone.now()
        task_log.save()

        logger.info(f"Created periodic message {message.id}")
        return f"Periodic message {message.id} created successfully"

    except Exception as e:
        error_msg = f"Error creating periodic message: {str(e)}"
        task_log.status = "FAILURE"
        task_log.result = error_msg
        task_log.completed_at = timezone.now()
        task_log.save()

        logger.error(error_msg)
        raise

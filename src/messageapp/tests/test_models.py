"""
Unit tests for messageapp models.
"""

from django.test import TestCase
from django.utils import timezone
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from ..models import Message, TaskLog


class MessageModelTest(TestCase):
    """Test cases for the Message model."""

    def setUp(self):
        """Set up test data."""
        self.message_data = {"content": "Test message content"}

    def test_message_creation(self):
        """Test creating a message with valid data."""
        message = Message.objects.create(**self.message_data)

        self.assertEqual(message.content, "Test message content")
        self.assertIsNotNone(message.created_at)
        self.assertIsNone(message.processed_at)
        self.assertTrue(message.id)

    def test_message_str_representation(self):
        """Test the string representation of a message."""
        message = Message.objects.create(**self.message_data)
        expected_str = f"Message: {message.content[:50]}... ({message.created_at})"
        self.assertEqual(str(message), expected_str)

    def test_message_content_required(self):
        """Test that content field is required."""
        with self.assertRaises(IntegrityError):
            Message.objects.create(content=None)

    def test_message_content_max_length(self):
        """Test content field max length validation."""
        # TextField doesn't have max_length by default, so this test is not applicable
        # We'll test that very long content can be stored
        long_content = "x" * 10000  # Very long content
        message = Message(content=long_content)

        # Should not raise validation error for TextField
        message.full_clean()
        message.save()
        self.assertEqual(message.content, long_content)

    def test_message_processed_at_field(self):
        """Test the processed_at field."""
        message = Message.objects.create(**self.message_data)

        # Initially not processed
        self.assertIsNone(message.processed_at)

        # Mark as processed
        message.processed_at = timezone.now()
        message.save()

        # Refresh from database
        message.refresh_from_db()
        self.assertIsNotNone(message.processed_at)

    def test_message_ordering(self):
        """Test that messages are ordered by creation date (newest first)."""
        # Create messages with slight delay
        message1 = Message.objects.create(content="First message")
        message2 = Message.objects.create(content="Second message")

        messages = Message.objects.all()
        # Should be ordered by -created_at (newest first)
        self.assertEqual(messages[0], message2)
        self.assertEqual(messages[1], message1)

    def test_message_mark_processed(self):
        """Test marking a message as processed."""
        message = Message.objects.create(**self.message_data)

        # Mark as processed
        before_time = timezone.now()
        message.processed_at = timezone.now()
        message.save()
        after_time = timezone.now()

        message.refresh_from_db()
        self.assertIsNotNone(message.processed_at)
        self.assertLessEqual(before_time, message.processed_at)
        self.assertLessEqual(message.processed_at, after_time)


class TaskLogModelTest(TestCase):
    """Test cases for the TaskLog model."""

    def setUp(self):
        """Set up test data."""
        self.message = Message.objects.create(content="Test message for task")
        self.task_data = {"task_id": "test-task-123", "task_name": "process_message_task", "status": "PENDING"}

    def test_task_log_creation(self):
        """Test creating a task log with valid data."""
        task_log = TaskLog.objects.create(**self.task_data)

        self.assertEqual(task_log.task_id, "test-task-123")
        self.assertEqual(task_log.task_name, "process_message_task")
        self.assertEqual(task_log.status, "PENDING")
        self.assertIsNotNone(task_log.started_at)
        self.assertIsNone(task_log.completed_at)
        self.assertIsNone(task_log.result)

    def test_task_log_str_representation(self):
        """Test the string representation of a task log."""
        task_log = TaskLog.objects.create(**self.task_data)
        expected_str = f"process_message_task (PENDING) - {task_log.started_at}"
        self.assertEqual(str(task_log), expected_str)

    def test_task_log_required_fields(self):
        """Test that required fields are enforced."""
        # Test missing task_id (which has unique=True constraint)
        with self.assertRaises(IntegrityError):
            TaskLog.objects.create(task_name="test_task", task_id=None, status="PENDING")

    def test_task_log_status_choices(self):
        """Test task status choices validation."""
        valid_statuses = ["PENDING", "STARTED", "SUCCESS", "FAILURE", "RETRY"]

        for status in valid_statuses:
            task_log = TaskLog(task_id=f"test-{status.lower()}", task_name="test_task", status=status)
            # Should not raise validation error
            task_log.full_clean()

    def test_task_log_invalid_status(self):
        """Test that invalid status raises validation error."""
        task_log = TaskLog(task_id="test-invalid", task_name="test_task", status="INVALID_STATUS")

        with self.assertRaises(ValidationError):
            task_log.full_clean()

    def test_task_log_completion(self):
        """Test completing a task log."""
        task_log = TaskLog.objects.create(**self.task_data)

        # Complete the task
        completion_time = timezone.now()
        task_log.status = "SUCCESS"
        task_log.completed_at = completion_time
        task_log.result = "Task completed successfully"
        task_log.save()

        task_log.refresh_from_db()
        self.assertEqual(task_log.status, "SUCCESS")
        self.assertEqual(task_log.completed_at, completion_time)
        self.assertEqual(task_log.result, "Task completed successfully")

    def test_task_log_failure(self):
        """Test failing a task log."""
        task_log = TaskLog.objects.create(**self.task_data)

        # Fail the task
        task_log.status = "FAILURE"
        task_log.completed_at = timezone.now()
        task_log.result = "Task failed due to error"
        task_log.save()

        task_log.refresh_from_db()
        self.assertEqual(task_log.status, "FAILURE")
        self.assertIsNotNone(task_log.completed_at)
        self.assertEqual(task_log.result, "Task failed due to error")

    def test_task_log_ordering(self):
        """Test that task logs are ordered by start time."""
        TaskLog.objects.create(task_id="task-1", task_name="test_task", status="PENDING")
        TaskLog.objects.create(task_id="task-2", task_name="test_task", status="PENDING")

        task_logs = TaskLog.objects.all()
        # Should be ordered by -started_at (newest first)
        self.assertEqual(task_logs[0].task_id, "task-2")
        self.assertEqual(task_logs[1].task_id, "task-1")

    def test_task_log_unique_task_id(self):
        """Test that task_id must be unique."""
        TaskLog.objects.create(**self.task_data)

        # Try to create another with same task_id
        with self.assertRaises(IntegrityError):
            TaskLog.objects.create(**self.task_data)


class ModelIntegrationTest(TestCase):
    """Integration tests for model interactions."""

    def test_multiple_task_logs(self):
        """Test creating multiple task logs."""
        # Create multiple task logs
        TaskLog.objects.create(task_id="task-1", task_name="process_message_task", status="SUCCESS")
        TaskLog.objects.create(task_id="task-2", task_name="send_notification_task", status="PENDING")

        # Test that both exist
        self.assertEqual(TaskLog.objects.count(), 2)
        self.assertTrue(TaskLog.objects.filter(task_id="task-1").exists())
        self.assertTrue(TaskLog.objects.filter(task_id="task-2").exists())

    def test_bulk_message_operations(self):
        """Test bulk operations on messages."""
        # Create multiple messages
        messages = [Message(content=f"Bulk message {i}") for i in range(5)]
        Message.objects.bulk_create(messages)

        # Verify creation
        self.assertEqual(Message.objects.count(), 5)

        # Test bulk update
        Message.objects.filter(content__startswith="Bulk").update(processed_at=timezone.now())

        # Verify all are processed
        processed_count = Message.objects.filter(processed_at__isnull=False).count()
        self.assertEqual(processed_count, 5)

"""
Unit tests for Celery tasks.
"""

from django.test import TestCase
from django.utils import timezone
from unittest.mock import patch
from ..models import Message, TaskLog
from ..tasks import process_message_task, periodic_message_task


class ProcessMessageTaskTest(TestCase):
    """Test cases for process_message_task."""

    def setUp(self):
        """Set up test data."""
        self.message = Message.objects.create(content="Test message for processing")

    @patch("messageapp.tasks.process_message_task.retry")
    def test_process_message_success(self, mock_retry):
        """Test successful message processing."""
        result = process_message_task(self.message.id)

        # Verify result
        self.assertEqual(result, f"Message {self.message.id} processed successfully")

        # Verify message properties
        self.message.refresh_from_db()
        self.assertIsNotNone(self.message.processed_at)

        # Verify task log was created
        task_log = TaskLog.objects.latest("started_at")
        self.assertIsNotNone(task_log)
        self.assertEqual(task_log.status, "SUCCESS")
        self.assertEqual(task_log.task_name, "process_message_task")

    def test_process_nonexistent_message(self):
        """Test processing a message that doesn't exist."""
        with self.assertRaises(Exception) as context:
            process_message_task(99999)

        # Verify the exception message
        self.assertIn("Message with id 99999 not found", str(context.exception))

    @patch("messageapp.tasks.process_message_task.retry")
    @patch("time.sleep")
    def test_process_message_with_simulated_delay(self, mock_sleep, mock_retry):
        """Test message processing with simulated processing time."""
        # The task includes a sleep - we mock it to speed up tests
        result = process_message_task(self.message.id)

        # Verify sleep was called (simulating processing time)
        mock_sleep.assert_called_once()

        # Verify successful processing
        self.assertEqual(result, f"Message {self.message.id} processed successfully")

    @patch("messageapp.tasks.process_message_task.retry")
    def test_process_already_processed_message(self, mock_retry):
        """Test processing a message that's already been processed."""
        # Mark message as already processed
        self.message.processed_at = timezone.now()
        self.message.save()

        result = process_message_task(self.message.id)

        # Should still return success
        self.assertEqual(result, f"Message {self.message.id} processed successfully")

    @patch("messageapp.models.Message.objects.get")
    def test_process_message_database_error(self, mock_get):
        """Test handling of database errors during processing."""
        # Mock database error
        mock_get.side_effect = Exception("Database connection lost")

        with self.assertRaises(Exception) as context:
            process_message_task(self.message.id)

        # Verify the exception message
        self.assertIn("Database connection lost", str(context.exception))

        # Verify task log shows failure
        task_log = TaskLog.objects.latest("started_at")
        self.assertEqual(task_log.status, "FAILURE")


class PeriodicMessageTaskTest(TestCase):
    """Test cases for periodic_message_task."""

    def test_periodic_message_creation(self):
        """Test that periodic task creates a message."""
        initial_count = Message.objects.count()

        result = periodic_message_task()

        # Verify message was created
        self.assertEqual(Message.objects.count(), initial_count + 1)

        # Verify result message
        self.assertIn("created successfully", result)

        # Verify the created message
        latest_message = Message.objects.latest("created_at")
        self.assertIn("System message created by periodic task", latest_message.content)

    def test_periodic_message_content_format(self):
        """Test that periodic messages have correct content format."""
        periodic_message_task()

        latest_message = Message.objects.latest("created_at")

        # Should contain system message text
        self.assertIn("System message created by periodic task", latest_message.content)

    def test_multiple_periodic_messages(self):
        """Test creating multiple periodic messages."""
        initial_count = Message.objects.count()

        # Create multiple periodic messages
        for _ in range(3):
            periodic_message_task()

        # Verify all were created
        self.assertEqual(Message.objects.count(), initial_count + 3)

        # Verify they have different timestamps
        periodic_messages = Message.objects.filter(
            content__startswith="System message created by periodic task"
        ).order_by("created_at")

        contents = [msg.content for msg in list(periodic_messages)[-3:]]
        self.assertEqual(len(set(contents)), 3)  # All should be unique

    @patch("messageapp.models.Message.objects.create")
    def test_periodic_message_database_error(self, mock_create):
        """Test handling of database errors in periodic task."""
        # Mock database error
        mock_create.side_effect = Exception("Database error")

        with self.assertRaises(Exception):
            periodic_message_task()


class TaskIntegrationTest(TestCase):
    """Integration tests for task functionality."""

    def setUp(self):
        """Set up test data."""
        self.message = Message.objects.create(content="Integration test message")

    def test_task_log_creation_and_updates(self):
        """Test that task logs are properly created and updated."""
        # Process the message
        process_message_task(self.message.id)

        # Verify task log was created
        task_log = TaskLog.objects.latest("started_at")
        self.assertIsNotNone(task_log)
        self.assertEqual(task_log.task_name, "process_message_task")
        self.assertEqual(task_log.status, "SUCCESS")
        self.assertIsNotNone(task_log.task_id)  # Should have a generated task ID
        self.assertIsNotNone(task_log.started_at)
        self.assertIsNotNone(task_log.completed_at)
        self.assertIn("Successfully processed message", task_log.result)

    def test_end_to_end_message_processing(self):
        """Test complete message processing workflow."""
        # Initial state
        self.assertIsNone(self.message.processed_at)
        initial_task_count = TaskLog.objects.count()

        # Process the message
        process_message_task(self.message.id)

        # Verify message was updated
        self.message.refresh_from_db()
        self.assertIsNotNone(self.message.processed_at)
        self.assertIsNotNone(self.message.task_id)  # Should have a generated task ID

        # Verify task log was created
        self.assertEqual(TaskLog.objects.count(), initial_task_count + 1)
        task_log = TaskLog.objects.latest("started_at")
        self.assertEqual(task_log.status, "SUCCESS")
        self.assertEqual(task_log.task_id, self.message.task_id)

    def test_periodic_and_process_task_interaction(self):
        """Test interaction between periodic task and process task."""
        initial_message_count = Message.objects.count()

        # Create periodic message
        periodic_result = periodic_message_task()

        # Verify message was created
        self.assertEqual(Message.objects.count(), initial_message_count + 1)

        # Get the created message
        new_message = Message.objects.latest("created_at")

        # Process the periodic message
        process_result = process_message_task(new_message.id)

        # Verify both tasks completed successfully
        self.assertIn("created successfully", periodic_result)
        self.assertIn("processed successfully", process_result)

        # Verify message state
        new_message.refresh_from_db()
        self.assertIsNotNone(new_message.processed_at)

        # Verify task logs
        task_logs = TaskLog.objects.order_by("-started_at")[:2]
        self.assertEqual(len(task_logs), 2)
        for task_log in task_logs:
            self.assertEqual(task_log.status, "SUCCESS")


class TaskErrorHandlingTest(TestCase):
    """Test cases for task error handling."""

    def setUp(self):
        """Set up test data."""
        self.message = Message.objects.create(content="Error handling test message")

    @patch("time.sleep")
    @patch("messageapp.models.Message.save")
    def test_task_retry_mechanism(self, mock_save, mock_sleep):
        """Test task retry mechanism on transient errors."""
        # Mock a transient error on first call, success on second
        mock_save.side_effect = [Exception("Transient error"), None]

        # This should fail due to the exception
        with self.assertRaises(Exception):
            process_message_task(self.message.id)

        # Verify task log shows failure
        task_log = TaskLog.objects.latest("started_at")
        self.assertEqual(task_log.status, "FAILURE")
        self.assertIn("Transient error", task_log.result)

    @patch("messageapp.tasks.logger")
    def test_task_logging(self, mock_logger):
        """Test that tasks log appropriately."""
        process_message_task(self.message.id)

        # Verify info logging occurred
        mock_logger.info.assert_called()

        # Check log message content
        log_calls = mock_logger.info.call_args_list
        log_messages = [call[0][0] for call in log_calls]

        # Should log successful processing
        success_logs = [msg for msg in log_messages if "Successfully processed" in msg]
        self.assertGreater(len(success_logs), 0)

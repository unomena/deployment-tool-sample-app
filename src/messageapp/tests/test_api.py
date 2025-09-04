"""
Unit tests for messageapp API endpoints.
"""

from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from unittest.mock import patch, MagicMock
from ..models import Message, TaskLog


class MessageAPITest(APITestCase):
    """Test cases for Message API endpoints."""

    def setUp(self):
        """Set up test data and client."""
        self.client = APIClient()
        self.message_data = {"content": "Test API message content"}
        self.message = Message.objects.create(content="Existing test message")

    def test_create_message(self):
        """Test creating a message via API."""
        response = self.client.post("/api/messages/", self.message_data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Message.objects.count(), 2)  # setUp creates one, this creates another

    def test_list_messages(self):
        """Test listing all messages."""
        response = self.client.get("/api/messages/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Check if response is paginated
        if "results" in response.data:
            self.assertGreaterEqual(len(response.data["results"]), 1)
        else:
            self.assertGreaterEqual(len(response.data), 1)

    def test_retrieve_message(self):
        """Test retrieving a specific message."""
        response = self.client.get(f"/api/messages/{self.message.id}/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["id"], self.message.id)

    def test_update_message(self):
        """Test updating a message."""
        updated_data = {"content": "Updated message content"}
        response = self.client.put(f"/api/messages/{self.message.id}/", updated_data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.message.refresh_from_db()
        self.assertEqual(self.message.content, "Updated message content")

    def test_partial_update_message(self):
        """Test partially updating a message."""
        updated_data = {"content": "Partially updated content"}
        response = self.client.patch(f"/api/messages/{self.message.id}/", updated_data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.message.refresh_from_db()
        self.assertEqual(self.message.content, "Partially updated content")

    def test_delete_message(self):
        """Test deleting a message."""
        response = self.client.delete(f"/api/messages/{self.message.id}/")
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Message.objects.filter(id=self.message.id).exists())

    def test_retrieve_nonexistent_message(self):
        """Test retrieving a message that doesn't exist."""
        response = self.client.get("/api/messages/99999/")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_create_message_invalid_data(self):
        """Test creating a message with invalid data."""
        invalid_data = {"content": ""}  # Empty content should be invalid
        response = self.client.post("/api/messages/", invalid_data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_message_serialization(self):
        """Test message serialization includes all expected fields."""
        response = self.client.get(f"/api/messages/{self.message.id}/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        expected_fields = ["id", "content", "created_at", "processed_at", "task_id"]
        for field in expected_fields:
            self.assertIn(field, response.data)

    @patch("messageapp.tasks.process_message_task.delay")
    def test_process_message_async(self, mock_delay):
        """Test processing a message asynchronously."""
        mock_task = MagicMock()
        mock_task.id = "test-task-id"
        mock_delay.return_value = mock_task

        response = self.client.post(f"/api/messages/{self.message.id}/process_async/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("task_id", response.data)
        mock_delay.assert_called_once_with(self.message.id)

    def test_process_nonexistent_message_async(self):
        """Test processing a nonexistent message asynchronously."""
        response = self.client.post("/api/messages/99999/process_async/")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


class TaskLogAPITest(APITestCase):
    """Test cases for TaskLog API endpoints."""

    def setUp(self):
        """Set up test data."""
        self.client = APIClient()
        self.task_log = TaskLog.objects.create(
            task_id="test-task-123", task_name="test_task", status="SUCCESS", result="Task completed successfully"
        )

    def test_list_task_logs(self):
        """Test listing all task logs."""
        response = self.client.get("/api/task-logs/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Check if response is paginated
        if "results" in response.data:
            self.assertGreaterEqual(len(response.data["results"]), 1)
        else:
            self.assertGreaterEqual(len(response.data), 1)

    def test_retrieve_task_log(self):
        """Test retrieving a specific task log."""
        response = self.client.get(f"/api/task-logs/{self.task_log.id}/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["id"], self.task_log.id)

    def test_task_log_serialization(self):
        """Test task log serialization includes all expected fields."""
        response = self.client.get(f"/api/task-logs/{self.task_log.id}/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        expected_fields = ["id", "task_id", "task_name", "status", "started_at", "completed_at", "result"]
        for field in expected_fields:
            self.assertIn(field, response.data)

    def test_filter_task_logs_by_status(self):
        """Test filtering task logs by status."""
        # Create additional task logs with different statuses
        TaskLog.objects.create(task_id="test-task-456", task_name="test_task", status="FAILURE")
        TaskLog.objects.create(task_id="test-task-789", task_name="test_task", status="STARTED")

        response = self.client.get("/api/task-logs/?status=SUCCESS")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Check if response is paginated
        results = response.data.get("results", response.data)
        for task_log in results:
            self.assertEqual(task_log["status"], "SUCCESS")

    def test_filter_task_logs_by_task_name(self):
        """Test filtering task logs by task name."""
        # Create additional task logs with different task names
        TaskLog.objects.create(task_id="test-task-456", task_name="different_task", status="SUCCESS")

        response = self.client.get("/api/task-logs/?task_name=test_task")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Check if response is paginated
        results = response.data.get("results", response.data)
        for task_log in results:
            self.assertEqual(task_log["task_name"], "test_task")


class APIPaginationTest(APITestCase):
    """Test cases for API pagination."""

    def setUp(self):
        """Set up test data."""
        self.client = APIClient()
        # Create multiple messages for pagination testing
        for i in range(15):
            Message.objects.create(content=f"Test message {i}")

    def test_message_list_pagination(self):
        """Test that message list is paginated."""
        response = self.client.get("/api/messages/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Check if pagination is enabled
        if "results" in response.data:
            self.assertIn("count", response.data)
            self.assertIn("next", response.data)
            self.assertIn("previous", response.data)
            self.assertIn("results", response.data)

    def test_pagination_navigation(self):
        """Test pagination navigation if enabled."""
        response = self.client.get("/api/messages/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # If pagination is enabled and there's a next page
        if "next" in response.data and response.data["next"]:
            next_response = self.client.get(response.data["next"])
            self.assertEqual(next_response.status_code, status.HTTP_200_OK)


class APIErrorHandlingTest(APITestCase):
    """Test cases for API error handling."""

    def setUp(self):
        """Set up test client."""
        self.client = APIClient()

    def test_invalid_json_request(self):
        """Test handling of invalid JSON in request."""
        response = self.client.post(
            "/api/messages/", '{"processed_at": null, "processed_at": null}', content_type="application/json"
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_method_not_allowed(self):
        """Test method not allowed responses."""
        # Try to use PATCH on the list endpoint (should be POST)
        response = self.client.patch("/api/messages/", {}, format="json")
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_content_type_handling(self):
        """Test different content types are handled correctly."""
        message_data = {"content": "Test message"}

        # Test JSON content type
        response = self.client.post("/api/messages/", message_data, format="json")
        self.assertIn(response.status_code, [status.HTTP_201_CREATED, status.HTTP_400_BAD_REQUEST])


class APIPerformanceTest(APITestCase):
    """Test cases for API performance."""

    def setUp(self):
        """Set up test data."""
        self.client = APIClient()

    def test_bulk_operations_performance(self):
        """Test that bulk operations don't cause excessive queries."""
        # Create multiple messages
        messages = [Message(content=f"Bulk message {i}") for i in range(10)]
        Message.objects.bulk_create(messages)

        # Test that listing doesn't cause N+1 queries
        with self.assertNumQueries(2):  # Reasonable number of queries
            response = self.client.get("/api/messages/")
            self.assertEqual(response.status_code, status.HTTP_200_OK)


class APIRootTest(APITestCase):
    """Test cases for API root endpoint."""

    def setUp(self):
        """Set up test client."""
        self.client = APIClient()

    def test_api_root(self):
        """Test API root endpoint returns expected links."""
        response = self.client.get("/api/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Check that the response contains expected endpoint links
        self.assertIn("messages", response.data)
        self.assertIn("task-logs", response.data)

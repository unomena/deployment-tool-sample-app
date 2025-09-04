"""
Unit tests for health check endpoints.
"""

from django.test import TestCase, Client
from unittest.mock import patch, MagicMock
from ..models import Message, TaskLog


class HealthCheckTest(TestCase):
    """Test cases for health check endpoints."""

    def setUp(self):
        """Set up test data."""
        self.client = Client()
        # Create some test data
        self.message = Message.objects.create(content="Health check test message")
        TaskLog.objects.create(task_id="health-test-task", task_name="test_task", status="SUCCESS")

    def test_liveness_check(self):
        """Test liveness probe endpoint."""
        response = self.client.get("/health/liveness/")

        self.assertEqual(response.status_code, 200)
        data = response.json()

        self.assertEqual(data["status"], "alive")
        self.assertIn("timestamp", data)
        self.assertIn("message", data)
        self.assertEqual(data["message"], "Application is alive and responding")

    @patch("redis.from_url")
    def test_readiness_check_success(self, mock_redis):
        """Test readiness probe endpoint when all services are ready."""
        # Mock Redis connection
        mock_redis_instance = MagicMock()
        mock_redis_instance.ping.return_value = True
        mock_redis.return_value = mock_redis_instance

        response = self.client.get("/health/readiness/")

        self.assertEqual(response.status_code, 200)
        data = response.json()

        self.assertEqual(data["status"], "ready")
        self.assertIn("timestamp", data)
        self.assertEqual(data["message"], "Application is ready to serve traffic")

    @patch("redis.from_url")
    def test_readiness_check_failure(self, mock_redis):
        """Test readiness probe endpoint when services are not ready."""
        # Mock Redis connection failure
        mock_redis.side_effect = Exception("Redis connection failed")

        response = self.client.get("/health/readiness/")

        self.assertEqual(response.status_code, 503)
        data = response.json()

        self.assertEqual(data["status"], "not_ready")
        self.assertIn("timestamp", data)
        self.assertIn("Application not ready", data["message"])

    @patch("celery.current_app.control.inspect")
    @patch("redis.from_url")
    def test_comprehensive_health_check_healthy(self, mock_redis, mock_inspect):
        """Test comprehensive health check when all systems are healthy."""
        # Mock Redis with proper return value matching
        mock_redis_instance = MagicMock()

        def mock_get(key):
            # Return the same value that was set
            if hasattr(mock_redis_instance, "_test_value"):
                return mock_redis_instance._test_value
            return b"test_value"

        def mock_set(key, value, ex=None):
            # Store the value for later retrieval
            mock_redis_instance._test_value = value.encode() if isinstance(value, str) else value
            return True

        mock_redis_instance.set.side_effect = mock_set
        mock_redis_instance.get.side_effect = mock_get
        mock_redis_instance.delete.return_value = 1
        mock_redis.return_value = mock_redis_instance

        # Mock Celery
        mock_inspect_instance = MagicMock()
        mock_inspect_instance.active.return_value = {"worker1": []}
        mock_inspect.return_value = mock_inspect_instance

        response = self.client.get("/health/")

        self.assertEqual(response.status_code, 200)
        data = response.json()

        self.assertEqual(data["status"], "healthy")
        self.assertIn("timestamp", data)
        self.assertIn("checks", data)
        self.assertIn("summary", data)
        self.assertIn("response_time_ms", data)

        # Check individual components
        self.assertEqual(data["checks"]["database"]["status"], "healthy")
        self.assertEqual(data["checks"]["redis"]["status"], "healthy")
        self.assertEqual(data["checks"]["celery"]["status"], "healthy")
        self.assertEqual(data["checks"]["application"]["status"], "healthy")

    @patch("celery.current_app.control.inspect")
    @patch("redis.from_url")
    def test_comprehensive_health_check_unhealthy(self, mock_redis, mock_inspect):
        """Test comprehensive health check when some systems are unhealthy."""
        # Mock Redis failure
        mock_redis.side_effect = Exception("Redis connection failed")

        # Mock Celery failure
        mock_inspect_instance = MagicMock()
        mock_inspect.return_value = mock_inspect_instance
        mock_inspect_instance.active.return_value = None  # No active workers

        response = self.client.get("/health/")

        self.assertEqual(response.status_code, 503)
        data = response.json()
        self.assertEqual(data["status"], "unhealthy")
        self.assertEqual(data["checks"]["redis"]["status"], "unhealthy")
        self.assertEqual(data["checks"]["celery"]["status"], "unhealthy")

        # Check that some components failed
        self.assertEqual(data["checks"]["database"]["status"], "healthy")  # DB should still work
        self.assertEqual(data["checks"]["redis"]["status"], "unhealthy")
        self.assertEqual(data["checks"]["celery"]["status"], "unhealthy")

        # Check summary shows failures
        self.assertGreater(data["summary"]["failed"], 0)

    def test_database_health_check_details(self):
        """Test database health check returns detailed information."""
        response = self.client.get("/health/")
        data = response.json()

        db_check = data["checks"]["database"]
        self.assertEqual(db_check["status"], "healthy")
        self.assertIn("details", db_check)
        self.assertIn("connection_test", db_check["details"])
        self.assertIn("table_access", db_check["details"])
        self.assertIn("message_count", db_check["details"])
        self.assertIn("database_name", db_check["details"])

        # Verify message count matches our test data
        self.assertEqual(db_check["details"]["message_count"], 1)

    @patch("celery.current_app.control.inspect")
    @patch("redis.from_url")
    def test_redis_health_check_details(self, mock_redis, mock_inspect):
        """Test Redis health check returns detailed information."""
        # Mock Redis with proper return value matching
        mock_redis_instance = MagicMock()

        def mock_get(key):
            if hasattr(mock_redis_instance, "_test_value"):
                return mock_redis_instance._test_value
            return b"test_value"

        def mock_set(key, value, ex=None):
            mock_redis_instance._test_value = value.encode() if isinstance(value, str) else value
            return True

        mock_redis_instance.set.side_effect = mock_set
        mock_redis_instance.get.side_effect = mock_get
        mock_redis_instance.delete.return_value = 1
        mock_redis.return_value = mock_redis_instance

        # Mock Celery
        mock_inspect_instance = MagicMock()
        mock_inspect_instance.active.return_value = {"worker1": []}
        mock_inspect.return_value = mock_inspect_instance

        response = self.client.get("/health/")

        self.assertEqual(response.status_code, 200)
        data = response.json()
        redis_check = data["checks"]["redis"]
        self.assertEqual(redis_check["status"], "healthy")
        self.assertIn("connection_test", redis_check["details"])
        self.assertIn("read_write_test", redis_check["details"])
        self.assertIn("redis_url", redis_check["details"])

    def test_application_health_check_details(self):
        """Test application health check returns detailed information."""
        response = self.client.get("/health/")
        data = response.json()

        app_check = data["checks"]["application"]
        self.assertEqual(app_check["status"], "healthy")
        self.assertIn("details", app_check)
        self.assertIn("total_messages", app_check["details"])
        self.assertIn("processed_messages", app_check["details"])
        self.assertIn("total_tasks", app_check["details"])
        self.assertIn("recent_messages_24h", app_check["details"])
        self.assertIn("recent_tasks_24h", app_check["details"])
        self.assertIn("processing_rate", app_check["details"])

    def test_health_check_response_time(self):
        """Test that health check includes response time measurement."""
        response = self.client.get("/health/")
        data = response.json()

        self.assertIn("response_time_ms", data)
        self.assertIsInstance(data["response_time_ms"], (int, float))
        self.assertGreater(data["response_time_ms"], 0)

    def test_health_check_caching_headers(self):
        """Test that health check endpoints have proper caching headers."""
        endpoints = ["/health/", "/health/readiness/", "/health/liveness/"]

        for endpoint in endpoints:
            response = self.client.get(endpoint)

            # Should have cache control headers to prevent caching
            self.assertIn("Cache-Control", response)
            cache_control = response["Cache-Control"]
            self.assertIn("no-cache", cache_control.lower())

    def test_health_check_content_type(self):
        """Test that health check endpoints return JSON content type."""
        endpoints = ["/health/", "/health/readiness/", "/health/liveness/"]

        for endpoint in endpoints:
            response = self.client.get(endpoint)
            self.assertEqual(response["Content-Type"], "application/json")

    def test_health_check_http_methods(self):
        """Test that health check endpoints only accept GET requests."""
        endpoints = ["/health/", "/health/readiness/", "/health/liveness/"]

        for endpoint in endpoints:
            # GET should work
            response = self.client.get(endpoint)
            self.assertIn(response.status_code, [200, 503])

            # POST should not be allowed
            response = self.client.post(endpoint)
            self.assertEqual(response.status_code, 405)

            # PUT should not be allowed
            response = self.client.put(endpoint)
            self.assertEqual(response.status_code, 405)

            # DELETE should not be allowed
            response = self.client.delete(endpoint)
            self.assertEqual(response.status_code, 405)


class HealthCheckIntegrationTest(TestCase):
    """Integration tests for health check functionality."""

    def setUp(self):
        """Set up test data."""
        self.client = Client()

    def test_health_check_with_real_database(self):
        """Test health check with actual database operations."""
        # Create some test data
        messages = []
        for i in range(5):
            message = Message.objects.create(content=f"Integration test message {i}")
            messages.append(message)

        # Mark some as processed
        for message in messages[:3]:
            message.processed_at = message.created_at
            message.save()

        response = self.client.get("/health/")
        data = response.json()

        # Verify database check reflects actual data
        db_check = data["checks"]["database"]
        self.assertEqual(db_check["status"], "healthy")
        self.assertEqual(db_check["details"]["message_count"], 5)

        # Verify application check reflects processing
        app_check = data["checks"]["application"]
        self.assertEqual(app_check["details"]["total_messages"], 5)
        self.assertEqual(app_check["details"]["processed_messages"], 3)
        self.assertEqual(app_check["details"]["processing_rate"], 60.0)  # 3/5 * 100

    def test_health_check_performance(self):
        """Test that health check completes within reasonable time."""
        import time

        start_time = time.time()
        response = self.client.get("/health/")
        end_time = time.time()

        # Health check should complete within 5 seconds
        self.assertLess(end_time - start_time, 5.0)

        # Response should include timing information
        data = response.json()
        self.assertIn("response_time_ms", data)

        # Reported time should be reasonable
        reported_time_seconds = data["response_time_ms"] / 1000
        actual_time = end_time - start_time

        # Allow some variance but should be in the same ballpark
        self.assertLess(abs(reported_time_seconds - actual_time), 1.0)

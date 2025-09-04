"""
Health check views for system monitoring and deployment verification.
"""

import time
from django.http import JsonResponse
from django.db import connection
from django.views.decorators.http import require_http_methods
from django.views.decorators.cache import never_cache
from django.conf import settings
from celery import current_app
import redis
import logging

logger = logging.getLogger(__name__)


@require_http_methods(["GET"])
@never_cache
def health_check(request):
    """
    Comprehensive health check endpoint that verifies all system components.
    Returns detailed status of database, Redis, Celery, and overall system health.
    """
    start_time = time.time()
    health_status = {
        "status": "healthy",
        "timestamp": time.time(),
        "checks": {},
        "summary": {"total_checks": 0, "passed": 0, "failed": 0},
    }

    # Database connectivity check
    db_check = check_database()
    health_status["checks"]["database"] = db_check

    # Redis connectivity check
    redis_check = check_redis()
    health_status["checks"]["redis"] = redis_check

    # Celery worker check
    celery_check = check_celery()
    health_status["checks"]["celery"] = celery_check

    # Application-specific checks
    app_check = check_application()
    health_status["checks"]["application"] = app_check

    # Calculate summary
    all_checks = [db_check, redis_check, celery_check, app_check]
    health_status["summary"]["total_checks"] = len(all_checks)
    health_status["summary"]["passed"] = sum(1 for check in all_checks if check["status"] == "healthy")
    health_status["summary"]["failed"] = sum(1 for check in all_checks if check["status"] != "healthy")

    # Overall status
    if health_status["summary"]["failed"] > 0:
        health_status["status"] = "unhealthy"

    # Response time
    health_status["response_time_ms"] = round((time.time() - start_time) * 1000, 2)

    # HTTP status code based on health
    status_code = 200 if health_status["status"] == "healthy" else 503

    return JsonResponse(health_status, status=status_code)


def check_database():
    """Check database connectivity and basic operations."""
    try:
        # Test database connection
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            cursor.fetchone()

        # Test table access
        from ..models import Message

        message_count = Message.objects.count()

        return {
            "status": "healthy",
            "message": "Database connection successful",
            "details": {
                "connection_test": "passed",
                "table_access": "passed",
                "message_count": message_count,
                "database_name": connection.settings_dict.get("NAME", "unknown"),
            },
        }
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        return {
            "status": "unhealthy",
            "message": f"Database connection failed: {str(e)}",
            "details": {"error": str(e), "connection_test": "failed"},
        }


def check_redis():
    """Check Redis connectivity and basic operations."""
    try:
        # Get Redis URL from Celery settings
        redis_url = getattr(settings, "CELERY_BROKER_URL", "redis://localhost:6379/0")

        # Connect to Redis
        r = redis.from_url(redis_url)

        # Test basic operations
        test_key = "health_check_test"
        test_value = str(time.time())

        # Set and get test
        r.set(test_key, test_value, ex=10)  # Expire in 10 seconds
        retrieved_value = r.get(test_key)

        # Clean up
        r.delete(test_key)

        # Verify operation
        if retrieved_value and retrieved_value.decode() == test_value:
            return {
                "status": "healthy",
                "message": "Redis connection successful",
                "details": {
                    "connection_test": "passed",
                    "read_write_test": "passed",
                    "redis_url": redis_url.split("@")[-1] if "@" in redis_url else redis_url,  # Hide credentials
                },
            }
        else:
            return {
                "status": "unhealthy",
                "message": "Redis read/write test failed",
                "details": {"connection_test": "passed", "read_write_test": "failed"},
            }

    except Exception as e:
        logger.error(f"Redis health check failed: {e}")
        return {
            "status": "unhealthy",
            "message": f"Redis connection failed: {str(e)}",
            "details": {"error": str(e), "connection_test": "failed"},
        }


def check_celery():
    """Check Celery worker availability and task queue."""
    try:
        # Get Celery app instance
        celery_app = current_app

        # Check if workers are available
        inspect = celery_app.control.inspect()
        active_workers = inspect.active()

        if active_workers:
            worker_count = len(active_workers)
            worker_names = list(active_workers.keys())

            return {
                "status": "healthy",
                "message": f"Celery workers available: {worker_count}",
                "details": {
                    "worker_count": worker_count,
                    "worker_names": worker_names,
                    "broker_url": (
                        celery_app.conf.broker_url.split("@")[-1]
                        if "@" in celery_app.conf.broker_url
                        else celery_app.conf.broker_url
                    ),
                },
            }
        else:
            return {
                "status": "unhealthy",
                "message": "No Celery workers available",
                "details": {"worker_count": 0, "worker_names": [], "issue": "No active workers found"},
            }

    except Exception as e:
        logger.error(f"Celery health check failed: {e}")
        return {
            "status": "unhealthy",
            "message": f"Celery check failed: {str(e)}",
            "details": {"error": str(e), "worker_check": "failed"},
        }


def check_application():
    """Check application-specific health indicators."""
    try:
        from ..models import Message, TaskLog

        # Check model access
        total_messages = Message.objects.count()
        processed_messages = Message.objects.filter(processed_at__isnull=False).count()
        total_tasks = TaskLog.objects.count()

        # Check recent activity (last 24 hours)
        from django.utils import timezone
        from datetime import timedelta

        recent_cutoff = timezone.now() - timedelta(hours=24)
        recent_messages = Message.objects.filter(created_at__gte=recent_cutoff).count()
        recent_tasks = TaskLog.objects.filter(started_at__gte=recent_cutoff).count()

        return {
            "status": "healthy",
            "message": "Application components working",
            "details": {
                "total_messages": total_messages,
                "processed_messages": processed_messages,
                "total_tasks": total_tasks,
                "recent_messages_24h": recent_messages,
                "recent_tasks_24h": recent_tasks,
                "processing_rate": round((processed_messages / total_messages * 100), 2) if total_messages > 0 else 0,
            },
        }

    except Exception as e:
        logger.error(f"Application health check failed: {e}")
        return {
            "status": "unhealthy",
            "message": f"Application check failed: {str(e)}",
            "details": {"error": str(e), "model_access": "failed"},
        }


@require_http_methods(["GET"])
@never_cache
def readiness_check(request):
    """
    Readiness probe - checks if the application is ready to serve traffic.
    This is a lighter check focused on critical dependencies.
    """
    try:
        # Quick database check
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")

        # Quick Redis check
        redis_url = getattr(settings, "CELERY_BROKER_URL", "redis://localhost:6379/0")
        r = redis.from_url(redis_url)
        r.ping()

        return JsonResponse(
            {"status": "ready", "timestamp": time.time(), "message": "Application is ready to serve traffic"}
        )

    except Exception as e:
        logger.error(f"Readiness check failed: {e}")
        return JsonResponse(
            {"status": "not_ready", "timestamp": time.time(), "message": f"Application not ready: {str(e)}"}, status=503
        )


@require_http_methods(["GET"])
@never_cache
def liveness_check(request):
    """
    Liveness probe - checks if the application is alive and responding.
    This is the most basic check.
    """
    return JsonResponse({"status": "alive", "timestamp": time.time(), "message": "Application is alive and responding"})

#!/usr/bin/env python
"""
Test runner script for deployment validation.
This script runs the Django test suite and provides detailed output for CI/CD integration.
"""

import os
import sys
import django
from django.conf import settings
from django.test.utils import get_runner
import json
from datetime import datetime


def setup_django():
    """Set up Django environment for testing."""
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "sampleapp.settings")
    django.setup()


def run_tests(verbosity=2, pattern=None, failfast=False):
    """
    Run Django tests with specified options.

    Args:
        verbosity (int): Verbosity level (0-3)
        pattern (str): Test pattern to match
        failfast (bool): Stop on first failure

    Returns:
        dict: Test results summary
    """
    TestRunner = get_runner(settings)
    test_runner = TestRunner(verbosity=verbosity, interactive=False, failfast=failfast)

    # Determine which tests to run
    test_labels = []
    if pattern:
        test_labels = [pattern]
    else:
        # Run all messageapp tests
        test_labels = ["messageapp"]

    print(f"Running tests: {test_labels}")
    print("=" * 70)

    # Run the tests
    start_time = datetime.now()
    failures = test_runner.run_tests(test_labels)
    end_time = datetime.now()

    duration = (end_time - start_time).total_seconds()

    return {
        "failures": failures,
        "duration": duration,
        "start_time": start_time.isoformat(),
        "end_time": end_time.isoformat(),
        "success": failures == 0,
    }


def run_coverage_tests():
    """Run tests with coverage reporting if coverage is available."""
    try:
        import coverage

        print("Running tests with coverage...")
        print("=" * 70)

        # Start coverage
        cov = coverage.Coverage()
        cov.start()

        # Run tests
        result = run_tests(verbosity=1)

        # Stop coverage and generate report
        cov.stop()
        cov.save()

        print("\nCoverage Report:")
        print("-" * 50)
        cov.report(show_missing=True)

        return result

    except ImportError:
        print("Coverage not available, running tests without coverage...")
        return run_tests()


def run_specific_test_categories():
    """Run tests by category for detailed reporting."""
    categories = {
        "models": "messageapp.test_models",
        "api": "messageapp.test_api",
        "health": "messageapp.test_health",
        "tasks": "messageapp.test_tasks",
    }

    results = {}
    total_failures = 0

    print("Running tests by category...")
    print("=" * 70)

    for category, test_module in categories.items():
        print(f"\n🧪 Running {category.upper()} tests...")
        print("-" * 50)

        result = run_tests(verbosity=1, pattern=test_module)
        results[category] = result
        total_failures += result["failures"]

        status = "✅ PASSED" if result["success"] else "❌ FAILED"
        print(f"{status} - {category} tests completed in {result['duration']:.2f}s")

    return results, total_failures


def check_test_database():
    """Verify test database setup."""
    try:
        from django.db import connection

        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
        print("✅ Test database connection: OK")
        return True
    except Exception as e:
        print(f"❌ Test database connection failed: {e}")
        return False


def run_health_check_validation():
    """Run a quick health check validation."""
    try:
        from django.test import Client

        client = Client()

        # Test liveness endpoint
        response = client.get("/health/liveness/")
        if response.status_code == 200:
            print("✅ Liveness endpoint: OK")
        else:
            print(f"❌ Liveness endpoint failed: {response.status_code}")
            return False

        # Test readiness endpoint (may fail in test environment, that's OK)
        response = client.get("/health/readiness/")
        if response.status_code in [200, 503]:
            print("✅ Readiness endpoint: OK")
        else:
            print(f"❌ Readiness endpoint unexpected status: {response.status_code}")

        return True

    except Exception as e:
        print(f"❌ Health check validation failed: {e}")
        return False


def main():
    """Main test runner function."""
    import argparse

    parser = argparse.ArgumentParser(description="Run Django tests for deployment validation")
    parser.add_argument("--coverage", action="store_true", help="Run with coverage reporting")
    parser.add_argument("--categories", action="store_true", help="Run tests by category")
    parser.add_argument("--pattern", help="Specific test pattern to run")
    parser.add_argument("--failfast", action="store_true", help="Stop on first failure")
    parser.add_argument("--health-check", action="store_true", help="Run health check validation")
    parser.add_argument("--json-output", help="Output results to JSON file")

    args = parser.parse_args()

    print("🚀 Django Test Runner for Deployment Validation")
    print("=" * 70)
    print(f"Timestamp: {datetime.now().isoformat()}")
    print(f"Python: {sys.version}")
    print(f"Django: {django.get_version()}")
    print()

    # Setup Django
    setup_django()

    # Check database connection
    if not check_test_database():
        sys.exit(1)

    # Run health check validation if requested
    if args.health_check:
        print("\n🏥 Running health check validation...")
        print("-" * 50)
        if not run_health_check_validation():
            sys.exit(1)

    # Run tests based on arguments
    if args.coverage:
        result = run_coverage_tests()
        total_failures = result["failures"]
    elif args.categories:
        results, total_failures = run_specific_test_categories()
        result = {"failures": total_failures, "success": total_failures == 0}
    else:
        result = run_tests(verbosity=2, pattern=args.pattern, failfast=args.failfast)
        total_failures = result["failures"]

    # Print summary
    print("\n" + "=" * 70)
    print("📊 TEST SUMMARY")
    print("=" * 70)

    if total_failures == 0:
        print("✅ ALL TESTS PASSED")
        exit_code = 0
    else:
        print(f"❌ {total_failures} TEST(S) FAILED")
        exit_code = 1

    if "duration" in result:
        print(f"⏱️  Total duration: {result['duration']:.2f} seconds")

    # Output JSON results if requested
    if args.json_output:
        with open(args.json_output, "w") as f:
            json.dump(result, f, indent=2)
        print(f"📄 Results saved to: {args.json_output}")

    print("=" * 70)
    sys.exit(exit_code)


if __name__ == "__main__":
    main()

# Makefile for Sample Django Application
# Provides commands for local development, testing, and deployment

# Variables
PYTHON := python3
PIP := pip3
VENV_DIR := .venv
PYTHON_VENV := $(VENV_DIR)/bin/python
PIP_VENV := $(VENV_DIR)/bin/pip
SRC_DIR := src
MANAGE := $(PYTHON_VENV) $(SRC_DIR)/manage.py

# Default environment variables for local development
export DJANGO_SETTINGS_MODULE := sampleapp.settings
export SECRET_KEY := django-insecure-local-dev-key-change-in-production
export DEBUG := True
export ALLOWED_HOSTS := localhost,127.0.0.1,0.0.0.0
export DB_NAME := sampleapp_local
export DB_USER := sampleapp_user
export DB_PASSWORD := sampleapp_password
export DB_HOST := localhost
export DB_PORT := 5432
export REDIS_URL := redis://localhost:6379/0
export DEFAULT_SUPERUSER_USERNAME := admin
export DEFAULT_SUPERUSER_PASSWORD := admin123
export DEFAULT_SUPERUSER_EMAIL := admin@sampleapp.local

# Colors for output
GREEN := \033[0;32m
YELLOW := \033[1;33m
RED := \033[0;31m
NC := \033[0m # No Color

.PHONY: help build install clean test test-models test-api test-health test-tasks test-coverage test-fast run worker beat superuser migrate shell lint format check deps-check services-check all

# Default target
help: ## Show this help message
	@echo "$(GREEN)Sample Django Application - Available Commands:$(NC)"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  $(YELLOW)%-20s$(NC) %s\n", $$1, $$2}'
	@echo ""
	@echo "$(GREEN)Quick Start:$(NC)"
	@echo "  1. make deps-check    # Check system dependencies"
	@echo "  2. make build         # Set up development environment"
	@echo "  3. make services-check # Check PostgreSQL and Redis"
	@echo "  4. make migrate       # Set up database"
	@echo "  5. make superuser     # Create admin user"
	@echo "  6. make all           # Start all services"

build: ## Set up development environment
	@echo "$(GREEN)Setting up development environment...$(NC)"
	$(PYTHON) -m venv $(VENV_DIR)
	$(PIP_VENV) install --upgrade pip
	$(PIP_VENV) install -r requirements.txt
	@echo "$(GREEN)✓ Development environment ready$(NC)"

install: build ## Alias for build

clean: ## Clean up generated files and virtual environment
	@echo "$(YELLOW)Cleaning up...$(NC)"
	rm -rf $(VENV_DIR)
	rm -rf $(SRC_DIR)/__pycache__
	rm -rf $(SRC_DIR)/*/__pycache__
	rm -rf $(SRC_DIR)/*/*/__pycache__
	rm -rf $(SRC_DIR)/staticfiles
	find $(SRC_DIR) -name "*.pyc" -delete
	find $(SRC_DIR) -name "*.pyo" -delete
	find $(SRC_DIR) -name "__pycache__" -type d -exec rm -rf {} +
	@echo "$(GREEN)✓ Cleanup complete$(NC)"

deps-check: ## Check system dependencies
	@echo "$(GREEN)Checking system dependencies...$(NC)"
	@command -v $(PYTHON) >/dev/null 2>&1 || { echo "$(RED)✗ Python 3 not found$(NC)"; exit 1; }
	@command -v $(PIP) >/dev/null 2>&1 || { echo "$(RED)✗ pip3 not found$(NC)"; exit 1; }
	@command -v psql >/dev/null 2>&1 || { echo "$(RED)✗ PostgreSQL client not found. Install with: sudo apt-get install postgresql-client$(NC)"; exit 1; }
	@command -v redis-cli >/dev/null 2>&1 || { echo "$(RED)✗ Redis client not found. Install with: sudo apt-get install redis-tools$(NC)"; exit 1; }
	@echo "$(GREEN)✓ All system dependencies found$(NC)"

services-check: ## Check if PostgreSQL and Redis services are running
	@echo "$(GREEN)Checking services...$(NC)"
	@pg_isready -h $(DB_HOST) -p $(DB_PORT) >/dev/null 2>&1 || { echo "$(RED)✗ PostgreSQL not running on $(DB_HOST):$(DB_PORT)$(NC)"; echo "  Start with: sudo systemctl start postgresql"; exit 1; }
	@redis-cli -u $(REDIS_URL) ping >/dev/null 2>&1 || { echo "$(RED)✗ Redis not running$(NC)"; echo "  Start with: sudo systemctl start redis-server"; exit 1; }
	@echo "$(GREEN)✓ PostgreSQL and Redis are running$(NC)"

migrate: $(VENV_DIR) ## Run database migrations
	@echo "$(GREEN)Running database migrations...$(NC)"
	$(MANAGE) makemigrations
	$(MANAGE) migrate
	@echo "$(GREEN)✓ Database migrations complete$(NC)"

superuser: $(VENV_DIR) ## Create Django superuser
	@echo "$(GREEN)Creating Django superuser...$(NC)"
	@echo "Username: $(DEFAULT_SUPERUSER_USERNAME)"
	@echo "Email: $(DEFAULT_SUPERUSER_EMAIL)"
	@echo "Password: $(DEFAULT_SUPERUSER_PASSWORD)"
	@echo "from django.contrib.auth import get_user_model; User = get_user_model(); User.objects.filter(username='$(DEFAULT_SUPERUSER_USERNAME)').exists() or User.objects.create_superuser('$(DEFAULT_SUPERUSER_USERNAME)', '$(DEFAULT_SUPERUSER_EMAIL)', '$(DEFAULT_SUPERUSER_PASSWORD)')" | $(MANAGE) shell
	@echo "$(GREEN)✓ Superuser ready$(NC)"

shell: $(VENV_DIR) ## Open Django shell
	$(MANAGE) shell

run: $(VENV_DIR) ## Start Django development server
	@echo "$(GREEN)Starting Django development server...$(NC)"
	@echo "$(YELLOW)Access the app at: http://localhost:8000$(NC)"
	$(MANAGE) runserver 0.0.0.0:8005

worker: $(VENV_DIR) ## Start Celery worker
	@echo "$(GREEN)Starting Celery worker...$(NC)"
	cd $(SRC_DIR) && ../$(PYTHON_VENV) -m celery -A sampleapp worker -l info

beat: $(VENV_DIR) ## Start Celery beat scheduler
	@echo "$(GREEN)Starting Celery beat scheduler...$(NC)"
	cd $(SRC_DIR) && ../$(PYTHON_VENV) -m celery -A sampleapp beat -l info

test: $(VENV_DIR) ## Run all tests with Django test framework
	@echo "$(GREEN)Running all tests with Django test framework...$(NC)"
	$(MANAGE) test messageapp.tests --verbosity=2
	@echo "$(GREEN)✓ All tests complete$(NC)"

test-models: $(VENV_DIR) ## Run model tests only
	@echo "$(GREEN)Running model tests...$(NC)"
	$(MANAGE) test messageapp.tests.test_models --verbosity=2
	@echo "$(GREEN)✓ Model tests complete$(NC)"

test-api: $(VENV_DIR) ## Run API tests only
	@echo "$(GREEN)Running API tests...$(NC)"
	$(MANAGE) test messageapp.tests.test_api --verbosity=2
	@echo "$(GREEN)✓ API tests complete$(NC)"

test-health: $(VENV_DIR) ## Run health check tests only
	@echo "$(GREEN)Running health check tests...$(NC)"
	$(MANAGE) test messageapp.tests.test_health --verbosity=2
	@echo "$(GREEN)✓ Health check tests complete$(NC)"

test-tasks: $(VENV_DIR) ## Run task tests only
	@echo "$(GREEN)Running task tests...$(NC)"
	$(MANAGE) test messageapp.tests.test_tasks --verbosity=2
	@echo "$(GREEN)✓ Task tests complete$(NC)"

test-coverage: $(VENV_DIR) ## Run tests with coverage report
	@echo "$(GREEN)Running tests with coverage...$(NC)"
	$(PIP_VENV) install coverage >/dev/null 2>&1
	$(VENV_DIR)/bin/coverage run --source='.' $(SRC_DIR)/manage.py test messageapp.tests
	$(VENV_DIR)/bin/coverage report
	@echo "$(GREEN)✓ Coverage report complete$(NC)"

test-fast: $(VENV_DIR) ## Run tests with minimal output
	@echo "$(GREEN)Running tests (fast mode)...$(NC)"
	$(MANAGE) test messageapp.tests --verbosity=1 --failfast
	@echo "$(GREEN)✓ Fast tests complete$(NC)"

lint: $(VENV_DIR) ## Run code linting
	@echo "$(GREEN)Running code linting...$(NC)"
	$(PIP_VENV) install flake8 >/dev/null 2>&1
	$(VENV_DIR)/bin/flake8 $(SRC_DIR) --max-line-length=120 --exclude=migrations
	@echo "$(GREEN)✓ Linting complete$(NC)"

format: $(VENV_DIR) ## Format code with black
	@echo "$(GREEN)Formatting code...$(NC)"
	$(PIP_VENV) install black >/dev/null 2>&1
	$(VENV_DIR)/bin/black $(SRC_DIR) --line-length=120
	@echo "$(GREEN)✓ Code formatting complete$(NC)"

check: $(VENV_DIR) ## Run Django system checks
	@echo "$(GREEN)Running Django system checks...$(NC)"
	$(MANAGE) check
	@echo "$(GREEN)✓ System checks passed$(NC)"

collectstatic: $(VENV_DIR) ## Collect static files
	@echo "$(GREEN)Collecting static files...$(NC)"
	$(MANAGE) collectstatic --noinput
	@echo "$(GREEN)✓ Static files collected$(NC)"

all: $(VENV_DIR) ## Start all services (web, worker, beat) in parallel
	@echo "$(GREEN)Starting all services...$(NC)"
	@echo "$(YELLOW)Press Ctrl+C to stop all services$(NC)"
	@echo ""
	@echo "$(GREEN)Services starting:$(NC)"
	@echo "  - Django server: http://localhost:8002"
	@echo "  - Celery worker: Background task processing"
	@echo "  - Celery beat: Periodic task scheduler"
	@echo ""
	@trap 'kill 0' INT; \
	$(MANAGE) runserver 0.0.0.0:8002 & \
	cd $(SRC_DIR) && ../$(PYTHON_VENV) -m celery -A sampleapp worker -l info & \
	cd $(SRC_DIR) && ../$(PYTHON_VENV) -m celery -A sampleapp beat -l info & \
	wait

# Ensure virtual environment exists for targets that need it
$(VENV_DIR):
	@if [ ! -d "$(VENV_DIR)" ]; then \
		echo "$(YELLOW)Virtual environment not found. Run 'make build' first.$(NC)"; \
		exit 1; \
	fi

# Development workflow targets
dev-setup: deps-check build services-check migrate superuser ## Complete development setup
	@echo "$(GREEN)🎉 Development environment is ready!$(NC)"
	@echo ""
	@echo "$(GREEN)Next steps:$(NC)"
	@echo "  1. make all           # Start all services"
	@echo "  2. Open http://localhost:8000 in your browser"
	@echo "  3. Login to admin at http://localhost:8000/admin"
	@echo "     Username: $(DEFAULT_SUPERUSER_USERNAME)"
	@echo "     Password: $(DEFAULT_SUPERUSER_PASSWORD)"

reset-db: $(VENV_DIR) ## Reset database (WARNING: Destroys all data)
	@echo "$(RED)WARNING: This will destroy all database data!$(NC)"
	@read -p "Are you sure? [y/N] " -n 1 -r; \
	echo; \
	if [[ $$REPLY =~ ^[Yy]$$ ]]; then \
		echo "$(YELLOW)Resetting database...$(NC)"; \
		$(MANAGE) flush --noinput; \
		$(MANAGE) migrate; \
		echo "$(GREEN)✓ Database reset complete$(NC)"; \
	else \
		echo "$(GREEN)Database reset cancelled$(NC)"; \
	fi

logs: ## Show application logs (if any)
	@echo "$(GREEN)Application logs:$(NC)"
	@if [ -f "$(SRC_DIR)/logs/django.log" ]; then \
		tail -f $(SRC_DIR)/logs/django.log; \
	else \
		echo "$(YELLOW)No log files found. Logs will appear here when the application runs.$(NC)"; \
	fi

status: ## Show service status
	@echo "$(GREEN)Service Status:$(NC)"
	@echo -n "PostgreSQL: "
	@pg_isready -h $(DB_HOST) -p $(DB_PORT) >/dev/null 2>&1 && echo "$(GREEN)✓ Running$(NC)" || echo "$(RED)✗ Not running$(NC)"
	@echo -n "Redis: "
	@redis-cli -u $(REDIS_URL) ping >/dev/null 2>&1 && echo "$(GREEN)✓ Running$(NC)" || echo "$(RED)✗ Not running$(NC)"
	@echo -n "Virtual Environment: "
	@[ -d "$(VENV_DIR)" ] && echo "$(GREEN)✓ Ready$(NC)" || echo "$(RED)✗ Not created$(NC)"

# Sample Django Application

A demonstration Django REST API application showcasing modular architecture with Celery task processing, comprehensive health checks, and extensive test coverage. Built with PostgreSQL and Redis integration, designed for deployment with PyDeployer.

## Features

- **Django REST API**: Full REST API with Django REST Framework
- **Modular Architecture**: Clean separation with api/, health/, and tests/ sub-packages
- **Celery Task Processing**: Asynchronous message processing with task logging
- **Celery Beat**: Periodic task scheduling
- **Health Checks**: Comprehensive health monitoring endpoints
- **PostgreSQL Database**: Message and task log storage
- **Redis**: Message broker for Celery
- **Admin Interface**: Django admin for data management
- **Extensive Testing**: 94% test coverage with 69 comprehensive tests

## Quick Start

### Prerequisites
- Python 3.11+
- PostgreSQL
- Redis
- Git

### Local Development Setup

1. **Clone and Setup**:
   ```bash
   git clone <repository-url>
   cd sample-app
   make help                    # See all available commands
   make deps-check             # Check system dependencies
   make dev-setup              # Complete setup (build + migrate + superuser)
   ```

2. **Start All Services**:
   ```bash
   make all                    # Starts Django, Celery worker, and Celery beat
   ```

3. **Access the Application**:
   - Web App: http://localhost:8005
   - Admin: http://localhost:8005/admin (admin/admin123)
   - API Root: http://localhost:8005/api/
   - Health Check: http://localhost:8005/health/
   - Status: http://localhost:8005/status/

### Available Make Commands

| Command | Description |
|---------|-------------|
| `make help` | Show all available commands |
| `make build` | Set up development environment |
| `make deps-check` | Check system dependencies |
| `make services-check` | Check PostgreSQL and Redis |
| `make dev-setup` | Complete development setup |
| `make migrate` | Run database migrations |
| `make superuser` | Create Django superuser |
| `make run` | Start Django development server |
| `make worker` | Start Celery worker |
| `make beat` | Start Celery beat scheduler |
| `make all` | Start all services in parallel |
| `make test` | Run all tests (69 tests) |
| `make test-api` | Run API tests only (23 tests) |
| `make test-health` | Run health check tests (14 tests) |
| `make test-models` | Run model tests (18 tests) |
| `make test-tasks` | Run task tests (14 tests) |
| `make test-fast` | Run tests with minimal output |
| `make test-coverage` | Run tests with coverage report |
| `make lint` | Run code linting |
| `make format` | Format code with black |
| `make clean` | Clean up generated files |
| `make reset-db` | Reset database (destroys data) |
| `make status` | Show service status |

## Application Structure

```
sample-app/
├── src/                          # Source code directory
│   ├── manage.py                 # Django management script
│   ├── sampleapp/               # Django project
│   │   ├── __init__.py
│   │   ├── settings.py          # Django settings
│   │   ├── urls.py              # URL configuration
│   │   ├── wsgi.py              # WSGI application
│   │   └── celery.py            # Celery configuration
│   ├── messageapp/              # Main Django app (modular structure)
│   │   ├── api/                 # API sub-package
│   │   │   ├── __init__.py
│   │   │   ├── urls.py          # API URL routing
│   │   │   └── views.py         # API ViewSets (Message, TaskLog)
│   │   ├── health/              # Health check sub-package
│   │   │   ├── __init__.py
│   │   │   ├── urls.py          # Health check URLs
│   │   │   └── views.py         # Health monitoring endpoints
│   │   ├── tests/               # Test sub-package
│   │   │   ├── __init__.py
│   │   │   ├── test_api.py      # API tests (23 tests)
│   │   │   ├── test_health.py   # Health check tests (14 tests)
│   │   │   ├── test_models.py   # Model tests (18 tests)
│   │   │   └── test_tasks.py    # Task tests (14 tests)
│   │   ├── models.py            # Database models (Message, TaskLog)
│   │   ├── serializers.py       # DRF serializers
│   │   ├── tasks.py             # Celery tasks
│   │   ├── views.py             # Basic web views
│   │   ├── forms.py             # Django forms
│   │   ├── urls.py              # Main app URLs
│   │   └── admin.py             # Admin configuration
│   ├── templates/               # HTML templates
│   │   ├── base.html
│   │   └── messageapp/
│   │       └── home.html
│   └── run_tests.py             # Test runner script
├── Makefile                     # Development automation
├── requirements.txt             # Python dependencies
├── deploy-dev.yml              # Development deployment config
├── deploy-stage.yml            # Staging deployment config
├── deploy-prod.yml             # Production deployment config
├── .gitignore                  # Git ignore rules
└── README.md                   # This file
```

## Functionality

### REST API Endpoints
- **Messages API**: Full CRUD operations for messages with async processing
- **Task Logs API**: Read-only access to task execution logs with filtering
- **Health Checks**: Comprehensive monitoring of database, Redis, and Celery
- **Status Endpoint**: Application statistics and system information

### Web Interface
- **Home Page**: Message submission form and display
- **Admin Interface**: Django admin for data management
- **API Browser**: Django REST Framework browsable API

### Celery Tasks
- **Message Processing**: Processes user-submitted messages asynchronously (2-second delay simulation)
- **Periodic Tasks**: Creates system messages every minute via Celery Beat
- **Task Logging**: Tracks all task executions with status and results
- **Error Handling**: Retry mechanisms and comprehensive error logging

### Database Models
- **Message**: Stores user messages with creation and processing timestamps
- **TaskLog**: Logs Celery task executions for monitoring and debugging

### Health Monitoring
- **Liveness Probe**: Basic application health check
- **Readiness Probe**: Checks database and Redis connectivity
- **Comprehensive Health**: Detailed system status with response times

## Environment Configuration

The application uses environment variables for configuration. Default values for local development are set in the Makefile:

```bash
# Database (application credentials)
DB_NAME=sampleapp_local
DB_USER=sampleapp_user
DB_PASSWORD=sampleapp_password
DB_HOST=localhost
DB_PORT=5432

# Redis
REDIS_URL=redis://localhost:6379/0

# Django
SECRET_KEY=django-insecure-local-dev-key
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1,0.0.0.0

# Superuser
DEFAULT_SUPERUSER_USERNAME=admin
DEFAULT_SUPERUSER_PASSWORD=admin123
DEFAULT_SUPERUSER_EMAIL=admin@sampleapp.local
```

## Production Deployment with PyDeployer

This application demonstrates database credential separation:

### Database Credential Separation
- **Root Credentials**: Stored in server config (`config.yml`), used only for database creation
- **Application Credentials**: Defined in `deploy-dev.yml`, used by Django for all operations

### Deployment Process
```bash
./deploy https://github.com/yourusername/sampleapp.git main dev
```

The deployment will:
1. Use root credentials to create PostgreSQL database and user
2. Install dependencies and run migrations with application credentials
3. Start three services: Gunicorn web server, Celery worker, Celery beat
4. Create Django superuser
5. Perform health checks

### Services Configuration
- **Web**: Gunicorn WSGI server (port 8000, 2 workers)
- **Worker**: Celery worker processes (2 workers)
- **Beat**: Celery beat scheduler for periodic tasks

## API Endpoints

### REST API
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/` | GET | API root with endpoint discovery |
| `/api/messages/` | GET, POST | List/create messages |
| `/api/messages/{id}/` | GET, PUT, PATCH, DELETE | Message detail operations |
| `/api/messages/{id}/process_async/` | POST | Trigger async message processing |
| `/api/task-logs/` | GET | List task logs with filtering |
| `/api/task-logs/{id}/` | GET | Task log details |

### Health & Monitoring
| Endpoint | Description |
|----------|-------------|
| `/health/` | Comprehensive health check (database, Redis, Celery) |
| `/health/liveness/` | Liveness probe (basic application health) |
| `/health/readiness/` | Readiness probe (external dependencies) |

### Web Interface
| Endpoint | Description |
|----------|-------------|
| `/` | Home page with message form and display |
| `/status/` | JSON API endpoint with application statistics |
| `/admin/` | Django admin interface |

## Development Workflow

### First Time Setup
```bash
make deps-check      # Ensure PostgreSQL and Redis are installed
make dev-setup       # Complete environment setup
```

### Daily Development
```bash
make all            # Start all services
# Work on your changes
make test           # Run tests
make lint           # Check code quality
make format         # Format code
```

### Database Operations
```bash
make migrate        # Apply new migrations
make superuser      # Create admin user
make reset-db       # Reset database (careful!)
```

### Troubleshooting
```bash
make status         # Check service status
make services-check # Verify PostgreSQL and Redis
make logs          # View application logs
```

## Testing

### Comprehensive Test Suite (94% Coverage)
The application includes 69 comprehensive tests organized by functionality:

| Test Category | Count | Coverage | Command |
|---------------|-------|----------|---------|
| **API Tests** | 23 | REST API endpoints, serialization, error handling | `make test-api` |
| **Health Tests** | 14 | Health checks, monitoring, performance | `make test-health` |
| **Model Tests** | 18 | Database models, validation, relationships | `make test-models` |
| **Task Tests** | 14 | Celery tasks, error handling, integration | `make test-tasks` |
| **All Tests** | 69 | Complete test suite | `make test` |

### Test Features
- **Mock-based Testing**: External dependencies (Redis, Celery) are mocked
- **Isolated Test Database**: Tests run with Django's isolated test database
- **Performance Testing**: Query count validation and response time checks
- **Error Handling**: Comprehensive error scenario testing
- **Integration Testing**: End-to-end workflow validation

### Running Tests
```bash
make test                # Run all 69 tests with verbose output
make test-fast          # Run tests with minimal output
make test-coverage      # Run tests with coverage report (94%)
make test-api           # Run only API tests (23 tests)
make test-health        # Run only health check tests (14 tests)
make test-models        # Run only model tests (18 tests)
make test-tasks         # Run only task tests (14 tests)
```

### Testing the Application

1. **Start Services**: `make all`
2. **Open Browser**: http://localhost:8005
3. **Test REST API**: http://localhost:8005/api/
4. **Submit Message**: Use the form to submit a message
5. **Watch Processing**: Message will show as "Pending" then "Processed"
6. **Check Health**: http://localhost:8005/health/
7. **Check Admin**: http://localhost:8005/admin to see database records
8. **Monitor Tasks**: Watch console output for Celery task execution
9. **Periodic Tasks**: System messages appear every minute

## Code Quality

The project enforces high code quality standards:
- **Linting**: `make lint` (flake8 with 120 char line length)
- **Formatting**: `make format` (black code formatter)
- **Testing**: `make test` (94% test coverage)
- **Type Safety**: Proper type hints and validation
- **Documentation**: Comprehensive docstrings and comments

## Security Features

- Database credential separation (root vs application credentials)
- CSRF protection on forms
- Secure session handling
- Environment-based configuration
- Input validation and sanitization

## Monitoring and Logging

- Task logs stored in database (visible in Django admin)
- Application logs written to configured files
- Health checks for web server and API endpoints
- Real-time task status updates in web interface

## Architecture Benefits

### Modular Design
The reorganized structure provides clear separation of concerns:
- **API Package**: Dedicated REST API endpoints with proper serialization
- **Health Package**: Comprehensive monitoring and health check capabilities
- **Tests Package**: Organized test suite with 94% coverage
- **Clean Imports**: Relative imports maintain package boundaries

### Scalability
- Easy to add new API endpoints in the `api/` package
- Health checks can be extended without affecting core logic
- Test organization makes it simple to add new test categories
- Modular structure supports team development

### Maintainability
- Clear code organization improves readability
- Isolated concerns reduce coupling between components
- Comprehensive test coverage ensures reliability
- Consistent code quality standards enforced

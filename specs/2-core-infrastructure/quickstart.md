# Quick Start Guide: Sistema Core de Infraestrutura

**Feature**: 2-core-infrastructure  
**Date**: 2026-04-11  
**Purpose**: Get the core infrastructure running locally for development

## Prerequisites

### Required Software
- **Python 3.11+** - Primary development language
- **Docker & Docker Compose** - Containerization for local services
- **Git** - Version control
- **PostgreSQL Client** - Database management (psql)

### Optional but Recommended 
- **Redis CLI** - Cache/session debugging
- **Postman/Insomnia** - API testing
- **pgAdmin** - PostgreSQL GUI management

## Environment Setup

### 1. Clone and Setup Repository

```bash
# Clone repository
git clone <repository-url>
cd sistema-tintas

# Switch to infrastructure branch
git checkout 2-core-infrastructure

# Create Python virtual environment
python3.11 -m venv venv
source venv/bin/activate  # Linux/Mac
# OR
venv\Scripts\activate     # Windows

# Install dependencies
pip install -r requirements/development.txt
```

### 2. Local Services with Docker

```bash
# Start PostgreSQL and Redis containers
docker-compose up -d postgres redis

# Verify services are running
docker-compose ps

# Expected output:
# NAME                STATUS              PORTS
# postgres           Up 30 seconds       0.0.0.0:5432->5432/tcp
# redis              Up 30 seconds       0.0.0.0:6379->6379/tcp
```

### 3. Database Setup

```bash
# Create database schema
python manage.py migrate

# Create initial superuser
python manage.py createsuperuser
# Enter: username=admin, email=admin@tintas.local, password=admin123!

# Load initial configuration data
python manage.py loaddata initial_config

# Verify database connection
python manage.py dbshell
```

### 4. Start Development Server

```bash
# Start Django development server
python manage.py runserver 127.0.0.1:8000

# Start Celery worker (separate terminal)
celery -A tintas_system worker -l info

# Start Celery beat scheduler (separate terminal) 
celery -A tintas_system beat -l info
```

## Verify Installation

### 1. API Health Check

```bash
# Test basic health endpoint
curl http://localhost:8000/api/v1/health

# Expected response:
{
  "status": "healthy",
  "timestamp": "2026-04-11T10:00:00Z",
  "version": "1.0.0",
  "uptime_seconds": 300
}
```

### 2. Authentication Test

```bash
# Login with created superuser
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "username": "admin",
    "password": "admin123!"
  }'

# Expected response includes session cookie and user profile
{
  "success": true,
  "user": {
    "id": 1,
    "username": "admin",
    "role": "ADMIN",
    "email": "admin@tintas.local"
  }
}
```

### 3. Database Verification

```bash
# Check database tables were created
python manage.py dbshell

SELECT table_name FROM information_schema.tables 
WHERE table_schema = 'public' 
ORDER BY table_name;

# Expected tables:
# - auth_user (Django built-in)
# - core_userprofile
# - core_usersession  
# - core_auditlog
# - monitoring_systemhealth
# - monitoring_alertnotification
# - core_configuration
# - core_backuprecord
```

### 4. Redis Verification

```bash
# Connect to Redis
redis-cli -h localhost -p 6379

# Test session storage
127.0.0.1:6379> KEYS django.contrib.sessions.*
# Should show active sessions

# Test health check data
127.0.0.1:6379> KEYS health:*
# Should show cached health metrics
```

## Development Workflow

### 1. Making Changes

```bash
# Create database migrations after model changes
python manage.py makemigrations

# Apply migrations
python manage.py migrate

# Run tests
python manage.py test

# Check code style
flake8 apps/
black apps/ --check
isort apps/ --check-only
```

### 2. API Development

```bash
# Generate OpenAPI schema
python manage.py spectacular --color --file schema.yml

# Validate API spec
swagger-codegen validate -i schema.yml

# Test API endpoints
python manage.py test apps.core.tests.test_api
```

### 3. Background Tasks

```bash
# Test backup task manually
python manage.py shell
>>> from apps.core.tasks import create_backup
>>> create_backup.delay()

# Monitor task execution
celery -A tintas_system flower  # Web UI at http://localhost:5555
```

## Configuration

### Environment Variables (.env file)

```bash
# Database
DATABASE_URL=postgresql://tintas:tintas123@localhost:5432/tintas_db

# Redis
REDIS_URL=redis://localhost:6379/0

# Django
SECRET_KEY=your-secret-key-here
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# Email (for alerts)
EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=alerts@tintas.com
EMAIL_HOST_PASSWORD=app-password

# SMS (for critical alerts)
SMS_PROVIDER=twilio
TWILIO_ACCOUNT_SID=your-sid
TWILIO_AUTH_TOKEN=your-token
TWILIO_FROM_NUMBER=+1234567890

# Monitoring
HEALTH_CHECK_INTERVAL=60  # seconds
ALERT_COOLDOWN=900        # 15 minutes

# Backup
BACKUP_RETENTION_DAYS=90
BACKUP_PATH=/var/backups/tintas
```

### Django Settings

```python
# settings/development.py
from .base import *

DEBUG = True
ALLOWED_HOSTS = ['localhost', '127.0.0.1']

# Database
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'tintas_db',
        'USER': 'tintas',
        'PASSWORD': 'tintas123',
        'HOST': 'localhost',
        'PORT': '5432',
    }
}

# Cache
CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': 'redis://127.0.0.1:6379/1',
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
        }
    }
}

# Session storage
SESSION_ENGINE = 'django.contrib.sessions.backends.cache'
SESSION_CACHE_ALIAS = 'default'
SESSION_COOKIE_AGE = 28800  # 8 hours
```

## Troubleshooting

### Common Issues

**1. Database Connection Error**
```bash
# Check PostgreSQL is running
docker-compose ps postgres

# Check connection manually
psql -h localhost -U tintas -d tintas_db

# Reset database (development only)
python manage.py flush
python manage.py migrate
```

**2. Redis Connection Error** 
```bash
# Check Redis is running
docker-compose ps redis

# Test connection
redis-cli -h localhost ping
# Should return: PONG

# Clear Redis data
redis-cli -h localhost FLUSHALL
```

**3. Celery Worker Not Running**
```bash
# Check worker process
ps aux | grep celery

# Restart worker
pkill -f "celery worker"
celery -A tintas_system worker -l info
```

**4. Migration Conflicts**
```bash
# Reset migrations (development only)
python manage.py migrate core zero
rm apps/core/migrations/0*.py
python manage.py makemigrations core
python manage.py migrate
```

### Development Tools

**Database Inspection**
```bash
# Django shell with models loaded
python manage.py shell_plus

# Create test data
python manage.py loaddata test_fixtures.json

# Database schema dump
pg_dump -h localhost -U tintas -s tintas_db > schema.sql
```

**API Testing**
```bash
# Django REST Framework browsable API
http://localhost:8000/api/v1/

# Generate API client
swagger-codegen generate -i schema.yml -l python -o api_client/
```

**Performance Monitoring**
```bash
# Django debug toolbar (development)
pip install django-debug-toolbar

# SQL query analysis
python manage.py shell
>>> from django.db import connection
>>> connection.queries  # Show all SQL queries
```

## Next Steps

After successful local setup:

1. **Run Tests**: `python manage.py test` - Ensure all tests pass
2. **API Documentation**: Visit http://localhost:8000/api/docs/ for interactive API docs
3. **Admin Interface**: Visit http://localhost:8000/admin/ to manage users and configuration
4. **Monitoring Dashboard**: Check system health at http://localhost:8000/api/v1/health/detailed
5. **Continue Development**: Ready to implement business logic features

## Security Notes

**Development Environment Only**:
- Default passwords are used (change for production)
- DEBUG mode enabled (disable for production)  
- Console email backend (configure SMTP for production)
- Permissive CORS settings (restrict for production)

**Production Deployment**: Follow separate production deployment guide for security hardening, SSL certificates, and environment-specific configuration.
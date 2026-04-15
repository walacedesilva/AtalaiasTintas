"""
Testing settings for tintas_system project.
Optimized for fast test execution and isolated testing environment.
"""

from .base import *
from decouple import config
import tempfile

# Test mode
DEBUG = False

# Strip development-only apps that may have been appended to INSTALLED_APPS via
# base.py list mutation when __init__.py imports development.py first.
INSTALLED_APPS = [
    app for app in INSTALLED_APPS
    if app not in ('debug_toolbar', 'django_extensions')
]

# Strip debug_toolbar middleware for the same reason
MIDDLEWARE = [m for m in MIDDLEWARE if 'debug_toolbar' not in m]

# Secret key for testing
SECRET_KEY = 'test-secret-key-not-for-production'

# Allowed hosts in testing
ALLOWED_HOSTS = ['testserver', 'localhost', '127.0.0.1']

# Database configuration for testing
# Use in-memory SQLite by default for fast, portable tests.
# Set USE_SQLITE_TESTS=false to use PostgreSQL instead.
if config('USE_SQLITE_TESTS', default=True, cast=bool):
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': ':memory:',
            'TEST': {
                'NAME': ':memory:',
            }
        }
    }
else:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': config('TEST_DB_NAME', default='test_tintas_system'),
            'USER': config('TEST_DB_USER', default='postgres'),
            'PASSWORD': config('TEST_DB_PASSWORD', default='postgres'),
            'HOST': config('TEST_DB_HOST', default='127.0.0.1'),
            'PORT': config('TEST_DB_PORT', default='5432'),
            'OPTIONS': {
                'connect_timeout': 10,
            },
            'TEST': {
                'NAME': 'test_tintas_system',
            }
        }
    }

# Email backend for testing
EMAIL_BACKEND = 'django.core.mail.backends.locmem.EmailBackend'

# Cache configuration for testing (dummy cache for isolation)
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.dummy.DummyCache',
    }
}

# Session backend for testing
SESSION_ENGINE = 'django.contrib.sessions.backends.db'

# Disable Celery tasks in testing (run synchronously)
CELERY_TASK_ALWAYS_EAGER = True
CELERY_TASK_EAGER_PROPAGATES = True

# Disable CORS in testing
CORS_ALLOW_ALL_ORIGINS = True

# Password hashers for faster tests
PASSWORD_HASHERS = [
    'django.contrib.auth.hashers.MD5PasswordHasher',  # Fast but insecure (testing only)
]

# Logging configuration for testing (less verbose)
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'level': 'WARNING',
            'propagate': False,
        },
        'tintas_system': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': False,
        },
    },
}

# Media files for testing (use temporary directory)
MEDIA_ROOT = tempfile.mkdtemp()

# Static files for testing
STATIC_ROOT = tempfile.mkdtemp()

# Disable migrations for faster tests
class DisableMigrations:
    def __contains__(self, item):
        return True

    def __getitem__(self, item):
        return None

    def setdefault(self, key, value=None):
        return None

if config('DISABLE_MIGRATIONS_IN_TESTS', default=True, cast=bool):
    MIGRATION_MODULES = DisableMigrations()

# Test-specific settings
TEST_RUNNER = 'django.test.runner.DiscoverRunner'

# Testing framework configuration
TESTING_SETTINGS = {
    'USE_FACTORIES': True,
    'FAST_TESTS': config('FAST_TESTS', default=True, cast=bool),
    'COVERAGE_MINIMUM': 90,  # Minimum code coverage percentage
}

# DRF settings for testing
REST_FRAMEWORK.update({
    'TEST_REQUEST_DEFAULT_FORMAT': 'json',
})

# Disable throttling in tests
REST_FRAMEWORK['DEFAULT_THROTTLE_CLASSES'] = []
REST_FRAMEWORK['DEFAULT_THROTTLE_RATES'] = {}

# Security settings for testing (less restrictive)
SECURE_SSL_REDIRECT = False
SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False

# Factory Boy settings
FACTORY_FOR_DJANGO_SIGNALS = False
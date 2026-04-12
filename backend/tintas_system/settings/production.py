"""
Production settings for tintas_system project.
These settings are optimized for production deployment with security and performance.
"""

from .base import *
from decouple import config, Csv
import sentry_sdk
from sentry_sdk.integrations.django import DjangoIntegration
from sentry_sdk.integrations.celery import CeleryIntegration

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = False

# SECURITY WARNING: define a secure secret key in production
SECRET_KEY = config('SECRET_KEY')

# Allowed hosts must be explicitly defined
ALLOWED_HOSTS = config('ALLOWED_HOSTS', cast=Csv())

# Database configuration for production (PostgreSQL)
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': config('DB_NAME'),
        'USER': config('DB_USER'),
        'PASSWORD': config('DB_PASSWORD'),
        'HOST': config('DB_HOST', default='localhost'),
        'PORT': config('DB_PORT', default='5432', cast=int),
        'OPTIONS': {
            'connect_timeout': 20,
            'sslmode': config('DB_SSL_MODE', default='require'),
        },
        'CONN_MAX_AGE': 60,  # Connection pooling
    }
}

# Email configuration for production
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = config('EMAIL_HOST')
EMAIL_PORT = config('EMAIL_PORT', default=587, cast=int)
EMAIL_HOST_USER = config('EMAIL_HOST_USER')
EMAIL_HOST_PASSWORD = config('EMAIL_HOST_PASSWORD')
EMAIL_USE_TLS = config('EMAIL_USE_TLS', default=True, cast=bool)
EMAIL_USE_SSL = config('EMAIL_USE_SSL', default=False, cast=bool)
DEFAULT_FROM_EMAIL = config('DEFAULT_FROM_EMAIL')

# HTTPS and security settings for production
SECURE_SSL_REDIRECT = config('SECURE_SSL_REDIRECT', default=True, cast=bool)
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_HSTS_SECONDS = 31536000  # 1 year
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True

# Session security
SESSION_COOKIE_SECURE = True
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = 'Lax'

# CSRF security
CSRF_COOKIE_SECURE = True
CSRF_COOKIE_HTTPONLY = True
CSRF_COOKIE_SAMESITE = 'Lax'

# Static files configuration for production
STATIC_ROOT = config('STATIC_ROOT', default=BASE_DIR / 'staticfiles')
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# Media files configuration for production  
MEDIA_ROOT = config('MEDIA_ROOT', default=BASE_DIR / 'mediafiles')

# Add WhiteNoise middleware for static file serving
MIDDLEWARE.insert(1, 'whitenoise.middleware.WhiteNoiseMiddleware')

# Cache configuration for production (Redis)
CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': config('REDIS_URL'),
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
            'CONNECTION_POOL_KWARGS': {
                'max_connections': 20,
                'retry_on_timeout': True,
            }
        },
        'KEY_PREFIX': 'tintas_system',
        'TIMEOUT': 300,  # 5 minutes default timeout
    }
}

# Session backend for production (Redis)
SESSION_ENGINE = 'django.contrib.sessions.backends.cache'
SESSION_CACHE_ALIAS = 'default'

# Celery configuration for production
CELERY_BROKER_URL = config('CELERY_BROKER_URL')
CELERY_RESULT_BACKEND = config('CELERY_RESULT_BACKEND')
CELERY_TASK_ALWAYS_EAGER = False
CELERY_WORKER_PREFETCH_MULTIPLIER = 4
CELERY_TASK_ROUTES = {
    'apps.monitoring.tasks.*': {'queue': 'monitoring'},
    'apps.core.tasks.*': {'queue': 'core'},
}

# CORS settings for production
CORS_ALLOWED_ORIGINS = config('CORS_ALLOWED_ORIGINS', cast=Csv())
CORS_ALLOW_CREDENTIALS = True

# Logging configuration for production
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
        'json': {
            'format': '{"level": "{levelname}", "time": "{asctime}", "module": "{module}", "message": "{message}"}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'json',
        },
        'file': {
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': config('LOG_FILE_PATH', default='/var/log/tintas_system/django.log'),
            'maxBytes': 1024*1024*10,  # 10 MB
            'backupCount': 10,
            'formatter': 'json',
        },
        'sentry': {
            'class': 'sentry_sdk.integrations.logging.SentryHandler',
            'level': 'ERROR',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['console', 'file', 'sentry'],
            'level': 'INFO',
            'propagate': False,
        },
        'tintas_system': {
            'handlers': ['console', 'file', 'sentry'],
            'level': 'INFO',
            'propagate': False,
        },
        'django.security': {
            'handlers': ['console', 'file', 'sentry'],
            'level': 'WARNING',
            'propagate': False,
        },
    },
}

# Sentry configuration for error monitoring
if config('SENTRY_DSN', default=''):
    sentry_sdk.init(
        dsn=config('SENTRY_DSN'),
        integrations=[
            DjangoIntegration(
                transaction_survey_sample_rate=0.1,
            ),
            CeleryIntegration(
                monitor_beat_tasks=True,
            ),
        ],
        traces_sample_rate=0.1,
        send_default_pii=False,
        environment=config('SENTRY_ENVIRONMENT', default='production'),
    )

# Production database backup settings
DATABASE_BACKUP = {
    'ENGINE': 'django.core.management.commands.dbbackup',
    'STORAGE': 'storages.backends.s3boto3.S3Boto3Storage',
    'STORAGE_OPTIONS': {
        'access_key': config('AWS_ACCESS_KEY_ID', default=''),
        'secret_key': config('AWS_SECRET_ACCESS_KEY', default=''),
        'bucket_name': config('BACKUP_BUCKET_NAME', default=''),
    }
}

# Production-specific settings override
PAINT_STORE_SETTINGS.update({
    'BACKUP_ENABLED': True,
    'MONITORING_ENABLED': True,
    'ALERT_EMAIL_LIST': config('ALERT_EMAIL_LIST', default='', cast=Csv()),
    'ALERT_SMS_LIST': config('ALERT_SMS_LIST', default='', cast=Csv()),
})

# Health check configuration
HEALTH_CHECK = {
    'DATABASE_TIMEOUT': 10,
    'REDIS_TIMEOUT': 5,
    'DISK_USAGE_MAX': 90,  # percentage
    'MEMORY_USAGE_MAX': 90,  # percentage
})

# Performance optimizations
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Add production middleware
MIDDLEWARE += [
    'apps.core.middleware.AuditLogMiddleware',
    'apps.monitoring.middleware.HealthCheckMiddleware',
]
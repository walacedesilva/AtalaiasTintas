"""
Development settings for tintas_system project.
These settings are optimized for local development with debug information.
"""

from .base import *
from decouple import config

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = config('SECRET_KEY', default='django-insecure-@&e&f3gvgy2md1pr$1o+o$s1^j+stky_+(5%srkxrxaoz2idmi')

# Allow all hosts in development
ALLOWED_HOSTS = ['*']

# Database
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# Use SQLite for development to avoid PostgreSQL setup complexity
# PostgreSQL configuration (commented for now)
# DATABASES = {
#     'default': {
#         'ENGINE': 'django.db.backends.postgresql',
#         'NAME': config('DB_NAME', default='tintas_system_dev'),
#         'USER': config('DB_USER', default='postgres'),
#         'PASSWORD': config('DB_PASSWORD', default='postgres'),
#         'HOST': config('DB_HOST', default='127.0.0.1'),
#         'PORT': config('DB_PORT', default='5432'),
#         'OPTIONS': {
#             'connect_timeout': 20,
#         }
#     }
# }

# Development-specific installed apps
INSTALLED_APPS += [
    'django_extensions',
]

# Development middleware (add debug toolbar if available)
try:
    import debug_toolbar
    INSTALLED_APPS += ['debug_toolbar']
    MIDDLEWARE.insert(1, 'debug_toolbar.middleware.DebugToolbarMiddleware')
    
    # Debug toolbar configuration
    INTERNAL_IPS = [
        '127.0.0.1',
        'localhost',
    ]
    
    DEBUG_TOOLBAR_CONFIG = {
        'SHOW_TOOLBAR_CALLBACK': lambda request: DEBUG,
    }
except ImportError:
    pass

# Email backend for development (console output)
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# Static files in development
STATICFILES_DIRS = [
    BASE_DIR / 'static',
]

# Media files in development  
MEDIA_ROOT = BASE_DIR / 'media'

# Cache configuration for development
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'tintas-system-dev',
    }
}

# Session configuration for development
SESSION_ENGINE = 'django.contrib.sessions.backends.db'

# Celery configuration for development (Redis optional)
CELERY_TASK_ALWAYS_EAGER = config('CELERY_ALWAYS_EAGER', default=True, cast=bool)
CELERY_TASK_EAGER_PROPAGATES = True

# CORS settings for development
CORS_ALLOW_ALL_ORIGINS = True
CORS_ALLOW_CREDENTIALS = True

# Logging configuration for development
LOGGING['loggers']['django']['level'] = 'DEBUG'
LOGGING['loggers']['tintas_system']['level'] = 'DEBUG'

# Add more verbose logging for development
LOGGING['handlers']['console']['formatter'] = 'verbose'

# Development-specific settings
DEVELOPMENT_SETTINGS = {
    'SHOW_SQL_QUERIES': config('SHOW_SQL_QUERIES', default=False, cast=bool),
    'DISABLE_MIGRATIONS': config('DISABLE_MIGRATIONS', default=False, cast=bool),
    'USE_DUMMY_CACHE': True,
}

# Performance settings for development
if DEVELOPMENT_SETTINGS['SHOW_SQL_QUERIES']:
    LOGGING['loggers']['django.db.backends'] = {
        'level': 'DEBUG',
        'handlers': ['console'],
        'propagate': False,
    }

# Disable migrations in development if needed (for faster testing)
if DEVELOPMENT_SETTINGS['DISABLE_MIGRATIONS']:
    class DisableMigrations:
        def __contains__(self, item):
            return True

        def __getitem__(self, item):
            return None

    MIGRATION_MODULES = DisableMigrations()

# Development tools settings
SHELL_PLUS_PRINT_SQL = True
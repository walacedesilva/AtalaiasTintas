"""
Celery configuration for tintas_system project.
Background task processing for monitoring, backups, and other async operations.
"""

import os
from celery import Celery
from celery.schedules import crontab
from django.conf import settings

# Set the default Django settings module for the 'celery' program
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'tintas_system.settings')

# Create the Celery app
app = Celery('tintas_system')

# Load task modules from all registered Django app configs
app.config_from_object('django.conf:settings', namespace='CELERY')

# Auto-discover tasks in all Django apps
app.autodiscover_tasks()

# Celery beat schedule for periodic tasks
app.conf.beat_schedule = {
    # System health check every 5 minutes
    'system-health-check': {
        'task': 'apps.monitoring.tasks.check_system_health',
        'schedule': 300.0,  # 5 minutes
    },
    
    # Database backup every day at 2 AM
    'daily-database-backup': {
        'task': 'apps.core.tasks.create_database_backup',
        'schedule': crontab(hour=2, minute=0),
    },
    
    # Cleanup old logs every week
    'weekly-log-cleanup': {
        'task': 'apps.monitoring.tasks.cleanup_old_logs',
        'schedule': crontab(hour=3, minute=0, day_of_week=0),  # Sunday 3 AM
    },
    
    # Check disk space every hour
    'hourly-disk-check': {
        'task': 'apps.monitoring.tasks.check_disk_space',
        'schedule': 3600.0,  # 1 hour
    },
}

# Celery task routes
app.conf.task_routes = {
    'apps.monitoring.tasks.*': {'queue': 'monitoring'},
    'apps.core.tasks.*': {'queue': 'core'},
    'apps.companies.tasks.*': {'queue': 'business'},
    'apps.inventory.tasks.*': {'queue': 'business'},
    'apps.sales.tasks.*': {'queue': 'business'},
    'apps.tintometry.tasks.*': {'queue': 'business'},
    'apps.fiscal.tasks.*': {'queue': 'business'},
    'apps.marketplaces.tasks.*': {'queue': 'business'},
}

# Task configuration
app.conf.update(
    # Task serialization
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='America/Sao_Paulo',
    enable_utc=True,
    
    # Task result backend configuration
    result_expires=3600,  # 1 hour
    
    # Worker configuration
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=1000,
    
    # Task routing
    task_create_missing_queues=True,
    task_default_queue='default',
    
    # Task retry configuration
    task_acks_late=True,
    task_reject_on_worker_lost=True,
)

@app.task(bind=True)
def debug_task(self):
    """Debug task for testing Celery configuration"""
    print(f'Request: {self.request!r}')
    return 'Celery is working correctly!'
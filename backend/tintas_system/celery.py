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
# Task: T046 - Setup Celery beat scheduler for automated monitoring
app.conf.beat_schedule = {
    # System health checks every 5 minutes
    'run-health-checks': {
        'task': 'apps.monitoring.tasks.run_health_checks',
        'schedule': 300.0,  # 5 minutes
        'options': {'queue': 'monitoring'}
    },
    
    # Process alert notifications every 2 minutes
    'process-alerts': {
        'task': 'apps.monitoring.tasks.process_alert_notifications',
        'schedule': 120.0,  # 2 minutes  
        'options': {'queue': 'monitoring'}
    },
    
    # Full database backup daily at 2 AM
    'daily-full-backup': {
        'task': 'apps.monitoring.tasks.create_scheduled_backup',
        'schedule': crontab(hour=2, minute=0),
        'kwargs': {'backup_type': 'full'},
        'options': {'queue': 'monitoring'}
    },
    
    # Incremental backup every 4 hours
    'incremental-backup': {
        'task': 'apps.monitoring.tasks.create_scheduled_backup',
        'schedule': crontab(minute=0, hour='*/4'),
        'kwargs': {'backup_type': 'incremental'},
        'options': {'queue': 'monitoring'}
    },
    
    # Cleanup old backups daily at 1 AM
    'cleanup-old-backups': {
        'task': 'apps.monitoring.tasks.cleanup_old_backups',
        'schedule': crontab(hour=1, minute=0),
        'options': {'queue': 'monitoring'}
    },
    
    # Cleanup old monitoring data weekly on Sunday at 3 AM
    'cleanup-monitoring-data': {
        'task': 'apps.monitoring.tasks.cleanup_old_monitoring_data',
        'schedule': crontab(hour=3, minute=0, day_of_week=0),
        'options': {'queue': 'monitoring'}
    },
    
    # Generate daily health report at 6 AM
    'daily-health-report': {
        'task': 'apps.monitoring.tasks.generate_health_summary_report',
        'schedule': crontab(hour=6, minute=0),
        'kwargs': {'hours': 24},
        'options': {'queue': 'monitoring'}
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
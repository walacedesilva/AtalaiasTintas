from django.apps import AppConfig


class MonitoringConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.monitoring'
    verbose_name = 'System Monitoring'
    
    def ready(self):
        """
        Initialize monitoring system when Django starts up.
        """
        # Import signal handlers
        try:
            import apps.monitoring.signals  # noqa
        except ImportError:
            pass
from django.apps import AppConfig


class MonitoringConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.monitoring'
    verbose_name = 'Monitoramento do Sistema'
    
    def ready(self):
        """
        Initialize monitoring system when Django starts up.
        """
        # Import signal handlers
        try:
            import apps.monitoring.signals  # noqa
        except ImportError:
            pass
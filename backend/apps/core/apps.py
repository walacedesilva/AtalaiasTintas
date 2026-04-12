from django.apps import AppConfig


class CoreConfig(AppConfig):
    """
    Core app configuration.
    
    Feature: 3-modern-web-interface
    Task: T006 - User Preferences Model
    """
    
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.core'
    verbose_name = 'Core Application'
    
    def ready(self):
        """
        Initialize core application when Django starts up.
        Import signal handlers to ensure UserPreferences are created automatically.
        """
        # Import signal handlers
        try:
            import apps.core.signals  # noqa
        except ImportError:
            pass

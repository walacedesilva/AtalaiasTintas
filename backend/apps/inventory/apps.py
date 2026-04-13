from django.apps import AppConfig


class InventoryConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.inventory'
    verbose_name = 'Gestão de Estoque'

    def ready(self):
        try:
            from apps.core.signals import connect_inventory_signals
            connect_inventory_signals()
        except Exception:
            pass

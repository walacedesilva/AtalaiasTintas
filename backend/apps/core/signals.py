"""
Signal handlers for the core app.

Feature: 3-modern-web-interface / 4-inventory-fiscal-integration
Task: T006 - User Preferences Model, T014 - Inventory/Fiscal Event Signals
"""

import logging

from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from .models import UserPreferences

logger = logging.getLogger(__name__)
User = get_user_model()


@receiver(post_save, sender=User)
def create_user_preferences(sender, instance, created, **kwargs):
    """
    Automatically create UserPreferences when a new User is created.
    
    This ensures every user has associated interface preferences with
    sensible defaults from the moment their account is created.
    
    Args:
        sender: The User model class
        instance: The specific User instance that was saved
        created: Boolean indicating if this is a new user
        **kwargs: Additional signal arguments
    """
    if created:
        UserPreferences.objects.create(
            user=instance,
            theme='light',
            density='comfortable',
            sidebar_collapsed=False,
            show_breadcrumbs=True,
            high_contrast=False,
            reduce_motion=False,
            quick_actions=[
                {'action': 'create_label', 'label': 'Nova Etiqueta', 'icon': 'bi-tag'},
                {'action': 'inventory_count', 'label': 'Contagem', 'icon': 'bi-clipboard-check'},
                {'action': 'sales_report', 'label': 'Vendas', 'icon': 'bi-graph-up'},
                {'action': 'tint_mix', 'label': 'Misturar Tinta', 'icon': 'bi-palette'},
            ]
        )


# ---------------------------------------------------------------------------
# Inventory / Fiscal integration signals — T014
# ---------------------------------------------------------------------------

def connect_inventory_signals():
    """Register inventory & fiscal event handlers.

    Called from InventoryConfig.ready() to avoid import-time circular imports.
    """
    try:
        from apps.sales.models import Venda as _Venda  # noqa: F401
        post_save.connect(_on_venda_finalizada, sender=_Venda, dispatch_uid='inventory_venda_finalizada')
        logger.debug("Inventory signal handlers connected.")
    except ImportError:
        logger.warning("Sales app not available — inventory signals not connected.")


def _on_venda_finalizada(sender, instance, created, **kwargs):
    """Trigger NFe automation check when a sale is saved with status FINALIZADA.

    - Confirms stock reservations for the checkout session.
    - Triggers NFe emission if applicable (B2B customer).

    Full NFe transmission logic lives in Phase 3 (T041-T055).
    """
    status = getattr(instance, 'status', None)
    if status != 'FINALIZADA':
        return

    sessao = getattr(instance, 'sessao_checkout', None) or str(instance.pk)

    # 1. Confirm stock reservations
    try:
        from apps.inventory.services import EstoqueService
        EstoqueService.confirmar_reservas(sessao_checkout=sessao, venda_id=instance.pk)
    except Exception as exc:
        logger.error("Erro ao confirmar reservas para venda %s: %s", instance.pk, exc)

    # 2. Trigger NFe processing (async, Phase 3 stub)
    try:
        from apps.fiscal.services import NFEService
        if NFEService.deve_emitir_nfe_automatica(instance):
            NFEService.processar_nfe_venda(str(instance.pk), usuario=None)
    except Exception as exc:
        logger.error("Erro ao processar NFe para venda %s: %s", instance.pk, exc)
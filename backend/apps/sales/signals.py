"""Sales signals — T051: trigger NF-e processing on Venda.cancelada change."""
from __future__ import annotations

import logging

from django.db.models.signals import post_save
from django.dispatch import receiver

logger = logging.getLogger(__name__)


@receiver(post_save, sender='sales.Venda')
def venda_post_save(sender, instance, created, **kwargs):
    """Trigger automatic NF-e emission when a Venda is newly created.

    Only fires when:
    - The Venda was just **created** (not updated).
    - nfe_situacao is not already set (avoids duplicate processing).
    - The sale is not cancelled.

    The actual NF-e logic runs asynchronously via Celery to avoid blocking
    the HTTP response.
    """
    if not created:
        return

    if instance.cancelada:
        return

    if instance.nfe_situacao not in ('', 'NAO_APLICAVEL', None):
        # Already being processed (e.g., set by view before save)
        return

    try:
        from apps.fiscal.services import NFEService
        # This will check deve_emitir_nfe_automatica internally
        NFEService.processar_nfe_venda(str(instance.pk), None)
    except Exception as exc:
        logger.error(
            "venda_post_save: erro ao agendar NF-e para venda %s: %s",
            instance.pk, exc,
        )

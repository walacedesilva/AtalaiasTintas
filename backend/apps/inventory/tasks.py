"""
Inventory Celery Tasks
======================
limpar_reservas_expiradas — T030: expire pending reservations
marcar_lotes_vencidos     — new: mark expired batches daily
alertar_estoque_minimo    — new: daily low-stock alert
"""
from __future__ import annotations

import logging

from celery import shared_task
from django.utils import timezone

logger = logging.getLogger(__name__)


@shared_task(
    name='inventory.limpar_reservas_expiradas',
    bind=True,
    max_retries=3,
    default_retry_delay=60,
)
def limpar_reservas_expiradas(self):
    """Expire all active EstoqueReserva records past their expiry time.

    Runs scheduled via Celery Beat (recommended: every 5 minutes).
    Releases reserved quantities back to available stock.
    """
    from apps.inventory.models import EstoqueReserva, EstoqueLoja
    from django.db import transaction

    agora = timezone.now()
    reservas_expiradas = EstoqueReserva.objects.filter(
        status='ATIVA',
        expira_em__lt=agora,
    ).select_related('produto')

    count = 0
    for reserva in reservas_expiradas:
        try:
            with transaction.atomic():
                # Release reserved quantity
                EstoqueLoja.objects.filter(
                    produto_variacao=reserva.produto,
                ).update_quantity_reservada_subtract(reserva.quantidade_reservada)

                reserva.status = 'EXPIRADA'
                reserva.save(update_fields=['status', 'updated_at'])
                count += 1
        except Exception as exc:
            logger.error("Erro ao expirar reserva %s: %s", reserva.pk, exc)
            self.retry(exc=exc)

    if count:
        logger.info("Reservas expiradas: %d", count)
    return count


@shared_task(
    name='inventory.limpar_reservas_expiradas_v2',
    bind=True,
    max_retries=3,
    default_retry_delay=60,
)
def limpar_reservas_expiradas_v2(self):
    """Expire all active EstoqueReserva records past their expiry time.

    Safer version using direct ORM queries for the quantity release.
    Runs scheduled via Celery Beat (every 5 minutes).
    """
    from apps.inventory.models import EstoqueReserva, EstoqueLoja
    from django.db import transaction
    from decimal import Decimal

    agora = timezone.now()
    reservas_expiradas = (
        EstoqueReserva.objects
        .filter(status='ATIVA', expira_em__lt=agora)
        .select_for_update(skip_locked=True)
    )

    count = 0
    with transaction.atomic():
        for reserva in reservas_expiradas:
            try:
                # Release quantity from EstoqueLoja (all stores holding the reservation)
                estoque_qs = EstoqueLoja.objects.filter(produto_variacao=reserva.produto)
                for estoque in estoque_qs.select_for_update():
                    estoque.quantidade_reservada = max(
                        Decimal('0'),
                        estoque.quantidade_reservada - reserva.quantidade_reservada,
                    )
                    estoque.save(update_fields=['quantidade_reservada', 'updated_at'])

                reserva.status = 'EXPIRADA'
                reserva.save(update_fields=['status', 'updated_at'])
                count += 1
            except Exception as exc:
                logger.error("Erro ao expirar reserva %s: %s", reserva.pk, exc)

    if count:
        logger.info("Reservas expiradas (v2): %d", count)
    return count


@shared_task(name='inventory.marcar_lotes_vencidos')
def marcar_lotes_vencidos():
    """Mark all LoteProduto records past their data_validade as VENCIDO.

    Runs scheduled via Celery Beat (recommended: daily at midnight).
    """
    from apps.inventory.services import LoteService

    count = LoteService.marcar_lotes_vencidos()
    logger.info("Lotes marcados como vencidos: %d", count)
    return count


@shared_task(name='inventory.alertar_estoque_minimo')
def alertar_estoque_minimo():
    """Log/alert products that have fallen below their minimum stock level.

    Runs scheduled via Celery Beat (recommended: daily morning).
    Extend to send email/Slack alerts as needed.
    """
    from apps.inventory.models import EstoqueLoja

    abaixo_minimo = (
        EstoqueLoja.objects
        .select_related('produto_variacao__produto_base', 'loja')
        .filter(
            quantidade_atual__lte=models_estoque_minimo(),
            produto_variacao__ativo=True,
        )
    )

    count = 0
    for estoque in abaixo_minimo:
        logger.warning(
            "ESTOQUE MÍNIMO: loja=%s produto=%s atual=%s minimo=%s",
            estoque.loja,
            estoque.produto_variacao,
            estoque.quantidade_atual,
            estoque.produto_variacao.estoque_minimo,
        )
        count += 1

    logger.info("Produtos abaixo do estoque mínimo: %d", count)
    return count


def models_estoque_minimo():
    """Helper: return F() expression for the comparison."""
    from django.db.models import F
    from apps.inventory.models import EstoqueLoja
    # This returns abaixo_do_minimo using Django F expression
    # The actual filter uses annotate approach; simplified here
    from django.db.models import OuterRef, Subquery
    return F('produto_variacao__estoque_minimo')

"""Fiscal async Celery tasks — T047, T048.

T047 — processar_nfe_async: async NF-e processing for a completed sale.
T048 — retry_nfe_falhadas: scheduled task that reprocesses failed NF-e records.
"""
from __future__ import annotations

import logging
from datetime import timedelta

from celery import shared_task
from django.utils import timezone as tz

logger = logging.getLogger(__name__)

# How many minutes to wait between automatic retry attempts
RETRY_BASE_DELAY_MINUTES = 5
MAX_TENTATIVAS_AUTO = 3


# ---------------------------------------------------------------------------
# T047 — processar_nfe_async
# ---------------------------------------------------------------------------

@shared_task(
    bind=True,
    name="fiscal.processar_nfe_async",
    max_retries=MAX_TENTATIVAS_AUTO,
    default_retry_delay=RETRY_BASE_DELAY_MINUTES * 60,
    acks_late=True,
)
def processar_nfe_async(self, venda_id: str, usuario_id=None):
    """Process NF-e emission for a completed sale asynchronously.

    Flow:
    1. Generate unsigned NF-e XML from Venda data.
    2. Create / update a ``NotaFiscal`` record.
    3. Call ``SefazClient.autorizar_nfe`` via ``NFEService.enviar_sefaz``.
    4. On success: update Venda.nfe_situacao = 'AUTORIZADA'.
    5. On ``SefazRejeicaoError``: flag sale for manual review.
    6. On transient errors: retry up to ``MAX_TENTATIVAS_AUTO`` times.
    """
    from apps.fiscal.models import NotaFiscal, ConfiguracaoFiscal
    from apps.fiscal.services import NFEService
    from apps.fiscal.sefaz.exceptions import (
        SefazConnectionError, SefazTimeoutError, SefazRejeicaoError, SefazError,
    )
    from apps.sales.models import Venda

    logger.info("processar_nfe_async: iniciando venda=%s tentativa=%d", venda_id, self.request.retries + 1)

    # Mark as processing
    Venda.objects.filter(pk=venda_id).update(
        nfe_situacao='PROCESSANDO',
        nfe_ultima_tentativa=tz.now(),
        nfe_tentativas=self.request.retries + 1,
    )

    try:
        venda = Venda.objects.select_related('cliente', 'loja', 'loja__empresa', 'pedido_origem').get(pk=venda_id)
    except Venda.DoesNotExist:
        logger.error("processar_nfe_async: Venda %s não encontrada", venda_id)
        return

    config = ConfiguracaoFiscal.objects.filter(
        empresa=venda.loja.empresa, nfe_ativo=True
    ).first()

    if config is None:
        logger.warning(
            "processar_nfe_async: NF-e não habilitada para empresa %s — abortando",
            venda.loja.empresa_id,
        )
        Venda.objects.filter(pk=venda_id).update(
            nfe_situacao='ERRO_TECNICO',
            nfe_erro="ConfiguracaoFiscal com nfe_ativo=True não encontrada",
        )
        return

    # Step 1: Generate XML
    try:
        xml_nfe = NFEService.gerar_xml_nfe(str(venda_id))
    except Exception as exc:
        logger.error("processar_nfe_async: falha ao gerar XML para venda %s: %s", venda_id, exc)
        Venda.objects.filter(pk=venda_id).update(
            nfe_situacao='ERRO_TECNICO',
            nfe_erro=f"Erro na geração do XML: {exc}",
        )
        if self.request.retries < self.max_retries:
            raise self.retry(exc=exc)
        NFEService.marcar_para_retry_manual(str(venda_id), str(exc))
        return

    # Step 2: Create/update NotaFiscal record
    nota, _created = NotaFiscal.objects.get_or_create(
        venda=venda,
        tipo_nota='NFE',
        defaults={
            'loja': venda.loja,
            'serie': config.nfe_serie,
            'numero': config.nfe_numero_atual,
            'situacao': 'PENDENTE',
            'xml_envio': xml_nfe,
            'valor_total_produtos': venda.valor_total or 0,
            'valor_total_nota': venda.valor_liquido or venda.valor_total or 0,
            'valor_desconto': venda.valor_desconto or 0,
        },
    )

    if not _created:
        nota.xml_envio = xml_nfe
        nota.situacao = 'PENDENTE'
        nota.save(update_fields=['xml_envio', 'situacao', 'updated_at'])

    # Step 3: Send to SEFAZ
    try:
        resultado = NFEService.enviar_sefaz(str(nota.pk))
        logger.info(
            "processar_nfe_async: NF-e autorizada. venda=%s protocolo=%s",
            venda_id,
            resultado.get('numero_protocolo'),
        )
    except SefazRejeicaoError as exc:
        logger.warning(
            "processar_nfe_async: rejeição SEFAZ venda=%s código=%s motivo=%s corrigível=%s",
            venda_id, exc.codigo, exc.motivo, exc.corrigivel,
        )
        Venda.objects.filter(pk=venda_id).update(
            nfe_situacao='REJEITADA',
            nfe_erro=f"Rejeição {exc.codigo}: {exc.motivo}",
        )
        if exc.corrigivel and self.request.retries < self.max_retries:
            raise self.retry(exc=exc)
        NFEService.marcar_para_retry_manual(str(venda_id), f"Rejeição {exc.codigo}: {exc.motivo}")

    except (SefazConnectionError, SefazTimeoutError) as exc:
        logger.warning("processar_nfe_async: erro conexão SEFAZ venda=%s: %s", venda_id, exc)
        Venda.objects.filter(pk=venda_id).update(
            nfe_situacao='ERRO_TECNICO',
            nfe_erro=str(exc),
        )
        if self.request.retries < self.max_retries:
            raise self.retry(exc=exc, countdown=_backoff(self.request.retries))
        NFEService.marcar_para_retry_manual(str(venda_id), str(exc))

    except SefazError as exc:
        logger.error("processar_nfe_async: erro SEFAZ inespera venda=%s: %s", venda_id, exc)
        Venda.objects.filter(pk=venda_id).update(
            nfe_situacao='ERRO_TECNICO',
            nfe_erro=str(exc),
        )
        NFEService.marcar_para_retry_manual(str(venda_id), str(exc))


# ---------------------------------------------------------------------------
# T048 — retry_nfe_falhadas
# ---------------------------------------------------------------------------

@shared_task(name="fiscal.retry_nfe_falhadas")
def retry_nfe_falhadas():
    """Periodic task: requeue NF-e records flagged for manual retry.

    Intended to be scheduled via ``django-celery-beat`` (e.g. every 30 min).
    Will NOT re-attempt records that have exceeded MAX_TENTATIVAS_AUTO unless
    ''nfe_requer_retry_manual'' was explicitly cleared by an operator.
    """
    from apps.sales.models import Venda

    pendentes = Venda.objects.filter(
        nfe_situacao__in=('ERRO_TECNICO', 'AGUARDANDO_RETRY'),
        nfe_requer_retry_manual=False,
        nfe_tentativas__lt=MAX_TENTATIVAS_AUTO,
    ).values_list('pk', flat=True)[:50]

    count = 0
    for venda_id in pendentes:
        processar_nfe_async.delay(str(venda_id))
        count += 1

    logger.info("retry_nfe_falhadas: %d NF-e(s) reenviadas", count)
    return count


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _backoff(retries: int) -> int:
    """Exponential back-off: 5, 10, 20 minutes."""
    return RETRY_BASE_DELAY_MINUTES * (2 ** retries) * 60


# ---------------------------------------------------------------------------
# cancelar_nfe_async — called by VendaService.cancelar_venda (T060)
# ---------------------------------------------------------------------------

@shared_task(name="fiscal.cancelar_nfe_async", max_retries=2, default_retry_delay=120)
def cancelar_nfe_async(venda_id: str, justificativa: str, usuario_id=None):
    """Async NF-e cancellation for a sale that was already authorised.

    Calls SefazClient.cancelar_nfe and updates NotaFiscal + Venda records.
    """
    from apps.fiscal.models import NotaFiscal
    from apps.fiscal.sefaz.client import criar_sefaz_client
    from apps.fiscal.sefaz.exceptions import SefazCancelamentoError, SefazError
    from apps.sales.models import Venda

    try:
        venda = Venda.objects.get(pk=venda_id)
    except Venda.DoesNotExist:
        logger.error("cancelar_nfe_async: Venda %s não encontrada", venda_id)
        return

    nota = NotaFiscal.objects.filter(venda=venda, situacao='AUTORIZADA').first()
    if not nota:
        logger.warning("cancelar_nfe_async: nota autorizada não encontrada para venda %s", venda_id)
        return

    try:
        criar_sefaz_client().cancelar_nfe(
            nota.chave_acesso or '',
            justificativa,
            nota.protocolo_autorizacao or '',
        )
    except SefazCancelamentoError as exc:
        logger.error("cancelar_nfe_async: cancelamento rejeitado venda=%s: %s", venda_id, exc)
        return
    except SefazError as exc:
        logger.warning("cancelar_nfe_async: erro transiente — venda=%s: %s", venda_id, exc)
        raise  # triggers Celery retry

    nota.situacao = 'CANCELADA'
    nota.motivo_cancelamento = justificativa
    nota.save(update_fields=['situacao', 'motivo_cancelamento', 'updated_at'])

    Venda.objects.filter(pk=venda_id).update(nfe_situacao='CANCELADA')
    logger.info("cancelar_nfe_async: NF-e cancelada para venda %s", venda_id)


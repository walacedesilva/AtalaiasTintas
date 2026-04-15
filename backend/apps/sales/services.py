"""Sales Service Layer — T058, T059, T060.

VendaService — orchestrates the full sales lifecycle:
  - checkout with stock reservation (T058)
  - sale completion with NF-e trigger (T059)
  - sale cancellation with reservation release (T060)
"""
from __future__ import annotations

import logging
from decimal import Decimal
from typing import Optional

from django.contrib.auth import get_user_model
from django.db import transaction
from django.utils import timezone

logger = logging.getLogger(__name__)
User = get_user_model()


class CheckoutInsuficienteError(Exception):
    """Raised when one or more items lack sufficient stock at checkout."""

    def __init__(self, faltas: list[dict]):
        self.faltas = faltas  # list of {'produto': ..., 'solicitado': ..., 'disponivel': ...}
        super().__init__(f"{len(faltas)} item(ns) sem estoque suficiente")


class VendaService:
    """Orchestrates the full sales workflow with inventory and fiscal integration."""

    # ------------------------------------------------------------------
    # T058 — Checkout with stock reservation
    # ------------------------------------------------------------------

    @staticmethod
    @transaction.atomic
    def iniciar_checkout(
        pedido_id: str,
        sessao_checkout: str,
        usuario: User,
        override_estoque: bool = False,
    ) -> dict:
        """Reserve stock for all items in a PedidoVenda.

        Creates EstoqueReserva for each item.  If *override_estoque* is True
        (manager permission required), items with insufficient stock are
        allowed through without a reservation (flagged in result).

        Returns:
            {
              'sessao_checkout': str,
              'reservas': [EstoqueReserva, ...],
              'avisos':   [{'produto': ..., 'disponivel': Decimal}, ...],
            }

        Raises:
            CheckoutInsuficienteError — if stock is insufficient and override is False.
        """
        from apps.inventory.services import EstoqueService, ConversaoService
        from apps.sales.models import ItemPedidoVenda, PedidoVenda

        pedido = PedidoVenda.objects.select_related('loja').prefetch_related('itens').get(pk=pedido_id)

        faltas = []
        avisos = []
        reservas = []

        for item in pedido.itens.select_related('produto_variacao', 'unidade_venda').all():
            produto_id = str(item.produto_variacao_id)
            loja_id    = pedido.loja_id

            # Determine base unit and quantity
            unidade_id = (
                item.unidade_venda_id
                if item.unidade_venda_id
                else ConversaoService.obter_unidade_base(produto_id).id
            )
            quantidade = item.quantidade

            disponivel = EstoqueService.calcular_disponibilidade(produto_id, loja_id)
            qtd_base = ConversaoService.converter_quantidade(produto_id, quantidade, unidade_id)

            if qtd_base > disponivel:
                if override_estoque:
                    avisos.append({
                        'produto': produto_id,
                        'descricao': item.produto_variacao.nome_completo,
                        'disponivel': disponivel,
                        'solicitado': qtd_base,
                        'ignorado_por_override': True,
                    })
                    logger.warning(
                        "Override de estoque: produto=%s solicitado=%s disponivel=%s usuário=%s",
                        produto_id, qtd_base, disponivel, usuario,
                    )
                    continue
                else:
                    faltas.append({
                        'produto': produto_id,
                        'descricao': item.produto_variacao.nome_completo,
                        'solicitado': qtd_base,
                        'disponivel': disponivel,
                    })

        if faltas:
            raise CheckoutInsuficienteError(faltas)

        # Create reservations only for items that passed the check
        for item in pedido.itens.select_related('produto_variacao', 'unidade_venda').all():
            produto_id = str(item.produto_variacao_id)
            loja_id    = pedido.loja_id
            unidade_id = (
                item.unidade_venda_id
                if item.unidade_venda_id
                else ConversaoService.obter_unidade_base(produto_id).id
            )
            # Skip overridden items (already in avisos)
            overridden_ids = {a['produto'] for a in avisos}
            if produto_id in overridden_ids:
                continue

            try:
                reserva = EstoqueService.criar_reserva(
                    produto_variacao_id=produto_id,
                    loja_id=loja_id,
                    quantidade=item.quantidade,
                    unidade_id=unidade_id,
                    sessao_checkout=sessao_checkout,
                    usuario=usuario,
                    minutos_expiracao=30,
                )
                reservas.append(reserva)
            except ValueError as exc:
                logger.error("Falha ao criar reserva para item %s: %s", item.pk, exc)

        logger.info(
            "Checkout iniciado: pedido=%s sessao=%s reservas=%d avisos=%d",
            pedido_id, sessao_checkout, len(reservas), len(avisos),
        )

        return {
            'sessao_checkout': sessao_checkout,
            'reservas': reservas,
            'avisos': avisos,
        }

    # ------------------------------------------------------------------
    # T059 — Sale completion: confirm reservations + trigger NF-e
    # ------------------------------------------------------------------

    @staticmethod
    @transaction.atomic
    def finalizar_venda(
        pedido_id: str,
        sessao_checkout: str,
        usuario: User,
        numero_venda: str,
    ):
        """Convert a PedidoVenda into a confirmed Venda, commit stock, and trigger NF-e.

        1. Confirm all reservas for the session.
        2. Trigger stock deductions (MovimentacaoEstoque) per item.
        3. Create Venda record (or update existing).
        4. Call NFEService.processar_nfe_venda to queue NF-e if applicable.

        Returns the Venda instance.
        """
        from apps.fiscal.services import NFEService
        from apps.inventory.services import EstoqueService, ConversaoService
        from apps.sales.models import ItemPedidoVenda, PedidoVenda, Venda

        pedido = PedidoVenda.objects.select_related(
            'loja', 'cliente', 'vendedor'
        ).prefetch_related('itens__produto_variacao').get(pk=pedido_id)

        # 1. Confirm reservations
        from apps.inventory.services import EstoqueService as _ES
        reservas = _ES.confirmar_reservas(sessao_checkout, venda_id=None)  # will link below

        # 2. Create Venda record
        venda, created = Venda.objects.get_or_create(
            numero_venda=numero_venda,
            defaults={
                'pedido_origem': pedido,
                'loja': pedido.loja,
                'cliente': pedido.cliente,
                'vendedor': pedido.vendedor,
                'valor_total': pedido.valor_total,
                'valor_desconto': pedido.valor_desconto,
                'valor_liquido': pedido.valor_total - pedido.valor_desconto,
                'nfe_situacao': 'NAO_APLICAVEL',
            },
        )

        # 3. Back-link reservations to the venda
        if reservas:
            from apps.inventory.models import EstoqueReserva
            EstoqueReserva.objects.filter(
                pk__in=[r.pk for r in reservas]
            ).update(venda=venda)

        # 4. Process stock deductions per item
        for item in pedido.itens.select_related('produto_variacao', 'unidade_venda').all():
            produto_id = str(item.produto_variacao_id)
            unidade_id = (
                item.unidade_venda_id
                if item.unidade_venda_id
                else ConversaoService.obter_unidade_base(produto_id).id
            )
            try:
                EstoqueService.processar_baixa_venda(
                    produto_variacao_id=produto_id,
                    loja_id=pedido.loja_id,
                    quantidade=item.quantidade,
                    unidade_id=unidade_id,
                    venda_id=venda.pk,
                    usuario=usuario,
                )
            except Exception as exc:
                logger.error(
                    "Falha ao baixar estoque: produto=%s venda=%s: %s",
                    produto_id, venda.pk, exc,
                )

        # 5. Update pedido status
        PedidoVenda.objects.filter(pk=pedido_id).update(
            situacao='ENTREGUE',
            data_entrega_real=timezone.now(),
        )

        # 6. Trigger NF-e if applicable (async via Celery)
        try:
            NFEService.processar_nfe_venda(str(venda.pk), usuario)
        except Exception as exc:
            logger.error(
                "Erro ao enfileirar NF-e para venda %s: %s — venda salva normalmente",
                venda.pk, exc,
            )

        logger.info("Venda finalizada: %s (pedido=%s)", venda.numero_venda, pedido_id)
        return venda

    # ------------------------------------------------------------------
    # T060 — Sale cancellation: release reservations
    # ------------------------------------------------------------------

    @staticmethod
    @transaction.atomic
    def cancelar_venda(
        venda_id: str,
        motivo: str,
        usuario: User,
    ):
        """Cancel a sale, reverse stock movements, and release any open reservations.

        1. Mark the Venda as cancelled.
        2. Reverse stock deductions (create DEVOLUCAO_VENDA movements).
        3. Cancel any still-active checkout reservations linked to the sale.
        4. If NF-e was authorized, queue NF-e cancellation with SEFAZ.

        Raises ValueError if the sale is already cancelled.
        """
        from apps.inventory.services import EstoqueService, ConversaoService
        from apps.inventory.models import EstoqueReserva, MovimentacaoEstoque
        from apps.sales.models import Venda

        venda = Venda.objects.select_related(
            'loja', 'pedido_origem', 'vendedor'
        ).get(pk=venda_id)

        if venda.cancelada:
            raise ValueError(f"Venda {venda.numero_venda} já está cancelada")

        # 1. Mark as cancelled
        venda.cancelada = True
        venda.motivo_cancelamento = motivo
        venda.data_cancelamento = timezone.now()
        venda.save(update_fields=['cancelada', 'motivo_cancelamento', 'data_cancelamento', 'updated_at'])

        # 2. Reverse stock movements
        movs = MovimentacaoEstoque.objects.filter(venda=venda, tipo_movimentacao='SAIDA_VENDA')
        for mov in movs:
            try:
                EstoqueService.processar_entrada(
                    produto_variacao_id=str(mov.produto_id),
                    loja_id=venda.loja_id,
                    quantidade=mov.quantidade_base,
                    unidade_id=mov.unidade_base_id,
                    usuario=usuario,
                    tipo_movimentacao='DEVOLUCAO_VENDA',
                    documento_referencia=str(venda.numero_venda),
                )
            except Exception as exc:
                logger.error("Erro ao estornar mov %s: %s", mov.pk, exc)

        # 3. Release any still-active reservations
        reservas_abertas = EstoqueReserva.objects.filter(venda=venda, status='ATIVA')
        if reservas_abertas.exists():
            sessoes = reservas_abertas.values_list('sessao_checkout', flat=True).distinct()
            for sessao in sessoes:
                try:
                    EstoqueService.cancelar_reservas(sessao)
                except Exception as exc:
                    logger.error("Erro ao cancelar reservas sessão %s: %s", sessao, exc)

        # 4. Queue NF-e cancellation if authorized
        if venda.nfe_situacao == 'AUTORIZADA' and venda.nfe_chave_acesso:
            _cancelar_nfe_async(str(venda.pk), motivo, usuario)
        elif venda.nfe_situacao in ('PENDENTE', 'PROCESSANDO', 'AGUARDANDO_RETRY'):
            # Abort in-flight NF-e
            Venda.objects.filter(pk=venda_id).update(nfe_situacao='CANCELADA')

        logger.info("Venda cancelada: %s por %s — motivo: %s", venda.numero_venda, usuario, motivo)
        return venda

    # ------------------------------------------------------------------
    # T064 — Manager override for insufficient stock
    # ------------------------------------------------------------------

    @staticmethod
    def checkout_com_override(
        pedido_id: str,
        sessao_checkout: str,
        usuario: User,
    ) -> dict:
        """Checkout with manager override for insufficient stock.

        The calling view must verify that *usuario* has the
        'inventory.override_estoque_insuficiente' permission.
        """
        return VendaService.iniciar_checkout(
            pedido_id=pedido_id,
            sessao_checkout=sessao_checkout,
            usuario=usuario,
            override_estoque=True,
        )


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _cancelar_nfe_async(venda_id: str, justificativa: str, usuario: User):
    """Queue NF-e cancellation via Celery (fire-and-forget)."""
    try:
        from apps.fiscal.tasks import cancelar_nfe_async  # type: ignore[attr-defined]
        usuario_id = getattr(usuario, 'pk', None)
        cancelar_nfe_async.delay(venda_id, justificativa, usuario_id)
    except Exception as exc:
        logger.error(
            "Não foi possível enfileirar cancelamento NF-e para venda %s: %s",
            venda_id, exc,
        )

"""
Inventory Service Layer
======================
ConversaoService  — unit conversion logic (T011, T020-T021)
EstoqueService    — stock availability, reservations, stock movements (T010, T019, T025-T031, T034)
LoteService       — batch/expiry management (new feature)
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


# ---------------------------------------------------------------------------
# ConversaoService — T011, T020, T021
# ---------------------------------------------------------------------------

class ConversaoService:
    """Handles unit conversions for inventory operations.

    All conversions go through the product's base unit.  Factors are stored in
    ``ProdutoUnidade.fator_conversao``: 1 unit of *unidade* = fator units of base.
    """

    @staticmethod
    def obter_unidade_base(produto_variacao_id: str):
        """Return the UnidadeMedida designated as base for a product variant.

        Raises ``ValueError`` if no base unit is configured.
        """
        from apps.inventory.models import ProdutoUnidade

        pu = (
            ProdutoUnidade.objects
            .select_related('unidade')
            .filter(produto_id=produto_variacao_id, unidade_base=True, ativa=True)
            .first()
        )
        if pu is None:
            # Fall back to the variant's own estoque unit
            from apps.inventory.models import ProdutoVariacao
            pv = ProdutoVariacao.objects.select_related('unidade_estoque').get(pk=produto_variacao_id)
            return pv.unidade_estoque
        return pu.unidade

    @staticmethod
    def converter_quantidade(
        produto_variacao_id: str,
        quantidade: Decimal,
        unidade_origem_id: int,
    ) -> Decimal:
        """Convert *quantidade* from *unidade_origem* to the product's base unit.

        Returns the converted quantity with 6-decimal precision.
        """
        from apps.inventory.models import ProdutoUnidade, UnidadeMedida

        base_unit = ConversaoService.obter_unidade_base(produto_variacao_id)

        if base_unit.id == unidade_origem_id:
            return quantidade

        pu = (
            ProdutoUnidade.objects
            .filter(produto_id=produto_variacao_id, unidade_id=unidade_origem_id, ativa=True)
            .first()
        )
        if pu is None:
            raise ValueError(
                f"No conversion configured for produto={produto_variacao_id} "
                f"unidade={unidade_origem_id}"
            )
        return (quantidade * pu.fator_conversao).quantize(Decimal('0.000001'))

    @staticmethod
    def converter_para_unidade(
        produto_variacao_id: str,
        quantidade_base: Decimal,
        unidade_destino_id: int,
    ) -> Decimal:
        """Convert *quantidade_base* (base unit) to *unidade_destino*.

        Useful for displaying stock in non-base units (e.g. show litres as cans).
        """
        from apps.inventory.models import ProdutoUnidade

        base_unit = ConversaoService.obter_unidade_base(produto_variacao_id)
        if base_unit.id == unidade_destino_id:
            return quantidade_base

        pu = (
            ProdutoUnidade.objects
            .filter(produto_id=produto_variacao_id, unidade_id=unidade_destino_id, ativa=True)
            .first()
        )
        if pu is None or pu.fator_conversao == 0:
            raise ValueError(
                f"No reverse conversion for produto={produto_variacao_id} "
                f"unidade={unidade_destino_id}"
            )
        return (quantidade_base / pu.fator_conversao).quantize(Decimal('0.000001'))


# ---------------------------------------------------------------------------
# EstoqueService — T010, T019, T025-T031, T034
# ---------------------------------------------------------------------------

class EstoqueService:
    """Core inventory operations: availability, reservations, movements."""

    # ------------------------------------------------------------------
    # Availability  (T019)
    # ------------------------------------------------------------------

    @staticmethod
    def calcular_disponibilidade(produto_variacao_id: str, loja_id: int) -> Decimal:
        """Return the available quantity in the product's base unit.

        Available = quantidade_atual - quantidade_reservada in EstoqueLoja.
        """
        from apps.inventory.models import EstoqueLoja

        try:
            estoque = EstoqueLoja.objects.get(
                produto_variacao_id=produto_variacao_id, loja_id=loja_id
            )
            return estoque.quantidade_disponivel
        except EstoqueLoja.DoesNotExist:
            return Decimal('0')

    @staticmethod
    def verificar_disponibilidade(
        produto_variacao_id: str,
        loja_id: int,
        quantidade: Decimal,
        unidade_id: int,
    ) -> bool:
        """Return True if the requested quantity (in *unidade*) is available."""
        qtd_base = ConversaoService.converter_quantidade(
            produto_variacao_id, quantidade, unidade_id
        )
        disponivel = EstoqueService.calcular_disponibilidade(produto_variacao_id, loja_id)
        return disponivel >= qtd_base

    # ------------------------------------------------------------------
    # Reservations  (T025-T027)
    # ------------------------------------------------------------------

    @staticmethod
    @transaction.atomic
    def criar_reserva(
        produto_variacao_id: str,
        loja_id: int,
        quantidade: Decimal,
        unidade_id: int,
        sessao_checkout: str,
        usuario: User,
        minutos_expiracao: int = 30,
    ):
        """Create a temporary stock reservation.

        Converts quantity to base unit, validates availability, updates
        EstoqueLoja.quantidade_reservada and creates EstoqueReserva record.

        Returns the created EstoqueReserva instance.
        Raises ``ValueError`` if insufficient stock.
        """
        from apps.inventory.models import EstoqueLoja, EstoqueReserva, UnidadeMedida

        qtd_base = ConversaoService.converter_quantidade(
            produto_variacao_id, quantidade, unidade_id
        )
        unidade = UnidadeMedida.objects.get(pk=unidade_id)

        estoque = EstoqueLoja.objects.select_for_update().get(
            produto_variacao_id=produto_variacao_id, loja_id=loja_id
        )
        disponivel = estoque.quantidade_atual - estoque.quantidade_reservada
        if qtd_base > disponivel:
            raise ValueError(
                f"Estoque insuficiente. Disponível: {disponivel}, Solicitado: {qtd_base}"
            )

        expira_em = timezone.now() + timezone.timedelta(minutes=minutos_expiracao)

        reserva = EstoqueReserva.objects.create(
            produto_id=produto_variacao_id,
            quantidade_reservada=qtd_base,
            unidade=unidade,
            sessao_checkout=sessao_checkout,
            usuario=usuario,
            expira_em=expira_em,
            status='ATIVA',
        )

        estoque.quantidade_reservada += qtd_base
        estoque.save(update_fields=['quantidade_reservada', 'updated_at'])

        logger.info(
            "Reserva criada: produto=%s sessao=%s qtd=%s expira=%s",
            produto_variacao_id, sessao_checkout, qtd_base, expira_em,
        )
        return reserva

    @staticmethod
    @transaction.atomic
    def confirmar_reservas(sessao_checkout: str, venda_id):
        """Confirm all active reservations for a checkout session.

        Sets status to CONFIRMADA and links to the finalised sale.
        Returns the list of confirmed EstoqueReserva instances.
        """
        from apps.inventory.models import EstoqueReserva

        reservas = (
            EstoqueReserva.objects
            .select_for_update()
            .filter(sessao_checkout=sessao_checkout, status='ATIVA')
        )
        confirmadas = []
        for reserva in reservas:
            reserva.status = 'CONFIRMADA'
            reserva.venda_id = venda_id
            reserva.save(update_fields=['status', 'venda', 'updated_at'])
            confirmadas.append(reserva)

        logger.info(
            "Reservas confirmadas: sessao=%s venda=%s total=%d",
            sessao_checkout, venda_id, len(confirmadas),
        )
        return confirmadas

    @staticmethod
    @transaction.atomic
    def cancelar_reservas(sessao_checkout: str):
        """Release all active reservations for a checkout session.

        Decrements EstoqueLoja.quantidade_reservada for each reservation.
        """
        from apps.inventory.models import EstoqueLoja, EstoqueReserva

        reservas = EstoqueReserva.objects.select_for_update().filter(
            sessao_checkout=sessao_checkout, status='ATIVA'
        )
        for reserva in reservas:
            try:
                estoque = EstoqueLoja.objects.select_for_update().get(
                    produto_variacao=reserva.produto,
                    loja__lojas_usuario__isnull=True,  # fallback — use signal instead
                )
            except EstoqueLoja.DoesNotExist:
                pass
            else:
                estoque.quantidade_reservada = max(
                    Decimal('0'), estoque.quantidade_reservada - reserva.quantidade_reservada
                )
                estoque.save(update_fields=['quantidade_reservada', 'updated_at'])

            reserva.status = 'CANCELADA'
            reserva.save(update_fields=['status', 'updated_at'])

        logger.info("Reservas canceladas: sessao=%s", sessao_checkout)

    # ------------------------------------------------------------------
    # Stock movements  (T031, T034)
    # ------------------------------------------------------------------

    @staticmethod
    @transaction.atomic
    def processar_baixa_venda(
        produto_variacao_id: str,
        loja_id: int,
        quantidade: Decimal,
        unidade_id: int,
        venda_id,
        usuario: User,
        lote_id: Optional[str] = None,
        nfe_id: Optional[str] = None,
    ):
        """Definitively deduct sold quantity from stock.

        Converts to base unit, records MovimentacaoEstoque with before/after
        balances.  If reservas were already created for this sale, they should
        have been confirmed via confirmar_reservas beforehand.
        """
        from apps.inventory.models import EstoqueLoja, MovimentacaoEstoque, UnidadeMedida

        qtd_base = ConversaoService.converter_quantidade(
            produto_variacao_id, quantidade, unidade_id
        )
        unidade_orig = UnidadeMedida.objects.get(pk=unidade_id)
        base_unit = ConversaoService.obter_unidade_base(produto_variacao_id)

        estoque = EstoqueLoja.objects.select_for_update().get(
            produto_variacao_id=produto_variacao_id, loja_id=loja_id
        )
        estoque_antes = estoque.quantidade_atual

        estoque.quantidade_atual -= qtd_base
        estoque.quantidade_reservada = max(
            Decimal('0'), estoque.quantidade_reservada - qtd_base
        )
        estoque.data_ultima_movimentacao = timezone.now()
        estoque.save(update_fields=['quantidade_atual', 'quantidade_reservada', 'data_ultima_movimentacao', 'updated_at'])

        mov = MovimentacaoEstoque.objects.create(
            produto_id=produto_variacao_id,
            tipo_movimentacao='SAIDA_VENDA',
            quantidade_original=quantidade,
            unidade_original=unidade_orig,
            quantidade_base=qtd_base,
            unidade_base=base_unit,
            estoque_antes=estoque_antes,
            estoque_depois=estoque.quantidade_atual,
            venda_id=venda_id,
            nfe_id=nfe_id,
            usuario=usuario,
        )

        if lote_id:
            EstoqueService._baixar_lote(lote_id, qtd_base, usuario)

        # Alert if below minimum
        from apps.inventory.models import ProdutoVariacao
        pv = ProdutoVariacao.objects.get(pk=produto_variacao_id)
        if estoque.quantidade_atual <= pv.estoque_minimo:
            logger.warning(
                "ESTOQUE MÍNIMO ATINGIDO: produto=%s loja=%s atual=%s minimo=%s",
                produto_variacao_id, loja_id, estoque.quantidade_atual, pv.estoque_minimo,
            )

        logger.info(
            "Baixa venda: produto=%s qtd_base=%s venda=%s",
            produto_variacao_id, qtd_base, venda_id,
        )
        return mov

    @staticmethod
    @transaction.atomic
    def processar_entrada(
        produto_variacao_id: str,
        loja_id: int,
        quantidade: Decimal,
        unidade_id: int,
        usuario: User,
        tipo_movimentacao: str = 'ENTRADA_COMPRA',
        documento_referencia: str = '',
        nfe_id=None,
        numero_lote: Optional[str] = None,
        data_validade=None,
        data_fabricacao=None,
        custo_unitario: Decimal = Decimal('0'),
    ):
        """Record an inbound stock movement and optionally create a LoteProduto.

        Returns (MovimentacaoEstoque, LoteProduto | None).
        """
        from apps.inventory.models import EstoqueLoja, LoteProduto, MovimentacaoEstoque, UnidadeMedida

        qtd_base = ConversaoService.converter_quantidade(
            produto_variacao_id, quantidade, unidade_id
        )
        unidade_orig = UnidadeMedida.objects.get(pk=unidade_id)
        base_unit = ConversaoService.obter_unidade_base(produto_variacao_id)

        estoque, _ = EstoqueLoja.objects.select_for_update().get_or_create(
            produto_variacao_id=produto_variacao_id,
            loja_id=loja_id,
            defaults={'quantidade_atual': Decimal('0'), 'quantidade_reservada': Decimal('0')},
        )
        estoque_antes = estoque.quantidade_atual
        estoque.quantidade_atual += qtd_base
        estoque.data_ultima_movimentacao = timezone.now()
        estoque.save(update_fields=['quantidade_atual', 'data_ultima_movimentacao', 'updated_at'])

        mov = MovimentacaoEstoque.objects.create(
            produto_id=produto_variacao_id,
            tipo_movimentacao=tipo_movimentacao,
            quantidade_original=quantidade,
            unidade_original=unidade_orig,
            quantidade_base=qtd_base,
            unidade_base=base_unit,
            estoque_antes=estoque_antes,
            estoque_depois=estoque.quantidade_atual,
            nfe_id=nfe_id,
            usuario=usuario,
            documento_referencia=documento_referencia,
        )

        lote = None
        if numero_lote:
            lote, _ = LoteProduto.objects.get_or_create(
                produto_id=produto_variacao_id,
                loja_id=loja_id,
                numero_lote=numero_lote,
                defaults={
                    'data_fabricacao': data_fabricacao,
                    'data_validade': data_validade,
                    'data_entrada': timezone.now().date(),
                    'quantidade_inicial': qtd_base,
                    'quantidade_atual': qtd_base,
                    'unidade': base_unit,
                    'custo_unitario': custo_unitario,
                    'documento_entrada': documento_referencia,
                },
            )
            if not _:
                lote.quantidade_atual += qtd_base
                lote.save(update_fields=['quantidade_atual', 'updated_at'])

        logger.info(
            "Entrada estoque: produto=%s loja=%s qtd_base=%s doc=%s lote=%s",
            produto_variacao_id, loja_id, qtd_base, documento_referencia, numero_lote,
        )
        return mov, lote

    # Internal helpers
    @staticmethod
    def _baixar_lote(lote_id: str, quantidade: Decimal, usuario: User):
        from apps.inventory.models import LoteProduto

        lote = LoteProduto.objects.select_for_update().get(pk=lote_id)
        lote.quantidade_atual = max(Decimal('0'), lote.quantidade_atual - quantidade)
        if lote.quantidade_atual == 0:
            lote.status = 'ESGOTADO'
        lote.save(update_fields=['quantidade_atual', 'status', 'updated_at'])


# ---------------------------------------------------------------------------
# LoteService — new feature: batch / expiry  management
# ---------------------------------------------------------------------------

class LoteService:
    """Operations specifically for batch (lote) and expiry (validade) management."""

    @staticmethod
    def listar_lotes_proximos_vencimento(loja_id: int, dias: int = 30):
        """Return lotes expiring within *dias* days, ordered by expiry date."""
        from apps.inventory.models import LoteProduto

        limite = timezone.now().date() + timezone.timedelta(days=dias)
        return (
            LoteProduto.objects
            .select_related('produto__produto_base', 'unidade')
            .filter(
                loja_id=loja_id,
                status='ATIVO',
                data_validade__lte=limite,
                data_validade__gte=timezone.now().date(),
                quantidade_atual__gt=0,
            )
            .order_by('data_validade')
        )

    @staticmethod
    def marcar_lotes_vencidos(loja_id: int | None = None):
        """Mark all expired lotes as VENCIDO.  Returns count updated."""
        from apps.inventory.models import LoteProduto

        qs = LoteProduto.objects.filter(
            status='ATIVO',
            data_validade__lt=timezone.now().date(),
        )
        if loja_id:
            qs = qs.filter(loja_id=loja_id)

        count = qs.update(status='VENCIDO')
        if count:
            logger.warning("Marcados %d lotes como VENCIDO", count)
        return count

    @staticmethod
    def obter_lote_fifo(produto_variacao_id: str, loja_id: int):
        """Return the oldest active lot with available quantity (FIFO strategy)."""
        from apps.inventory.models import LoteProduto

        return (
            LoteProduto.objects
            .filter(
                produto_id=produto_variacao_id,
                loja_id=loja_id,
                status='ATIVO',
                quantidade_atual__gt=0,
            )
            .order_by('data_validade', 'data_entrada')
            .first()
        )

    @staticmethod
    def obter_lote_fefo(produto_variacao_id: str, loja_id: int):
        """Return lot with earliest expiry (FEFO — First Expired, First Out)."""
        from apps.inventory.models import LoteProduto

        return (
            LoteProduto.objects
            .filter(
                produto_id=produto_variacao_id,
                loja_id=loja_id,
                status='ATIVO',
                quantidade_atual__gt=0,
                data_validade__isnull=False,
            )
            .order_by('data_validade')
            .first()
        )

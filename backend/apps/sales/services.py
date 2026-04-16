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

# Imported at module level so they can be patched in unit tests.
# (No circular import: models.py does not import from services.py)
from apps.sales.models import DescontoAuditLog, Recebivel

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


# ===========================================================================
# T009–T011 — DescontoService
# ===========================================================================

class DescontoInsuficientePermissaoError(Exception):
    """Raised when the approver lacks the required level for the discount."""


class DescontoPINError(Exception):
    """Raised on invalid PIN attempt. Carries attempt count."""

    def __init__(self, tentativas: int, max_tentativas: int = 3):
        self.tentativas = tentativas
        self.max_tentativas = max_tentativas
        super().__init__(
            f"PIN incorreto. Tentativa {tentativas}/{max_tentativas}."
        )


class DescontoCooldownError(Exception):
    """Raised when max PIN attempts exceeded; operation is locked."""


# Thread-local attempt counters keyed by (pedido_id, session key).
# For production, replace with cache (e.g., Django cache with TTL).
_pin_attempts: dict = {}


class DescontoService:
    """Business rules for discount authorization (T009–T011 / US004).

    Discount tiers (BR-004):
      ≤  5% — automatic, no PIN
      ≤ 20% — requires gerente PIN
      >  20% — requires diretor PIN
    """

    MAX_PIN_TENTATIVAS = 3

    # ------------------------------------------------------------------
    # T009 — validar_desconto
    # ------------------------------------------------------------------

    @staticmethod
    def validar_desconto(pedido, percentual: Decimal, solicitante) -> dict:
        """Validate whether a discount requires PIN approval.

        Returns:
            {'aprovado': bool, 'requer_pin': bool, 'nivel': str|None}
        """
        percentual = Decimal(str(percentual))
        if percentual <= Decimal('5.00'):
            return {'aprovado': True, 'requer_pin': False, 'nivel': None}
        elif percentual <= Decimal('20.00'):
            return {'aprovado': False, 'requer_pin': True, 'nivel': 'gerente'}
        else:
            return {'aprovado': False, 'requer_pin': True, 'nivel': 'diretor'}

    # ------------------------------------------------------------------
    # T010 — aprovar_com_pin (total discount on PedidoVenda)
    # ------------------------------------------------------------------

    @staticmethod
    @transaction.atomic
    def aprovar_com_pin(
        pedido,
        percentual: Decimal,
        motivo: str,
        pin: str,
        aprovador,
    ):
        """Apply a discount to a PedidoVenda after PIN verification.

        Raises:
            DescontoInsuficientePermissaoError — aprovador lacks the required group.
            DescontoPINError — PIN is wrong (up to MAX_PIN_TENTATIVAS).
            DescontoCooldownError — max attempts exceeded.
        """
        percentual = Decimal(str(percentual))
        validacao = DescontoService.validar_desconto(pedido, percentual, aprovador)

        if validacao['aprovado']:
            # ≤5% — no PIN required; apply directly
            return DescontoService._aplicar_desconto_total(
                pedido, percentual, motivo, solicitante=aprovador, aprovador=None,
            )

        nivel = validacao['nivel']
        DescontoService._verificar_nivel_aprovador(aprovador, nivel)

        # PIN verification with attempt tracking
        chave = f"desconto_pin_{pedido.pk}_{aprovador.pk}"
        tentativas = _pin_attempts.get(chave, 0)

        if tentativas >= DescontoService.MAX_PIN_TENTATIVAS:
            raise DescontoCooldownError(
                f"Máximo de {DescontoService.MAX_PIN_TENTATIVAS} tentativas atingido. "
                "Aguarde antes de tentar novamente."
            )

        if not aprovador.check_password(pin):
            tentativas += 1
            _pin_attempts[chave] = tentativas
            if tentativas >= DescontoService.MAX_PIN_TENTATIVAS:
                raise DescontoCooldownError(
                    f"Máximo de {DescontoService.MAX_PIN_TENTATIVAS} tentativas atingido. "
                    "Aguarde antes de tentar novamente."
                )
            raise DescontoPINError(tentativas, DescontoService.MAX_PIN_TENTATIVAS)

        # PIN correct — clear counter
        _pin_attempts.pop(chave, None)

        return DescontoService._aplicar_desconto_total(
            pedido, percentual, motivo, solicitante=aprovador, aprovador=aprovador,
            aprovado_com_pin=True,
        )

    # ------------------------------------------------------------------
    # T011 — aplicar_desconto_item (per-item discount)
    # ------------------------------------------------------------------

    @staticmethod
    @transaction.atomic
    def aplicar_desconto_item(
        item,
        percentual: Decimal,
        solicitante,
        aprovador=None,
        pin: str | None = None,
    ):
        """Apply a discount to a single ItemPedidoVenda.

        If percentual > 5%, *aprovador* and *pin* are required.
        Recalculates pedido totals after applying.

        Returns the updated item.
        """
        percentual = Decimal(str(percentual))

        if percentual > Decimal('5.00'):
            if aprovador is None or pin is None:
                raise DescontoInsuficientePermissaoError(
                    "Desconto > 5% requer aprovador e PIN."
                )
            nivel = DescontoService.validar_desconto(item.pedido, percentual, solicitante)['nivel']
            DescontoService._verificar_nivel_aprovador(aprovador, nivel)

            chave = f"desconto_pin_{item.pedido.pk}_{aprovador.pk}"
            tentativas = _pin_attempts.get(chave, 0)
            if tentativas >= DescontoService.MAX_PIN_TENTATIVAS:
                raise DescontoCooldownError("Máximo de tentativas atingido.")

            if not aprovador.check_password(pin):
                tentativas += 1
                _pin_attempts[chave] = tentativas
                if tentativas >= DescontoService.MAX_PIN_TENTATIVAS:
                    raise DescontoCooldownError("Máximo de tentativas atingido.")
                raise DescontoPINError(tentativas, DescontoService.MAX_PIN_TENTATIVAS)

            _pin_attempts.pop(chave, None)
            aprovado_com_pin = True
        else:
            aprovado_com_pin = False

        valor_antes = item.preco_total
        desconto_valor = (item.preco_unitario * item.quantidade * percentual / Decimal('100')).quantize(Decimal('0.01'))
        item.desconto_percentual = percentual
        item.desconto_valor = desconto_valor
        item.preco_total = max(Decimal('0.00'), item.preco_unitario * item.quantidade - desconto_valor)
        item.save(update_fields=['desconto_percentual', 'desconto_valor', 'preco_total', 'updated_at'])

        DescontoAuditLog.objects.create(
            pedido=item.pedido,
            solicitante=solicitante,
            aprovador=aprovador,
            tipo_desconto='ITEM',
            item=item,
            valor_antes=valor_antes,
            valor_depois=item.preco_total,
            percentual=percentual,
            aprovado_com_pin=aprovado_com_pin,
        )

        # Recalculate pedido totals
        DescontoService._recalcular_totais_pedido(item.pedido)

        return item

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _verificar_nivel_aprovador(aprovador, nivel: str):
        grupos = aprovador.groups.values_list('name', flat=True)
        if nivel == 'gerente' and not (
            'gerente' in grupos or 'diretor' in grupos or aprovador.is_superuser
        ):
            raise DescontoInsuficientePermissaoError(
                "Desconto > 5% requer aprovação de gerente."
            )
        if nivel == 'diretor' and not ('diretor' in grupos or aprovador.is_superuser):
            raise DescontoInsuficientePermissaoError(
                "Desconto > 20% requer aprovação de diretor."
            )

    @staticmethod
    def _aplicar_desconto_total(pedido, percentual, motivo, solicitante, aprovador, aprovado_com_pin=False):
        valor_antes = pedido.valor_total
        desconto = (pedido.valor_subtotal * percentual / Decimal('100')).quantize(Decimal('0.01'))
        pedido.valor_desconto = desconto
        pedido.percentual_desconto = percentual
        pedido.valor_total = max(Decimal('0.00'), pedido.valor_subtotal - desconto)
        pedido.desconto_aprovador = aprovador
        pedido.desconto_motivo = motivo
        if aprovador:
            from django.utils import timezone as tz
            pedido.desconto_aprovado_em = tz.now()
        pedido.save(update_fields=[
            'valor_desconto', 'percentual_desconto', 'valor_total',
            'desconto_aprovador', 'desconto_motivo', 'desconto_aprovado_em', 'updated_at',
        ])

        DescontoAuditLog.objects.create(
            pedido=pedido,
            solicitante=solicitante,
            aprovador=aprovador,
            tipo_desconto='TOTAL',
            item=None,
            valor_antes=valor_antes,
            valor_depois=pedido.valor_total,
            percentual=percentual,
            motivo=motivo,
            aprovado_com_pin=aprovado_com_pin,
        )
        return pedido

    @staticmethod
    def _recalcular_totais_pedido(pedido):
        from apps.sales.models import ItemPedidoVenda
        from django.db.models import Sum

        subtotal = (
            ItemPedidoVenda.objects
            .filter(pedido=pedido)
            .aggregate(total=Sum('preco_total'))['total']
            or Decimal('0.00')
        )
        pedido.valor_subtotal = subtotal
        pedido.valor_total = subtotal - pedido.valor_desconto
        pedido.save(update_fields=['valor_subtotal', 'valor_total', 'updated_at'])


# ===========================================================================
# T012–T014 — CreditoService
# ===========================================================================

class CreditoInsuficienteError(Exception):
    """Raised when a customer's credit limit would be exceeded."""

    def __init__(self, disponivel: Decimal, solicitado: Decimal):
        self.disponivel = disponivel
        self.solicitado = solicitado
        super().__init__(
            f"Crédito insuficiente: disponível R$ {disponivel}, solicitado R$ {solicitado}"
        )


class CreditoOverrideError(Exception):
    """Raised on PIN failure during credit override."""

    def __init__(self, tentativas: int, max_tentativas: int = 3):
        self.tentativas = tentativas
        self.max_tentativas = max_tentativas
        super().__init__(f"PIN de override incorreto. Tentativa {tentativas}/{max_tentativas}.")


_credito_pin_attempts: dict = {}


class CreditoService:
    """Credit limit management for crediário/fiado sales (T012–T014 / US005)."""

    MAX_PIN_TENTATIVAS = 3

    # ------------------------------------------------------------------
    # T012 — verificar_disponivel
    # ------------------------------------------------------------------

    @staticmethod
    def verificar_disponivel(cliente, valor_novo: Decimal) -> dict:
        """Check available credit for the cliente before a new sale.

        Returns:
            {'disponivel': Decimal, 'saldo_devedor': Decimal, 'limite': Decimal, 'ok': bool}
        """
        from django.db.models import Sum

        valor_novo = Decimal(str(valor_novo))

        saldo_devedor = (
            Recebivel.objects
            .filter(
                cliente=cliente,
                situacao__in=('ABERTO', 'PARCIAL', 'VENCIDO'),
            )
            .aggregate(total=Sum('valor_saldo'))['total']
            or Decimal('0.00')
        )

        limite = Decimal(str(cliente.limite_credito))
        disponivel = limite - saldo_devedor

        return {
            'disponivel': disponivel,
            'saldo_devedor': saldo_devedor,
            'limite': limite,
            'ok': disponivel >= valor_novo,
        }

    # ------------------------------------------------------------------
    # T013 — bloquear_para_venda
    # ------------------------------------------------------------------

    @staticmethod
    @transaction.atomic
    def bloquear_para_venda(cliente, valor: Decimal, venda) -> 'Recebivel':
        """Create a Recebivel for a crediário sale.

        Raises CreditoInsuficienteError if credit is insufficient.
        """
        from django.conf import settings
        import datetime

        valor = Decimal(str(valor))
        resultado = CreditoService.verificar_disponivel(cliente, valor)
        if not resultado['ok']:
            raise CreditoInsuficienteError(resultado['disponivel'], valor)

        prazo = getattr(settings, 'CREDITO_PRAZO_DIAS', 30)
        data_venc = (timezone.now().date() + datetime.timedelta(days=prazo))

        return RecebivelService.criar(
            cliente=cliente,
            venda=venda,
            valor=valor,
            data_vencimento=data_venc,
            loja=venda.loja,
        )

    # ------------------------------------------------------------------
    # T013a — override_com_pin
    # ------------------------------------------------------------------

    @staticmethod
    @transaction.atomic
    def override_com_pin(
        cliente,
        valor: Decimal,
        venda,
        pin: str,
        aprovador,
    ) -> 'Recebivel':
        """Create a Recebivel even when the credit limit is exceeded (manager override).

        Requires:
            - aprovador has permission 'sales.override_credit'
            - PIN verification

        Raises:
            PermissionDenied — aprovador lacks 'sales.override_credit'
            CreditoOverrideError — PIN incorrect (up to MAX_PIN_TENTATIVAS)
            DescontoCooldownError — max attempts exceeded
        """
        from django.core.exceptions import PermissionDenied
        import datetime
        from django.conf import settings

        if not (aprovador.has_perm('sales.override_credit') or aprovador.is_superuser):
            raise PermissionDenied("Permissão 'sales.override_credit' necessária para override de crédito.")

        chave = f"credito_override_{cliente.pk}_{aprovador.pk}"
        tentativas = _credito_pin_attempts.get(chave, 0)

        if tentativas >= CreditoService.MAX_PIN_TENTATIVAS:
            raise DescontoCooldownError(
                f"Máximo de {CreditoService.MAX_PIN_TENTATIVAS} tentativas de PIN atingido."
            )

        if not aprovador.check_password(pin):
            tentativas += 1
            _credito_pin_attempts[chave] = tentativas
            if tentativas >= CreditoService.MAX_PIN_TENTATIVAS:
                raise DescontoCooldownError(
                    f"Máximo de {CreditoService.MAX_PIN_TENTATIVAS} tentativas de PIN atingido."
                )
            raise CreditoOverrideError(tentativas, CreditoService.MAX_PIN_TENTATIVAS)

        _credito_pin_attempts.pop(chave, None)

        resultado = CreditoService.verificar_disponivel(cliente, Decimal(str(valor)))
        prazo = getattr(settings, 'CREDITO_PRAZO_DIAS', 30)
        data_venc = timezone.now().date() + datetime.timedelta(days=prazo)

        recebivel = Recebivel.objects.create(
            cliente=cliente,
            venda=venda,
            loja=venda.loja,
            valor_original=Decimal(str(valor)),
            valor_pago=Decimal('0.00'),
            valor_saldo=Decimal(str(valor)),
            data_vencimento=data_venc,
            situacao='ABERTO',
            criado_com_override=True,
            aprovador_override=aprovador,
        )
        logger.info(
            "Override de crédito: cliente=%s valor=%s aprovador=%s limite=%s saldo_devedor=%s",
            cliente.pk, valor, aprovador, resultado['limite'], resultado['saldo_devedor'],
        )
        return recebivel

    # ------------------------------------------------------------------
    # T014 — registrar_pagamento
    # ------------------------------------------------------------------

    @staticmethod
    @transaction.atomic
    def registrar_pagamento(recebivel, valor_pago: Decimal):
        """Register a partial or full payment on a Recebivel.

        Uses select_for_update to prevent concurrent double-payment.
        Updates situacao: PAGO if saldo==0, PARCIAL otherwise.

        Returns the updated Recebivel.
        """
        valor_pago = Decimal(str(valor_pago))
        if valor_pago <= Decimal('0.00'):
            raise ValueError("valor_pago deve ser maior que zero.")

        # Re-fetch with row lock
        recebivel = Recebivel.objects.select_for_update().get(pk=recebivel.pk)

        if recebivel.situacao == 'CANCELADO':
            raise ValueError("Recebível cancelado não pode receber pagamento.")

        recebivel.valor_pago = recebivel.valor_pago + valor_pago
        # valor_saldo is recomputed in save()
        recebivel.save(update_fields=['valor_pago', 'valor_saldo', 'situacao', 'updated_at'])
        return recebivel


# ===========================================================================
# T015–T017 — RecebivelService
# ===========================================================================

class RecebivelService:
    """CRUD and lifecycle for Recebivel instances (T015–T017 / US005)."""

    # ------------------------------------------------------------------
    # T015 — criar
    # ------------------------------------------------------------------

    @staticmethod
    def criar(cliente, venda, valor: Decimal, data_vencimento, loja) -> 'Recebivel':
        """Create a new Recebivel.  valor_saldo is computed in model.save()."""
        return Recebivel.objects.create(
            cliente=cliente,
            venda=venda,
            loja=loja,
            valor_original=Decimal(str(valor)),
            valor_pago=Decimal('0.00'),
            valor_saldo=Decimal(str(valor)),  # will be re-computed in save()
            data_vencimento=data_vencimento,
            situacao='ABERTO',
        )

    # ------------------------------------------------------------------
    # T016 — baixar (payment registration)
    # ------------------------------------------------------------------

    @staticmethod
    @transaction.atomic
    def baixar(recebivel, valor_pago: Decimal, usuario) -> 'Recebivel':
        """Record a payment on a Recebivel (atomic, select_for_update).

        Delegates to CreditoService.registrar_pagamento for the actual
        accounting update.  Adds audit log if AuditLog model is available.
        """
        return CreditoService.registrar_pagamento(recebivel, valor_pago)

    # ------------------------------------------------------------------
    # T017 — cancelar
    # ------------------------------------------------------------------

    @staticmethod
    @transaction.atomic
    def cancelar(recebivel, motivo: str, usuario) -> 'Recebivel':
        """Cancel a Recebivel and restore the client's available credit.

        * Marks situacao='CANCELADO'.
        * Restoring credit is implicit: the Recebivel no longer appears in
          the ABERTO/PARCIAL/VENCIDO filter used by verificar_disponivel().

        Returns the updated Recebivel.
        """
        if recebivel.situacao == 'CANCELADO':
            raise ValueError("Recebível já está cancelado.")

        recebivel.situacao = 'CANCELADO'
        recebivel.cancelado_por = usuario
        recebivel.data_cancelamento = timezone.now()
        recebivel.motivo_cancelamento = motivo
        recebivel.save(update_fields=[
            'situacao', 'cancelado_por', 'data_cancelamento', 'motivo_cancelamento', 'updated_at',
        ])

        logger.info(
            "Recebível %s cancelado por %s — motivo: %s",
            recebivel.pk, usuario, motivo,
        )
        return recebivel

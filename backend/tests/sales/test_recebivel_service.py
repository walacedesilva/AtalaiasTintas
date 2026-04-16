"""Unit tests for RecebivelService — T020 / US005.

Covers:
  - criar: valor_saldo == valor_original
  - baixar: delegates to CreditoService.registrar_pagamento (atomic)
  - cancelar: sets CANCELADO, restores credit visibility, raises on double-cancel
"""
from __future__ import annotations

from decimal import Decimal
from unittest.mock import MagicMock, patch, call, ANY
import datetime

from django.test import TestCase


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_user():
    u = MagicMock()
    u.pk = 1
    u.username = 'operador'
    return u


def _make_loja():
    l = MagicMock()
    l.pk = 1
    return l


def _make_cliente():
    c = MagicMock()
    c.pk = 1
    c.nome_completo = 'Cliente Teste'
    return c


def _make_venda():
    v = MagicMock()
    v.pk = 'venda-xyz'
    return v


# ---------------------------------------------------------------------------
# T015 — criar
# ---------------------------------------------------------------------------

class RecebivelCriarTests(TestCase):

    @patch('apps.sales.models.Recebivel.objects')
    def test_criar_seta_valor_saldo_igual_ao_original(self, mock_qs):
        from apps.sales.services import RecebivelService

        recebivel_mock = MagicMock()
        recebivel_mock.valor_saldo = Decimal('150.00')
        mock_qs.create.return_value = recebivel_mock

        resultado = RecebivelService.criar(
            cliente=_make_cliente(),
            venda=_make_venda(),
            valor=Decimal('150.00'),
            data_vencimento=datetime.date.today(),
            loja=_make_loja(),
        )

        self.assertEqual(resultado, recebivel_mock)
        call_kwargs = mock_qs.create.call_args[1]
        self.assertEqual(call_kwargs['valor_original'], Decimal('150.00'))
        self.assertEqual(call_kwargs['valor_saldo'], Decimal('150.00'))
        self.assertEqual(call_kwargs['valor_pago'], Decimal('0.00'))
        self.assertEqual(call_kwargs['situacao'], 'ABERTO')

    @patch('apps.sales.models.Recebivel.objects')
    def test_criar_sem_venda_ok(self, mock_qs):
        """Recebivel can be created without a linked Venda (venda=None)."""
        from apps.sales.services import RecebivelService

        mock_qs.create.return_value = MagicMock()

        RecebivelService.criar(
            cliente=_make_cliente(),
            venda=None,
            valor=Decimal('200.00'),
            data_vencimento=datetime.date.today(),
            loja=_make_loja(),
        )

        call_kwargs = mock_qs.create.call_args[1]
        self.assertIsNone(call_kwargs['venda'])


# ---------------------------------------------------------------------------
# T016 — baixar (delegates to CreditoService)
# ---------------------------------------------------------------------------

class RecebivelBaixarTests(TestCase):

    @patch('apps.sales.services.CreditoService.registrar_pagamento')
    def test_baixar_delega_para_credito_service(self, mock_registrar):
        from apps.sales.services import RecebivelService

        recebivel = MagicMock()
        recebivel.pk = 1
        updated = MagicMock()
        mock_registrar.return_value = updated

        resultado = RecebivelService.baixar(recebivel, Decimal('75.00'), _make_user())

        mock_registrar.assert_called_once_with(recebivel, Decimal('75.00'))
        self.assertEqual(resultado, updated)

    @patch('apps.sales.services.CreditoService.registrar_pagamento')
    def test_baixar_propaga_value_error_de_cancelado(self, mock_registrar):
        """Should propagate ValueError when recebivel is already cancelled."""
        from apps.sales.services import RecebivelService

        mock_registrar.side_effect = ValueError("Recebível cancelado não pode receber pagamento.")
        recebivel = MagicMock()

        with self.assertRaises(ValueError):
            RecebivelService.baixar(recebivel, Decimal('50.00'), _make_user())


# ---------------------------------------------------------------------------
# T017 — cancelar
# ---------------------------------------------------------------------------

class RecebivelCancelarTests(TestCase):

    def test_cancelar_aberto_atualiza_campos(self):
        from apps.sales.services import RecebivelService

        recebivel = MagicMock()
        recebivel.situacao = 'ABERTO'
        recebivel.save = MagicMock()

        usuario = _make_user()
        RecebivelService.cancelar(recebivel, 'teste de cancelamento', usuario)

        self.assertEqual(recebivel.situacao, 'CANCELADO')
        self.assertEqual(recebivel.cancelado_por, usuario)
        self.assertIsNotNone(recebivel.data_cancelamento)
        self.assertEqual(recebivel.motivo_cancelamento, 'teste de cancelamento')
        recebivel.save.assert_called_once()

    def test_cancelar_parcial_ok(self):
        from apps.sales.services import RecebivelService

        recebivel = MagicMock()
        recebivel.situacao = 'PARCIAL'
        recebivel.save = MagicMock()

        RecebivelService.cancelar(recebivel, 'ajuste', _make_user())
        self.assertEqual(recebivel.situacao, 'CANCELADO')

    def test_duplo_cancelamento_levanta_value_error(self):
        """Cancelling an already-cancelled Recebivel must raise ValueError."""
        from apps.sales.services import RecebivelService

        recebivel = MagicMock()
        recebivel.situacao = 'CANCELADO'

        with self.assertRaises(ValueError):
            RecebivelService.cancelar(recebivel, 'segunda vez', _make_user())

    def test_cancelar_restaura_credito_implicita(self):
        """After cancellation the recebivel's situacao is CANCELADO so it is
        excluded from CreditoService.verificar_disponivel's queryset
        (situacao__in=ABERTO/PARCIAL/VENCIDO).  This test verifies the
        state transition that makes the credit visible again."""
        from apps.sales.services import RecebivelService, CreditoService

        recebivel = MagicMock()
        recebivel.situacao = 'VENCIDO'
        recebivel.save = MagicMock()

        RecebivelService.cancelar(recebivel, 'motivo', _make_user())

        # After cancel, situacao == 'CANCELADO' — excluded from saldo_devedor
        self.assertEqual(recebivel.situacao, 'CANCELADO')

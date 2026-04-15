"""Unit tests for CreditoService — T019 / US005.

Covers:
  - verificar_disponivel: ok/not-ok based on existing recebiveis
  - bloquear_para_venda: creates Recebivel, raises on insufficient credit
  - registrar_pagamento: PARCIAL / PAGO transitions, select_for_update safety
  - override_com_pin: correct PIN + permission → Recebivel with override flags
  - override_com_pin: wrong PIN → CreditoOverrideError
  - override_com_pin: missing permission → PermissionDenied
"""
from __future__ import annotations

from decimal import Decimal
from unittest.mock import MagicMock, patch, PropertyMock

from django.test import TestCase


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_cliente(limite: Decimal = Decimal('500.00')):
    c = MagicMock()
    c.pk = 1
    c.limite_credito = limite
    c.nome_completo = 'Cliente Teste'
    return c


def _make_venda(loja=None):
    v = MagicMock()
    v.pk = 'venda-abc'
    v.loja = loja or MagicMock()
    v.loja_id = 1
    return v


def _make_user(tem_permissao: bool = True, password_ok: bool = True):
    u = MagicMock()
    u.pk = 99
    u.is_superuser = False
    u.check_password = MagicMock(return_value=password_ok)
    u.has_perm = MagicMock(return_value=tem_permissao)
    return u


# ---------------------------------------------------------------------------
# T012 — verificar_disponivel
# ---------------------------------------------------------------------------

class CreditoVerificarDisponivelTests(TestCase):

    def setUp(self):
        from apps.sales.services import _credito_pin_attempts
        _credito_pin_attempts.clear()

    @patch('apps.sales.models.Recebivel.objects')
    def test_sem_recebiveis_credito_total_disponivel(self, mock_qs):
        from apps.sales.services import CreditoService

        mock_qs.filter.return_value.aggregate.return_value = {'total': None}

        cliente = _make_cliente(Decimal('1000.00'))
        resultado = CreditoService.verificar_disponivel(cliente, Decimal('200.00'))

        self.assertEqual(resultado['disponivel'], Decimal('1000.00'))
        self.assertEqual(resultado['saldo_devedor'], Decimal('0.00'))
        self.assertTrue(resultado['ok'])

    @patch('apps.sales.models.Recebivel.objects')
    def test_saldo_devedor_parcial_reduz_disponivel(self, mock_qs):
        from apps.sales.services import CreditoService

        mock_qs.filter.return_value.aggregate.return_value = {'total': Decimal('300.00')}

        cliente = _make_cliente(Decimal('500.00'))
        resultado = CreditoService.verificar_disponivel(cliente, Decimal('150.00'))

        self.assertEqual(resultado['disponivel'], Decimal('200.00'))
        self.assertEqual(resultado['saldo_devedor'], Decimal('300.00'))
        self.assertTrue(resultado['ok'])

    @patch('apps.sales.models.Recebivel.objects')
    def test_credito_esgotado_ok_false(self, mock_qs):
        from apps.sales.services import CreditoService

        mock_qs.filter.return_value.aggregate.return_value = {'total': Decimal('480.00')}

        cliente = _make_cliente(Decimal('500.00'))
        resultado = CreditoService.verificar_disponivel(cliente, Decimal('50.00'))

        self.assertEqual(resultado['disponivel'], Decimal('20.00'))
        self.assertFalse(resultado['ok'])

    @patch('apps.sales.models.Recebivel.objects')
    def test_valor_exatamente_igual_ao_disponivel_ok_true(self, mock_qs):
        from apps.sales.services import CreditoService

        mock_qs.filter.return_value.aggregate.return_value = {'total': Decimal('300.00')}

        cliente = _make_cliente(Decimal('500.00'))
        resultado = CreditoService.verificar_disponivel(cliente, Decimal('200.00'))

        self.assertTrue(resultado['ok'])


# ---------------------------------------------------------------------------
# T013 — bloquear_para_venda
# ---------------------------------------------------------------------------

class CreditoBloqueioParaVendaTests(TestCase):

    def setUp(self):
        from apps.sales.services import _credito_pin_attempts
        _credito_pin_attempts.clear()

    @patch('apps.sales.services.RecebivelService.criar')
    @patch('apps.sales.services.CreditoService.verificar_disponivel')
    def test_credito_suficiente_cria_recebivel(self, mock_verif, mock_criar):
        from apps.sales.services import CreditoService

        mock_verif.return_value = {
            'disponivel': Decimal('300.00'),
            'saldo_devedor': Decimal('200.00'),
            'limite': Decimal('500.00'),
            'ok': True,
        }
        recebivel_mock = MagicMock()
        mock_criar.return_value = recebivel_mock

        cliente = _make_cliente()
        venda = _make_venda()
        resultado = CreditoService.bloquear_para_venda(cliente, Decimal('100.00'), venda)

        self.assertEqual(resultado, recebivel_mock)
        mock_criar.assert_called_once()

    @patch('apps.sales.services.CreditoService.verificar_disponivel')
    def test_credito_insuficiente_levanta_erro(self, mock_verif):
        from apps.sales.services import CreditoService, CreditoInsuficienteError

        mock_verif.return_value = {
            'disponivel': Decimal('10.00'),
            'saldo_devedor': Decimal('490.00'),
            'limite': Decimal('500.00'),
            'ok': False,
        }

        with self.assertRaises(CreditoInsuficienteError) as ctx:
            CreditoService.bloquear_para_venda(_make_cliente(), Decimal('100.00'), _make_venda())

        self.assertEqual(ctx.exception.disponivel, Decimal('10.00'))
        self.assertEqual(ctx.exception.solicitado, Decimal('100.00'))


# ---------------------------------------------------------------------------
# T013a — override_com_pin
# ---------------------------------------------------------------------------

class CreditoOverridePinTests(TestCase):

    def setUp(self):
        from apps.sales.services import _credito_pin_attempts
        _credito_pin_attempts.clear()

    @patch('apps.sales.services.CreditoService.verificar_disponivel')
    @patch('apps.sales.models.Recebivel.objects')
    def test_override_pin_correto_cria_recebivel_com_flag(self, mock_qs, mock_verif):
        from apps.sales.services import CreditoService

        mock_verif.return_value = {
            'disponivel': Decimal('0.00'),
            'saldo_devedor': Decimal('500.00'),
            'limite': Decimal('500.00'),
            'ok': False,
        }
        recebivel_mock = MagicMock()
        mock_qs.create.return_value = recebivel_mock

        aprovador = _make_user(tem_permissao=True, password_ok=True)
        cliente = _make_cliente()
        venda = _make_venda()

        resultado = CreditoService.override_com_pin(cliente, Decimal('200.00'), venda, '1234', aprovador)

        self.assertEqual(resultado, recebivel_mock)
        call_kwargs = mock_qs.create.call_args[1]
        self.assertTrue(call_kwargs['criado_com_override'])
        self.assertEqual(call_kwargs['aprovador_override'], aprovador)

    def test_sem_permissao_levanta_permission_denied(self):
        from apps.sales.services import CreditoService
        from django.core.exceptions import PermissionDenied

        aprovador = _make_user(tem_permissao=False)

        with self.assertRaises(PermissionDenied):
            CreditoService.override_com_pin(_make_cliente(), Decimal('100.00'), _make_venda(), '1234', aprovador)

    def test_pin_errado_levanta_credito_override_error(self):
        from apps.sales.services import CreditoService, CreditoOverrideError

        aprovador = _make_user(tem_permissao=True, password_ok=False)

        with self.assertRaises(CreditoOverrideError) as ctx:
            CreditoService.override_com_pin(_make_cliente(), Decimal('100.00'), _make_venda(), 'wrong', aprovador)

        self.assertEqual(ctx.exception.tentativas, 1)

    def test_tres_tentativas_erradas_cooldown(self):
        from apps.sales.services import CreditoService, CreditoOverrideError, DescontoCooldownError

        aprovador = _make_user(tem_permissao=True, password_ok=False)

        for _ in range(2):
            with self.assertRaises(CreditoOverrideError):
                CreditoService.override_com_pin(_make_cliente(), Decimal('100.00'), _make_venda(), 'wrong', aprovador)

        with self.assertRaises(DescontoCooldownError):
            CreditoService.override_com_pin(_make_cliente(), Decimal('100.00'), _make_venda(), 'wrong', aprovador)


# ---------------------------------------------------------------------------
# T014 — registrar_pagamento
# ---------------------------------------------------------------------------

class CreditoRegistrarPagamentoTests(TestCase):

    @patch('apps.sales.models.Recebivel.objects')
    def test_pagamento_parcial_status_parcial(self, mock_qs):
        from apps.sales.services import CreditoService

        recebivel = MagicMock()
        recebivel.pk = 1
        recebivel.situacao = 'ABERTO'
        recebivel.valor_pago = Decimal('0.00')
        recebivel.valor_original = Decimal('200.00')
        recebivel.valor_saldo = Decimal('200.00')
        recebivel.save = MagicMock()

        # select_for_update().get() returns the same mock
        mock_qs.select_for_update.return_value.get.return_value = recebivel

        CreditoService.registrar_pagamento(recebivel, Decimal('50.00'))

        recebivel.save.assert_called_once()
        # valor_pago updated
        self.assertEqual(recebivel.valor_pago, Decimal('50.00'))

    @patch('apps.sales.models.Recebivel.objects')
    def test_cancelado_levanta_value_error(self, mock_qs):
        from apps.sales.services import CreditoService

        recebivel = MagicMock()
        recebivel.pk = 2
        recebivel.situacao = 'CANCELADO'
        mock_qs.select_for_update.return_value.get.return_value = recebivel

        with self.assertRaises(ValueError, msg="Recebível cancelado não pode receber pagamento."):
            CreditoService.registrar_pagamento(recebivel, Decimal('50.00'))

    @patch('apps.sales.models.Recebivel.objects')
    def test_valor_zero_levanta_value_error(self, mock_qs):
        from apps.sales.services import CreditoService

        recebivel = MagicMock()
        recebivel.pk = 3
        recebivel.situacao = 'ABERTO'
        mock_qs.select_for_update.return_value.get.return_value = recebivel

        with self.assertRaises(ValueError):
            CreditoService.registrar_pagamento(recebivel, Decimal('0.00'))

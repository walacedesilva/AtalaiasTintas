"""Unit tests for DescontoService — T018 / US004.

Covers:
  - Automatic approval for ≤5%
  - PIN required for 5%–20% (gerente) and >20% (diretor)
  - PIN verification: correct → approval, wrong → DescontoPINError
  - 3 wrong attempts → DescontoCooldownError
  - aplicar_desconto_item recalculates pedido totals
"""
from __future__ import annotations

from decimal import Decimal
from unittest.mock import MagicMock, patch

from django.test import TestCase


def _make_pedido(subtotal: Decimal = Decimal('100.00')):
    """Return a mock PedidoVenda-like object."""
    pedido = MagicMock()
    pedido.pk = 'test-pedido-pk'
    pedido.valor_subtotal = subtotal
    pedido.valor_desconto = Decimal('0.00')
    pedido.percentual_desconto = Decimal('0.00')
    pedido.valor_total = subtotal
    pedido.desconto_aprovador = None
    pedido.desconto_motivo = None
    pedido.desconto_aprovado_em = None
    pedido.save = MagicMock()
    return pedido


def _make_user(is_superuser: bool = False, grupos: list[str] | None = None, password_ok: bool = True):
    """Return a mock User-like object."""
    user = MagicMock()
    user.pk = 1
    user.is_superuser = is_superuser
    user.check_password = MagicMock(return_value=password_ok)
    grupos = grupos or []
    user.groups.values_list.return_value = grupos
    return user


class DescontoValidarTests(TestCase):
    """T009 — validar_desconto (no DB needed, pure logic)."""

    def setUp(self):
        from apps.sales.services import _pin_attempts
        _pin_attempts.clear()

    def test_5_porcento_aprovado_automaticamente(self):
        from apps.sales.services import DescontoService
        pedido = _make_pedido()
        resultado = DescontoService.validar_desconto(pedido, Decimal('5.00'), _make_user())
        self.assertTrue(resultado['aprovado'])
        self.assertFalse(resultado['requer_pin'])
        self.assertIsNone(resultado['nivel'])

    def test_4_porcento_aprovado_automaticamente(self):
        from apps.sales.services import DescontoService
        resultado = DescontoService.validar_desconto(_make_pedido(), Decimal('4.99'), _make_user())
        self.assertTrue(resultado['aprovado'])

    def test_6_porcento_requer_gerente(self):
        from apps.sales.services import DescontoService
        resultado = DescontoService.validar_desconto(_make_pedido(), Decimal('6.00'), _make_user())
        self.assertFalse(resultado['aprovado'])
        self.assertTrue(resultado['requer_pin'])
        self.assertEqual(resultado['nivel'], 'gerente')

    def test_20_porcento_requer_gerente(self):
        from apps.sales.services import DescontoService
        resultado = DescontoService.validar_desconto(_make_pedido(), Decimal('20.00'), _make_user())
        self.assertEqual(resultado['nivel'], 'gerente')

    def test_21_porcento_requer_diretor(self):
        from apps.sales.services import DescontoService
        resultado = DescontoService.validar_desconto(_make_pedido(), Decimal('21.00'), _make_user())
        self.assertEqual(resultado['nivel'], 'diretor')

    def test_100_porcento_requer_diretor(self):
        from apps.sales.services import DescontoService
        resultado = DescontoService.validar_desconto(_make_pedido(), Decimal('100.00'), _make_user())
        self.assertEqual(resultado['nivel'], 'diretor')


class DescontoAprovarComPinTests(TestCase):
    """T010 — aprovar_com_pin."""

    def setUp(self):
        from apps.sales.services import _pin_attempts
        _pin_attempts.clear()

    @patch('apps.sales.services.DescontoAuditLog', autospec=True)
    def test_5_porcento_aprovado_sem_pin(self, mock_log):
        """≤5% should be approved directly without PIN check."""
        from apps.sales.services import DescontoService

        pedido = _make_pedido(Decimal('200.00'))
        solicitante = _make_user()
        mock_log.objects = MagicMock()
        mock_log.objects.create = MagicMock()

        with patch('apps.sales.services.DescontoService._aplicar_desconto_total') as mock_apply:
            mock_apply.return_value = pedido
            DescontoService.aprovar_com_pin(pedido, Decimal('5.00'), 'Promoção', '9999', solicitante)
            mock_apply.assert_called_once()
            # check_password must NOT be called for auto-approval
            solicitante.check_password.assert_not_called()

    @patch('apps.sales.services.DescontoAuditLog', autospec=True)
    def test_pin_correto_aplica_desconto_gerente(self, mock_log):
        """Correct PIN from gerente should apply the discount."""
        from apps.sales.services import DescontoService

        pedido = _make_pedido(Decimal('200.00'))
        aprovador = _make_user(grupos=['gerente'], password_ok=True)
        mock_log.objects = MagicMock()
        mock_log.objects.create = MagicMock()

        with patch('apps.sales.services.DescontoService._aplicar_desconto_total') as mock_apply:
            mock_apply.return_value = pedido
            DescontoService.aprovar_com_pin(pedido, Decimal('10.00'), 'Black Friday', '1234', aprovador)
            mock_apply.assert_called_once()
            aprovador.check_password.assert_called_once_with('1234')

    def test_pin_errado_levanta_DescontoPINError(self):
        """Wrong PIN should raise DescontoPINError with attempt count."""
        from apps.sales.services import DescontoService, DescontoPINError

        pedido = _make_pedido()
        aprovador = _make_user(grupos=['gerente'], password_ok=False)

        with self.assertRaises(DescontoPINError) as ctx:
            DescontoService.aprovar_com_pin(pedido, Decimal('10.00'), 'Desconto', 'errado', aprovador)

        self.assertEqual(ctx.exception.tentativas, 1)

    def test_tres_tentativas_erradas_cooldown(self):
        """Three wrong PIN attempts should trigger DescontoCooldownError on the 3rd."""
        from apps.sales.services import DescontoService, DescontoPINError, DescontoCooldownError

        pedido = _make_pedido()
        aprovador = _make_user(grupos=['gerente'], password_ok=False)

        for i in range(2):
            with self.assertRaises(DescontoPINError):
                DescontoService.aprovar_com_pin(pedido, Decimal('10.00'), 'x', 'ruim', aprovador)

        with self.assertRaises(DescontoCooldownError):
            DescontoService.aprovar_com_pin(pedido, Decimal('10.00'), 'x', 'ruim', aprovador)

    def test_aprovador_sem_grupo_levanta_permissao_error(self):
        """Approver without gerente/diretor group should raise DescontoInsuficientePermissaoError."""
        from apps.sales.services import DescontoService, DescontoInsuficientePermissaoError

        pedido = _make_pedido()
        aprovador = _make_user(grupos=[], is_superuser=False, password_ok=True)

        with self.assertRaises(DescontoInsuficientePermissaoError):
            DescontoService.aprovar_com_pin(pedido, Decimal('15.00'), 'x', '1234', aprovador)

    def test_desconto_20_requer_diretor_gerente_nao_basta(self):
        """21% discount should require diretor, not just gerente."""
        from apps.sales.services import DescontoService, DescontoInsuficientePermissaoError

        pedido = _make_pedido()
        gerente = _make_user(grupos=['gerente'], password_ok=True)

        with self.assertRaises(DescontoInsuficientePermissaoError):
            DescontoService.aprovar_com_pin(pedido, Decimal('21.00'), 'x', '1234', gerente)

    def test_cooldown_bloqueio_apos_tres_tentativas(self):
        """4th call (after 3 failures) should immediately raise DescontoCooldownError."""
        from apps.sales.services import DescontoService, DescontoPINError, DescontoCooldownError, _pin_attempts

        pedido = _make_pedido()
        aprovador = _make_user(grupos=['gerente'], password_ok=False)

        # Reset attempts to 3 directly (simulates already exhausted)
        chave = f"desconto_pin_{pedido.pk}_{aprovador.pk}"
        _pin_attempts[chave] = 3

        with self.assertRaises(DescontoCooldownError):
            DescontoService.aprovar_com_pin(pedido, Decimal('10.00'), 'x', 'ruim', aprovador)


class DescontoAplicarItemTests(TestCase):
    """T011 — aplicar_desconto_item recalculates pedido totals."""

    def setUp(self):
        from apps.sales.services import _pin_attempts
        _pin_attempts.clear()

    @patch('apps.sales.services.DescontoService._recalcular_totais_pedido')
    @patch('apps.sales.services.DescontoAuditLog', autospec=True)
    def test_desconto_ate_5_aplicado_sem_pin(self, mock_log, mock_recalc):
        """≤5% item discount should be applied without PIN and trigger total recalc."""
        from apps.sales.services import DescontoService

        mock_log.objects = MagicMock()
        mock_log.objects.create = MagicMock()

        item = MagicMock()
        item.pedido.pk = 'pedido-1'
        item.preco_unitario = Decimal('50.00')
        item.quantidade = Decimal('2.00')
        item.preco_total = Decimal('100.00')
        item.desconto_percentual = Decimal('0.00')
        item.desconto_valor = Decimal('0.00')
        item.save = MagicMock()

        solicitante = _make_user()

        DescontoService.aplicar_desconto_item(item, Decimal('5.00'), solicitante)

        # preco_total must decrease
        self.assertLess(item.preco_total, Decimal('100.00'))
        # recalc must be called
        mock_recalc.assert_called_once_with(item.pedido)
        # audit log created
        mock_log.objects.create.assert_called_once()

    @patch('apps.sales.services.DescontoService._recalcular_totais_pedido')
    @patch('apps.sales.services.DescontoAuditLog', autospec=True)
    def test_desconto_acima_5_com_pin_correto(self, mock_log, mock_recalc):
        """Item discount > 5% with correct PIN and gerente aprovador is applied."""
        from apps.sales.services import DescontoService

        mock_log.objects = MagicMock()
        mock_log.objects.create = MagicMock()

        item = MagicMock()
        item.pedido.pk = 'pedido-2'
        item.preco_unitario = Decimal('100.00')
        item.quantidade = Decimal('1.00')
        item.preco_total = Decimal('100.00')
        item.desconto_percentual = Decimal('0.00')
        item.desconto_valor = Decimal('0.00')
        item.save = MagicMock()

        solicitante = _make_user()
        aprovador = _make_user(grupos=['gerente'], password_ok=True)

        DescontoService.aplicar_desconto_item(item, Decimal('10.00'), solicitante, aprovador, pin='1234')
        self.assertLess(item.preco_total, Decimal('100.00'))
        mock_recalc.assert_called_once()

    def test_desconto_acima_5_sem_aprovador_levanta_erro(self):
        """Item discount > 5% without aprovador must raise DescontoInsuficientePermissaoError."""
        from apps.sales.services import DescontoService, DescontoInsuficientePermissaoError

        item = MagicMock()
        item.pedido.pk = 'pedido-3'

        with self.assertRaises(DescontoInsuficientePermissaoError):
            DescontoService.aplicar_desconto_item(item, Decimal('10.00'), _make_user())

    @patch('apps.sales.services.DescontoAuditLog', autospec=True)
    def test_audit_log_tipo_item(self, mock_log):
        """Audit log created with tipo_desconto='ITEM' and FK to item."""
        from apps.sales.services import DescontoService

        mock_log.objects = MagicMock()
        create_mock = MagicMock()
        mock_log.objects.create = create_mock

        item = MagicMock()
        item.pedido.pk = 'pedido-4'
        item.preco_unitario = Decimal('50.00')
        item.quantidade = Decimal('1.00')
        item.preco_total = Decimal('50.00')
        item.desconto_percentual = Decimal('0.00')
        item.desconto_valor = Decimal('0.00')
        item.save = MagicMock()

        with patch('apps.sales.services.DescontoService._recalcular_totais_pedido'):
            DescontoService.aplicar_desconto_item(item, Decimal('3.00'), _make_user())

        call_kwargs = create_mock.call_args[1]
        self.assertEqual(call_kwargs['tipo_desconto'], 'ITEM')
        self.assertEqual(call_kwargs['item'], item)

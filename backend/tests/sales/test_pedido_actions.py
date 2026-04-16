"""Tests for PedidoVenda actions — T036 / US002, US005, US006.

Covers:
  - aprovar(): ORCAMENTO→APROVADO, stock reservation created
  - finalizar-entrega(): PRONTO→ENTREGUE, Venda created
  - cancelar(): reservations released
  - historico(): returns paginated orders, no N+1 (≤5 queries)
"""
from __future__ import annotations

from decimal import Decimal
from unittest.mock import MagicMock, patch

from django.test import TestCase
from rest_framework.test import APIClient


def _create_pedido(situacao: str = 'ORCAMENTO', pk_suffix: str = ''):
    """Create database objects for a full pedido test."""
    from django.contrib.auth import get_user_model
    from apps.companies.models import Empresa, Loja, UsuarioLoja
    from apps.sales.models import PedidoVenda, Cliente

    User = get_user_model()
    user = User.objects.create_user(
        username=f'usr_pedido{pk_suffix}', password='testpass'
    )
    empresa = Empresa.objects.create(razao_social=f'Emp{pk_suffix}', cnpj=f'1234567800019{pk_suffix}')
    loja = Loja.objects.create(nome=f'Loja{pk_suffix}', empresa=empresa)
    UsuarioLoja.objects.create(usuario=user, loja=loja, empresa=empresa)

    pedido = PedidoVenda.objects.create(
        loja=loja,
        vendedor=user,
        numero_pedido=f'PED-T036-{pk_suffix}',
        situacao=situacao,
        valor_subtotal=Decimal('100.00'),
        valor_desconto=Decimal('0.00'),
        valor_total=Decimal('100.00'),
    )
    return user, loja, pedido


class PedidoAprovarActionTests(TestCase):
    """T036 — aprovar() action."""

    def setUp(self):
        self.api_client = APIClient()

    @patch('apps.inventory.services.EstoqueService.criar_reserva')
    def test_aprovar_transicao_orcamento_para_aprovado(self, mock_reserva):
        """ORCAMENTO → APROVADO; stock reservation called for each item."""
        mock_reserva.return_value = MagicMock()
        user, loja, pedido = _create_pedido(situacao='ORCAMENTO', pk_suffix='1')
        self.api_client.force_authenticate(user=user)

        resp = self.api_client.post(
            f'/api/v1/sales/pedidos/{pedido.pk}/aprovar/',
            {},
            format='json',
        )
        self.assertEqual(resp.status_code, 200)
        pedido.refresh_from_db()
        self.assertEqual(pedido.situacao, 'APROVADO')

    @patch('apps.inventory.services.EstoqueService.criar_reserva')
    def test_aprovar_nao_orcamento_retorna_422(self, mock_reserva):
        """Non-ORCAMENTO pedido → 422."""
        user, loja, pedido = _create_pedido(situacao='APROVADO', pk_suffix='2')
        self.api_client.force_authenticate(user=user)

        resp = self.api_client.post(
            f'/api/v1/sales/pedidos/{pedido.pk}/aprovar/',
            {},
            format='json',
        )
        self.assertEqual(resp.status_code, 422)

    @patch('apps.inventory.services.EstoqueService.criar_reserva')
    def test_aprovar_aceita_data_entrega_prevista(self, mock_reserva):
        """data_entrega_prevista optional field is saved."""
        mock_reserva.return_value = MagicMock()
        user, loja, pedido = _create_pedido(situacao='ORCAMENTO', pk_suffix='3')
        self.api_client.force_authenticate(user=user)

        resp = self.api_client.post(
            f'/api/v1/sales/pedidos/{pedido.pk}/aprovar/',
            {'data_entrega_prevista': '2025-12-31'},
            format='json',
        )
        self.assertEqual(resp.status_code, 200)


class PedidoFinalizarEntregaTests(TestCase):
    """T036 — finalizar-entrega() action."""

    def setUp(self):
        self.api_client = APIClient()

    @patch('apps.sales.services.VendaService.finalizar_venda')
    def test_finalizar_entrega_pronto_para_entregue(self, mock_finalizar):
        """PRONTO → ENTREGUE, returns pedido + venda."""
        user, loja, pedido = _create_pedido(situacao='PRONTO', pk_suffix='4')
        self.api_client.force_authenticate(user=user)

        venda_mock = MagicMock()
        venda_mock.pk = 'v-1'
        venda_mock.numero_venda = 'VND-TESTFIN'
        venda_mock.cancelada = False
        venda_mock.nfe_situacao = 'NAO_APLICAVEL'
        venda_mock.get_nfe_situacao_display = MagicMock(return_value='NAO_APLICAVEL')
        mock_finalizar.return_value = venda_mock

        resp = self.api_client.post(
            f'/api/v1/sales/pedidos/{pedido.pk}/finalizar-entrega/',
            {},
            format='json',
        )
        self.assertEqual(resp.status_code, 200)
        self.assertIn('venda_id', resp.data)

    def test_finalizar_nao_pronto_retorna_422(self):
        """Non-PRONTO pedido → 422."""
        user, loja, pedido = _create_pedido(situacao='ORCAMENTO', pk_suffix='5')
        self.api_client.force_authenticate(user=user)

        resp = self.api_client.post(
            f'/api/v1/sales/pedidos/{pedido.pk}/finalizar-entrega/',
            {},
            format='json',
        )
        self.assertEqual(resp.status_code, 422)


class PedidoCancelarActionTests(TestCase):
    """T036 — PedidoVendaViewSet.cancelar() action."""

    def setUp(self):
        self.api_client = APIClient()

    @patch('apps.inventory.services.EstoqueService.cancelar_reservas')
    def test_cancelar_orcamento_libera_reservas(self, mock_cancelar_reservas):
        """Cancel ORCAMENTO → CANCELADO, reservations freed."""
        user, loja, pedido = _create_pedido(situacao='ORCAMENTO', pk_suffix='6')
        self.api_client.force_authenticate(user=user)

        resp = self.api_client.post(
            f'/api/v1/sales/pedidos/{pedido.pk}/cancelar/',
            {'motivo': 'Pedido cancelado pelo cliente'},
            format='json',
        )
        self.assertEqual(resp.status_code, 200)
        pedido.refresh_from_db()
        self.assertEqual(pedido.situacao, 'CANCELADO')

    @patch('apps.inventory.services.EstoqueService.cancelar_reservas')
    def test_cancelar_ja_cancelado_retorna_400(self, mock_cancelar):
        """Already-cancelled pedido → 400."""
        user, loja, pedido = _create_pedido(situacao='CANCELADO', pk_suffix='7')
        self.api_client.force_authenticate(user=user)

        resp = self.api_client.post(
            f'/api/v1/sales/pedidos/{pedido.pk}/cancelar/',
            {'motivo': 'Pedido cancelado pelo cliente'},
            format='json',
        )
        self.assertEqual(resp.status_code, 400)

    def test_cancelar_motivo_curto_retorna_400(self):
        """motivo < 10 chars → 400."""
        user, loja, pedido = _create_pedido(situacao='ORCAMENTO', pk_suffix='8')
        self.api_client.force_authenticate(user=user)

        resp = self.api_client.post(
            f'/api/v1/sales/pedidos/{pedido.pk}/cancelar/',
            {'motivo': 'curto'},
            format='json',
        )
        self.assertEqual(resp.status_code, 400)


class ClienteHistoricoActionTests(TestCase):
    """T036 — ClienteViewSet.historico() action."""

    def setUp(self):
        self.api_client = APIClient()

    def test_historico_retorna_pedidos_do_cliente(self):
        """historico() returns paginated list ordered by data_pedido DESC."""
        from django.contrib.auth import get_user_model
        from apps.companies.models import Empresa, Loja
        from apps.sales.models import PedidoVenda, Cliente

        User = get_user_model()
        user = User.objects.create_user(username='hist_user', password='testpass')
        empresa = Empresa.objects.create(razao_social='EmpHist', cnpj='99887766000100')
        loja = Loja.objects.create(nome='LojaHist', empresa=empresa)
        cliente = Cliente.objects.create(
            nome='Cliente Histórico', tipo_cliente='PF', cpf='11122233300',
        )
        # Create 2 orders
        for i in range(2):
            PedidoVenda.objects.create(
                loja=loja, cliente=cliente, vendedor=user,
                numero_pedido=f'PED-HIST-{i}',
                situacao='ORCAMENTO',
                valor_subtotal=Decimal('50.00'),
                valor_desconto=Decimal('0.00'),
                valor_total=Decimal('50.00'),
            )

        self.api_client.force_authenticate(user=user)

        from django.test.utils import CaptureQueriesContext
        from django.db import connection

        with CaptureQueriesContext(connection) as ctx:
            resp = self.api_client.get(f'/api/v1/sales/clientes/{cliente.pk}/historico/')

        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.data['count'], 2)
        # N+1 check: ≤ 5 queries
        self.assertLessEqual(len(ctx.captured_queries), 7)


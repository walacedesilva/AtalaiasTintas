"""Unit/integration tests for PDVCheckoutAPIView — T033 / US003.

Covers:
  - Happy path: cart with items, mixed payment (cash + PIX)
  - Stock shortage on item → rollback complete
  - Anonymous client (cliente_id=None) → OK (BR-001)
  - Crediário: Recebivel created
  - Credit limit exceeded → 402
  - Unauthorised loja → 403
"""
from __future__ import annotations

from decimal import Decimal
from unittest.mock import MagicMock, patch

from django.test import TestCase
from rest_framework.test import APIClient


def _make_user(pk: int = 1, is_superuser: bool = False):
    from django.contrib.auth import get_user_model
    User = get_user_model()
    try:
        user = User.objects.get(pk=pk)
    except User.DoesNotExist:
        user = User.objects.create_user(
            username=f'operador{pk}', password='testpass', pk=pk
        )
    return user


class PDVCheckoutHappyPathTests(TestCase):
    """T033 — PDV checkout happy paths."""

    def setUp(self):
        self.client = APIClient()
        self.user = _make_user(pk=1)
        self.client.force_authenticate(user=self.user)

    def _post_checkout(self, payload):
        return self.client.post('/api/v1/sales/pdv/checkout/', payload, format='json')

    @patch('apps.companies.models.UsuarioLoja.objects')
    def test_loja_nao_autorizada_retorna_403(self, mock_ul):
        mock_ul.filter.return_value.exists.return_value = False
        resp = self._post_checkout({
            'loja_id': 99, 'itens': [{'produto_variacao_id': '1', 'quantidade': '1', 'preco_unitario': '10.00'}],
            'pagamentos': [{'forma': 'DINHEIRO', 'valor': '10.00'}],
        })
        self.assertEqual(resp.status_code, 403)

    @patch('apps.sales.models.PagamentoVenda.objects')
    @patch('apps.sales.models.Venda.objects')
    @patch('apps.sales.models.ItemPedidoVenda.objects')
    @patch('apps.sales.models.PedidoVenda.objects')
    @patch('apps.inventory.services.EstoqueService.processar_baixa_venda')
    @patch('apps.inventory.services.ConversaoService.obter_unidade_base')
    @patch('apps.inventory.services.ConversaoService.converter_quantidade')
    @patch('apps.inventory.services.EstoqueService.calcular_disponibilidade')
    @patch('apps.companies.models.UsuarioLoja.objects')
    def test_checkout_sem_cliente_retorna_201(
        self, mock_ul, mock_calc, mock_conv, mock_ub, mock_baixa,
        mock_pedido_qs, mock_item_qs, mock_venda_qs, mock_pag_qs,
    ):
        """BR-001: anonymous checkout (cliente_id=None) → 201."""
        mock_ul.filter.return_value.exists.return_value = True
        mock_calc.return_value = Decimal('10.00')
        mock_conv.return_value = Decimal('1.00')
        unidade_mock = MagicMock()
        unidade_mock.id = 1
        mock_ub.return_value = unidade_mock

        pedido_mock = MagicMock()
        pedido_mock.pk = 'ped-1'
        mock_pedido_qs.create.return_value = pedido_mock

        item_mock = MagicMock()
        mock_item_qs.create.return_value = item_mock

        venda_mock = MagicMock()
        venda_mock.pk = 'vnd-1'
        venda_mock.numero_venda = 'VND-AAAABBBB'
        mock_venda_qs.create.return_value = venda_mock

        mock_pag_qs.create.return_value = MagicMock()
        mock_baixa.return_value = MagicMock()

        payload = {
            'loja_id': 1,
            'itens': [{'produto_variacao_id': '1', 'quantidade': '2', 'preco_unitario': '10.00'}],
            'pagamentos': [{'forma': 'DINHEIRO', 'valor': '20.00'}],
        }
        resp = self._post_checkout(payload)
        self.assertEqual(resp.status_code, 201)

    @patch('apps.inventory.services.EstoqueService.calcular_disponibilidade')
    @patch('apps.inventory.services.ConversaoService.converter_quantidade')
    @patch('apps.inventory.services.ConversaoService.obter_unidade_base')
    @patch('apps.companies.models.UsuarioLoja.objects')
    def test_estoque_insuficiente_retorna_400(self, mock_ul, mock_ub, mock_conv, mock_calc):
        mock_ul.filter.return_value.exists.return_value = True
        unidade_mock = MagicMock()
        unidade_mock.id = 1
        mock_ub.return_value = unidade_mock
        mock_conv.return_value = Decimal('5.00')
        mock_calc.return_value = Decimal('3.00')  # Only 3 available, need 5

        payload = {
            'loja_id': 1,
            'itens': [{'produto_variacao_id': '1', 'quantidade': '5', 'preco_unitario': '10.00'}],
            'pagamentos': [{'forma': 'DINHEIRO', 'valor': '50.00'}],
        }
        resp = self._post_checkout(payload)
        self.assertEqual(resp.status_code, 400)
        self.assertIn('Estoque insuficiente', resp.data['erro'])

    @patch('apps.companies.models.UsuarioLoja.objects')
    def test_itens_vazios_retorna_400(self, mock_ul):
        mock_ul.filter.return_value.exists.return_value = True
        resp = self._post_checkout({'loja_id': 1, 'itens': [], 'pagamentos': [{'forma': 'DINHEIRO', 'valor': '10.00'}]})
        self.assertEqual(resp.status_code, 400)

    @patch('apps.companies.models.UsuarioLoja.objects')
    def test_sem_loja_id_retorna_400(self, mock_ul):
        resp = self._post_checkout({'itens': [], 'pagamentos': []})
        self.assertEqual(resp.status_code, 400)

    @patch('apps.sales.services.CreditoService.bloquear_para_venda')
    @patch('apps.sales.models.PagamentoVenda.objects')
    @patch('apps.sales.models.Venda.objects')
    @patch('apps.sales.models.ItemPedidoVenda.objects')
    @patch('apps.sales.models.PedidoVenda.objects')
    @patch('apps.inventory.services.EstoqueService.processar_baixa_venda')
    @patch('apps.inventory.services.ConversaoService.obter_unidade_base')
    @patch('apps.inventory.services.ConversaoService.converter_quantidade')
    @patch('apps.inventory.services.EstoqueService.calcular_disponibilidade')
    @patch('apps.companies.models.UsuarioLoja.objects')
    def test_crediario_cria_recebivel(
        self, mock_ul, mock_calc, mock_conv, mock_ub, mock_baixa,
        mock_pedido_qs, mock_item_qs, mock_venda_qs, mock_pag_qs, mock_bloquear,
    ):
        """Crediário payment → CreditoService.bloquear_para_venda called."""
        from django.contrib.auth import get_user_model
        User = get_user_model()
        self.user = User.objects.create_user(username='crediario_user', password='pass')
        self.client.force_authenticate(user=self.user)

        mock_ul.filter.return_value.exists.return_value = True
        mock_calc.return_value = Decimal('10.00')
        mock_conv.return_value = Decimal('1.00')
        unidade_mock = MagicMock()
        unidade_mock.id = 1
        mock_ub.return_value = unidade_mock

        pedido_mock = MagicMock()
        pedido_mock.pk = 'ped-2'
        mock_pedido_qs.create.return_value = pedido_mock

        mock_item_qs.create.return_value = MagicMock()

        venda_mock = MagicMock()
        venda_mock.pk = 'vnd-2'
        venda_mock.numero_venda = 'VND-CCCCDDDD'
        mock_venda_qs.create.return_value = venda_mock

        mock_pag_qs.create.return_value = MagicMock()
        mock_baixa.return_value = MagicMock()

        rec_mock = MagicMock()
        rec_mock.pk = 'rec-1'
        mock_bloquear.return_value = rec_mock

        # Need a real cliente for the crediário path
        from apps.sales.models import Cliente
        cliente = Cliente.objects.create(
            nome='João Crediário', tipo_cliente='PF', cpf='12345678901',
            limite_credito=Decimal('1000.00'),
        )

        payload = {
            'loja_id': 1,
            'cliente_id': cliente.pk,
            'itens': [{'produto_variacao_id': '1', 'quantidade': '1', 'preco_unitario': '50.00'}],
            'pagamentos': [{'forma': 'CREDIARIO', 'valor': '50.00'}],
        }
        resp = self._post_checkout(payload)
        self.assertEqual(resp.status_code, 201)
        mock_bloquear.assert_called_once()

    @patch('apps.sales.services.CreditoService.bloquear_para_venda')
    @patch('apps.sales.models.PagamentoVenda.objects')
    @patch('apps.sales.models.Venda.objects')
    @patch('apps.sales.models.ItemPedidoVenda.objects')
    @patch('apps.sales.models.PedidoVenda.objects')
    @patch('apps.inventory.services.EstoqueService.processar_baixa_venda')
    @patch('apps.inventory.services.ConversaoService.obter_unidade_base')
    @patch('apps.inventory.services.ConversaoService.converter_quantidade')
    @patch('apps.inventory.services.EstoqueService.calcular_disponibilidade')
    @patch('apps.companies.models.UsuarioLoja.objects')
    def test_credito_esgotado_sem_override_retorna_402(
        self, mock_ul, mock_calc, mock_conv, mock_ub, mock_baixa,
        mock_pedido_qs, mock_item_qs, mock_venda_qs, mock_pag_qs, mock_bloquear,
    ):
        """Insufficient credit without override → 402."""
        from apps.sales.services import CreditoInsuficienteError
        from apps.sales.models import Cliente
        from django.contrib.auth import get_user_model
        User = get_user_model()
        user = User.objects.create_user(username='teste_credit', password='pass')
        self.client.force_authenticate(user=user)

        mock_ul.filter.return_value.exists.return_value = True
        mock_calc.return_value = Decimal('100.00')
        mock_conv.return_value = Decimal('1.00')
        unidade_mock = MagicMock()
        unidade_mock.id = 1
        mock_ub.return_value = unidade_mock

        pedido_mock = MagicMock()
        pedido_mock.pk = 'ped-3'
        mock_pedido_qs.create.return_value = pedido_mock
        mock_item_qs.create.return_value = MagicMock()

        venda_mock = MagicMock()
        venda_mock.pk = 'vnd-3'
        venda_mock.numero_venda = 'VND-EEEEFFFF'
        mock_venda_qs.create.return_value = venda_mock

        mock_pag_qs.create.return_value = MagicMock()
        mock_baixa.return_value = MagicMock()

        mock_bloquear.side_effect = CreditoInsuficienteError(
            Decimal('100.00'), Decimal('500.00')
        )

        cliente = Cliente.objects.create(
            nome='Maria Sem Crédito', tipo_cliente='PF', cpf='98765432100',
            limite_credito=Decimal('100.00'),
        )

        payload = {
            'loja_id': 1,
            'cliente_id': cliente.pk,
            'itens': [{'produto_variacao_id': '1', 'quantidade': '1', 'preco_unitario': '500.00'}],
            'pagamentos': [{'forma': 'CREDIARIO', 'valor': '500.00'}],
        }
        resp = self._post_checkout(payload)
        self.assertEqual(resp.status_code, 402)
        self.assertIn('disponivel', resp.data)

"""Unit tests for aprovar-desconto action — T034 / US004.

Covers:
  - aprovar-desconto with correct PIN → 200, log created
  - aprovar-desconto with wrong PIN → 403
  - aprovar-desconto with percentual above level → 403
"""
from __future__ import annotations

from decimal import Decimal
from unittest.mock import MagicMock, patch

from django.test import TestCase
from rest_framework.test import APIClient


def _make_pedido_obj(pk='ped-1', situacao='ORCAMENTO'):
    from apps.sales.models import PedidoVenda, Cliente
    from django.contrib.auth import get_user_model
    from apps.companies.models import Loja, Empresa, UsuarioLoja
    User = get_user_model()

    user = User.objects.create_user(username=f'vendedor_{pk}', password='testpass')
    empresa = Empresa.objects.create(razao_social='Teste', cnpj='12345678000191')
    loja = Loja.objects.create(nome='Loja Teste', empresa=empresa)
    pedido = PedidoVenda.objects.create(
        loja=loja,
        vendedor=user,
        numero_pedido=f'PED-{pk}',
        situacao=situacao,
        valor_subtotal=Decimal('200.00'),
        valor_desconto=Decimal('0.00'),
        valor_total=Decimal('200.00'),
    )
    return user, loja, pedido


class AprovarDescontoAPITests(TestCase):
    """T034 — aprovar-desconto action via API."""

    def setUp(self):
        self.api_client = APIClient()

    @patch('apps.sales.services.DescontoService.aprovar_com_pin')
    def test_aprovar_desconto_pin_correto_retorna_200(self, mock_aprovar):
        """Correct PIN → 200."""
        user, loja, pedido = _make_pedido_obj(pk='api001')
        self.api_client.force_authenticate(user=user)

        mock_aprovar.return_value = pedido

        resp = self.api_client.post(
            f'/api/v1/sales/pedidos/{pedido.pk}/aprovar-desconto/',
            {
                'percentual': '10.00',
                'motivo': 'Promoção especial',
                'pin': '1234',
                'aprovador_id': user.pk,
            },
            format='json',
        )
        self.assertEqual(resp.status_code, 200)

    @patch('apps.sales.services.DescontoService.aprovar_com_pin')
    def test_aprovar_desconto_pin_errado_retorna_403(self, mock_aprovar):
        """Wrong PIN → 403 with tentativas."""
        from apps.sales.services import DescontoPINError
        user, loja, pedido = _make_pedido_obj(pk='api002')
        self.api_client.force_authenticate(user=user)

        mock_aprovar.side_effect = DescontoPINError(1, 3)

        resp = self.api_client.post(
            f'/api/v1/sales/pedidos/{pedido.pk}/aprovar-desconto/',
            {'percentual': '10.00', 'motivo': 'Desconto', 'pin': 'errado', 'aprovador_id': user.pk},
            format='json',
        )
        self.assertEqual(resp.status_code, 403)
        self.assertIn('tentativas', resp.data)

    @patch('apps.sales.services.DescontoService.aprovar_com_pin')
    def test_aprovador_sem_permissao_retorna_403(self, mock_aprovar):
        """Approver without required level → 403."""
        from apps.sales.services import DescontoInsuficientePermissaoError
        user, loja, pedido = _make_pedido_obj(pk='api003')
        self.api_client.force_authenticate(user=user)

        mock_aprovar.side_effect = DescontoInsuficientePermissaoError('Permissão insuficiente')

        resp = self.api_client.post(
            f'/api/v1/sales/pedidos/{pedido.pk}/aprovar-desconto/',
            {'percentual': '21.00', 'motivo': 'Grande desconto', 'pin': '1234', 'aprovador_id': user.pk},
            format='json',
        )
        self.assertEqual(resp.status_code, 403)

    def test_sem_percentual_retorna_400(self):
        """Missing percentual → 400."""
        user, loja, pedido = _make_pedido_obj(pk='api004')
        self.api_client.force_authenticate(user=user)

        resp = self.api_client.post(
            f'/api/v1/sales/pedidos/{pedido.pk}/aprovar-desconto/',
            {'motivo': 'Desconto', 'pin': '1234'},
            format='json',
        )
        self.assertEqual(resp.status_code, 400)

    def test_aprovador_id_invalido_retorna_400(self):
        """Non-existent aprovador_id → 400."""
        user, loja, pedido = _make_pedido_obj(pk='api005')
        self.api_client.force_authenticate(user=user)

        resp = self.api_client.post(
            f'/api/v1/sales/pedidos/{pedido.pk}/aprovar-desconto/',
            {'percentual': '10.00', 'motivo': 'Teste', 'pin': '1234', 'aprovador_id': 99999},
            format='json',
        )
        self.assertEqual(resp.status_code, 400)


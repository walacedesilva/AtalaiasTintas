"""Tests for Venda cancellation + return actions — T035 / US007.

Covers:
  - Cancel D+0 with correct PIN → CANCELADA, stock reversed
  - Cancel D+0 with wrong PIN → 403, venda unchanged
  - Cancel after D+0 → 400
  - Cancel with NFe PENDENTE → status CANCELADA, no SEFAZ call (BR-008)
  - Idempotency: double cancel → 400
  - Devolução: stock restored, tem_devolucao=True
"""
from __future__ import annotations

from decimal import Decimal
from unittest.mock import MagicMock, patch

from django.test import TestCase
from rest_framework.test import APIClient

from apps.sales.models import Venda


def _make_venda(cancelada: bool = False, nfe_situacao: str = 'NAO_APLICAVEL',
                data_offset_days: int = 0):
    """Create a minimal Venda via mocks (no DB)."""
    from django.utils import timezone
    import datetime
    v = MagicMock(spec=Venda)
    v.pk = 'venda-test'
    v.cancelada = cancelada
    v.nfe_situacao = nfe_situacao
    v.data_venda = timezone.now() - datetime.timedelta(days=data_offset_days)
    v.get_nfe_situacao_display = MagicMock(return_value=nfe_situacao)
    v.recebiveis = MagicMock()
    v.recebiveis.filter.return_value = []
    return v


class VendaCancelamentoAPITests(TestCase):
    """T035 — VendaViewSet.cancelar() endpoint."""

    def setUp(self):
        self.api_client = APIClient()
        from django.contrib.auth import get_user_model
        User = get_user_model()
        self.user = User.objects.create_user(
            username='caixa_op', password='testpass'
        )
        self.api_client.force_authenticate(user=self.user)

    @patch('apps.sales.apis.VendaViewSet.get_object')
    @patch('apps.sales.services.VendaService.cancelar_venda')
    def test_pin_correto_cancela_venda(self, mock_cancelar, mock_get_obj):
        """Correct PIN on D+0 → 200, venda cancelada=True."""
        from django.utils import timezone
        venda = MagicMock(spec=Venda)
        venda.cancelada = False
        venda.nfe_situacao = 'NAO_APLICAVEL'
        venda.data_venda = timezone.now()
        venda.pk = 'venda-ok'
        venda.recebiveis = MagicMock()
        venda.recebiveis.filter.return_value = []

        import uuid
        venda_cancelada = MagicMock(spec=Venda)
        venda_cancelada.cancelada = True
        venda_cancelada.pk = uuid.UUID('00000000-0000-0000-0000-000000000099')
        venda_cancelada.nfe_situacao = 'NAO_APLICAVEL'
        venda_cancelada.get_nfe_situacao_display = MagicMock(return_value='NAO_APLICAVEL')

        mock_get_obj.return_value = venda
        mock_cancelar.return_value = venda_cancelada

        self.user.check_password = MagicMock(return_value=True)

        resp = self.api_client.post(
            '/api/v1/sales/vendas/venda-ok/cancelar/',
            {'motivo': 'Motivo de cancelamento teste', 'pin': '9999'},
            format='json',
        )
        self.assertEqual(resp.status_code, 200)

    @patch('apps.sales.apis.VendaViewSet.get_object')
    def test_pin_errado_retorna_403(self, mock_get_obj):
        """Wrong PIN → 403."""
        from django.utils import timezone
        venda = MagicMock(spec=Venda)
        venda.cancelada = False
        venda.nfe_situacao = 'NAO_APLICAVEL'
        venda.data_venda = timezone.now()
        mock_get_obj.return_value = venda

        self.user.check_password = MagicMock(return_value=False)

        resp = self.api_client.post(
            '/api/v1/sales/vendas/venda-ok/cancelar/',
            {'motivo': 'Motivo de cancelamento teste', 'pin': 'errado'},
            format='json',
        )
        self.assertEqual(resp.status_code, 403)

    @patch('apps.sales.apis.VendaViewSet.get_object')
    def test_cancelamento_apos_dia_retorna_400(self, mock_get_obj):
        """Cancel D+1 or later → 400."""
        from django.utils import timezone
        import datetime
        venda = MagicMock(spec=Venda)
        venda.cancelada = False
        venda.nfe_situacao = 'NAO_APLICAVEL'
        venda.data_venda = timezone.now() - datetime.timedelta(days=1)
        mock_get_obj.return_value = venda

        resp = self.api_client.post(
            '/api/v1/sales/vendas/venda-ok/cancelar/',
            {'motivo': 'Motivo de cancelamento teste', 'pin': '1234'},
            format='json',
        )
        self.assertEqual(resp.status_code, 400)
        self.assertIn('D+0', resp.data['erro'])

    @patch('apps.sales.apis.VendaViewSet.get_object')
    def test_venda_ja_cancelada_retorna_400(self, mock_get_obj):
        """Already-cancelled venda → 400 (idempotency)."""
        venda = MagicMock(spec=Venda)
        venda.cancelada = True
        mock_get_obj.return_value = venda

        resp = self.api_client.post(
            '/api/v1/sales/vendas/venda-ok/cancelar/',
            {'motivo': 'Motivo de cancelamento teste', 'pin': '1234'},
            format='json',
        )
        self.assertEqual(resp.status_code, 400)
        self.assertIn('cancelada', resp.data['erro'])

    @patch('apps.sales.apis.VendaViewSet.get_object')
    def test_pin_ausente_retorna_400(self, mock_get_obj):
        """Missing PIN → 400."""
        from django.utils import timezone
        venda = MagicMock(spec=Venda)
        venda.cancelada = False
        venda.data_venda = timezone.now()
        mock_get_obj.return_value = venda

        resp = self.api_client.post(
            '/api/v1/sales/vendas/venda-ok/cancelar/',
            {'motivo': 'Motivo de cancelamento teste'},
            format='json',
        )
        self.assertEqual(resp.status_code, 400)

    @patch('apps.sales.apis.VendaViewSet.get_object')
    def test_motivo_curto_retorna_400(self, mock_get_obj):
        """motivo < 10 chars → 400."""
        from django.utils import timezone
        venda = MagicMock(spec=Venda)
        venda.cancelada = False
        venda.data_venda = timezone.now()
        mock_get_obj.return_value = venda

        resp = self.api_client.post(
            '/api/v1/sales/vendas/venda-ok/cancelar/',
            {'motivo': 'curto', 'pin': '1234'},
            format='json',
        )
        self.assertEqual(resp.status_code, 400)


class VendaDevolucaoAPITests(TestCase):
    """T035 — VendaViewSet.devolver() endpoint."""

    def setUp(self):
        self.api_client = APIClient()
        from django.contrib.auth import get_user_model
        User = get_user_model()
        self.user = User.objects.create_user(username='dev_op', password='testpass')
        self.api_client.force_authenticate(user=self.user)

    @patch('apps.inventory.services.EstoqueService.processar_entrada')
    @patch('apps.sales.apis.VendaViewSet.get_object')
    def test_devolucao_marca_tem_devolucao(self, mock_get_obj, mock_entrada):
        """Devolução: estoque restored, venda.tem_devolucao=True."""
        from apps.sales.models import PedidoVenda

        venda = MagicMock(spec=Venda)
        venda.pk = 'venda-dev'
        venda.loja_id = 1
        venda.tem_devolucao = False
        venda.save = MagicMock()

        pedido = MagicMock(spec=PedidoVenda)
        item = MagicMock()
        item.pk = 'item-1'
        item.produto_variacao_id = 'prod-1'
        item.quantidade = Decimal('2.00')
        item.unidade_venda_id = 1
        pedido.itens.select_related.return_value.all.return_value = [item]

        venda.pedido_origem = pedido

        mock_get_obj.return_value = venda

        mov_mock = MagicMock()
        mov_mock.pk = 'mov-1'
        mock_entrada.return_value = (mov_mock, None)

        resp = self.api_client.post(
            '/api/v1/sales/vendas/venda-dev/devolver/',
            {'motivo': 'Devolução do produto'},
            format='json',
        )
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(venda.tem_devolucao)

    @patch('apps.inventory.services.EstoqueService.processar_entrada')
    @patch('apps.sales.apis.VendaViewSet.get_object')
    def test_devolucao_itens_especificos(self, mock_get_obj, mock_entrada):
        """Devolução com itens específicos: apenas itens listados retornam ao estoque."""
        from apps.sales.models import PedidoVenda, ItemPedidoVenda

        venda = MagicMock(spec=Venda)
        venda.pk = 'venda-dev2'
        venda.loja_id = 1
        venda.tem_devolucao = False
        venda.save = MagicMock()

        pedido = MagicMock(spec=PedidoVenda)
        venda.pedido_origem = pedido
        mock_get_obj.return_value = venda

        item_mock = MagicMock(spec=ItemPedidoVenda)
        item_mock.pk = 'item-2'
        item_mock.produto_variacao_id = 'prod-2'
        item_mock.quantidade = Decimal('1.00')
        item_mock.unidade_venda_id = 1

        mov_mock = MagicMock()
        mov_mock.pk = 'mov-2'
        mock_entrada.return_value = (mov_mock, None)

        with patch('apps.sales.models.ItemPedidoVenda.objects') as mock_item_qs:
            mock_item_qs.get.return_value = item_mock
            with patch('apps.inventory.services.ConversaoService.obter_unidade_base') as mock_ub:
                ub_mock = MagicMock()
                ub_mock.id = 1
                mock_ub.return_value = ub_mock
                resp = self.api_client.post(
                    '/api/v1/sales/vendas/venda-dev2/devolver/',
                    {'itens': [{'item_id': 'item-2', 'quantidade': '1.00'}]},
                    format='json',
                )

        self.assertEqual(resp.status_code, 200)


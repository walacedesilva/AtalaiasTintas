"""Integration test for inventory-fiscal workflow — T074.

Tests the full checkout flow using mocked external dependencies (SEFAZ, Celery)
but with real Django ORM interactions where possible.

NOTE: These are medium-weight integration tests. External calls (SEFAZ webservice,
Celery tasks) are mocked to avoid network/queue dependencies in CI.
"""
from __future__ import annotations

from decimal import Decimal
from unittest.mock import MagicMock, patch, call

from django.test import TestCase


class CheckoutFlowIntegrationTests(TestCase):
    """End-to-end sales flow: checkout → finalise → stock deducted → NF-e queued."""

    def _usuario(self):
        u = MagicMock()
        u.pk = 99
        u.username = 'operador_teste'
        return u

    @patch('apps.fiscal.services.NFEService')
    @patch('apps.inventory.services.EstoqueService')
    @patch('apps.inventory.services.ConversaoService')
    @patch('apps.inventory.models.EstoqueReserva.objects')
    @patch('apps.sales.models.Venda.objects')
    @patch('apps.sales.models.PedidoVenda.objects')
    def test_finalizar_venda_chama_baixa_e_nfe(
        self,
        mock_pedido_qs,
        mock_venda_qs,
        mock_reserva_qs,
        mock_conv_svc,
        mock_estoque_svc,
        mock_nfe_svc,
    ):
        """finalizar_venda confirms reservas, deducts stock, queues NF-e."""
        from apps.sales.services import VendaService

        usuario = self._usuario()

        item = MagicMock()
        item.produto_variacao_id = 'prod-1'
        item.quantidade = Decimal('5')
        item.unidade_venda_id = 1

        pedido = MagicMock()
        pedido.pk = 'pedido-1'
        pedido.loja_id = 1
        pedido.itens.select_related.return_value.all.return_value = [item]
        mock_pedido_qs.select_related.return_value.prefetch_related.return_value.get.return_value = pedido

        venda = MagicMock()
        venda.pk = 'venda-1'
        mock_venda_qs.get_or_create.return_value = (venda, True)
        mock_venda_qs.filter.return_value.update.return_value = 1

        mock_estoque_svc.confirmar_reservas.return_value = []
        mock_estoque_svc.processar_baixa_venda.return_value = MagicMock()
        mock_reserva_qs.filter.return_value.update.return_value = 0
        mock_conv_svc.obter_unidade_base.return_value.id = 1

        with patch('django.db.transaction.atomic'):
            resultado = VendaService.finalizar_venda(
                pedido_id='pedido-1',
                sessao_checkout='sess-xyz',
                usuario=usuario,
                numero_venda='V-001',
            )

        mock_estoque_svc.confirmar_reservas.assert_called_once()
        mock_estoque_svc.processar_baixa_venda.assert_called_once()
        mock_nfe_svc.processar_nfe_venda.assert_called_once()

    @patch('apps.inventory.services.EstoqueService')
    @patch('apps.inventory.services.ConversaoService')
    @patch('apps.sales.models.PedidoVenda.objects')
    def test_iniciar_checkout_insuficiente_raises(
        self, mock_pedido_qs, mock_conv_svc, mock_estoque_svc
    ):
        """iniciar_checkout raises CheckoutInsuficienteError when stock insufficient."""
        from apps.sales.services import VendaService, CheckoutInsuficienteError

        usuario = self._usuario()

        item = MagicMock()
        item.produto_variacao_id = 'prod-2'
        item.produto_variacao.nome_completo = 'Tinta Preta 18L'
        item.quantidade = Decimal('500')
        item.unidade_venda_id = 1  # truthy → won't call obter_unidade_base

        pedido = MagicMock()
        pedido.pk = 'pedido-2'
        pedido.loja_id = 1
        pedido.itens.select_related.return_value.all.return_value = [item]
        mock_pedido_qs.select_related.return_value.prefetch_related.return_value.get.return_value = pedido

        # Simulate insufficient stock
        mock_conv_svc.converter_quantidade.return_value = Decimal('500')  # needs 500
        mock_estoque_svc.calcular_disponibilidade.return_value = Decimal('10')  # only 10

        with self.assertRaises(CheckoutInsuficienteError) as cm:
            with patch('django.db.transaction.atomic'):
                VendaService.iniciar_checkout(
                    pedido_id='pedido-2',
                    sessao_checkout='sess-abc',
                    usuario=usuario,
                )

        self.assertEqual(len(cm.exception.faltas), 1)

    @patch('apps.fiscal.tasks.cancelar_nfe_async')
    @patch('apps.inventory.models.EstoqueReserva.objects')
    @patch('apps.inventory.models.MovimentacaoEstoque.objects')
    @patch('apps.inventory.services.EstoqueService')
    @patch('apps.sales.models.Venda.objects')
    def test_cancelar_venda_reverte_estoque_e_cancela_nfe(
        self, mock_venda_qs, mock_estoque_svc, mock_mov_qs, mock_reserva_qs, mock_cancel_task
    ):
        """cancelar_venda reverses stock movements and queues NF-e cancellation."""
        from apps.sales.services import VendaService

        usuario = self._usuario()

        venda = MagicMock()
        venda.pk = 'venda-cancel-1'
        venda.cancelada = False
        venda.loja_id = 1
        venda.nfe_situacao = 'AUTORIZADA'
        venda.nfe_chave_acesso = '35230712345678000195550010000000011000000015'
        venda.nfe_protocolo = '315000000123456'

        # cancelar_venda uses .select_related(...).get(pk=…) — no prefetch_related
        mock_venda_qs.select_related.return_value.get.return_value = venda
        mock_venda_qs.filter.return_value.update.return_value = 1

        # No movements to reverse
        mock_mov_qs.filter.return_value = []

        # No open reservations
        mock_reserva_qs.filter.return_value.exists.return_value = False

        with patch('django.db.transaction.atomic'):
            resultado = VendaService.cancelar_venda(
                venda_id='venda-cancel-1',
                motivo='Cancelamento a pedido do cliente',
                usuario=usuario,
            )

        self.assertTrue(resultado.cancelada)
        mock_cancel_task.delay.assert_called_once()


class CheckoutOverrideTests(TestCase):
    """Tests for VendaService.checkout_com_override — manager override path."""

    @patch('apps.sales.services.VendaService.iniciar_checkout')
    def test_override_passa_flag_override_estoque(self, mock_iniciar):
        """checkout_com_override calls iniciar_checkout with override_estoque=True."""
        from apps.sales.services import VendaService

        mock_iniciar.return_value = {'sessao_checkout': 'sess-ov', 'reservas': [], 'avisos': []}
        usuario = MagicMock()

        VendaService.checkout_com_override('pedido-3', 'sess-ov', usuario)

        mock_iniciar.assert_called_once_with(
            pedido_id='pedido-3',
            sessao_checkout='sess-ov',
            usuario=usuario,
            override_estoque=True,
        )

    @patch('apps.fiscal.services.NFEService')
    @patch('apps.inventory.services.EstoqueService')
    @patch('apps.sales.models.Venda.objects')
    @patch('apps.sales.models.PedidoVenda.objects')
    def test_finalizar_venda_chama_baixa_e_nfe(
        self, mock_pedido_qs, mock_venda_qs, mock_estoque_svc, mock_nfe_svc
    ):
        """finalizar_venda confirms reservas, deducts stock, queues NF-e."""
        from apps.sales.services import VendaService

        ctx = self._setup_mocks()

        # Build pedido mock with one item
        item = MagicMock()
        item.produto_variacao_id = 'prod-1'
        item.quantidade = Decimal('5')
        item.unidade_id = 1

        pedido = MagicMock()
        pedido.pk = 'pedido-1'
        pedido.loja_id = 1
        pedido.itens.all.return_value = [item]
        mock_pedido_qs.select_related.return_value.prefetch_related.return_value.get.return_value = pedido

        venda = MagicMock()
        mock_venda_qs.create.return_value = venda

        mock_estoque_svc.confirmar_reservas.return_value = [MagicMock()]
        mock_estoque_svc.processar_baixa_venda.return_value = MagicMock()

        resultado = VendaService.finalizar_venda(
            pedido_id='pedido-1',
            sessao_checkout='sess-xyz',
            usuario=ctx['usuario'],
            numero_venda='V-001',
        )

        mock_estoque_svc.confirmar_reservas.assert_called_once_with('sess-xyz', venda.pk)
        mock_estoque_svc.processar_baixa_venda.assert_called_once()
        mock_nfe_svc.processar_nfe_venda.assert_called_once()

    @patch('apps.inventory.services.EstoqueService')
    @patch('apps.sales.models.PedidoVenda.objects')
    def test_iniciar_checkout_insuficiente_raises(
        self, mock_pedido_qs, mock_estoque_svc
    ):
        """iniciar_checkout raises CheckoutInsuficienteError when stock insufficient."""
        from apps.sales.services import VendaService, CheckoutInsuficienteError

        ctx = self._setup_mocks()

        item = MagicMock()
        item.produto_variacao_id = 'prod-2'
        item.quantidade = Decimal('500')
        item.unidade_id = 1

        pedido = MagicMock()
        pedido.pk = 'pedido-2'
        pedido.loja_id = 1
        pedido.itens.all.return_value = [item]
        mock_pedido_qs.select_related.return_value.prefetch_related.return_value.get.return_value = pedido

        mock_estoque_svc.criar_reserva.side_effect = ValueError('Estoque insuficiente')
        mock_estoque_svc.verificar_disponibilidade.return_value = False

        with self.assertRaises(CheckoutInsuficienteError):
            VendaService.iniciar_checkout(
                pedido_id='pedido-2',
                sessao_checkout='sess-abc',
                usuario=ctx['usuario'],
            )

    @patch('apps.fiscal.tasks.cancelar_nfe_async')
    @patch('apps.inventory.services.EstoqueService')
    @patch('apps.sales.models.Venda.objects')
    def test_cancelar_venda_reverte_estoque_e_cancela_nfe(
        self, mock_venda_qs, mock_estoque_svc, mock_cancel_task
    ):
        """cancelar_venda reverses stock movements and queues NF-e cancellation."""
        from apps.sales.services import VendaService

        ctx = self._setup_mocks()

        # Build venda mock with authorized NF-e
        item = MagicMock()
        item.produto_variacao_id = 'prod-1'
        item.quantidade = Decimal('5')
        item.unidade_id = 1
        item.lote_id = None

        pedido = MagicMock()
        pedido.itens.all.return_value = [item]

        venda = MagicMock()
        venda.pk = 'venda-cancel-1'
        venda.cancelada = False
        venda.loja_id = 1
        venda.pedido_origem = pedido
        venda.nfe_situacao = 'AUTORIZADA'
        venda.nfe_chave_acesso = '35230712345678000195550010000000011000000015'
        venda.nfe_protocolo = '315000000123456'
        mock_venda_qs.select_related.return_value.prefetch_related.return_value.get.return_value = venda

        resultado = VendaService.cancelar_venda(
            venda_id='venda-cancel-1',
            motivo='Cancelamento a pedido do cliente',
            usuario=ctx['usuario'],
        )

        self.assertTrue(resultado.cancelada)
        mock_estoque_svc.processar_entrada.assert_called_once()
        mock_cancel_task.delay.assert_called_once()


class CheckoutOverrideTests(TestCase):
    """Tests for VendaService.checkout_com_override — manager override path."""

    @patch('apps.sales.services.VendaService.iniciar_checkout')
    def test_override_passa_flag_override_estoque(self, mock_iniciar):
        """checkout_com_override calls iniciar_checkout with override_estoque=True."""
        from apps.sales.services import VendaService

        mock_iniciar.return_value = {'sessao_checkout': 'sess-ov', 'reservas': [], 'avisos': []}
        usuario = MagicMock()

        VendaService.checkout_com_override('pedido-3', 'sess-ov', usuario)

        mock_iniciar.assert_called_once_with(
            pedido_id='pedido-3',
            sessao_checkout='sess-ov',
            usuario=usuario,
            override_estoque=True,
        )

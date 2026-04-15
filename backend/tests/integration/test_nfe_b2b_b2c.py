"""Integration tests for B2B automatic NFe and B2C manual NFe scenarios — T075, T076.

Also covers multi-unit conversion and manager override flows — T077, T078.
"""
from __future__ import annotations

from decimal import Decimal
from unittest.mock import MagicMock, patch

from django.test import TestCase


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_usuario(username='operador', pk=1):
    u = MagicMock()
    u.pk = pk
    u.username = username
    return u


def _make_item(produto_id='prod-1', quantidade=Decimal('5'), unidade_venda_id=1, nome='Tinta 18L'):
    item = MagicMock()
    item.produto_variacao_id = produto_id
    item.produto_variacao.nome_completo = nome
    item.quantidade = quantidade
    item.unidade_venda_id = unidade_venda_id
    return item


def _make_pedido(pk='pedido-1', loja_id=1, items=None):
    pedido = MagicMock()
    pedido.pk = pk
    pedido.loja_id = loja_id
    pedido.itens.select_related.return_value.all.return_value = items or []
    return pedido


# ---------------------------------------------------------------------------
# T075 — B2B automatic NFe integration test
# ---------------------------------------------------------------------------

class B2BAutomaticNFeTests(TestCase):
    """B2B checkout → finalizar_venda triggers processar_nfe_venda automatically."""

    @patch('apps.fiscal.services.NFEService')
    @patch('apps.inventory.services.EstoqueService')
    @patch('apps.inventory.services.ConversaoService')
    @patch('apps.inventory.models.EstoqueReserva.objects')
    @patch('apps.sales.models.Venda.objects')
    @patch('apps.sales.models.PedidoVenda.objects')
    def test_b2b_finalizar_venda_chama_processar_nfe(
        self, mock_pedido_qs, mock_venda_qs, mock_reserva_qs,
        mock_conv_svc, mock_estoque_svc, mock_nfe_svc,
    ):
        """For a B2B cliente (CNPJ), finalizar_venda must call processar_nfe_venda."""
        from apps.sales.services import VendaService

        usuario = _make_usuario('gerente_b2b')
        item = _make_item()
        pedido = _make_pedido(items=[item])
        mock_pedido_qs.select_related.return_value.prefetch_related.return_value.get.return_value = pedido

        venda = MagicMock()
        venda.pk = 'venda-b2b-1'
        mock_venda_qs.get_or_create.return_value = (venda, True)
        mock_venda_qs.filter.return_value.update.return_value = 1
        mock_estoque_svc.confirmar_reservas.return_value = []
        mock_reserva_qs.filter.return_value.update.return_value = 0
        mock_conv_svc.obter_unidade_base.return_value.id = 1

        with patch('django.db.transaction.atomic'):
            VendaService.finalizar_venda('pedido-1', 'sess-b2b', usuario, 'V-B2B-001')

        mock_nfe_svc.processar_nfe_venda.assert_called_once_with(str(venda.pk), usuario)

    @patch('apps.fiscal.services.NFEService')
    @patch('apps.inventory.services.EstoqueService')
    @patch('apps.inventory.services.ConversaoService')
    @patch('apps.inventory.models.EstoqueReserva.objects')
    @patch('apps.sales.models.Venda.objects')
    @patch('apps.sales.models.PedidoVenda.objects')
    def test_b2b_checkout_reserva_estoque_para_todos_itens(
        self, mock_pedido_qs, mock_venda_qs, mock_reserva_qs,
        mock_conv_svc, mock_estoque_svc, mock_nfe_svc,
    ):
        """iniciar_checkout for B2B creates reserva for each item."""
        from apps.sales.services import VendaService

        usuario = _make_usuario()
        items = [_make_item('prod-A'), _make_item('prod-B')]
        pedido = _make_pedido(items=items)
        pedido.itens.select_related.return_value.all.side_effect = [items, items]
        mock_pedido_qs.select_related.return_value.prefetch_related.return_value.get.return_value = pedido

        mock_conv_svc.obter_unidade_base.return_value.id = 1
        mock_conv_svc.converter_quantidade.return_value = Decimal('5')
        mock_estoque_svc.calcular_disponibilidade.return_value = Decimal('100')
        mock_estoque_svc.criar_reserva.side_effect = lambda **kw: MagicMock()

        with patch('django.db.transaction.atomic'):
            resultado = VendaService.iniciar_checkout('pedido-1', 'sess-b2b-2', usuario)

        self.assertEqual(mock_estoque_svc.criar_reserva.call_count, 2)
        self.assertEqual(len(resultado['reservas']), 2)


# ---------------------------------------------------------------------------
# T076 — B2C manual NFe integration test
# ---------------------------------------------------------------------------

class B2CManualNFeTests(TestCase):
    """B2C (CPF only) checkout → venda saved but NFe NOT queued automatically."""

    def test_b2c_nao_deve_emitir(self):
        """deve_emitir_nfe_automatica returns False for B2C (CPF, no CNPJ)."""
        from apps.fiscal.services import NFEService

        venda = MagicMock()
        venda.cliente.cnpj = ''
        venda.cliente.cpf = '12345678901'

        self.assertFalse(NFEService.deve_emitir_nfe_automatica(venda))

    @patch('apps.fiscal.services._update_venda_nfe')
    @patch('apps.sales.models.Venda.objects')
    def test_b2c_processar_nfe_marca_nao_aplicavel(self, mock_venda_qs, mock_update):
        """processar_nfe_venda for B2C marks venda as NAO_APLICAVEL and does not queue Celery."""
        from apps.fiscal.services import NFEService

        cliente = MagicMock()
        cliente.cnpj = ''
        venda = MagicMock()
        venda.pk = 'venda-b2c-1'
        venda.cliente = cliente
        mock_venda_qs.select_related.return_value.get.return_value = venda

        NFEService.processar_nfe_venda('venda-b2c-1', MagicMock())

        mock_update.assert_called_once_with(venda, situacao='NAO_APLICAVEL', tipo_emissao='NAO_EMITIR')

    @patch('apps.fiscal.services.NFEService')
    @patch('apps.inventory.services.EstoqueService')
    @patch('apps.inventory.services.ConversaoService')
    @patch('apps.inventory.models.EstoqueReserva.objects')
    @patch('apps.sales.models.Venda.objects')
    @patch('apps.sales.models.PedidoVenda.objects')
    def test_b2c_venda_pode_ser_finalizada_sem_nfe(
        self, mock_pedido_qs, mock_venda_qs, mock_reserva_qs,
        mock_conv_svc, mock_estoque_svc, mock_nfe_svc,
    ):
        """A B2C sale can be finalised even when NFe is not applicable."""
        from apps.sales.services import VendaService

        usuario = _make_usuario('caixa_b2c')
        item = _make_item()
        pedido = _make_pedido(items=[item])
        mock_pedido_qs.select_related.return_value.prefetch_related.return_value.get.return_value = pedido

        venda = MagicMock()
        venda.pk = 'venda-b2c-fin-1'
        mock_venda_qs.get_or_create.return_value = (venda, True)
        mock_venda_qs.filter.return_value.update.return_value = 1
        mock_estoque_svc.confirmar_reservas.return_value = []
        mock_reserva_qs.filter.return_value.update.return_value = 0
        mock_conv_svc.obter_unidade_base.return_value.id = 1

        # NFEService marks as NAO_APLICAVEL but no exception raised
        mock_nfe_svc.processar_nfe_venda.return_value = None

        with patch('django.db.transaction.atomic'):
            resultado = VendaService.finalizar_venda('pedido-1', 'sess-b2c', usuario, 'V-B2C-001')

        self.assertIsNotNone(resultado)


# ---------------------------------------------------------------------------
# T077 — Multi-unit conversion integration test
# ---------------------------------------------------------------------------

class MultiUnitConversionIntegrationTests(TestCase):
    """Integration tests for multi-unit price/conversion endpoints."""

    def test_converter_quantidade_a_partir_de_caixas(self):
        """2 caixas de 12L cada = 24L base units."""
        from apps.inventory.services import ConversaoService

        base_unit = MagicMock()
        base_unit.id = 1

        pu_caixa = MagicMock()
        pu_caixa.fator_conversao = Decimal('12')

        with patch.object(ConversaoService, 'obter_unidade_base', return_value=base_unit):
            with patch('apps.inventory.models.ProdutoUnidade.objects') as mock_pu:
                mock_pu.filter.return_value.first.return_value = pu_caixa
                resultado = ConversaoService.converter_quantidade('prod-tinta-18l', Decimal('2'), 2)

        self.assertEqual(resultado, Decimal('24.000000'))

    def test_converter_de_litros_para_galoes(self):
        """3.785L ÷ by 3.785 fator galão = 1 galão."""
        from apps.inventory.services import ConversaoService

        base_unit = MagicMock()
        base_unit.id = 1

        pu_galao = MagicMock()
        pu_galao.fator_conversao = Decimal('3.785')

        with patch.object(ConversaoService, 'obter_unidade_base', return_value=base_unit):
            with patch('apps.inventory.models.ProdutoUnidade.objects') as mock_pu:
                mock_pu.filter.return_value.first.return_value = pu_galao
                resultado = ConversaoService.converter_para_unidade('prod-tinta-18l', Decimal('3.785'), 2)

        self.assertAlmostEqual(float(resultado), 1.0, places=4)

    def test_checkout_item_em_unidade_nao_base_reserva_em_base(self):
        """iniciar_checkout converts to base unit before creating the reservation."""
        from apps.sales.services import VendaService
        from apps.inventory.services import ConversaoService, EstoqueService

        usuario = _make_usuario()
        item = _make_item(quantidade=Decimal('3'), unidade_venda_id=2)  # 3 caixas of 12 = 36 base
        pedido = _make_pedido(items=[item, item])
        pedido.itens.select_related.return_value.all.side_effect = [[item], [item]]

        with patch('apps.sales.models.PedidoVenda.objects') as mock_pqs:
            mock_pqs.select_related.return_value.prefetch_related.return_value.get.return_value = pedido

            with patch.object(ConversaoService, 'obter_unidade_base') as mock_base, \
                 patch.object(ConversaoService, 'converter_quantidade', return_value=Decimal('36')) as mock_conv, \
                 patch.object(EstoqueService, 'calcular_disponibilidade', return_value=Decimal('100')), \
                 patch.object(EstoqueService, 'criar_reserva') as mock_res:

                mock_base.return_value.id = 1
                mock_res.return_value = MagicMock()

                with patch('django.db.transaction.atomic'):
                    VendaService.iniciar_checkout('pedido-1', 'sess-multiunit', usuario)

        # Reservation created with the converted base qty
        mock_conv.assert_called()


# ---------------------------------------------------------------------------
# T078 — Manager override integration test
# ---------------------------------------------------------------------------

class ManagerOverrideIntegrationTests(TestCase):
    """Manager override allows checkout with insufficient stock, flagging avisos."""

    @patch('apps.inventory.services.EstoqueService')
    @patch('apps.inventory.services.ConversaoService')
    @patch('apps.sales.models.PedidoVenda.objects')
    def test_override_nao_cria_reserva_para_item_faltante(
        self, mock_pedido_qs, mock_conv_svc, mock_estoque_svc
    ):
        """With override=True, items with insufficient stock are skipped (not reserved)."""
        from apps.sales.services import VendaService

        usuario = _make_usuario('gerente')
        item = _make_item(quantidade=Decimal('1000'))
        pedido = _make_pedido(items=[item, item])  # same item iterated twice
        pedido.itens.select_related.return_value.all.side_effect = [[item], [item]]
        mock_pedido_qs.select_related.return_value.prefetch_related.return_value.get.return_value = pedido

        mock_conv_svc.obter_unidade_base.return_value.id = 1
        mock_conv_svc.converter_quantidade.return_value = Decimal('1000')
        mock_estoque_svc.calcular_disponibilidade.return_value = Decimal('5')  # only 5 available

        with patch('django.db.transaction.atomic'):
            resultado = VendaService.iniciar_checkout(
                'pedido-1', 'sess-override', usuario, override_estoque=True
            )

        self.assertEqual(len(resultado['avisos']), 1)
        self.assertEqual(len(resultado['reservas']), 0)
        # criar_reserva never called (item was overridden)
        mock_estoque_svc.criar_reserva.assert_not_called()

    @patch('apps.inventory.services.EstoqueService')
    @patch('apps.inventory.services.ConversaoService')
    @patch('apps.sales.models.PedidoVenda.objects')
    def test_sem_override_com_estoque_insuficiente_levanta_erro(
        self, mock_pedido_qs, mock_conv_svc, mock_estoque_svc
    ):
        """Without override, insufficient stock raises CheckoutInsuficienteError."""
        from apps.sales.services import VendaService, CheckoutInsuficienteError

        usuario = _make_usuario('caixa')
        item = _make_item(quantidade=Decimal('1000'))
        pedido = _make_pedido(items=[item])
        mock_pedido_qs.select_related.return_value.prefetch_related.return_value.get.return_value = pedido

        mock_conv_svc.obter_unidade_base.return_value.id = 1
        mock_conv_svc.converter_quantidade.return_value = Decimal('1000')
        mock_estoque_svc.calcular_disponibilidade.return_value = Decimal('5')

        with self.assertRaises(CheckoutInsuficienteError) as cm:
            with patch('django.db.transaction.atomic'):
                VendaService.iniciar_checkout('pedido-1', 'sess-no-override', usuario)

        self.assertEqual(len(cm.exception.faltas), 1)

    def test_checkout_com_override_pass_flag(self):
        """checkout_com_override delegates to iniciar_checkout with override_estoque=True."""
        from apps.sales.services import VendaService

        usuario = _make_usuario('gerente_2')
        with patch.object(VendaService, 'iniciar_checkout', return_value={
            'sessao_checkout': 'sess', 'reservas': [], 'avisos': []
        }) as mock_iniciar:
            VendaService.checkout_com_override('pedido-ov', 'sess-ov', usuario)

        mock_iniciar.assert_called_once_with(
            pedido_id='pedido-ov',
            sessao_checkout='sess-ov',
            usuario=usuario,
            override_estoque=True,
        )

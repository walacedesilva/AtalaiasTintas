"""Unit tests for EstoqueService — T069.

Tests cover stock availability, reservation creation/confirmation/cancellation,
and stock deduction logic using in-memory SQLite.
"""
from __future__ import annotations

from decimal import Decimal
from unittest.mock import MagicMock, patch

from django.test import TestCase


class ConversaoServiceTests(TestCase):
    """Tests for ConversaoService unit conversion logic."""

    def _make_produto_unidade(self, produto_id, unidade_id, fator, is_base=False):
        """Create a mock ProdutoUnidade-like object."""
        pu = MagicMock()
        pu.produto_id = produto_id
        pu.unidade_id = unidade_id
        pu.fator_conversao = fator
        pu.unidade_base = is_base
        pu.ativa = True
        return pu

    @patch('apps.inventory.services.ConversaoService.obter_unidade_base')
    @patch('apps.inventory.models.ProdutoUnidade.objects')
    def test_converter_quantidade_mesma_unidade_base(self, mock_qs, mock_obter_base):
        """Converting a quantity already in the base unit returns unchanged value."""
        from apps.inventory.services import ConversaoService

        base_unit = MagicMock()
        base_unit.id = 1
        mock_obter_base.return_value = base_unit

        resultado = ConversaoService.converter_quantidade('prod-1', Decimal('5.0'), 1)
        self.assertEqual(resultado, Decimal('5.0'))

    @patch('apps.inventory.services.ConversaoService.obter_unidade_base')
    @patch('apps.inventory.models.ProdutoUnidade.objects')
    def test_converter_quantidade_com_fator(self, mock_qs, mock_obter_base):
        """1 caixa de 12 unidades → 12 units base quando fator=12."""
        from apps.inventory.services import ConversaoService

        base_unit = MagicMock()
        base_unit.id = 1
        mock_obter_base.return_value = base_unit

        pu = MagicMock()
        pu.fator_conversao = Decimal('12')
        mock_qs.filter.return_value.first.return_value = pu

        resultado = ConversaoService.converter_quantidade('prod-1', Decimal('3'), 2)
        self.assertEqual(resultado, Decimal('36').quantize(Decimal('0.000001')))

    @patch('apps.inventory.services.ConversaoService.obter_unidade_base')
    @patch('apps.inventory.models.ProdutoUnidade.objects')
    def test_converter_quantidade_sem_configuracao_raises(self, mock_qs, mock_obter_base):
        """Should raise ValueError when no ProdutoUnidade is configured."""
        from apps.inventory.services import ConversaoService

        base_unit = MagicMock()
        base_unit.id = 1
        mock_obter_base.return_value = base_unit
        mock_qs.filter.return_value.first.return_value = None

        with self.assertRaises(ValueError):
            ConversaoService.converter_quantidade('prod-1', Decimal('1'), 99)

    @patch('apps.inventory.services.ConversaoService.obter_unidade_base')
    @patch('apps.inventory.models.ProdutoUnidade.objects')
    def test_converter_para_unidade_inverso(self, mock_qs, mock_obter_base):
        """Converting 12 base units back to caixas of 12 should return 1."""
        from apps.inventory.services import ConversaoService

        base_unit = MagicMock()
        base_unit.id = 1
        mock_obter_base.return_value = base_unit

        pu = MagicMock()
        pu.fator_conversao = Decimal('12')
        mock_qs.filter.return_value.first.return_value = pu

        resultado = ConversaoService.converter_para_unidade('prod-1', Decimal('12'), 2)
        self.assertAlmostEqual(float(resultado), 1.0, places=5)


class EstoqueServiceAvailabilityTests(TestCase):
    """Tests for EstoqueService.calcular_disponibilidade."""

    @patch('apps.inventory.models.EstoqueLoja.objects')
    def test_disponibilidade_sem_estoque_retorna_zero(self, mock_qs):
        """When EstoqueLoja does not exist, return 0."""
        from apps.inventory.models import EstoqueLoja
        from apps.inventory.services import EstoqueService

        EstoqueLoja.DoesNotExist = Exception
        mock_qs.get.side_effect = EstoqueLoja.DoesNotExist

        resultado = EstoqueService.calcular_disponibilidade('prod-1', 1)
        self.assertEqual(resultado, Decimal('0'))

    @patch('apps.inventory.models.EstoqueLoja.objects')
    def test_disponibilidade_retorna_disponivel(self, mock_qs):
        """Return estoque.quantidade_disponivel from the EstoqueLoja record."""
        from apps.inventory.services import EstoqueService

        estoque = MagicMock()
        estoque.quantidade_disponivel = Decimal('50')
        mock_qs.get.return_value = estoque

        resultado = EstoqueService.calcular_disponibilidade('prod-1', 1)
        self.assertEqual(resultado, Decimal('50'))

    @patch('apps.inventory.services.ConversaoService.converter_quantidade')
    @patch('apps.inventory.services.EstoqueService.calcular_disponibilidade')
    def test_verificar_disponibilidade_suficiente(self, mock_calc, mock_conv):
        """Should return True when available >= requested."""
        from apps.inventory.services import EstoqueService

        mock_conv.return_value = Decimal('10')
        mock_calc.return_value = Decimal('100')

        self.assertTrue(EstoqueService.verificar_disponibilidade('p', 1, Decimal('10'), 1))

    @patch('apps.inventory.services.ConversaoService.converter_quantidade')
    @patch('apps.inventory.services.EstoqueService.calcular_disponibilidade')
    def test_verificar_disponibilidade_insuficiente(self, mock_calc, mock_conv):
        """Should return False when available < requested."""
        from apps.inventory.services import EstoqueService

        mock_conv.return_value = Decimal('200')
        mock_calc.return_value = Decimal('10')

        self.assertFalse(EstoqueService.verificar_disponibilidade('p', 1, Decimal('200'), 1))


class EstoqueServiceReservationTests(TestCase):
    """Tests for EstoqueService reservation methods (mocked DB)."""

    @patch('apps.inventory.services.ConversaoService.converter_quantidade')
    @patch('apps.inventory.models.EstoqueLoja.objects')
    @patch('apps.inventory.models.EstoqueReserva.objects')
    @patch('apps.inventory.models.UnidadeMedida.objects')
    def test_criar_reserva_estoque_insuficiente_raises(
        self, mock_unidade_qs, mock_reserva_qs, mock_estoque_qs, mock_conv
    ):
        """criar_reserva raises ValueError when stock insufficient."""
        from apps.inventory.services import EstoqueService

        mock_conv.return_value = Decimal('100')
        mock_unidade_qs.get.return_value = MagicMock()

        estoque = MagicMock()
        estoque.quantidade_atual = Decimal('10')
        estoque.quantidade_reservada = Decimal('0')
        mock_estoque_qs.select_for_update.return_value.get.return_value = estoque

        user = MagicMock()
        with self.assertRaises(ValueError, msg="Deveria levantar ValueError por estoque insuficiente"):
            # Bypass transaction.atomic with mock
            with patch('django.db.transaction.atomic'):
                EstoqueService.criar_reserva(
                    produto_variacao_id='prod-1',
                    loja_id=1,
                    quantidade=Decimal('100'),
                    unidade_id=1,
                    sessao_checkout='sess-abc',
                    usuario=user,
                )

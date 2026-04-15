"""Unit tests for ConversaoService — T070.

Covers unit conversion logic: base-unit detection, factor application,
reverse conversion, and error cases.
"""
from __future__ import annotations

from decimal import Decimal
from unittest.mock import MagicMock, patch, call

from django.test import SimpleTestCase


class ConversaoServiceObterUnidadeBaseTests(SimpleTestCase):
    """Tests for ConversaoService.obter_unidade_base."""

    @patch('apps.inventory.models.ProdutoUnidade.objects')
    def test_retorna_unidade_da_configuracao_base(self, mock_pu_qs):
        """When a ProdutoUnidade with unidade_base=True exists, return its unidade."""
        from apps.inventory.services import ConversaoService

        unidade_mock = MagicMock()
        unidade_mock.id = 5
        pu = MagicMock()
        pu.unidade = unidade_mock
        mock_pu_qs.select_related.return_value.filter.return_value.first.return_value = pu

        resultado = ConversaoService.obter_unidade_base('prod-x')
        self.assertEqual(resultado.id, 5)

    @patch('apps.inventory.models.ProdutoVariacao.objects')
    @patch('apps.inventory.models.ProdutoUnidade.objects')
    def test_fallback_para_unidade_estoque(self, mock_pu_qs, mock_pv_qs):
        """When no ProdutoUnidade is configured, fall back to ProdutoVariacao.unidade_estoque."""
        from apps.inventory.services import ConversaoService

        mock_pu_qs.select_related.return_value.filter.return_value.first.return_value = None

        unidade_estoque = MagicMock()
        unidade_estoque.id = 2
        pv = MagicMock()
        pv.unidade_estoque = unidade_estoque
        mock_pv_qs.select_related.return_value.get.return_value = pv

        resultado = ConversaoService.obter_unidade_base('prod-y')
        self.assertEqual(resultado.id, 2)


class ConversaoServiceConverterQuantidadeTests(SimpleTestCase):
    """Tests for ConversaoService.converter_quantidade."""

    @patch('apps.inventory.services.ConversaoService.obter_unidade_base')
    def test_mesma_unidade_nao_converte(self, mock_base):
        """Converting to the base unit when already in base returns unchanged value."""
        from apps.inventory.services import ConversaoService

        base = MagicMock()
        base.id = 1
        mock_base.return_value = base

        resultado = ConversaoService.converter_quantidade('p', Decimal('7.5'), 1)
        self.assertEqual(resultado, Decimal('7.5'))

    @patch('apps.inventory.models.ProdutoUnidade.objects')
    @patch('apps.inventory.services.ConversaoService.obter_unidade_base')
    def test_converte_com_fator_12(self, mock_base, mock_pu_qs):
        """3 caixas × fator 12 = 36 base units."""
        from apps.inventory.services import ConversaoService

        base = MagicMock()
        base.id = 1
        mock_base.return_value = base

        pu = MagicMock()
        pu.fator_conversao = Decimal('12')
        mock_pu_qs.filter.return_value.first.return_value = pu

        resultado = ConversaoService.converter_quantidade('p', Decimal('3'), 2)
        self.assertEqual(resultado, Decimal('36').quantize(Decimal('0.000001')))

    @patch('apps.inventory.models.ProdutoUnidade.objects')
    @patch('apps.inventory.services.ConversaoService.obter_unidade_base')
    def test_fator_fracionario(self, mock_base, mock_pu_qs):
        """0.5 L × fator 1000 (ml) = 500.000000 base units."""
        from apps.inventory.services import ConversaoService

        base = MagicMock()
        base.id = 1
        mock_base.return_value = base

        pu = MagicMock()
        pu.fator_conversao = Decimal('1000')
        mock_pu_qs.filter.return_value.first.return_value = pu

        resultado = ConversaoService.converter_quantidade('p', Decimal('0.5'), 3)
        self.assertEqual(resultado, Decimal('500.000000'))

    @patch('apps.inventory.models.ProdutoUnidade.objects')
    @patch('apps.inventory.services.ConversaoService.obter_unidade_base')
    def test_sem_configuracao_raises_value_error(self, mock_base, mock_pu_qs):
        """Raises ValueError when no ProdutoUnidade is found for the given unit."""
        from apps.inventory.services import ConversaoService

        base = MagicMock()
        base.id = 1
        mock_base.return_value = base
        mock_pu_qs.filter.return_value.first.return_value = None

        with self.assertRaises(ValueError) as cm:
            ConversaoService.converter_quantidade('p', Decimal('1'), 99)

        self.assertIn('99', str(cm.exception))


class ConversaoServiceConverterParaUnidadeTests(SimpleTestCase):
    """Tests for ConversaoService.converter_para_unidade (reverse conversion)."""

    @patch('apps.inventory.services.ConversaoService.obter_unidade_base')
    def test_mesma_unidade_retorna_inalterado(self, mock_base):
        """Reverse converting to the base unit returns unchanged value."""
        from apps.inventory.services import ConversaoService

        base = MagicMock()
        base.id = 7
        mock_base.return_value = base

        resultado = ConversaoService.converter_para_unidade('p', Decimal('20'), 7)
        self.assertEqual(resultado, Decimal('20'))

    @patch('apps.inventory.models.ProdutoUnidade.objects')
    @patch('apps.inventory.services.ConversaoService.obter_unidade_base')
    def test_divide_pela_fator(self, mock_base, mock_pu_qs):
        """36 base units ÷ fator 12 = 3 caixas."""
        from apps.inventory.services import ConversaoService

        base = MagicMock()
        base.id = 1
        mock_base.return_value = base

        pu = MagicMock()
        pu.fator_conversao = Decimal('12')
        mock_pu_qs.filter.return_value.first.return_value = pu

        resultado = ConversaoService.converter_para_unidade('p', Decimal('36'), 2)
        self.assertAlmostEqual(float(resultado), 3.0, places=5)

    @patch('apps.inventory.models.ProdutoUnidade.objects')
    @patch('apps.inventory.services.ConversaoService.obter_unidade_base')
    def test_fator_zero_raises_value_error(self, mock_base, mock_pu_qs):
        """Division by zero factor should raise ValueError."""
        from apps.inventory.services import ConversaoService

        base = MagicMock()
        base.id = 1
        mock_base.return_value = base

        pu = MagicMock()
        pu.fator_conversao = Decimal('0')
        mock_pu_qs.filter.return_value.first.return_value = pu

        with self.assertRaises(ValueError):
            ConversaoService.converter_para_unidade('p', Decimal('50'), 2)

    @patch('apps.inventory.models.ProdutoUnidade.objects')
    @patch('apps.inventory.services.ConversaoService.obter_unidade_base')
    def test_sem_configuracao_raises_value_error(self, mock_base, mock_pu_qs):
        """Raises ValueError when no ProdutoUnidade configured for the target unit."""
        from apps.inventory.services import ConversaoService

        base = MagicMock()
        base.id = 1
        mock_base.return_value = base
        mock_pu_qs.filter.return_value.first.return_value = None

        with self.assertRaises(ValueError):
            ConversaoService.converter_para_unidade('p', Decimal('10'), 99)

    @patch('apps.inventory.models.ProdutoUnidade.objects')
    @patch('apps.inventory.services.ConversaoService.obter_unidade_base')
    def test_precisao_seis_casas_decimais(self, mock_base, mock_pu_qs):
        """Results are quantized to 6 decimal places."""
        from apps.inventory.services import ConversaoService

        base = MagicMock()
        base.id = 1
        mock_base.return_value = base

        pu = MagicMock()
        pu.fator_conversao = Decimal('3')
        mock_pu_qs.filter.return_value.first.return_value = pu

        resultado = ConversaoService.converter_para_unidade('p', Decimal('1'), 2)
        # 1/3 = 0.333333 (6 decimal places)
        self.assertEqual(str(resultado), '0.333333')

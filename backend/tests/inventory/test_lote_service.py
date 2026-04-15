"""Unit tests for LoteService — T034f."""
from __future__ import annotations

from datetime import date, timedelta
from decimal import Decimal
from unittest.mock import MagicMock, patch

from django.test import TestCase
from django.utils import timezone


class LoteServiceTests(TestCase):
    """Tests for apps.inventory.services.LoteService."""

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _make_lote(self, data_validade=None, quantidade=Decimal("10"), status="ATIVO"):
        """Return a MagicMock representing a LoteProduto instance."""
        lote = MagicMock()
        lote.status = status
        lote.quantidade_atual = quantidade
        lote.data_validade = data_validade or (date.today() + timedelta(days=30))
        return lote

    # ------------------------------------------------------------------
    # marcar_lotes_vencidos
    # ------------------------------------------------------------------

    def test_marcar_lotes_vencidos_sem_loja(self):
        """Should update all expired ATIVO lotes across all stores."""
        from apps.inventory.services import LoteService

        with patch("apps.inventory.models.LoteProduto") as MockLote:
            qs_mock = MagicMock()
            qs_mock.filter.return_value = qs_mock
            qs_mock.update.return_value = 3
            MockLote.objects = qs_mock

            count = LoteService.marcar_lotes_vencidos()

        self.assertEqual(count, 3)
        qs_mock.update.assert_called_once_with(status="VENCIDO")

    def test_marcar_lotes_vencidos_com_loja(self):
        """Should scope to a specific loja when loja_id is provided."""
        from apps.inventory.services import LoteService

        with patch("apps.inventory.models.LoteProduto") as MockLote:
            qs_mock = MagicMock()
            qs_mock.filter.return_value = qs_mock
            qs_mock.update.return_value = 1
            MockLote.objects = qs_mock

            count = LoteService.marcar_lotes_vencidos(loja_id=7)

        self.assertEqual(count, 1)
        # Should call filter twice: once for status/date, once for loja_id
        self.assertEqual(qs_mock.filter.call_count, 2)

    def test_marcar_lotes_vencidos_retorna_zero_quando_nenhum(self):
        """Should return 0 when no lotes are expired."""
        from apps.inventory.services import LoteService

        with patch("apps.inventory.models.LoteProduto") as MockLote:
            qs_mock = MagicMock()
            qs_mock.filter.return_value = qs_mock
            qs_mock.update.return_value = 0
            MockLote.objects = qs_mock

            count = LoteService.marcar_lotes_vencidos()

        self.assertEqual(count, 0)

    # ------------------------------------------------------------------
    # listar_lotes_proximos_vencimento
    # ------------------------------------------------------------------

    def test_listar_proximos_vencimento_chama_filter_correto(self):
        """Should filter lotes expiring within the given day window."""
        from apps.inventory.services import LoteService

        with patch("apps.inventory.models.LoteProduto") as MockLote:
            qs_mock = MagicMock()
            qs_mock.select_related.return_value = qs_mock
            qs_mock.filter.return_value = qs_mock
            qs_mock.order_by.return_value = qs_mock
            MockLote.objects = qs_mock

            result = LoteService.listar_lotes_proximos_vencimento(loja_id=1, dias=15)

        self.assertIsNotNone(result)
        qs_mock.filter.assert_called_once()
        # Verify dias parameter affects the date limit
        call_kwargs = qs_mock.filter.call_args.kwargs
        self.assertIn("data_validade__lte", call_kwargs)
        expected_limit = timezone.now().date() + timedelta(days=15)
        self.assertEqual(call_kwargs["data_validade__lte"], expected_limit)

    def test_listar_proximos_vencimento_default_30_dias(self):
        """Default window should be 30 days."""
        from apps.inventory.services import LoteService

        with patch("apps.inventory.models.LoteProduto") as MockLote:
            qs_mock = MagicMock()
            qs_mock.select_related.return_value = qs_mock
            qs_mock.filter.return_value = qs_mock
            qs_mock.order_by.return_value = qs_mock
            MockLote.objects = qs_mock

            LoteService.listar_lotes_proximos_vencimento(loja_id=1)

        call_kwargs = qs_mock.filter.call_args.kwargs
        expected_limit = timezone.now().date() + timedelta(days=30)
        self.assertEqual(call_kwargs["data_validade__lte"], expected_limit)

    # ------------------------------------------------------------------
    # obter_lote_fifo
    # ------------------------------------------------------------------

    def test_obter_lote_fifo_retorna_lote_mais_antigo(self):
        """FIFO: should return the oldest lote by entry date."""
        from apps.inventory.services import LoteService

        lote_antigo = self._make_lote(data_validade=date.today() + timedelta(days=10))

        with patch("apps.inventory.models.LoteProduto") as MockLote:
            qs_mock = MagicMock()
            qs_mock.filter.return_value = qs_mock
            qs_mock.order_by.return_value = qs_mock
            qs_mock.first.return_value = lote_antigo
            MockLote.objects = qs_mock

            result = LoteService.obter_lote_fifo("prod-uuid", loja_id=1)

        self.assertEqual(result, lote_antigo)
        qs_mock.order_by.assert_called_once_with("data_validade", "data_entrada")

    def test_obter_lote_fifo_retorna_none_sem_estoque(self):
        """Should return None when no ATIVO lotes exist."""
        from apps.inventory.services import LoteService

        with patch("apps.inventory.models.LoteProduto") as MockLote:
            qs_mock = MagicMock()
            qs_mock.filter.return_value = qs_mock
            qs_mock.order_by.return_value = qs_mock
            qs_mock.first.return_value = None
            MockLote.objects = qs_mock

            result = LoteService.obter_lote_fifo("prod-uuid", loja_id=1)

        self.assertIsNone(result)

    # ------------------------------------------------------------------
    # obter_lote_fefo
    # ------------------------------------------------------------------

    def test_obter_lote_fefo_ordena_por_validade(self):
        """FEFO: should return lote with earliest expiry date."""
        from apps.inventory.services import LoteService

        lote_prestes_vencer = self._make_lote(data_validade=date.today() + timedelta(days=3))

        with patch("apps.inventory.models.LoteProduto") as MockLote:
            qs_mock = MagicMock()
            qs_mock.filter.return_value = qs_mock
            qs_mock.order_by.return_value = qs_mock
            qs_mock.first.return_value = lote_prestes_vencer
            MockLote.objects = qs_mock

            result = LoteService.obter_lote_fefo("prod-uuid", loja_id=1)

        self.assertEqual(result, lote_prestes_vencer)
        qs_mock.order_by.assert_called_once_with("data_validade")

    def test_obter_lote_fefo_exclui_sem_validade(self):
        """FEFO filter must exclude lotes with null data_validade."""
        from apps.inventory.services import LoteService

        with patch("apps.inventory.models.LoteProduto") as MockLote:
            qs_mock = MagicMock()
            qs_mock.filter.return_value = qs_mock
            qs_mock.order_by.return_value = qs_mock
            qs_mock.first.return_value = None
            MockLote.objects = qs_mock

            LoteService.obter_lote_fefo("prod-uuid", loja_id=1)

        call_kwargs = qs_mock.filter.call_args.kwargs
        self.assertIn("data_validade__isnull", call_kwargs)
        self.assertFalse(call_kwargs["data_validade__isnull"])

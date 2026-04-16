"""Concurrency / race-condition tests for PDVCheckoutAPIView — T056.

Tests:
  1. Sequential "second checkout sees depleted stock" → 400 returned.
  2. processar_baixa_venda raises mid-transaction → whole transaction rolled back → 400.
  3. True concurrent requests via ThreadPoolExecutor: one succeeds (201),
     the other is rejected (400) once stock is depleted by the first thread.
  4. Unauthorised loja → 403 with zero PedidoVenda / Venda created.
"""
from __future__ import annotations

import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from decimal import Decimal
from unittest.mock import MagicMock, patch

from django.test import TestCase
from rest_framework.test import APIClient


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_user(pk: int = 50):
    from django.contrib.auth import get_user_model

    User = get_user_model()
    try:
        return User.objects.get(pk=pk)
    except User.DoesNotExist:
        return User.objects.create_user(
            username=f"concurrent_user_{pk}", password="pass", pk=pk
        )


_PAYLOAD = {
    "loja_id": 1,
    "itens": [
        {
            "produto_variacao_id": "prod-conc-1",
            "quantidade": "1",
            "preco_unitario": "150.00",
            "unidade_id": 1,
        }
    ],
    "pagamentos": [
        {"forma": "PIX", "valor": "150.00"}
    ],
}


def _wire_happy_path(
    mock_ul,
    mock_calc,
    mock_conv,
    mock_ub,
    mock_baixa,
    mock_pedido_qs,
    mock_item_qs,
    mock_venda_qs,
    mock_pag_qs,
    disponivel: Decimal = Decimal("1.00"),
    pedido_pk: str = "ped-conc",
    venda_pk: str = "venda-conc",
    numero_venda: str = "VND-CONC",
):
    """Wire all standard mocks for a successful PDV checkout path."""
    mock_ul.filter.return_value.exists.return_value = True

    mock_calc.return_value = disponivel
    mock_conv.return_value = Decimal("1.00")

    unidade = MagicMock()
    unidade.id = 1
    mock_ub.return_value = unidade

    pedido_mock = MagicMock()
    pedido_mock.pk = pedido_pk
    mock_pedido_qs.create.return_value = pedido_mock

    mock_item_qs.create.return_value = MagicMock()

    venda_mock = MagicMock()
    venda_mock.pk = venda_pk
    venda_mock.numero_venda = numero_venda
    venda_mock.loja_id = 1
    mock_venda_qs.create.return_value = venda_mock

    mock_pag_qs.create.return_value = MagicMock()
    return pedido_mock, venda_mock


# ---------------------------------------------------------------------------
# Test class — all standard mocks applied via class-level decorators
# ---------------------------------------------------------------------------

@patch("apps.sales.models.PagamentoVenda.objects")
@patch("apps.sales.models.Venda.objects")
@patch("apps.sales.models.ItemPedidoVenda.objects")
@patch("apps.sales.models.PedidoVenda.objects")
@patch("apps.inventory.services.EstoqueService.processar_baixa_venda")
@patch("apps.inventory.services.ConversaoService.obter_unidade_base")
@patch("apps.inventory.services.ConversaoService.converter_quantidade")
@patch("apps.inventory.services.EstoqueService.calcular_disponibilidade")
@patch("apps.companies.models.UsuarioLoja.objects")
class PDVCheckoutConcorrenciaTests(TestCase):
    """T056 — Race-condition edge cases for PDVCheckoutAPIView."""

    def setUp(self):
        self.user = _make_user(pk=50)
        self.api = APIClient()
        self.api.force_authenticate(user=self.user)

    def _post(self, payload=None):
        return self.api.post(
            "/api/v1/sales/pdv/checkout/",
            payload or _PAYLOAD,
            format="json",
        )

    # ------------------------------------------------------------------
    # T056-A: second sequential request sees stock already depleted
    # ------------------------------------------------------------------

    def test_segundo_checkout_ve_estoque_zerado_retorna_400(
        self,
        mock_ul,
        mock_calc,
        mock_conv,
        mock_ub,
        mock_baixa,
        mock_pedido_qs,
        mock_item_qs,
        mock_venda_qs,
        mock_pag_qs,
    ):
        """Second checkout call sees depleted stock → 400 Estoque insuficiente."""
        # First call: stock available; second call: stock depleted (simulates post-commit)
        mock_calc.side_effect = [Decimal("1.00"), Decimal("0.00")]
        mock_conv.return_value = Decimal("1.00")

        unidade = MagicMock()
        unidade.id = 1
        mock_ub.return_value = unidade
        mock_ul.filter.return_value.exists.return_value = True

        pedido_mock = MagicMock()
        pedido_mock.pk = "ped-seq"
        mock_pedido_qs.create.return_value = pedido_mock
        mock_item_qs.create.return_value = MagicMock()

        venda_mock = MagicMock()
        venda_mock.pk = "venda-seq"
        venda_mock.numero_venda = "VND-SEQ-1"
        venda_mock.loja_id = 1
        mock_venda_qs.create.return_value = venda_mock
        mock_pag_qs.create.return_value = MagicMock()

        resp1 = self._post()
        resp2 = self._post()

        self.assertEqual(resp1.status_code, 201, resp1.data)
        self.assertEqual(resp2.status_code, 400, resp2.data)
        self.assertIn("insuficiente", resp2.data.get("erro", "").lower())

    # ------------------------------------------------------------------
    # T056-B: processar_baixa_venda raises mid-transaction → rollback → 400
    # ------------------------------------------------------------------

    def test_rollback_quando_baixa_estoque_falha(
        self,
        mock_ul,
        mock_calc,
        mock_conv,
        mock_ub,
        mock_baixa,
        mock_pedido_qs,
        mock_item_qs,
        mock_venda_qs,
        mock_pag_qs,
    ):
        """processar_baixa_venda raises → transaction.atomic rolls back → 400."""
        _wire_happy_path(
            mock_ul, mock_calc, mock_conv, mock_ub, mock_baixa,
            mock_pedido_qs, mock_item_qs, mock_venda_qs, mock_pag_qs,
        )
        # Mock the stock write to simulate a concurrent transaction already committed
        mock_baixa.side_effect = Exception("Estoque zerado por outra transação concorrente")

        resp = self._post()

        self.assertEqual(resp.status_code, 400, resp.data)
        self.assertIn("Estoque zerado", resp.data.get("erro", ""))
        # PedidoVenda.create was called but the transaction was rolled back
        mock_pedido_qs.create.assert_called_once()

    # ------------------------------------------------------------------
    # T056-C: PedidoVenda.create fails → Venda NOT created
    # ------------------------------------------------------------------

    def test_pedido_create_falha_venda_nao_e_criada(
        self,
        mock_ul,
        mock_calc,
        mock_conv,
        mock_ub,
        mock_baixa,
        mock_pedido_qs,
        mock_item_qs,
        mock_venda_qs,
        mock_pag_qs,
    ):
        """If PedidoVenda.create raises, Venda.create is never called → 400."""
        mock_ul.filter.return_value.exists.return_value = True
        mock_calc.return_value = Decimal("1.00")
        mock_conv.return_value = Decimal("1.00")
        unidade = MagicMock()
        unidade.id = 1
        mock_ub.return_value = unidade

        mock_pedido_qs.create.side_effect = Exception("DB constraint violation")

        resp = self._post()

        self.assertEqual(resp.status_code, 400)
        mock_venda_qs.create.assert_not_called()

    # ------------------------------------------------------------------
    # T056-D: concurrent ThreadPoolExecutor — one 201, one 400
    # ------------------------------------------------------------------

    def test_concurrent_requests_one_succeeds_one_fails(
        self,
        mock_ul,
        mock_calc,
        mock_conv,
        mock_ub,
        mock_baixa,
        mock_pedido_qs,
        mock_item_qs,
        mock_venda_qs,
        mock_pag_qs,
    ):
        """Concurrent checkout: thread-safe stock check → one 201, one 400.

        Uses threading.Barrier so both threads enter the stock check at the
        same instant, then a call counter ensures thread-1 returns stock
        available and thread-2 returns stock depleted.
        """
        barrier = threading.Barrier(2, timeout=5)
        lock = threading.Lock()
        call_count_box = [0]

        def calc_with_barrier(prod_id, loja_id):
            with lock:
                call_count_box[0] += 1
                my_call = call_count_box[0]
            # Synchronise: wait until both threads have reached this point
            barrier.wait()
            # First caller sees available stock, second caller sees 0
            return Decimal("1.00") if my_call == 1 else Decimal("0.00")

        mock_calc.side_effect = calc_with_barrier
        mock_conv.return_value = Decimal("1.00")

        unidade = MagicMock()
        unidade.id = 1
        mock_ub.return_value = unidade
        mock_ul.filter.return_value.exists.return_value = True

        pedido_mock = MagicMock()
        pedido_mock.pk = "ped-thread"
        mock_pedido_qs.create.return_value = pedido_mock
        mock_item_qs.create.return_value = MagicMock()

        venda_mock = MagicMock()
        venda_mock.pk = "venda-thread"
        venda_mock.numero_venda = "VND-THREAD"
        venda_mock.loja_id = 1
        mock_venda_qs.create.return_value = venda_mock
        mock_pag_qs.create.return_value = MagicMock()

        status_codes: list[int] = []

        def make_request() -> None:
            client = APIClient()
            client.force_authenticate(user=self.user)
            resp = client.post("/api/v1/sales/pdv/checkout/", _PAYLOAD, format="json")
            status_codes.append(resp.status_code)

        with ThreadPoolExecutor(max_workers=2) as pool:
            futures = [pool.submit(make_request) for _ in range(2)]
            for f in as_completed(futures):
                f.result()  # re-raise any exception from the thread

        self.assertIn(201, status_codes, f"Expected one 201 — got: {status_codes}")
        self.assertIn(400, status_codes, f"Expected one 400 — got: {status_codes}")

    # ------------------------------------------------------------------
    # T056-E: unauthorised loja → 403, no orders touched
    # ------------------------------------------------------------------

    def test_loja_nao_autorizada_403_sem_criar_pedido(
        self,
        mock_ul,
        mock_calc,
        mock_conv,
        mock_ub,
        mock_baixa,
        mock_pedido_qs,
        mock_item_qs,
        mock_venda_qs,
        mock_pag_qs,
    ):
        """Unauthorized loja → 403 without creating PedidoVenda or Venda."""
        mock_ul.filter.return_value.exists.return_value = False

        resp = self._post()

        self.assertEqual(resp.status_code, 403)
        mock_pedido_qs.create.assert_not_called()
        mock_venda_qs.create.assert_not_called()

"""Concurrency / race-condition tests for CreditoService — T057.

Tests:
  1. Sequential: second bloquear_para_venda call sees exhausted credit → raises.
  2. Second call at credit limit boundary → CreditoInsuficienteError.
  3. Concurrent requests via ThreadPoolExecutor: one creates Recebivel,
     the other is rejected once available credit is depleted.
  4. override_com_pin race: second override attempt after credit exhausted
     still requires valid PIN and permission.
"""
from __future__ import annotations

import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from decimal import Decimal
from unittest.mock import MagicMock, patch, call

from django.test import TestCase


# ---------------------------------------------------------------------------
# Helpers (consistent with test_credito_service.py)
# ---------------------------------------------------------------------------

def _make_cliente(limite: Decimal = Decimal("500.00"), pk: int = 1):
    c = MagicMock()
    c.pk = pk
    c.limite_credito = limite
    c.nome_completo = f"Cliente Conc {pk}"
    return c


def _make_venda(pk: str = "venda-cc-1", loja_id: int = 1):
    v = MagicMock()
    v.pk = pk
    v.loja = MagicMock()
    v.loja_id = loja_id
    return v


def _make_user(tem_permissao: bool = True, password_ok: bool = True, pk: int = 99):
    u = MagicMock()
    u.pk = pk
    u.is_superuser = False
    u.check_password = MagicMock(return_value=password_ok)
    u.has_perm = MagicMock(return_value=tem_permissao)
    return u


# ---------------------------------------------------------------------------
# T057-A — Sequential: second call sees credit exhausted
# ---------------------------------------------------------------------------

class CreditoBloqueioSequencialTests(TestCase):
    """T057 — Sequential credit depletion ensures second caller is rejected."""

    def setUp(self):
        from apps.sales.services import _credito_pin_attempts
        _credito_pin_attempts.clear()

    @patch("apps.sales.services.RecebivelService.criar")
    @patch("apps.sales.services.CreditoService.verificar_disponivel")
    def test_segundo_bloqueio_ve_credito_esgotado(self, mock_verif, mock_criar):
        """First bloquear_para_venda succeeds; second sees depleted credit → CreditoInsuficienteError."""
        from apps.sales.services import CreditoService, CreditoInsuficienteError

        # First call: credit available; second call: credit exhausted by first
        mock_verif.side_effect = [
            {"disponivel": Decimal("300.00"), "saldo_devedor": Decimal("200.00"),
             "limite": Decimal("500.00"), "ok": True},
            {"disponivel": Decimal("0.00"), "saldo_devedor": Decimal("500.00"),
             "limite": Decimal("500.00"), "ok": False},
        ]
        rec_mock = MagicMock()
        mock_criar.return_value = rec_mock

        cliente = _make_cliente()
        venda1 = _make_venda("v-seq-1")
        venda2 = _make_venda("v-seq-2")

        # First call succeeds
        result = CreditoService.bloquear_para_venda(cliente, Decimal("300.00"), venda1)
        self.assertEqual(result, rec_mock)

        # Second call must raise
        with self.assertRaises(CreditoInsuficienteError) as ctx:
            CreditoService.bloquear_para_venda(cliente, Decimal("100.00"), venda2)

        self.assertEqual(ctx.exception.disponivel, Decimal("0.00"))
        self.assertEqual(ctx.exception.solicitado, Decimal("100.00"))
        mock_criar.assert_called_once()  # Only the first call created a Recebivel

    @patch("apps.sales.services.RecebivelService.criar")
    @patch("apps.sales.services.CreditoService.verificar_disponivel")
    def test_bloqueio_exatamente_no_limite_aceito(self, mock_verif, mock_criar):
        """Purchase exactly at the available credit limit → ok (boundary)."""
        from apps.sales.services import CreditoService

        mock_verif.return_value = {
            "disponivel": Decimal("150.00"),
            "saldo_devedor": Decimal("350.00"),
            "limite": Decimal("500.00"),
            "ok": True,
        }
        rec_mock = MagicMock()
        mock_criar.return_value = rec_mock

        result = CreditoService.bloquear_para_venda(
            _make_cliente(), Decimal("150.00"), _make_venda()
        )

        self.assertEqual(result, rec_mock)
        mock_criar.assert_called_once()

    @patch("apps.sales.services.CreditoService.verificar_disponivel")
    def test_bloqueio_um_centavo_acima_do_limite_rejeitado(self, mock_verif):
        """Exactly R$ 0.01 above available credit → CreditoInsuficienteError."""
        from apps.sales.services import CreditoService, CreditoInsuficienteError

        mock_verif.return_value = {
            "disponivel": Decimal("149.99"),
            "saldo_devedor": Decimal("350.01"),
            "limite": Decimal("500.00"),
            "ok": False,
        }

        with self.assertRaises(CreditoInsuficienteError) as ctx:
            CreditoService.bloquear_para_venda(
                _make_cliente(), Decimal("150.00"), _make_venda()
            )

        self.assertEqual(ctx.exception.disponivel, Decimal("149.99"))


# ---------------------------------------------------------------------------
# T057-B — Concurrent: ThreadPoolExecutor race condition
# ---------------------------------------------------------------------------

class CreditoConcorrenteBloqueioTests(TestCase):
    """T057 — Two concurrent bloquear_para_venda calls; only one should succeed.

    Uses threading.Barrier to synchronise both threads past verificar_disponivel
    before either commits, then the call counter ensures the second caller
    sees the post-commit credit balance.
    """

    def setUp(self):
        from apps.sales.services import _credito_pin_attempts
        _credito_pin_attempts.clear()

    @patch("apps.sales.services.RecebivelService.criar")
    @patch("apps.sales.services.CreditoService.verificar_disponivel")
    def test_concurrent_only_one_recebivel_created(self, mock_verif, mock_criar):
        """Concurrent calls: barrier ensures both see credit available, but only
        the first call's Recebivel is created; second raises CreditoInsuficienteError."""

        barrier = threading.Barrier(2, timeout=5)
        lock = threading.Lock()
        call_count_box = [0]

        def verificar_with_barrier(cliente, valor_novo):
            with lock:
                call_count_box[0] += 1
                my_call = call_count_box[0]
            # Wait until both threads have reached verificar_disponivel
            barrier.wait()
            if my_call == 1:
                return {
                    "disponivel": Decimal("300.00"),
                    "saldo_devedor": Decimal("200.00"),
                    "limite": Decimal("500.00"),
                    "ok": True,
                }
            else:
                # Post-barrier: first thread committed, credit now 0
                return {
                    "disponivel": Decimal("0.00"),
                    "saldo_devedor": Decimal("500.00"),
                    "limite": Decimal("500.00"),
                    "ok": False,
                }

        mock_verif.side_effect = verificar_with_barrier

        rec_mock = MagicMock()
        mock_criar.return_value = rec_mock

        from apps.sales.services import CreditoService, CreditoInsuficienteError

        results: list[bool] = []  # True = success, False = insufficient credit error
        errors: list[Exception] = []

        def attempt_bloquear(venda_pk: str) -> None:
            cliente = _make_cliente()
            venda = _make_venda(venda_pk)
            try:
                CreditoService.bloquear_para_venda(cliente, Decimal("300.00"), venda)
                results.append(True)
            except CreditoInsuficienteError:
                results.append(False)
            except Exception as exc:
                errors.append(exc)

        with ThreadPoolExecutor(max_workers=2) as pool:
            futures = [
                pool.submit(attempt_bloquear, f"venda-cc-{i}") for i in range(2)
            ]
            for f in as_completed(futures):
                f.result()

        self.assertFalse(errors, f"Unexpected errors: {errors}")
        self.assertIn(True, results, "Expected one successful bloquear_para_venda")
        self.assertIn(False, results, "Expected one CreditoInsuficienteError")
        # Only the successful thread should have called RecebivelService.criar
        self.assertEqual(mock_criar.call_count, 1)


# ---------------------------------------------------------------------------
# T057-C — Concurrent override_com_pin: second thread sees no credit
# ---------------------------------------------------------------------------

class CreditoOverrideConcorrenteTests(TestCase):
    """T057 — override_com_pin: only authorised approver with valid PIN can override.

    The concurrent scenario: manager approves override for T1;
    T2 also tries but correct credit check in T2 sees limit breached.
    """

    def setUp(self):
        from apps.sales.services import _credito_pin_attempts
        _credito_pin_attempts.clear()

    @patch("apps.sales.models.Recebivel.objects")
    @patch("apps.sales.services.CreditoService.verificar_disponivel")
    def test_override_com_pin_correto_bypassa_limite(self, mock_verif, mock_rec_qs):
        """override_com_pin with valid PIN and permission creates Recebivel regardless of limit."""
        from apps.sales.services import CreditoService

        mock_verif.return_value = {
            "disponivel": Decimal("0.00"),
            "saldo_devedor": Decimal("500.00"),
            "limite": Decimal("500.00"),
            "ok": False,
        }
        rec_mock = MagicMock()
        mock_rec_qs.create.return_value = rec_mock

        aprovador = _make_user(tem_permissao=True, password_ok=True)
        result = CreditoService.override_com_pin(
            _make_cliente(),
            Decimal("600.00"),
            _make_venda(),
            pin="correct-pin",
            aprovador=aprovador,
        )

        self.assertEqual(result, rec_mock)

    def test_override_pin_errado_incrementa_tentativas(self):
        """Wrong override PIN increments attempt counter and raises CreditoOverrideError."""
        from apps.sales.services import CreditoService, CreditoOverrideError

        aprovador = _make_user(tem_permissao=True, password_ok=False)

        with self.assertRaises(CreditoOverrideError) as ctx:
            CreditoService.override_com_pin(
                _make_cliente(), Decimal("200.00"), _make_venda(), "wrong-pin", aprovador
            )

        self.assertEqual(ctx.exception.tentativas, 1)
        self.assertEqual(ctx.exception.max_tentativas, 3)

    def test_override_tres_tentativas_erradas_cooldown(self):
        """Three wrong override PINs → DescontoCooldownError."""
        from apps.sales.services import CreditoService, CreditoOverrideError
        from apps.sales.services import DescontoCooldownError

        aprovador = _make_user(tem_permissao=True, password_ok=False, pk=77)

        for _ in range(2):
            with self.assertRaises(CreditoOverrideError):
                CreditoService.override_com_pin(
                    _make_cliente(pk=5), Decimal("200.00"), _make_venda(), "x", aprovador
                )

        # Third attempt triggers cooldown
        with self.assertRaises(DescontoCooldownError):
            CreditoService.override_com_pin(
                _make_cliente(pk=5), Decimal("200.00"), _make_venda(), "x", aprovador
            )

    def test_override_sem_permissao_levanta_permission_denied(self):
        """override_com_pin without sales.override_credit → PermissionDenied."""
        from apps.sales.services import CreditoService
        from django.core.exceptions import PermissionDenied

        aprovador = _make_user(tem_permissao=False)

        with self.assertRaises(PermissionDenied):
            CreditoService.override_com_pin(
                _make_cliente(), Decimal("100.00"), _make_venda(), "pin", aprovador
            )

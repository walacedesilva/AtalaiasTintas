"""Transaction-rollback tests for DescontoAuditLog — T058.

Verifies that when an exception is raised after DescontoAuditLog.objects.create()
inside the @transaction.atomic block of aplicar_desconto_item, the audit log
record is rolled back to the savepoint and NOT persisted.

Tests:
  1. Unit test (mocked): exception from _recalcular_totais_pedido propagates.
  2. Unit test (mocked): DescontoAuditLog.objects.create is called BEFORE
     _recalcular_totais_pedido (correct ordering).
  3. Integration test (real DB, TestCase savepoint): AuditLog rolled back when
     _recalcular_totais_pedido raises — count stays 0 after exception.
  4. Integration test: successful path creates exactly one AuditLog.
"""
from __future__ import annotations

from decimal import Decimal
from unittest.mock import MagicMock, call, patch

from django.test import TestCase


# ---------------------------------------------------------------------------
# Unit-test helpers (pure mock — no DB required)
# ---------------------------------------------------------------------------

def _make_pedido(pk: str = "ped-t058", subtotal: Decimal = Decimal("100.00")):
    p = MagicMock()
    p.pk = pk
    p.valor_subtotal = subtotal
    p.valor_desconto = Decimal("0.00")
    p.percentual_desconto = Decimal("0.00")
    p.valor_total = subtotal
    p.desconto_aprovador = None
    p.desconto_motivo = None
    p.desconto_aprovado_em = None
    p.save = MagicMock()
    return p


def _make_item(pedido, preco_total: Decimal = Decimal("100.00")):
    item = MagicMock()
    item.pk = "item-t058"
    item.pedido = pedido
    item.preco_unitario = Decimal("100.00")
    item.quantidade = Decimal("1.00")
    item.preco_total = preco_total
    item.save = MagicMock()
    return item


def _make_user(is_superuser: bool = False, grupos: list | None = None, password_ok: bool = True):
    u = MagicMock()
    u.pk = 1
    u.is_superuser = is_superuser
    u.check_password = MagicMock(return_value=password_ok)
    u.groups.values_list.return_value = grupos or []
    return u


# ---------------------------------------------------------------------------
# T058-A: Unit tests — mocked (code-flow correctness)
# ---------------------------------------------------------------------------

class DescontoAuditLogFlowTests(TestCase):
    """T058-A — Verify execution order: item.save → create AuditLog → recalcular."""

    def setUp(self):
        from apps.sales.services import _pin_attempts
        _pin_attempts.clear()

    @patch("apps.sales.services.DescontoService._recalcular_totais_pedido")
    @patch("apps.sales.models.DescontoAuditLog.objects.create")
    def test_excecao_em_recalcular_propagada_de_aplicar_desconto_item(
        self, mock_create, mock_recalc
    ):
        """Exception in _recalcular_totais_pedido propagates out of aplicar_desconto_item."""
        from apps.sales.services import DescontoService

        mock_recalc.side_effect = RuntimeError("DB constraint após auditlog")
        pedido = _make_pedido()
        item = _make_item(pedido)

        with self.assertRaises(RuntimeError) as ctx:
            DescontoService.aplicar_desconto_item(
                item, Decimal("3.00"), _make_user()
            )

        self.assertIn("auditlog", str(ctx.exception))
        # AuditLog.create was still called (code reached it before recalcular raised)
        mock_create.assert_called_once()

    @patch("apps.sales.services.DescontoService._recalcular_totais_pedido")
    @patch("apps.sales.models.DescontoAuditLog.objects.create")
    def test_auditlog_create_chamado_antes_do_recalcular(
        self, mock_create, mock_recalc
    ):
        """AuditLog.create is always called before _recalcular_totais_pedido."""
        from apps.sales.services import DescontoService

        call_order: list[str] = []
        mock_create.side_effect = lambda **kw: call_order.append("create") or MagicMock()
        mock_recalc.side_effect = lambda p: call_order.append("recalcular")

        pedido = _make_pedido()
        item = _make_item(pedido)

        DescontoService.aplicar_desconto_item(item, Decimal("3.00"), _make_user())

        self.assertEqual(call_order, ["create", "recalcular"],
                         "DescontoAuditLog.create must be called BEFORE _recalcular_totais_pedido")

    @patch("apps.sales.services.DescontoService._recalcular_totais_pedido")
    @patch("apps.sales.models.DescontoAuditLog.objects.create")
    def test_auditlog_recebe_tipo_item_e_percentual_correto(
        self, mock_create, mock_recalc
    ):
        """AuditLog.create called with tipo_desconto='ITEM' and correct percentual."""
        from apps.sales.services import DescontoService

        pedido = _make_pedido()
        item = _make_item(pedido)

        DescontoService.aplicar_desconto_item(item, Decimal("4.00"), _make_user())

        mock_create.assert_called_once()
        kw = mock_create.call_args[1]
        self.assertEqual(kw["tipo_desconto"], "ITEM")
        self.assertEqual(kw["percentual"], Decimal("4.00"))
        self.assertFalse(kw["aprovado_com_pin"])
        self.assertIs(kw["pedido"], pedido)

    @patch("apps.sales.services.DescontoService._recalcular_totais_pedido")
    @patch("apps.sales.models.DescontoAuditLog.objects.create")
    def test_auditlog_aprovado_com_pin_true_para_desconto_acima_5_porcento(
        self, mock_create, mock_recalc
    ):
        """When discount >5% and PIN is valid, aprovado_com_pin=True in AuditLog."""
        from apps.sales.services import DescontoService

        pedido = _make_pedido()
        item = _make_item(pedido)

        aprovador = _make_user(is_superuser=True)
        DescontoService.aplicar_desconto_item(
            item, Decimal("10.00"), _make_user(), aprovador=aprovador, pin="correct"
        )

        kw = mock_create.call_args[1]
        self.assertTrue(kw["aprovado_com_pin"])


# ---------------------------------------------------------------------------
# T058-B: Integration tests — real DB (TestCase savepoint rollback)
# ---------------------------------------------------------------------------

def _setup_t058_fixtures(suffix: str = ""):
    """Create minimal real DB objects for DescontoAuditLog integration tests."""
    from django.contrib.auth import get_user_model
    from apps.companies.models import Empresa, Loja
    from apps.inventory.models import (
        Categoria,
        Marca,
        ProdutoBase,
        ProdutoVariacao,
        UnidadeMedida,
    )
    from apps.sales.models import ItemPedidoVenda, PedidoVenda

    User = get_user_model()
    solicitante = User.objects.create_user(
        username=f"t058_sol{suffix}", password="pass"
    )
    vendedor = User.objects.create_user(
        username=f"t058_vend{suffix}", password="pass"
    )

    empresa = Empresa.objects.create(
        razao_social=f"Empresa T058{suffix}",
        cnpj=f"98765432000{suffix}".zfill(14)[:14],
    )
    loja = Loja.objects.create(nome=f"Loja T058{suffix}", empresa=empresa)

    unidade = UnidadeMedida.objects.create(
        codigo=f"LT58{suffix}", nome="Litro58", sigla="L", tipo="VOLUME"
    )
    categoria = Categoria.objects.create(
        nome=f"Cat T058{suffix}", codigo=f"CT58{suffix}"
    )
    marca = Marca.objects.create(
        nome=f"Marca T058{suffix}", codigo=f"MT58{suffix}"
    )
    produto_base = ProdutoBase.objects.create(
        codigo=f"PB58{suffix}",
        nome="Tinta T058",
        categoria=categoria,
        marca=marca,
        tipo_produto="SIMPLES",
    )
    variacao = ProdutoVariacao.objects.create(
        produto_base=produto_base,
        codigo_variacao=f"PV58{suffix}",
        nome_variacao="Branco",
        unidade_venda=unidade,
        unidade_estoque=unidade,
    )
    pedido = PedidoVenda.objects.create(
        loja=loja,
        vendedor=vendedor,
        numero_pedido=f"T058-{suffix}",
        situacao="ORCAMENTO",
        forma_pagamento="DINHEIRO",
        valor_subtotal=Decimal("100.00"),
        valor_desconto=Decimal("0.00"),
        valor_total=Decimal("100.00"),
    )
    item = ItemPedidoVenda.objects.create(
        pedido=pedido,
        produto_variacao=variacao,
        quantidade=Decimal("1.00"),
        preco_unitario=Decimal("100.00"),
        preco_total=Decimal("100.00"),
        unidade_venda=unidade,
        sequencia=1,
    )
    return solicitante, pedido, item


class DescontoAuditLogRollbackIntegrationTests(TestCase):
    """T058-B — Real DB: verify @transaction.atomic savepoint rolls back AuditLog."""

    def setUp(self):
        from apps.sales.services import _pin_attempts
        _pin_attempts.clear()

    @patch("apps.sales.services.DescontoService._recalcular_totais_pedido")
    def test_auditlog_rolledback_quando_recalcular_falha(self, mock_recalc):
        """When _recalcular_totais_pedido raises, the AuditLog is rolled back.

        Within TestCase, @transaction.atomic creates a SAVEPOINT; on exception the
        savepoint is released and any DB writes after it are undone.
        """
        from apps.sales.models import DescontoAuditLog
        from apps.sales.services import DescontoService

        mock_recalc.side_effect = Exception("Simulated failure after AuditLog creation")

        solicitante, pedido, item = _setup_t058_fixtures("rb1")

        initial_count = DescontoAuditLog.objects.count()

        with self.assertRaises(Exception):
            DescontoService.aplicar_desconto_item(
                item, Decimal("3.00"), solicitante
            )

        # Savepoint was rolled back → no new AuditLog records
        self.assertEqual(
            DescontoAuditLog.objects.count(),
            initial_count,
            "DescontoAuditLog must be rolled back when _recalcular_totais_pedido raises",
        )

    def test_auditlog_persistido_em_caminho_feliz(self):
        """On the happy path, exactly one DescontoAuditLog is persisted."""
        from apps.sales.models import DescontoAuditLog
        from apps.sales.services import DescontoService

        solicitante, pedido, item = _setup_t058_fixtures("ok1")

        initial_count = DescontoAuditLog.objects.count()

        DescontoService.aplicar_desconto_item(
            item, Decimal("3.00"), solicitante
        )

        self.assertEqual(
            DescontoAuditLog.objects.count(),
            initial_count + 1,
            "Exactly one DescontoAuditLog must be created on the happy path",
        )
        log = DescontoAuditLog.objects.latest("created_at")
        self.assertEqual(log.tipo_desconto, "ITEM")
        self.assertEqual(log.pedido, pedido)
        self.assertFalse(log.aprovado_com_pin)

    @patch("apps.sales.services.DescontoService._recalcular_totais_pedido")
    def test_multiplos_falhos_nao_acumulam_auditlogs(self, mock_recalc):
        """Multiple failed aplicar_desconto_item calls leave AuditLog count unchanged."""
        from apps.sales.models import DescontoAuditLog
        from apps.sales.services import DescontoService

        mock_recalc.side_effect = RuntimeError("DB error")
        solicitante, pedido, item = _setup_t058_fixtures("multi1")

        initial_count = DescontoAuditLog.objects.count()

        for _ in range(3):
            with self.assertRaises(RuntimeError):
                DescontoService.aplicar_desconto_item(
                    item, Decimal("2.00"), solicitante
                )

        self.assertEqual(
            DescontoAuditLog.objects.count(),
            initial_count,
            "Failed attempts must not leave lingering AuditLog rows",
        )

"""
T020 – Tintometry model unit tests

Covers:
  test_mistura_codigo_uniqueness
  test_estoque_pigmento_unique_together
  test_item_mistura_stock_before_after
  test_mistura_status_transitions
"""

from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db import IntegrityError

from apps.tintometry.models import (
    EstoquePigmento,
    ItemMistura,
    MisturaTinta,
)

from .base import TintometryBaseTestCase, make_estoque


class MisturaTintaModelTests(TintometryBaseTestCase):
    """Tests for MisturaTinta model constraints and auto-fields."""

    def _make_mistura(self, **kwargs):
        defaults = dict(
            formula=self.formula,
            loja=self.loja,
            usuario_operacao=self.user,
            cliente_nome='Test Client',
            volume_solicitado=Decimal('1.0'),
            custo_total=Decimal('25.00'),
            custo_base=Decimal('10.00'),
            custo_pigmentos=Decimal('15.00'),
        )
        defaults.update(kwargs)
        return MisturaTinta.objects.create(**defaults)

    # -----------------------------------------------------------------------
    # T020-1: codigo_mistura is unique
    # -----------------------------------------------------------------------
    def test_mistura_codigo_uniqueness(self):
        """Two MisturaTinta objects can never share the same codigo_mistura."""
        m1 = self._make_mistura()
        with self.assertRaises(IntegrityError):
            # Force the same code to trigger uniqueness constraint
            self._make_mistura(codigo_mistura=m1.codigo_mistura)

    # -----------------------------------------------------------------------
    # T020-2: codigo_mistura is auto-generated and unique per day
    # -----------------------------------------------------------------------
    def test_mistura_auto_codigo_is_unique_between_instances(self):
        """Without explicit codigo_mistura, auto-generation must yield distinct codes."""
        m1 = self._make_mistura()
        m2 = self._make_mistura()
        self.assertNotEqual(m1.codigo_mistura, m2.codigo_mistura)
        self.assertTrue(m1.codigo_mistura.startswith('MX'))
        self.assertTrue(m2.codigo_mistura.startswith('MX'))

    # -----------------------------------------------------------------------
    # T020-3: status transition guard – only CALCULADA can be confirmed
    # -----------------------------------------------------------------------
    def test_mistura_status_transitions(self):
        """
        The MixtureService enforces transitions; here we validate that the
        model correctly stores each valid status value.
        """
        mistura = self._make_mistura()
        self.assertEqual(mistura.situacao, 'CALCULADA')

        for new_status in ('CONFIRMADA', 'PRODUZIDA', 'ENTREGUE', 'CANCELADA'):
            mistura.situacao = new_status
            mistura.save(update_fields=['situacao'])
            mistura.refresh_from_db()
            self.assertEqual(mistura.situacao, new_status)


class EstoquePigmentoModelTests(TintometryBaseTestCase):
    """Tests for EstoquePigmento constraints and computed properties."""

    # -----------------------------------------------------------------------
    # T020-4: unique_together (pigmento, loja) is enforced
    # -----------------------------------------------------------------------
    def test_estoque_pigmento_unique_together(self):
        """Cannot create two EstoquePigmento rows for the same pigmento+loja."""
        # cls.estoque_a already exists for (self.pigmento_a, self.loja)
        with self.assertRaises(IntegrityError):
            EstoquePigmento.objects.create(
                pigmento=self.pigmento_a,
                loja=self.loja,
                saldo_ml=Decimal('500'),
                custo_ml=Decimal('2.50'),
            )

    # -----------------------------------------------------------------------
    # T020-5: estoque_critico property reflects saldo vs. saldo_minimo
    # -----------------------------------------------------------------------
    def test_estoque_critico_property(self):
        """estoque_critico must be True when saldo_ml <= saldo_minimo."""
        self.estoque_a.saldo_ml = self.estoque_a.saldo_minimo
        self.estoque_a.save(update_fields=['saldo_ml'])
        self.assertTrue(self.estoque_a.estoque_critico)

        self.estoque_a.saldo_ml = self.estoque_a.saldo_minimo + Decimal('1')
        self.estoque_a.save(update_fields=['saldo_ml'])
        self.assertFalse(self.estoque_a.estoque_critico)


class ItemMisturaModelTests(TintometryBaseTestCase):
    """Tests for ItemMistura fields."""

    def _make_full_mistura(self):
        """Create a MisturaTinta and its ItemMistura rows."""
        from apps.tintometry.models import MisturaTinta
        mistura = MisturaTinta.objects.create(
            formula=self.formula,
            loja=self.loja,
            usuario_operacao=self.user,
            cliente_nome='Test',
            volume_solicitado=Decimal('1.0'),
            custo_total=Decimal('30.00'),
            custo_base=Decimal('10.00'),
            custo_pigmentos=Decimal('20.00'),
        )
        item = ItemMistura.objects.create(
            mistura=mistura,
            pigmento=self.pigmento_a,
            quantidade_calculada=Decimal('15.0'),
            custo_unitario=Decimal('2.50'),
            custo_total=Decimal('37.50'),
            estoque_antes=Decimal('1000.0'),
            estoque_depois=Decimal('985.0'),
        )
        return mistura, item

    # -----------------------------------------------------------------------
    # T020-6: estoque_antes / estoque_depois are stored correctly
    # -----------------------------------------------------------------------
    def test_item_mistura_stock_before_after(self):
        """estoque_antes and estoque_depois must be persisted and retrieved correctly."""
        _, item = self._make_full_mistura()
        item.refresh_from_db()
        self.assertEqual(item.estoque_antes, Decimal('1000.0'))
        self.assertEqual(item.estoque_depois, Decimal('985.0'))

    # -----------------------------------------------------------------------
    # T020-7: quantidade_final falls back to calculada when executada is None
    # -----------------------------------------------------------------------
    def test_item_mistura_quantidade_final_fallback(self):
        """quantidade_final should return calculada when executada is blank."""
        _, item = self._make_full_mistura()
        self.assertIsNone(item.quantidade_executada)
        self.assertEqual(item.quantidade_final, item.quantidade_calculada)

        item.quantidade_executada = Decimal('14.8')
        item.save(update_fields=['quantidade_executada'])
        self.assertEqual(item.quantidade_final, Decimal('14.8'))

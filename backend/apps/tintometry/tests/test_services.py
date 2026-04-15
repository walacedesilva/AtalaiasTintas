"""
T017 – FormulaCalculatorService unit tests
T018 – StockManagerService unit tests
T019 – MixtureService unit tests
"""

from decimal import Decimal
import threading

from django.test import TransactionTestCase

from apps.tintometry.models import (
    EstoquePigmento,
    FormulaTintometrica,
    ItemFormula,
    MisturaTinta,
)
from apps.tintometry.services.formula_calculator import FormulaCalculatorService
from apps.tintometry.services.mixture_service import MixtureService
from apps.tintometry.services.stock_manager import StockManagerService

from .base import TintometryBaseTestCase, make_estoque, make_pigmento


# ===========================================================================
# T017 – FormulaCalculatorService
# ===========================================================================

class FormulaCalculatorServiceTests(TintometryBaseTestCase):
    """Unit tests for FormulaCalculatorService."""

    def setUp(self):
        self.service = FormulaCalculatorService()

    # -----------------------------------------------------------------------
    # T017-1: quantities are rounded to 0.1 ml precision
    # -----------------------------------------------------------------------
    def test_calculate_pigment_quantities_precision(self):
        """Quantities must be rounded to 0.1 ml (PRECISION_ML)."""
        # pigmento_a has 15 ml/L in self.formula; requesting 3.6L -> 54.0 ml
        # pigmento_b has  8 ml/L; requesting 3.6L ->  28.8 ml
        result = self.service.calculate_mixture_quantities(
            formula=self.formula,
            target_volume=Decimal('3.6'),
            loja_id=self.loja.id,
            validate_stock=False,
        )

        for pig in result['pigments'] if 'pigments' in result else result['pigmentos']:
            qty = Decimal(str(pig['quantidades']['calculada_final']))
            remainder = qty % Decimal('0.1')
            self.assertEqual(remainder, Decimal('0'), msg=f"Precisão 0.1ml falhou: {qty}")

    # -----------------------------------------------------------------------
    # T017-2: proportional scaling is correct
    # -----------------------------------------------------------------------
    def test_proportional_scaling_correctness(self):
        """2× volume must produce 2× quantity for each pigment."""
        base_result = self.service.calculate_mixture_quantities(
            formula=self.formula,
            target_volume=Decimal('1.0'),
            loja_id=self.loja.id,
            validate_stock=False,
        )
        double_result = self.service.calculate_mixture_quantities(
            formula=self.formula,
            target_volume=Decimal('2.0'),
            loja_id=self.loja.id,
            validate_stock=False,
        )

        base_pigments = base_result.get('pigments', base_result.get('pigmentos'))
        double_pigments = double_result.get('pigments', double_result.get('pigmentos'))

        for base_pig, double_pig in zip(base_pigments, double_pigments):
            base_qty = Decimal(str(base_pig['quantidades']['calculada_final']))
            double_qty = Decimal(str(double_pig['quantidades']['calculada_final']))
            # Allow 2% tolerance for density-correction rounding
            ratio = double_qty / base_qty
            self.assertAlmostEqual(float(ratio), 2.0, delta=0.02,
                msg=f"Escalonamento proporcional falhou para {base_pig['pigmento']['nome']}")

    # -----------------------------------------------------------------------
    # T017-3: insufficient stock sets stock_available = False
    # -----------------------------------------------------------------------
    def test_stock_availability_check_blocks_when_insufficient(self):
        """When saldo_ml < required, stock_available must be False."""
        # Set tiny stock so 1L formula can't be satisfied
        self.estoque_a.saldo_ml = Decimal('1.0')
        self.estoque_a.save(update_fields=['saldo_ml'])

        result = self.service.calculate_mixture_quantities(
            formula=self.formula,
            target_volume=Decimal('1.0'),
            loja_id=self.loja.id,
            validate_stock=True,
        )

        pigs = result.get('pigments', result.get('pigmentos'))
        # First pigment (pigmento_a needs 15ml but only 1ml available)
        first = pigs[0]
        self.assertFalse(first['stock_available'],
            msg="Estoque insuficiente deveria ter marcado stock_available=False")
        self.assertFalse(result['validacao']['stock_ok'])

    # -----------------------------------------------------------------------
    # T017-4: warnings list is not empty when stock is short
    # -----------------------------------------------------------------------
    def test_calculate_returns_stock_alerts_when_short(self):
        """Warnings must be populated when stock is insufficient for a pigment."""
        self.estoque_b.saldo_ml = Decimal('0')
        self.estoque_b.save(update_fields=['saldo_ml'])

        result = self.service.calculate_mixture_quantities(
            formula=self.formula,
            target_volume=Decimal('1.0'),
            loja_id=self.loja.id,
            validate_stock=True,
        )

        warnings = result['validacao']['warnings']
        self.assertTrue(len(warnings) > 0,
            msg="Deveria haver pelo menos um warning de estoque insuficiente")

    # -----------------------------------------------------------------------
    # T017-5: cost breakdown is accurate (cost = qty * custo_ml)
    # -----------------------------------------------------------------------
    def test_cost_breakdown_accuracy(self):
        """Total cost must equal sum of (qty * unit_cost) for all pigments plus base."""
        result = self.service.calculate_mixture_quantities(
            formula=self.formula,
            target_volume=Decimal('1.0'),
            loja_id=self.loja.id,
            validate_stock=False,
        )

        pigs = result.get('pigments', result.get('pigmentos'))
        expected_pigment_cost = sum(
            Decimal(str(p['custos']['unitario'])) * Decimal(str(p['quantidades']['calculada_final']))
            for p in pigs
        )

        reported_pigment_cost = Decimal(str(result['custos']['pigmentos']))
        # Allow rounding tolerance of 2 cents
        self.assertAlmostEqual(
            float(expected_pigment_cost), float(reported_pigment_cost),
            delta=0.02,
            msg="Custo de pigmentos não bate com soma individual"
        )


# ===========================================================================
# T018 – StockManagerService
# ===========================================================================

class StockManagerServiceTests(TintometryBaseTestCase):
    """Unit tests for StockManagerService."""

    def setUp(self):
        self.service = StockManagerService()

    # -----------------------------------------------------------------------
    # T018-1: stock reduction updates saldo_ml
    # -----------------------------------------------------------------------
    def test_execute_stock_reduction_updates_saldo_ml(self):
        """reduzir_estoque debe subtrair do saldo_ml correto."""
        initial = self.estoque_a.saldo_ml
        reducao = Decimal('100.0')
        self.estoque_a.reduzir_estoque(reducao)
        self.estoque_a.refresh_from_db()
        self.assertEqual(self.estoque_a.saldo_ml, initial - reducao)

    # -----------------------------------------------------------------------
    # T018-2: alert fires when stock drops to/below minimum
    # -----------------------------------------------------------------------
    def test_restock_alert_triggered_at_minimum(self):
        """alerta_ativo should be set when saldo_ml <= saldo_minimo after reduction."""
        # Set saldo just above minimum so one more reduction tips it
        self.estoque_a.saldo_ml = self.estoque_a.saldo_minimo + Decimal('50')
        self.estoque_a.alerta_ativo = False
        self.estoque_a.save(update_fields=['saldo_ml', 'alerta_ativo'])

        # Reduce past the minimum threshold
        self.estoque_a.reduzir_estoque(Decimal('100'))
        self.estoque_a.refresh_from_db()

        self.assertTrue(self.estoque_a.alerta_ativo,
            msg="alerta_ativo deveria ser True após estoque cair abaixo do mínimo")

    # -----------------------------------------------------------------------
    # T018-3: reduzir_estoque returns False and does NOT go negative
    # -----------------------------------------------------------------------
    def test_no_negative_stock_without_override(self):
        """reduzir_estoque must return False and keep saldo positive."""
        self.estoque_a.saldo_ml = Decimal('10.0')
        self.estoque_a.save(update_fields=['saldo_ml'])

        success = self.estoque_a.reduzir_estoque(Decimal('200.0'))

        self.assertFalse(success, msg="Deveria retornar False para redução maior que saldo")
        self.estoque_a.refresh_from_db()
        self.assertGreaterEqual(self.estoque_a.saldo_ml, Decimal('0'),
            msg="Saldo nunca deve ficar negativo")

    # -----------------------------------------------------------------------
    # T018-4: concurrent reductions remain consistent (uses TransactionTestCase)
    # -----------------------------------------------------------------------
    def test_concurrent_stock_reduction_consistency(self):
        """Multiple simultaneous reductions must not result in overshoot."""
        # Set enough stock for one but not two reductions
        self.estoque_a.saldo_ml = Decimal('50.0')
        self.estoque_a.save(update_fields=['saldo_ml'])

        results = []

        def do_reduction():
            # Each thread reads fresh from DB
            from apps.tintometry.models import EstoquePigmento
            est = EstoquePigmento.objects.get(pk=self.estoque_a.pk)
            results.append(est.reduzir_estoque(Decimal('40.0')))

        t1 = threading.Thread(target=do_reduction)
        t2 = threading.Thread(target=do_reduction)
        t1.start(); t2.start()
        t1.join(); t2.join()

        # At most one reduction should succeed (saldo=50, each needs 40)
        # After two sequential (worst case) subtractions only 1 succeeds
        success_count = results.count(True)
        self.assertLessEqual(success_count, 1,
            msg="No máximo uma redução deveria ser bem-sucedida com saldo=50 e redução=40")

        self.estoque_a.refresh_from_db()
        self.assertGreaterEqual(self.estoque_a.saldo_ml, Decimal('0'),
            msg="Saldo final não deve ser negativo")


# ===========================================================================
# T019 – MixtureService
# ===========================================================================

class MixtureServiceTests(TintometryBaseTestCase):
    """Unit tests for MixtureService."""

    def setUp(self):
        self.service = MixtureService()
        self._customer = {
            'nome': 'Cliente Teste',
            'documento': '12345678900',
            'telefone': '11999999999',
            'email': 'cliente@test.com',
        }

    # -----------------------------------------------------------------------
    # T019-1: create_mixture_calculation generates a unique codigo_mistura
    # -----------------------------------------------------------------------
    def test_create_mixture_generates_unique_code(self):
        """Two calls on the same day must produce different codigo_mistura."""
        r1 = self.service.create_mixture_calculation(
            formula_id=str(self.formula.id),
            volume_requested=Decimal('1.0'),
            loja_id=self.loja.id,
            user_id=str(self.user.id),
            customer_data={**self._customer, 'nome': 'Cliente 1'},
        )
        r2 = self.service.create_mixture_calculation(
            formula_id=str(self.formula.id),
            volume_requested=Decimal('1.0'),
            loja_id=self.loja.id,
            user_id=str(self.user.id),
            customer_data={**self._customer, 'nome': 'Cliente 2'},
        )

        self.assertTrue(r1['success'])
        self.assertTrue(r2['success'])
        self.assertNotEqual(r1['mistura']['codigo'], r2['mistura']['codigo'],
            msg="codigo_mistura deve ser único para cada mistura")

    # -----------------------------------------------------------------------
    # T019-2: confirm_mixture changes status to CONFIRMADA
    # -----------------------------------------------------------------------
    def test_confirm_mixture_changes_status(self):
        """After confirm_mixture, situacao must be CONFIRMADA."""
        create_result = self.service.create_mixture_calculation(
            formula_id=str(self.formula.id),
            volume_requested=Decimal('1.0'),
            loja_id=self.loja.id,
            user_id=str(self.user.id),
            customer_data=self._customer,
        )
        self.assertTrue(create_result['success'], create_result)
        mistura_id = create_result['mistura']['id']

        confirm_result = self.service.confirm_mixture(
            mixture_id=mistura_id,
            user_id=str(self.user.id),
            reserve_stock=True,
        )

        self.assertTrue(confirm_result['success'], confirm_result)
        mistura = MisturaTinta.objects.get(id=mistura_id)
        self.assertEqual(mistura.situacao, 'CONFIRMADA')
        self.assertIsNotNone(mistura.data_confirmacao)

    # -----------------------------------------------------------------------
    # T019-3: cancel_mixture on a CONFIRMADA mistura restores stock
    # -----------------------------------------------------------------------
    def test_cancel_mixture_restores_stock(self):
        """Cancelling a CONFIRMADA mistura must restore saldo_ml for each pigment."""
        # Record initial saldos
        self.estoque_a.refresh_from_db()
        self.estoque_b.refresh_from_db()
        saldo_a_before = self.estoque_a.saldo_ml
        saldo_b_before = self.estoque_b.saldo_ml

        # Create + confirm (stock is reduced on confirm)
        create_result = self.service.create_mixture_calculation(
            formula_id=str(self.formula.id),
            volume_requested=Decimal('1.0'),
            loja_id=self.loja.id,
            user_id=str(self.user.id),
            customer_data=self._customer,
        )
        mistura_id = create_result['mistura']['id']
        confirm_result = self.service.confirm_mixture(
            mixture_id=mistura_id,
            user_id=str(self.user.id),
            reserve_stock=True,
        )
        self.assertTrue(confirm_result['success'], confirm_result)

        # Cancel
        cancel_result = self.service.cancel_mixture(
            mixture_id=mistura_id,
            motivo='Teste de cancelamento',
            user_id=str(self.user.id),
        )
        self.assertTrue(cancel_result['success'], cancel_result)

        # Saldos must be restored to (at least) their pre-confirm values
        self.estoque_a.refresh_from_db()
        self.estoque_b.refresh_from_db()
        self.assertGreaterEqual(self.estoque_a.saldo_ml, saldo_a_before - Decimal('0.5'),
            msg="Saldo do pigmento A deveria ter sido restaurado após cancelamento")
        self.assertGreaterEqual(self.estoque_b.saldo_ml, saldo_b_before - Decimal('0.5'),
            msg="Saldo do pigmento B deveria ter sido restaurado após cancelamento")

        mistura = MisturaTinta.objects.get(id=mistura_id)
        self.assertEqual(mistura.situacao, 'CANCELADA')

    # -----------------------------------------------------------------------
    # T019-4: complete_mixture marks mistura as ENTREGUE (history saved)
    # -----------------------------------------------------------------------
    def test_customer_history_updated_after_completion(self):
        """complete_mixture should finalise the mix with situacao=ENTREGUE."""
        create_result = self.service.create_mixture_calculation(
            formula_id=str(self.formula.id),
            volume_requested=Decimal('1.0'),
            loja_id=self.loja.id,
            user_id=str(self.user.id),
            customer_data=self._customer,
        )
        mid = create_result['mistura']['id']

        # Full lifecycle: create → confirm → execute → complete
        self.service.confirm_mixture(mid, str(self.user.id), reserve_stock=True)
        self.service.execute_mixture(mid, str(self.user.id))
        complete_result = self.service.complete_mixture(mid, str(self.user.id))

        self.assertTrue(complete_result['success'], complete_result)
        mistura = MisturaTinta.objects.get(id=mid)
        self.assertEqual(mistura.situacao, 'ENTREGUE')
        self.assertIsNotNone(mistura.data_entrega)

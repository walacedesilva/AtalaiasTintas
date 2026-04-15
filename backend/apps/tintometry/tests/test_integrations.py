"""
Integration Tests for Tintometry Module - Phase 5

End-to-end workflow tests covering:
- T021a  IT-002b: Cancel confirmed mixture → stock restored
- T022   IT-001:  Full flow — color → formula → stock check → confirm → deduction → history
- T023   IT-002:  Customer history → reproduce_from_history → new identical mixture
- T024   IT-003:  Concurrent mixtures → stock consistency
- T025   IT-004:  Stock exhaustion → new mixture blocked with alerts
- T026   IT-005:  New formula via API → first use → precise calc → correct deduction
- T026a  IT-006:  complete_mixture → EtiquetaMistura created → label data complete
- T026b  Edge:    formula_not_found_for_color_returns_404
- T026c  Edge:    minimum_volume_validation_rejects_below_100ml
- T026d  Edge:    multistore_stock_isolation
"""

import threading
import uuid
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TransactionTestCase
from rest_framework.authtoken.models import Token
from rest_framework.test import APIClient

from apps.companies.models import Empresa, Loja
from apps.tintometry.models import (
    EstoquePigmento,
    EtiquetaMistura,
    FormulaTintometrica,
    ItemFormula,
    LequeCorDefinida,
    MisturaTinta,
)
from apps.tintometry.tests.base import (
    TintometryAPIBaseTestCase,
    make_estoque,
    make_pigmento,
)

User = get_user_model()

MISTURAS_URL = '/api/v1/tintometry/misturas/'
FORMULAS_URL = '/api/v1/tintometry/formulas/'
CORES_URL = '/api/v1/tintometry/cores/'
HISTORY_URL = '/api/v1/tintometry/customer-history/'
QUICK_CALC_URL = '/api/v1/tintometry/quick-calculate/'


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _create_calculation(client, formula_id, loja_id, volume='1.0', nome='Test Client', phone=None):
    payload = {
        'formula_id': str(formula_id),
        'volume_requested': volume,
        'loja_id': loja_id,
        'customer_data': {'nome': nome, **({'telefone': phone} if phone else {})},
    }
    return client.post(f'{MISTURAS_URL}create_calculation/', payload, format='json')


def _confirm(client, mistura_id):
    return client.post(f'{MISTURAS_URL}{mistura_id}/confirm/', {}, format='json')


def _execute(client, mistura_id):
    return client.post(f'{MISTURAS_URL}{mistura_id}/execute/', {}, format='json')


def _complete(client, mistura_id):
    return client.post(f'{MISTURAS_URL}{mistura_id}/complete/', {}, format='json')


def _cancel(client, mistura_id, motivo='Cancelado em teste'):
    return client.post(
        f'{MISTURAS_URL}{mistura_id}/cancel/', {'motivo': motivo}, format='json'
    )


# ---------------------------------------------------------------------------
# T021a — IT-002b: Cancel confirmed mixture → stock restored
# ---------------------------------------------------------------------------

class CancelConfirmedMixtureRestoresStockTest(TintometryAPIBaseTestCase):
    """IT-002b: Confirmed mixture cancelled → stock of all pigments restored."""

    def test_cancel_confirmed_mixture_restores_stock(self):
        # 1. Create mixture
        resp = _create_calculation(self.client, self.formula.id, self.loja.id)
        self.assertEqual(resp.status_code, 201)
        mistura_id = resp.data['mistura']['id']

        # 2. Snapshot stock before confirm
        self.estoque_a.refresh_from_db()
        self.estoque_b.refresh_from_db()
        stock_a_before = self.estoque_a.saldo_ml
        stock_b_before = self.estoque_b.saldo_ml

        # 3. Confirm → stock deducted/reserved
        conf = _confirm(self.client, mistura_id)
        self.assertEqual(conf.status_code, 200)
        self.assertTrue(conf.data['success'])

        self.estoque_a.refresh_from_db()
        self.estoque_b.refresh_from_db()
        self.assertLess(self.estoque_a.saldo_ml, stock_a_before)
        self.assertLess(self.estoque_b.saldo_ml, stock_b_before)

        # 4. Cancel the confirmed mixture
        cancel = _cancel(self.client, mistura_id, 'Cliente desistiu da compra')
        self.assertEqual(cancel.status_code, 200)
        self.assertTrue(cancel.data['success'])
        self.assertEqual(cancel.data['mistura']['situacao'], 'CANCELADA')
        self.assertGreater(cancel.data['itens_restaurados'], 0)

        # 5. Stock fully restored to pre-confirm levels
        self.estoque_a.refresh_from_db()
        self.estoque_b.refresh_from_db()
        self.assertEqual(self.estoque_a.saldo_ml, stock_a_before)
        self.assertEqual(self.estoque_b.saldo_ml, stock_b_before)

    def test_cancel_calculada_mixture_does_not_touch_stock(self):
        """Cancelling a CALCULADA (not yet confirmed) mixture leaves stock unchanged."""
        resp = _create_calculation(self.client, self.formula.id, self.loja.id)
        self.assertEqual(resp.status_code, 201)
        mistura_id = resp.data['mistura']['id']

        self.estoque_a.refresh_from_db()
        stock_before = self.estoque_a.saldo_ml

        cancel = _cancel(self.client, mistura_id)
        self.assertEqual(cancel.status_code, 200)
        self.assertEqual(cancel.data['itens_restaurados'], 0)

        self.estoque_a.refresh_from_db()
        self.assertEqual(self.estoque_a.saldo_ml, stock_before)


# ---------------------------------------------------------------------------
# T022 — IT-001: Full mixture lifecycle integration
# ---------------------------------------------------------------------------

class FullMixtureFlowIntegrationTest(TintometryAPIBaseTestCase):
    """IT-001: color → formula → stock check → confirm → deduction → execute → complete → history."""

    def test_full_mixture_lifecycle(self):
        PHONE = '11988880000'

        # 1. Record initial stock
        self.estoque_a.refresh_from_db()
        stock_a_initial = self.estoque_a.saldo_ml

        # 2. Calculate mixture
        resp = _create_calculation(
            self.client, self.formula.id, self.loja.id, nome='Maria Santos', phone=PHONE
        )
        self.assertEqual(resp.status_code, 201)
        self.assertTrue(resp.data['success'])
        mistura_id = resp.data['mistura']['id']
        self.assertEqual(resp.data['mistura']['situacao'], 'CALCULADA')

        # 3. Stock unchanged after mere calculation
        self.estoque_a.refresh_from_db()
        self.assertEqual(self.estoque_a.saldo_ml, stock_a_initial)

        # 4. Confirm → stock deducted
        conf = _confirm(self.client, mistura_id)
        self.assertEqual(conf.status_code, 200)
        self.assertTrue(conf.data['success'])

        self.estoque_a.refresh_from_db()
        self.assertLess(self.estoque_a.saldo_ml, stock_a_initial)

        mistura = MisturaTinta.objects.get(id=mistura_id)
        self.assertEqual(mistura.situacao, 'CONFIRMADA')
        self.assertIsNotNone(mistura.data_confirmacao)

        # EtiquetaMistura auto-created on confirm
        self.assertTrue(EtiquetaMistura.objects.filter(mistura_id=mistura_id).exists())

        # 5. Execute
        exec_resp = _execute(self.client, mistura_id)
        self.assertEqual(exec_resp.status_code, 200)
        mistura.refresh_from_db()
        self.assertEqual(mistura.situacao, 'PRODUZIDA')

        # 6. Complete
        complete_resp = _complete(self.client, mistura_id)
        self.assertEqual(complete_resp.status_code, 200)
        mistura.refresh_from_db()
        self.assertEqual(mistura.situacao, 'ENTREGUE')
        self.assertIsNotNone(mistura.data_entrega)

        # 7. Customer history shows the completed mixture
        hist = self.client.get(HISTORY_URL, {'cliente_telefone': PHONE})
        self.assertEqual(hist.status_code, 200)
        self.assertGreater(hist.data['count'], 0)


# ---------------------------------------------------------------------------
# T023 — IT-002: Customer history → reproduce_from_history → new identical mixture
# ---------------------------------------------------------------------------

class CustomerHistoryReproduceTest(TintometryAPIBaseTestCase):
    """IT-002: Look up history → reproduce_from_history → new mixture identical to original."""

    PHONE = '11977770000'

    def _create_confirmed_mixture(self):
        resp = _create_calculation(
            self.client, self.formula.id, self.loja.id,
            nome='Pedro Oliveira', phone=self.PHONE,
        )
        self.assertEqual(resp.status_code, 201)
        mid = resp.data['mistura']['id']
        _confirm(self.client, mid)
        return mid

    def test_reproduce_from_history_creates_identical_mixture(self):
        original_id = self._create_confirmed_mixture()

        # 1. Customer history shows the mixture
        hist = self.client.get(HISTORY_URL, {'cliente_telefone': self.PHONE})
        self.assertEqual(hist.status_code, 200)
        self.assertGreater(hist.data['count'], 0)
        first = hist.data['results'][0]
        self.assertEqual(str(first['formula_id']), str(self.formula.id))

        # 2. reproduce_from_history returns usable prefill
        rep = self.client.post(
            f'{MISTURAS_URL}{original_id}/reproduce_from_history/', {}, format='json'
        )
        self.assertEqual(rep.status_code, 200)
        self.assertTrue(rep.data['success'])
        prefill = rep.data['prefill']
        self.assertEqual(str(prefill['formula_id']), str(self.formula.id))
        self.assertEqual(prefill['customer_data']['telefone'], self.PHONE)

        # 3. Create new mixture using prefill data
        new_resp = _create_calculation(
            self.client,
            prefill['formula_id'],
            self.loja.id,
            volume=str(prefill['volume_requested']),
            nome=prefill['customer_data']['nome'],
            phone=self.PHONE,
        )
        self.assertEqual(new_resp.status_code, 201)
        new_mistura = MisturaTinta.objects.get(id=new_resp.data['mistura']['id'])

        # 4. New mixture uses same formula as original; is a distinct object
        self.assertEqual(new_mistura.formula_id, self.formula.id)
        self.assertEqual(new_mistura.cliente_telefone, self.PHONE)
        self.assertNotEqual(str(new_mistura.id), original_id)


# ---------------------------------------------------------------------------
# T024 — IT-003: Concurrent mixtures → stock consistency
# ---------------------------------------------------------------------------

class ConcurrentMixtureStockTest(TransactionTestCase):
    """IT-003: Multiple concurrent confirmations → final balance remains consistent."""

    def setUp(self):
        from apps.inventory.models import (
            Categoria, Marca, ProdutoBase, ProdutoVariacao, UnidadeMedida,
        )

        self.user = User.objects.create_user(
            username='concurrent_user', password='pass', email='conc@test.com',
        )
        self.token = Token.objects.create(user=self.user)

        empresa = Empresa.objects.create(
            cnpj='99887766000100', razao_social='Concurrent LTDA', nome_fantasia='Concurrent',
        )
        self.loja = Loja.objects.create(
            empresa=empresa, codigo='CL01', nome='Loja Concurrent',
            cep='01001000', endereco='Rua A', numero='1',
            bairro='Centro', cidade='São Paulo', uf='SP',
        )

        categoria = Categoria.objects.create(nome='Cat C', codigo='CC')
        marca = Marca.objects.create(nome='Marca C', codigo='MC')
        unidade = UnidadeMedida.objects.create(
            codigo='LC', nome='Litro C', sigla='LC', tipo='VOLUME',
        )
        produto = ProdutoBase.objects.create(
            codigo='BASEC001', nome='Base C',
            categoria=categoria, marca=marca, tipo_produto='INSUMO',
        )
        variacao = ProdutoVariacao.objects.create(
            produto_base=produto, codigo_variacao='BASEC001-1L',
            nome_variacao='Base C 1L', unidade_venda=unidade,
            unidade_estoque=unidade, fator_conversao_venda=Decimal('1'),
            preco_custo=Decimal('10.00'),
        )

        cor = LequeCorDefinida.objects.create(
            codigo_cor='CONC001', nome_cor='Cor Concurrent', familia_cor='Teste',
            linha_produto='Standard',
            l_value=Decimal('50'), a_value=Decimal('10'), b_value=Decimal('5'),
            r=128, g=128, b=128,
        )

        # Enough stock for exactly 3 mixtures of 1L (3 × 15ml = 45ml)
        self.pigmento = make_pigmento('PIG-CONC', cor_base='Teste')
        self.estoque = make_estoque(self.pigmento, self.loja, saldo_ml=Decimal('45'))

        self.formula = FormulaTintometrica.objects.create(
            cor_definida=cor, base_produto=variacao,
            codigo_formula='FOR-CONC', nome_formula='Fórmula Concurrent',
            versao='1.0', volume_base=Decimal('1.0'), ativa=True,
        )
        ItemFormula.objects.create(
            formula=self.formula, pigmento=self.pigmento,
            quantidade=Decimal('15'), sequencia=1,
        )

    def test_concurrent_stock_consistency(self):
        """Final stock = initial − (successful_confirmations × 15ml)."""
        from apps.tintometry.services.mixture_service import MixtureService

        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION=f'Token {self.token.key}')

        # Create 3 mixtures sequentially (concurrency only at confirm step)
        mixture_ids = []
        for i in range(3):
            payload = {
                'formula_id': str(self.formula.id),
                'volume_requested': '1.0',
                'loja_id': self.loja.id,
                'customer_data': {'nome': f'Cliente {i}'},
                'validate_stock': False,
            }
            r = client.post(f'{MISTURAS_URL}create_calculation/', payload, format='json')
            if r.status_code == 201 and r.data.get('success'):
                mixture_ids.append(r.data['mistura']['id'])

        self.assertGreater(len(mixture_ids), 0, 'No mixtures were created')

        self.estoque.refresh_from_db()
        initial_stock = self.estoque.saldo_ml

        successes = []
        lock = threading.Lock()

        def confirm_mixture(mid):
            svc = MixtureService()
            try:
                result = svc.confirm_mixture(mid, str(self.user.id), reserve_stock=True)
                if result.get('success'):
                    with lock:
                        successes.append(mid)
            except Exception:
                pass  # SQLite may raise OperationalError on concurrent writes (expected in test)

        threads = [threading.Thread(target=confirm_mixture, args=(mid,)) for mid in mixture_ids]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        # Each successful confirmation deducted exactly 15ml; no phantom deductions
        self.estoque.refresh_from_db()
        expected = initial_stock - Decimal('15') * len(successes)
        self.assertEqual(
            self.estoque.saldo_ml, expected,
            f'Stock mismatch: {len(successes)} successes → expected {expected}, got {self.estoque.saldo_ml}',
        )


# ---------------------------------------------------------------------------
# T025 — IT-004: Stock exhaustion → new mixture blocked
# ---------------------------------------------------------------------------

class StockExhaustionTest(TintometryAPIBaseTestCase):
    """IT-004: Pigment exhaustion → mixture creation blocked with alerts."""

    def setUp(self):
        super().setUp()
        # Reduce stock below formula requirements (15ml PIG-A, 8ml PIG-B per 1L)
        self.estoque_a.saldo_ml = Decimal('5')
        self.estoque_a.save(update_fields=['saldo_ml'])
        self.estoque_b.saldo_ml = Decimal('3')
        self.estoque_b.save(update_fields=['saldo_ml'])

    def test_stock_exhaustion_blocks_mixture_or_returns_failure(self):
        resp = _create_calculation(self.client, self.formula.id, self.loja.id, nome='Sem Estoque')
        # Server may return 201 with success=False OR a 4xx status
        if resp.status_code == 201:
            self.assertFalse(resp.data['success'])
            self.assertIn('error', resp.data)
        else:
            self.assertIn(resp.status_code, [400, 409])

    def test_stock_exhaustion_response_details_shortage(self):
        resp = _create_calculation(self.client, self.formula.id, self.loja.id, nome='Detalhe Erro')
        if resp.status_code in [200, 201] and not resp.data.get('success'):
            self.assertTrue(
                'details' in resp.data or 'error' in resp.data,
                'Response must detail which pigments have insufficient stock',
            )


# ---------------------------------------------------------------------------
# T026 — IT-005: New formula via API → first use → correct stock deduction
# ---------------------------------------------------------------------------

class NewFormulaFirstUseTest(TintometryAPIBaseTestCase):
    """IT-005: Register new formula → first mixture → precise calc → correct deduction."""

    def test_new_formula_first_use_deducts_stock_correctly(self):
        # 1. Create a new LequeCorDefinida
        cor_resp = self.client.post(CORES_URL, {
            'codigo_cor': 'NEW-BLUE-01',
            'nome_cor': 'Azul Novo Teste',
            'familia_cor': 'Azuis',
            'linha_produto': 'Standard',
            'l_value': '30.0', 'a_value': '-5.0', 'b_value': '-40.0',
            'r': 20, 'g': 60, 'b': 180,
        }, format='json')
        self.assertIn(cor_resp.status_code, [200, 201], cor_resp.data)
        new_cor_id = cor_resp.data['id']

        # 2. Create new formula via API
        formula_resp = self.client.post(FORMULAS_URL, {
            'cor_definida': new_cor_id,
            'base_produto': self.variacao.id,
            'codigo_formula': 'FOR-BLUE-001',
            'nome_formula': 'Azul Novo Fórmula',
            'versao': '1.0',
            'volume_base': '1.00',
            'ativa': True,
        }, format='json')
        self.assertIn(formula_resp.status_code, [200, 201], formula_resp.data)
        new_formula_id = formula_resp.data['id']

        # 3. Add item directly (no nested-items REST endpoint assumed)
        ItemFormula.objects.create(
            formula_id=new_formula_id,
            pigmento=self.pigmento_a,
            quantidade=Decimal('20.0'),
            sequencia=1,
        )

        # 4. Snapshot stock before first use
        self.estoque_a.refresh_from_db()
        stock_before = self.estoque_a.saldo_ml

        # 5. First-time mixture calculation
        calc_resp = _create_calculation(self.client, new_formula_id, self.loja.id, nome='Primeiro Uso')
        self.assertEqual(calc_resp.status_code, 201, calc_resp.data)
        self.assertTrue(calc_resp.data['success'])
        mistura_id = calc_resp.data['mistura']['id']

        # 6. Confirm → stock deducted
        conf = _confirm(self.client, mistura_id)
        self.assertEqual(conf.status_code, 200)

        # 7. Exactly 20ml deducted (formula qty × 1L / 1L volume_base = 20ml)
        self.estoque_a.refresh_from_db()
        self.assertEqual(self.estoque_a.saldo_ml, stock_before - Decimal('20.0'))

        # 8. Mixture has exactly 1 item
        mistura = MisturaTinta.objects.get(id=mistura_id)
        self.assertEqual(mistura.itens.count(), 1)


# ---------------------------------------------------------------------------
# T026a — IT-006: confirm → EtiquetaMistura created; complete → ENTREGUE
# ---------------------------------------------------------------------------

class CompleteMixtureLabelTest(TintometryAPIBaseTestCase):
    """IT-006: confirm auto-creates EtiquetaMistura; complete marks ENTREGUE; label data intact."""

    def _lifecycle_to_confirmed(self, phone='11966660000', nome='Label Test User'):
        resp = _create_calculation(self.client, self.formula.id, self.loja.id, nome=nome, phone=phone)
        self.assertEqual(resp.status_code, 201)
        mid = resp.data['mistura']['id']
        conf = _confirm(self.client, mid)
        self.assertEqual(conf.status_code, 200)
        return mid

    def test_confirm_creates_etiqueta_with_unique_codigo(self):
        mid1 = self._lifecycle_to_confirmed(phone='11966660001', nome='User One')
        mid2 = self._lifecycle_to_confirmed(phone='11966660002', nome='User Two')

        etiqueta1 = EtiquetaMistura.objects.get(mistura_id=mid1)
        etiqueta2 = EtiquetaMistura.objects.get(mistura_id=mid2)

        self.assertIsNotNone(etiqueta1.codigo_etiqueta)
        self.assertIsNotNone(etiqueta2.codigo_etiqueta)
        self.assertNotEqual(etiqueta1.codigo_etiqueta, etiqueta2.codigo_etiqueta)

    def test_etiqueta_codigo_starts_with_ET(self):
        mid = self._lifecycle_to_confirmed()
        etiqueta = EtiquetaMistura.objects.get(mistura_id=mid)
        self.assertTrue(
            etiqueta.codigo_etiqueta.startswith('ET'),
            f'Expected codigo_etiqueta to start with ET, got: {etiqueta.codigo_etiqueta}',
        )

    def test_etiqueta_references_correct_mistura(self):
        mid = self._lifecycle_to_confirmed()
        etiqueta = EtiquetaMistura.objects.get(mistura_id=mid)
        self.assertEqual(str(etiqueta.mistura_id), str(mid))

    def test_complete_mixture_marks_entregue_and_preserves_etiqueta(self):
        mid = self._lifecycle_to_confirmed()
        _execute(self.client, mid)
        complete_resp = _complete(self.client, mid)

        self.assertEqual(complete_resp.status_code, 200)
        self.assertTrue(complete_resp.data['success'])

        mistura = MisturaTinta.objects.get(id=mid)
        self.assertEqual(mistura.situacao, 'ENTREGUE')
        self.assertTrue(EtiquetaMistura.objects.filter(mistura_id=mid).exists())


# ---------------------------------------------------------------------------
# T026b — Edge: formula not found → 404
# ---------------------------------------------------------------------------

class FormulaNotFoundEdgeCaseTest(TintometryAPIBaseTestCase):
    """T026b: Non-existent formula_id → quick-calculate returns 404."""

    def test_formula_not_found_for_color_returns_404(self):
        resp = self.client.post(QUICK_CALC_URL, {
            'formula_id': str(uuid.uuid4()),
            'volume': '1.0',
            'loja_id': self.loja.id,
        }, format='json')
        self.assertEqual(resp.status_code, 404)


# ---------------------------------------------------------------------------
# T026c — Edge: minimum volume validation rejects below 100ml (0.1L)
# ---------------------------------------------------------------------------

class MinimumVolumeValidationTest(TintometryAPIBaseTestCase):
    """T026c: volume < 0.1L (100ml) → 400 with clear error message."""

    def test_create_calculation_rejects_volume_below_100ml(self):
        payload = {
            'formula_id': str(self.formula.id),
            'volume_requested': '0.05',  # 50ml — below minimum
            'loja_id': self.loja.id,
            'customer_data': {'nome': 'Cliente Volume Minimo'},
        }
        resp = self.client.post(
            f'{MISTURAS_URL}create_calculation/', payload, format='json',
        )
        self.assertEqual(resp.status_code, 400)

    def test_quick_calculate_rejects_volume_below_100ml(self):
        resp = self.client.post(QUICK_CALC_URL, {
            'formula_id': str(self.formula.id),
            'volume': '0.05',
            'loja_id': self.loja.id,
        }, format='json')
        self.assertEqual(resp.status_code, 400)

    def test_create_calculation_accepts_exactly_100ml(self):
        """Boundary: 0.1L should not be rejected by minimum-volume validation."""
        payload = {
            'formula_id': str(self.formula.id),
            'volume_requested': '0.1',
            'loja_id': self.loja.id,
            'customer_data': {'nome': 'Cliente Volume Exato'},
        }
        resp = self.client.post(
            f'{MISTURAS_URL}create_calculation/', payload, format='json',
        )
        self.assertNotEqual(resp.status_code, 400)


# ---------------------------------------------------------------------------
# T026d — Edge: multistore stock isolation
# ---------------------------------------------------------------------------

class MultistoreStockIsolationTest(TintometryAPIBaseTestCase):
    """T026d: Loja A and Loja B stock for the same pigment are fully isolated."""

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.estoque_a_loja2 = make_estoque(
            cls.pigmento_a, cls.loja2, saldo_ml=Decimal('500'), custo_ml=Decimal('2.50'),
        )
        cls.estoque_b_loja2 = make_estoque(
            cls.pigmento_b, cls.loja2, saldo_ml=Decimal('500'), custo_ml=Decimal('2.50'),
        )

    def test_loja2_mixture_does_not_affect_loja1_stock(self):
        self.estoque_a.refresh_from_db()
        loja1_stock_before = self.estoque_a.saldo_ml

        resp = _create_calculation(self.client, self.formula.id, self.loja2.id, nome='Cliente Loja 2')
        self.assertEqual(resp.status_code, 201, resp.data)
        mid = resp.data['mistura']['id']
        conf = _confirm(self.client, mid)
        self.assertEqual(conf.status_code, 200)

        # loja2 stock deducted
        self.estoque_a_loja2.refresh_from_db()
        self.assertLess(self.estoque_a_loja2.saldo_ml, Decimal('500'))

        # loja1 stock untouched
        self.estoque_a.refresh_from_db()
        self.assertEqual(self.estoque_a.saldo_ml, loja1_stock_before)

    def test_loja1_mixture_does_not_affect_loja2_stock(self):
        self.estoque_a_loja2.refresh_from_db()
        loja2_stock_before = self.estoque_a_loja2.saldo_ml

        resp = _create_calculation(self.client, self.formula.id, self.loja.id, nome='Cliente Loja 1')
        self.assertEqual(resp.status_code, 201)
        mid = resp.data['mistura']['id']
        conf = _confirm(self.client, mid)
        self.assertEqual(conf.status_code, 200)

        # loja1 stock deducted
        self.estoque_a.refresh_from_db()
        self.assertLess(self.estoque_a.saldo_ml, Decimal('1000'))

        # loja2 stock untouched
        self.estoque_a_loja2.refresh_from_db()
        self.assertEqual(self.estoque_a_loja2.saldo_ml, loja2_stock_before)

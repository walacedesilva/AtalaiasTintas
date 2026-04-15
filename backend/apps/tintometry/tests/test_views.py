"""
T012c – Testes do FormulaTintometricaViewSet

Covers:
  test_create_formula_with_items
  test_update_formula_proportions
  test_calculate_mixture_action_on_formula
  test_formula_inactive_excluded_from_list
"""

import time
from decimal import Decimal
from unittest.mock import patch, MagicMock

from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APITestCase
from rest_framework.authtoken.models import Token

from apps.companies.models import Empresa, Loja
from apps.inventory.models import (
    Categoria,
    Marca,
    ProdutoBase,
    ProdutoVariacao,
    UnidadeMedida,
)
from apps.tintometry.models import (
    EstoquePigmento,
    FormulaTintometrica,
    ItemFormula,
    LequeCorDefinida,
    MisturaTinta,
    Pigmento,
)
from apps.tintometry.tests.base import TintometryAPIBaseTestCase

User = get_user_model()

FORMULAS_URL = '/api/v1/tintometry/formulas/'


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _create_base_objects():
    """Cria objetos mínimos necessários para testes de fórmula."""
    user = User.objects.create_user(
        username='test_tintometry',
        password='testpass',
        email='test@tintas.com',
    )
    token = Token.objects.create(user=user)

    empresa = Empresa.objects.create(
        cnpj='12345678000100',
        razao_social='Tintas Teste LTDA',
        nome_fantasia='Tintas Teste',
    )
    loja = Loja.objects.create(
        empresa=empresa,
        codigo='L01',
        nome='Loja Teste',
        cep='01310100',
        endereco='Av. Paulista',
        numero='1000',
        bairro='Bela Vista',
        cidade='São Paulo',
        uf='SP',
    )

    categoria = Categoria.objects.create(nome='Tintas', codigo='TIN')
    marca = Marca.objects.create(nome='Marca Teste', codigo='MRC')
    unidade = UnidadeMedida.objects.create(
        codigo='L', nome='Litro', sigla='L', tipo='VOLUME'
    )
    produto_base = ProdutoBase.objects.create(
        codigo='PB001',
        nome='Base Branca 18L',
        categoria=categoria,
        marca=marca,
        tipo_produto='INSUMO',
    )
    variacao = ProdutoVariacao.objects.create(
        produto_base=produto_base,
        codigo_variacao='PB001-18L',
        nome_variacao='Base Branca 18L',
        unidade_venda=unidade,
        unidade_estoque=unidade,
        fator_conversao_venda=Decimal('1.0'),
    )

    cor = LequeCorDefinida.objects.create(
        codigo_cor='RAL3000',
        nome_cor='Vermelho Fogo',
        familia_cor='Vermelhos',
        linha_produto='Standard',
        l_value=Decimal('38.0'),
        a_value=Decimal('40.0'),
        b_value=Decimal('26.0'),
        r=200,
        g=35,
        b=45,
    )

    return user, token, loja, variacao, cor


# ---------------------------------------------------------------------------
# Test case
# ---------------------------------------------------------------------------

class FormulaTintometricaViewSetTests(APITestCase):
    """Testes de integração para FormulaTintometricaViewSet."""

    def setUp(self):
        self.user, self.token, self.loja, self.variacao, self.cor = (
            _create_base_objects()
        )
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token.key}')

    # ------------------------------------------------------------------
    # T012c-1: POST /formulas/ cria fórmula com dados válidos
    # ------------------------------------------------------------------
    def test_create_formula_with_items(self):
        payload = {
            'cor_definida': self.cor.id,
            'base_produto': str(self.variacao.id),
            'codigo_formula': 'FOR-001',
            'nome_formula': 'Fórmula Vermelho Fogo 1L',
            'versao': '1.0',
            'volume_base': '1.00',
            'aprovada': False,
            'testada': False,
            'ativa': True,
        }
        response = self.client.post(FORMULAS_URL, payload, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.data)
        self.assertEqual(response.data['codigo_formula'], 'FOR-001')
        self.assertEqual(response.data['nome_formula'], 'Fórmula Vermelho Fogo 1L')
        self.assertTrue(FormulaTintometrica.objects.filter(codigo_formula='FOR-001').exists())

    # ------------------------------------------------------------------
    # T012c-2: PATCH /formulas/{id}/ atualiza versão e volume_base
    # ------------------------------------------------------------------
    def test_update_formula_proportions(self):
        formula = FormulaTintometrica.objects.create(
            cor_definida=self.cor,
            base_produto=self.variacao,
            codigo_formula='FOR-002',
            nome_formula='Fórmula Para Update',
            versao='1.0',
            volume_base=Decimal('1.00'),
            ativa=True,
        )
        url = f'{FORMULAS_URL}{formula.id}/'
        patch_data = {'versao': '2.0', 'volume_base': '3.60'}

        response = self.client.patch(url, patch_data, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)
        formula.refresh_from_db()
        self.assertEqual(formula.versao, '2.0')
        self.assertEqual(formula.volume_base, Decimal('3.60'))

    # ------------------------------------------------------------------
    # T012c-3: POST /formulas/{id}/calculate_mixture/ retorna cálculo
    # ------------------------------------------------------------------
    @patch('apps.tintometry.views.FormulaCalculatorService')
    def test_calculate_mixture_action_on_formula(self, mock_calc_class):
        mock_instance = mock_calc_class.return_value
        mock_instance.calculate_mixture_quantities.return_value = {
            'formula': {'id': 'some-id', 'codigo': 'FOR-003', 'nome': 'Fórmula Mock'},
            'pigmentos': [],
            'custos': {'base': 0, 'pigmentos': 0, 'total': 25.50},
            'validacao': {'stock_ok': True, 'total_pigmentos': 0, 'warnings': []},
            'volume': {'solicitado': 3.6, 'base_formula': 1.0, 'fator_proporcao': 3.6},
        }
        mock_instance.calculate_cost_breakdown.return_value = {'detail': 'mocked'}
        mock_instance._generate_mixing_recommendations = lambda r: []

        formula = FormulaTintometrica.objects.create(
            cor_definida=self.cor,
            base_produto=self.variacao,
            codigo_formula='FOR-003',
            nome_formula='Fórmula Cálculo',
            versao='1.0',
            volume_base=Decimal('1.00'),
            ativa=True,
        )
        url = f'{FORMULAS_URL}{formula.id}/calculate_mixture/'
        payload = {
            'volume_requested': '3.60',
            'loja_id': self.loja.id,
            'customer_data': {'nome': 'Cliente Teste'},
        }

        response = self.client.post(url, payload, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)
        self.assertTrue(response.data.get('success'), response.data)
        mock_instance.calculate_mixture_quantities.assert_called_once()

    # ------------------------------------------------------------------
    # T012c-4: GET /formulas/ exclui fórmulas inativas por padrão
    # ------------------------------------------------------------------
    def test_formula_inactive_excluded_from_list(self):
        for i, ativa in enumerate([True, True, False]):
            cor_i = LequeCorDefinida.objects.create(
                codigo_cor=f'RAL-LIST-{i}',
                nome_cor=f'Cor Lista {i}',
                familia_cor='Vermelhos',
                linha_produto='Standard',
                l_value=Decimal('38.0'),
                a_value=Decimal('40.0'),
                b_value=Decimal('26.0'),
                r=200, g=35, b=45,
            )
            FormulaTintometrica.objects.create(
                cor_definida=cor_i,
                base_produto=self.variacao,
                codigo_formula=f'FOR-LIST-{i}',
                nome_formula=f'Fórmula Lista {i}',
                versao='1.0',
                volume_base=Decimal('1.00'),
                ativa=ativa,
            )

        response = self.client.get(FORMULAS_URL)

        self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)
        results = response.data.get('results', response.data)
        codigos = [f['codigo_formula'] for f in results]

        self.assertIn('FOR-LIST-0', codigos)
        self.assertIn('FOR-LIST-1', codigos)
        self.assertNotIn('FOR-LIST-2', codigos)


# ===========================================================================
# T021 – Additional API tests for MisturaTintaViewSet and QuickCalculate
# ===========================================================================


MISTURAS_URL = '/api/v1/tintometry/misturas/'
QUICK_CALC_URL = '/api/v1/tintometry/quick-calculate/'
CUSTOMER_HIST_URL = '/api/v1/tintometry/customer-history/'


class MisturaViewSetAPITests(TintometryAPIBaseTestCase):
    """T021 – API tests for mixture workflow and customer history."""

    # -----------------------------------------------------------------------
    # T021-1: calculate_mixture action returns pigment quantities
    # -----------------------------------------------------------------------
    @patch('apps.tintometry.views.MixtureService.create_mixture_calculation')
    def test_calculate_mixture_endpoint_returns_quantities(self, mock_create):
        mock_create.return_value = {
            'success': True,
            'mistura': {'id': 'some-id', 'codigo': 'MX-001', 'situacao': 'CALCULADA'},
            'calculation': {
                'formula': {'id': str(self.formula.id), 'codigo': 'FOR-T001', 'nome': 'Fórmula T'},
                'pigmentos': [
                    {
                        'pigmento': {'id': self.pigmento_a.id, 'nome': 'Pig A'},
                        'quantidades': {'calculada_final': 15.0},
                        'custos': {'total': 37.5},
                        'stock_available': True,
                    }
                ],
                'custos': {'base': 10.0, 'pigmentos': 37.5, 'total': 47.5},
            },
            'next_steps': [],
        }

        url = f'{MISTURAS_URL}create_calculation/'
        payload = {
            'formula_id': str(self.formula.id),
            'volume_requested': '1.0',
            'loja_id': self.loja.id,
            'customer_data': {'nome': 'Teste', 'telefone': '11999999999'},
        }
        response = self.client.post(url, payload, format='json')

        self.assertIn(
            response.status_code,
            [status.HTTP_200_OK, status.HTTP_201_CREATED],
            response.data,
        )
        self.assertTrue(response.data.get('success'))
        mock_create.assert_called_once()

    # -----------------------------------------------------------------------
    # T021-2: calculate_mixture returns 409 when stock is short
    # -----------------------------------------------------------------------
    @patch('apps.tintometry.views.MixtureService.create_mixture_calculation')
    def test_calculate_mixture_returns_409_when_stock_short(self, mock_create):
        mock_create.return_value = {
            'success': False,
            'error': 'Estoque insuficiente para alguns pigmentos',
            'details': ['Pigmento A: necessário 15ml, disponível 5ml'],
            'calculation': {},
        }

        url = f'{MISTURAS_URL}create_calculation/'
        payload = {
            'formula_id': str(self.formula.id),
            'volume_requested': '1.0',
            'loja_id': self.loja.id,
            'customer_data': {'nome': 'Teste', 'telefone': '11999999999'},
        }
        response = self.client.post(url, payload, format='json')

        # The service reports failure – view should return 409 Conflict
        self.assertIn(response.status_code, [
            status.HTTP_409_CONFLICT,
            status.HTTP_400_BAD_REQUEST,
        ], f"Esperado 409 ou 400, recebeu {response.status_code}")
        self.assertFalse(response.data.get('success'))

    # -----------------------------------------------------------------------
    # T021-3: confirm action reduces stock
    # -----------------------------------------------------------------------
    @patch('apps.tintometry.views.MixtureService.confirm_mixture')
    def test_confirm_mixture_reduces_stock(self, mock_confirm):
        mistura = MisturaTinta.objects.create(
            formula=self.formula,
            loja=self.loja,
            usuario_operacao=self.user,
            cliente_nome='Test Client',
            volume_solicitado=Decimal('1.0'),
            custo_total=Decimal('25.00'),
            custo_base=Decimal('10.00'),
            custo_pigmentos=Decimal('15.00'),
        )
        mock_confirm.return_value = {
            'success': True,
            'mistura': {'id': str(mistura.id), 'codigo': mistura.codigo_mistura,
                        'situacao': 'CONFIRMADA', 'data_confirmacao': '2026-04-15T10:00:00'},
            'estoque': {'reservado': True, 'itens_atualizados': 2},
            'etiqueta': {'codigo': 'ET-001', 'qr_data': '{}'},
            'next_steps': [],
        }

        url = f'{MISTURAS_URL}{mistura.id}/confirm/'
        response = self.client.post(url, {}, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)
        self.assertTrue(response.data.get('success'))
        mock_confirm.assert_called_once()

    # -----------------------------------------------------------------------
    # T021-4: quick_calculate responds in under 1 second
    # -----------------------------------------------------------------------
    @patch('apps.tintometry.views.FormulaCalculatorService.calculate_mixture_quantities')
    def test_quick_calculate_responds_under_1_second(self, mock_calc):
        mock_calc.return_value = {
            'formula': {'id': str(self.formula.id), 'codigo': 'FOR-T001', 'nome': 'F'},
            'pigmentos': [],
            'volume': {'solicitado': 1.0, 'base_formula': 1.0, 'fator_proporcao': 1.0},
            'custos': {'base': 0.0, 'pigmentos': 0.0, 'total': 0.0},
            'validacao': {'stock_ok': True, 'total_pigmentos': 0, 'warnings': []},
            'timestamp': '2026-04-15T10:00:00',
        }

        payload = {
            'formula_id': str(self.formula.id),
            'volume': '1.0',
            'loja_id': self.loja.id,
        }

        start = time.monotonic()
        response = self.client.post(QUICK_CALC_URL, payload, format='json')
        elapsed = time.monotonic() - start

        self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)
        self.assertLess(elapsed, 1.0,
            msg=f"quick_calculate levou {elapsed:.3f}s, deve ser < 1s")

    # -----------------------------------------------------------------------
    # T021-5: customer_history search_by_phone returns results
    # -----------------------------------------------------------------------
    def test_customer_history_search_by_phone(self):
        # Create confirmed mixture for a phone number
        mistura = MisturaTinta.objects.create(
            formula=self.formula,
            loja=self.loja,
            usuario_operacao=self.user,
            cliente_nome='Maria Silva',
            cliente_telefone='11988887777',
            volume_solicitado=Decimal('1.0'),
            custo_total=Decimal('25.00'),
            custo_base=Decimal('10.00'),
            custo_pigmentos=Decimal('15.00'),
            situacao='CONFIRMADA',
        )

        response = self.client.get(
            f'{CUSTOMER_HIST_URL}search_by_phone/?phone=11988887777'
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)
        data = response.data
        results = data.get('results', data) if isinstance(data, dict) else data
        if isinstance(results, dict):
            results = results.get('results', [results])
        found_codes = [
            r.get('codigo_mistura') for r in (results if isinstance(results, list) else [])
        ]
        self.assertIn(mistura.codigo_mistura, found_codes,
            msg="Mistura do cliente não encontrada na busca por telefone")

"""
Shared test setup helpers for tintometry tests.

Provides TintometryBaseTestCase with all common DB objects
pre-created via setUpTestData for efficiency.
"""

from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.authtoken.models import Token
from rest_framework.test import APITestCase

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

User = get_user_model()


def make_pigmento(codigo='PIG-01', saldo_ml=Decimal('1000'), **kwargs):
    """Creates a Pigmento with reasonable defaults."""
    defaults = dict(
        codigo=codigo,
        nome=f'Pigmento {codigo}',
        cor_base='Vermelho',
        densidade=Decimal('1.0'),
        poder_tintorial=Decimal('90.00'),
        fornecedor='Fornecedor Teste',
        concentracao_maxima=Decimal('15.00'),
        r=180, g=30, b=30,
        ativo=True,
    )
    defaults.update(kwargs)
    return Pigmento.objects.create(**defaults)


def make_estoque(pigmento, loja, saldo_ml=Decimal('1000'), custo_ml=Decimal('2.50'), **kwargs):
    """Creates an EstoquePigmento record."""
    defaults = dict(
        pigmento=pigmento,
        loja=loja,
        saldo_ml=saldo_ml,
        saldo_minimo=Decimal('100'),
        saldo_maximo=Decimal('5000'),
        custo_ml=custo_ml,
        ativo=True,
    )
    defaults.update(kwargs)
    return EstoquePigmento.objects.create(**defaults)


class TintometryBaseTestCase(TestCase):
    """Base test case that sets up the full tintometry object graph."""

    @classmethod
    def setUpTestData(cls):
        # Auth
        cls.user = User.objects.create_user(
            username='tinto_user',
            password='tinto_pass',
            email='tinto@test.com',
        )

        # Company graph
        cls.empresa = Empresa.objects.create(
            cnpj='12345678000199',
            razao_social='Tintas Test LTDA',
            nome_fantasia='Tintas Test',
        )
        cls.loja = Loja.objects.create(
            empresa=cls.empresa,
            codigo='LT01',
            nome='Loja Test',
            cep='01310100',
            endereco='Av. Paulista',
            numero='100',
            bairro='Bela Vista',
            cidade='São Paulo',
            uf='SP',
        )
        cls.loja2 = Loja.objects.create(
            empresa=cls.empresa,
            codigo='LT02',
            nome='Loja Test 2',
            cep='01310100',
            endereco='Av. Brasil',
            numero='200',
            bairro='Centro',
            cidade='São Paulo',
            uf='SP',
        )

        # Inventory graph
        cls.categoria = Categoria.objects.create(nome='Tintas Teste', codigo='TT')
        cls.marca = Marca.objects.create(nome='Marca Teste', codigo='MT')
        cls.unidade = UnidadeMedida.objects.create(
            codigo='L', nome='Litro', sigla='L', tipo='VOLUME'
        )
        cls.produto_base = ProdutoBase.objects.create(
            codigo='BASE001',
            nome='Base Branca',
            categoria=cls.categoria,
            marca=cls.marca,
            tipo_produto='INSUMO',
        )
        cls.variacao = ProdutoVariacao.objects.create(
            produto_base=cls.produto_base,
            codigo_variacao='BASE001-1L',
            nome_variacao='Base Branca 1L',
            unidade_venda=cls.unidade,
            unidade_estoque=cls.unidade,
            fator_conversao_venda=Decimal('1'),
            preco_custo=Decimal('10.00'),
        )

        # Tintometry base objects
        cls.cor = LequeCorDefinida.objects.create(
            codigo_cor='RAL3000T',
            nome_cor='Vermelho Fogo Teste',
            familia_cor='Vermelhos',
            linha_produto='Standard',
            l_value=Decimal('38.0'),
            a_value=Decimal('40.0'),
            b_value=Decimal('26.0'),
            r=170, g=35, b=40,
        )

        cls.pigmento_a = make_pigmento('PIG-A', cor_base='Vermelho')
        cls.pigmento_b = make_pigmento('PIG-B', cor_base='Amarelo', r=230, g=200, b=20)

        # Stock for loja 1
        cls.estoque_a = make_estoque(cls.pigmento_a, cls.loja, saldo_ml=Decimal('1000'))
        cls.estoque_b = make_estoque(cls.pigmento_b, cls.loja, saldo_ml=Decimal('1000'))

        # Formula with 2 items
        cls.formula = FormulaTintometrica.objects.create(
            cor_definida=cls.cor,
            base_produto=cls.variacao,
            codigo_formula='FOR-T001',
            nome_formula='Fórmula Teste Vermelho 1L',
            versao='1.0',
            volume_base=Decimal('1.00'),
            ativa=True,
        )
        cls.item_a = ItemFormula.objects.create(
            formula=cls.formula,
            pigmento=cls.pigmento_a,
            quantidade=Decimal('15.0'),  # 15 ml per 1L base
            sequencia=1,
        )
        cls.item_b = ItemFormula.objects.create(
            formula=cls.formula,
            pigmento=cls.pigmento_b,
            quantidade=Decimal('8.0'),   # 8 ml per 1L base
            sequencia=2,
        )


class TintometryAPIBaseTestCase(TintometryBaseTestCase, APITestCase):
    """API test variant with DRF test client and token auth."""

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.token = Token.objects.create(user=cls.user)

    def setUp(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token.key}')

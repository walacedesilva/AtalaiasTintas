"""
Seed completo: carga de TODOS os dados de teste do projeto Atalaia Tintas.

Inclui: usuários, empresa/loja, produtos, estoque, tintometria,
        clientes, pedidos, vendas, pagamentos, recebíveis e fiscal.

Execução:
    cd C:\\Atalaia\\AtalaiasTintas\\backend
    C:\\Atalaia\\AtalaiasTintas\\.venv\\Scripts\\python.exe seed_completo.py

Flags opcionais:
    --limpar   Remove TODOS os dados antes de recriar (cuidado em produção!)
"""
import sys
import os
import argparse
from decimal import Decimal
from datetime import date, timedelta

# UTF-8 output (needed on Windows with cp1252 terminal)
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

# ─── Setup Django ────────────────────────────────────────────────────────────
sys.path.insert(0, r'C:\Atalaia\AtalaiasTintas\backend')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'tintas_system.settings')

import django
django.setup()

from django.contrib.auth import get_user_model
from django.utils import timezone

from apps.companies.models import Empresa, Loja, UsuarioLoja
from apps.inventory.models import (
    UnidadeMedida, Categoria, Marca, ProdutoBase,
    ProdutoVariacao, EstoqueLoja,
)
from apps.tintometry.models import (
    Pigmento, EstoquePigmento, LequeCorDefinida,
    FormulaTintometrica, ItemFormula, MisturaTinta, ItemMistura,
)
from apps.sales.models import (
    Cliente, PedidoVenda, ItemPedidoVenda, Venda,
    PagamentoVenda, Recebivel,
)
from apps.fiscal.models import (
    ConfiguracaoFiscal, NotaFiscal, ItemNotaFiscal,
)

User = get_user_model()


# ══════════════════════════════════════════════════════════════════════════════
# LIMPEZA OPCIONAL
# ══════════════════════════════════════════════════════════════════════════════
def limpar_dados():
    """Remove todos os dados (use apenas em ambiente de desenvolvimento)."""
    print("\n🗑️  Limpando dados existentes...")
    ItemNotaFiscal.objects.all().delete()
    NotaFiscal.objects.all().delete()
    ConfiguracaoFiscal.objects.all().delete()
    Recebivel.objects.all().delete()
    PagamentoVenda.objects.all().delete()
    Venda.objects.all().delete()
    ItemPedidoVenda.objects.all().delete()
    PedidoVenda.objects.all().delete()
    Cliente.objects.all().delete()
    ItemMistura.objects.all().delete()
    MisturaTinta.objects.all().delete()
    ItemFormula.objects.all().delete()
    FormulaTintometrica.objects.all().delete()
    LequeCorDefinida.objects.all().delete()
    EstoquePigmento.objects.all().delete()
    Pigmento.objects.all().delete()
    EstoqueLoja.objects.all().delete()
    ProdutoVariacao.objects.all().delete()
    ProdutoBase.objects.all().delete()
    Marca.objects.all().delete()
    Categoria.objects.all().delete()
    UnidadeMedida.objects.all().delete()
    UsuarioLoja.objects.all().delete()
    Loja.objects.all().delete()
    Empresa.objects.all().delete()
    User.objects.exclude(username='__placeholder__').delete()
    print("   ✅ Dados removidos")


# ══════════════════════════════════════════════════════════════════════════════
# 1. USUÁRIOS
# ══════════════════════════════════════════════════════════════════════════════
def criar_usuarios():
    print("\n👤 Usuários...")

    admin, _ = User.objects.get_or_create(
        username='admin',
        defaults=dict(
            email='admin@atalaiatingas.com.br',
            first_name='Administrador',
            last_name='Sistema',
            is_staff=True,
            is_superuser=True,
        )
    )
    admin.set_password('admin123')
    admin.save()
    print("   ✅ admin / admin123  [superuser]")

    gerente, _ = User.objects.get_or_create(
        username='gerente',
        defaults=dict(
            email='gerente@atalaiatingas.com.br',
            first_name='Roberto',
            last_name='Gerente',
            is_staff=True,
            is_superuser=False,
        )
    )
    gerente.set_password('gerente123')
    gerente.save()
    print("   ✅ gerente / gerente123  [staff]")

    vendedor, _ = User.objects.get_or_create(
        username='vendedor',
        defaults=dict(
            email='vendedor@atalaiatingas.com.br',
            first_name='Carlos',
            last_name='Vendedor',
            is_staff=False,
        )
    )
    vendedor.set_password('vendedor123')
    vendedor.save()
    print("   ✅ vendedor / vendedor123")

    caixa, _ = User.objects.get_or_create(
        username='caixa',
        defaults=dict(
            email='caixa@atalaiatingas.com.br',
            first_name='Fernanda',
            last_name='Caixa',
            is_staff=False,
        )
    )
    caixa.set_password('caixa123')
    caixa.save()
    print("   ✅ caixa / caixa123")

    return admin, gerente, vendedor, caixa


# ══════════════════════════════════════════════════════════════════════════════
# 2. EMPRESA + LOJA + USUÁRIO_LOJA
# ══════════════════════════════════════════════════════════════════════════════
def criar_empresa_loja(admin, gerente, vendedor, caixa):
    print("\n🏢 Empresa e Lojas...")

    empresa, _ = Empresa.objects.get_or_create(
        cnpj='12345678000195',
        defaults=dict(
            razao_social='Atalaia Tintas LTDA',
            nome_fantasia='Atalaia Tintas',
            inscricao_estadual='111222333444',
            telefone='1133334444',
            email='contato@atalaiatingas.com.br',
            cep='01310200',
            endereco='Av. Paulista',
            numero='1578',
            bairro='Bela Vista',
            cidade='São Paulo',
            uf='SP',
            ativa=True,
        )
    )
    print(f"   ✅ Empresa: {empresa.razao_social}")

    loja_sp, _ = Loja.objects.get_or_create(
        codigo='LJ001',
        defaults=dict(
            empresa=empresa,
            nome='Loja Principal SP',
            telefone='1133334444',
            email='sp@atalaiatingas.com.br',
            cep='01310200',
            endereco='Av. Paulista',
            numero='1578',
            bairro='Bela Vista',
            cidade='São Paulo',
            uf='SP',
            ativa=True,
        )
    )
    print(f"   ✅ Loja: {loja_sp.nome}")

    loja_abc, _ = Loja.objects.get_or_create(
        codigo='LJ002',
        defaults=dict(
            empresa=empresa,
            nome='Loja ABC Paulista',
            telefone='1144445555',
            email='abc@atalaiatingas.com.br',
            cep='09210580',
            endereco='Rua das Flores',
            numero='200',
            bairro='Centro',
            cidade='Santo André',
            uf='SP',
            ativa=True,
        )
    )
    print(f"   ✅ Loja: {loja_abc.nome}")

    for usuario in [admin, gerente, vendedor, caixa]:
        UsuarioLoja.objects.get_or_create(
            usuario=usuario, loja=loja_sp,
            defaults=dict(empresa=empresa, ativo=True)
        )

    UsuarioLoja.objects.get_or_create(
        usuario=gerente, loja=loja_abc,
        defaults=dict(empresa=empresa, ativo=True)
    )

    print("   ✅ UsuárioLoja: vínculos criados")
    return empresa, loja_sp, loja_abc


# ══════════════════════════════════════════════════════════════════════════════
# 3. UNIDADES DE MEDIDA
# ══════════════════════════════════════════════════════════════════════════════
def criar_unidades():
    print("\n📏 Unidades de Medida...")

    # (codigo, sigla, nome, tipo)  — tipo choices: VOLUME, PESO, UNIDADE, AREA
    dados = [
        ('L',    'L',    'Litro',          'VOLUME'),
        ('ML',   'ml',   'Mililitro',      'VOLUME'),
        ('GL',   'gl',   'Galão',          'VOLUME'),
        ('LATA', 'lt',   'Lata',           'UNIDADE'),
        ('KG',   'kg',   'Quilograma',     'PESO'),
        ('G',    'g',    'Grama',          'PESO'),
        ('UN',   'un',   'Unidade',        'UNIDADE'),
        ('PC',   'pc',   'Peça',           'UNIDADE'),
        ('M2',   'm2',   'Metro Quadrado', 'AREA'),
    ]

    unidades = {}
    for codigo, sigla, nome, tipo in dados:
        un, _ = UnidadeMedida.objects.get_or_create(
            codigo=codigo,
            defaults=dict(sigla=sigla, nome=nome, tipo=tipo)
        )
        unidades[codigo] = un
        print(f"   ✅ {codigo} — {nome}")

    return unidades


# ══════════════════════════════════════════════════════════════════════════════
# 4. CATEGORIAS E MARCAS
# ══════════════════════════════════════════════════════════════════════════════
def criar_categorias_marcas():
    print("\n🏷️  Categorias e Marcas...")

    cats_dados = [
        ('TINTAS',       'Tintas e Esmaltes',          None),
        ('BASES-TINT',   'Bases Tintométricas',         'TINTAS'),
        ('PRIMERS',      'Primers e Seladores',         None),
        ('VERNIZES',     'Vernizes e Stains',            None),
        ('FERRAMENTAS',  'Ferramentas e Utensílios',     None),
        ('ACESSORIOS',   'Acessórios e Complementos',   None),
        ('SOLVENTES',    'Solventes e Diluentes',        None),
        ('IMPERMEAB',    'Impermeabilizantes',           None),
    ]

    cats = {}
    for codigo, nome, pai_cod in cats_dados:
        cat, _ = Categoria.objects.get_or_create(
            codigo=codigo,
            defaults=dict(
                nome=nome,
                ativa=True,
            )
        )
        cats[codigo] = cat
        print(f"   ✅ Categoria: {nome}")

    marcas_dados = [
        ('SUVINIL',    'Suvinil',    'Suvinil Tintas'),
        ('CORAL',      'Coral',      'Coral Tintas'),
        ('LUKSCOLOR',  'Lukscolor',  'Lukscolor Tintas'),
        ('NOVACOR',    'Novacor',    'Novacor Pinturas'),
        ('SHERWIN',    'Sherwin',    'Sherwin-Williams'),
        ('IQUINE',     'Iquine',     'Iquine Tintas'),
        ('RENNER',     'Renner',     'Renner Tintas'),
    ]

    marcas = {}
    for codigo, nome, desc in marcas_dados:
        marca, _ = Marca.objects.get_or_create(
            codigo=codigo,
            defaults=dict(nome=nome, descricao=desc, ativa=True)
        )
        marcas[codigo] = marca
        print(f"   ✅ Marca: {nome}")

    return cats, marcas


# ══════════════════════════════════════════════════════════════════════════════
# 5. PRODUTOS E VARIAÇÕES
# ══════════════════════════════════════════════════════════════════════════════
def criar_produtos(cats, marcas, unidades):
    print("\n📦 Produtos e Variações...")

    produtos_dados = [
        # (codigo, nome, categoria, marca, unidade_venda, custo, preco, variações)
        # variações: [(cod_var, nome_var, codigo_barras, custo, preco)]
        (
            'TINTA-ACRIL-INT', 'Tinta Acrílica Interior Premium',
            'TINTAS', 'SUVINIL', 'L',
            Decimal('25.00'), Decimal('49.90'),
            [
                ('TINTA-ACRIL-INT-3.6L', '3,6 Litros', '7891000100100', Decimal('25.00'), Decimal('49.90')),
                ('TINTA-ACRIL-INT-18L',  '18 Litros',   '7891000100101', Decimal('110.00'), Decimal('219.90')),
            ]
        ),
        (
            'TINTA-ACRIL-EXT', 'Tinta Acrílica Exterior',
            'TINTAS', 'CORAL', 'L',
            Decimal('28.00'), Decimal('55.90'),
            [
                ('TINTA-ACRIL-EXT-3.6L', '3,6 Litros', '7891000200100', Decimal('28.00'), Decimal('55.90')),
                ('TINTA-ACRIL-EXT-18L',  '18 Litros',   '7891000200101', Decimal('128.00'), Decimal('249.90')),
            ]
        ),
        (
            'BASE-TINT-BRANCA', 'Base Branca Tintométrica',
            'BASES-TINT', 'LUKSCOLOR', 'LATA',
            Decimal('40.00'), Decimal('75.00'),
            [
                ('BASE-TINT-BRANCA-3.6L', '3,6 Litros', '7891000300100', Decimal('40.00'), Decimal('75.00')),
                ('BASE-TINT-BRANCA-18L',  '18 Litros',   '7891000300101', Decimal('185.00'), Decimal('350.00')),
            ]
        ),
        (
            'BASE-TINT-MEDIA', 'Base Média Tintométrica',
            'BASES-TINT', 'LUKSCOLOR', 'LATA',
            Decimal('42.00'), Decimal('78.00'),
            [
                ('BASE-TINT-MEDIA-3.6L', '3,6 Litros', '7891000400100', Decimal('42.00'), Decimal('78.00')),
            ]
        ),
        (
            'PRIMER-ACRIL', 'Primer Acrílico Selador',
            'PRIMERS', 'SUVINIL', 'L',
            Decimal('18.00'), Decimal('35.00'),
            [
                ('PRIMER-ACRIL-3.6L', '3,6 Litros', '7891000500100', Decimal('18.00'), Decimal('35.00')),
                ('PRIMER-ACRIL-18L',  '18 Litros',   '7891000500101', Decimal('82.00'), Decimal('159.00')),
            ]
        ),
        (
            'VERNIZ-MAD', 'Verniz Madeirite Semibrilho',
            'VERNIZES', 'NOVACOR', 'L',
            Decimal('30.00'), Decimal('59.90'),
            [
                ('VERNIZ-MAD-0.9L',  '900 mL',     '7891000600100', Decimal('15.00'), Decimal('29.90')),
                ('VERNIZ-MAD-3.6L',  '3,6 Litros', '7891000600101', Decimal('30.00'), Decimal('59.90')),
            ]
        ),
        (
            'ROLO-PINTURA', 'Rolo de Pintura Lã 23cm',
            'FERRAMENTAS', 'SHERWIN', 'UN',
            Decimal('8.00'), Decimal('15.90'),
            [
                ('ROLO-PINTURA-UN', 'Unidade', '7891000700100', Decimal('8.00'), Decimal('15.90')),
            ]
        ),
        (
            'PINCEL-2POL', 'Pincel Nº 2 Cerdas Mistas',
            'FERRAMENTAS', 'RENNER', 'UN',
            Decimal('4.50'), Decimal('9.90'),
            [
                ('PINCEL-2POL-UN', 'Unidade', '7891000800100', Decimal('4.50'), Decimal('9.90')),
            ]
        ),
        (
            'AGUARRAS', 'Aguarrás Mineral 500mL',
            'SOLVENTES', 'IQUINE', 'UN',
            Decimal('6.00'), Decimal('12.90'),
            [
                ('AGUARRAS-500ML', '500 mL', '7891000900100', Decimal('6.00'), Decimal('12.90')),
                ('AGUARRAS-1L',    '1 Litro', '7891000900101', Decimal('10.00'), Decimal('21.90')),
            ]
        ),
        (
            'FITA-CREPE', 'Fita Crepe 18mm × 50m',
            'ACESSORIOS', 'SHERWIN', 'UN',
            Decimal('2.50'), Decimal('5.90'),
            [
                ('FITA-CREPE-UN', 'Rolo', '7891001000100', Decimal('2.50'), Decimal('5.90')),
            ]
        ),
    ]

    produtos_base = {}
    variacoes = {}

    un_l   = unidades.get('L',    unidades.get('UN'))
    un_lata = unidades.get('LATA', unidades.get('UN'))
    un_un  = unidades.get('UN')

    # Map unidade_cod_key → UnidadeMedida for venda lookup
    _un_map = {'L': un_l, 'LATA': un_lata, 'UN': un_un}

    for cod, nome, cat_cod, marca_cod, un_cod, custo_base, preco_base, vars_dados in produtos_dados:
        un_venda = _un_map.get(un_cod, un_un)
        pb, _ = ProdutoBase.objects.get_or_create(
            codigo=cod,
            defaults=dict(
                nome=nome,
                categoria=cats[cat_cod],
                marca=marcas[marca_cod],
                tipo_produto='SIMPLES',
                ativo=True,
            )
        )
        produtos_base[cod] = pb

        for cod_var, nome_var, _cod_barras, custo, preco in vars_dados:
            var, _ = ProdutoVariacao.objects.get_or_create(
                produto_base=pb,
                codigo_variacao=cod_var,
                defaults=dict(
                    nome_variacao=nome_var,
                    unidade_venda=un_venda,
                    unidade_estoque=un_venda,
                    preco_custo=custo,
                    preco_venda=preco,
                    ativo=True,
                )
            )
            variacoes[cod_var] = var

        print(f"   ✅ {nome} ({len(vars_dados)} variação/ões)")

    return produtos_base, variacoes


# ══════════════════════════════════════════════════════════════════════════════
# 6. ESTOQUE
# ══════════════════════════════════════════════════════════════════════════════
def criar_estoque(loja_sp, loja_abc, variacoes):
    print("\n📊 Estoque...")

    # (cod_var, qtd_sp, qtd_abc, estoque_min, estoque_max)
    estoque_dados = [
        ('TINTA-ACRIL-INT-3.6L', Decimal('45'), Decimal('20'), Decimal('10'), Decimal('100')),
        ('TINTA-ACRIL-INT-18L',  Decimal('12'), Decimal('6'),  Decimal('3'),  Decimal('30')),
        ('TINTA-ACRIL-EXT-3.6L', Decimal('38'), Decimal('15'), Decimal('10'), Decimal('80')),
        ('TINTA-ACRIL-EXT-18L',  Decimal('9'),  Decimal('4'),  Decimal('3'),  Decimal('20')),
        ('BASE-TINT-BRANCA-3.6L',Decimal('60'), Decimal('25'), Decimal('15'), Decimal('120')),
        ('BASE-TINT-BRANCA-18L', Decimal('20'), Decimal('8'),  Decimal('5'),  Decimal('40')),
        ('BASE-TINT-MEDIA-3.6L', Decimal('35'), Decimal('12'), Decimal('8'),  Decimal('60')),
        ('PRIMER-ACRIL-3.6L',    Decimal('28'), Decimal('10'), Decimal('8'),  Decimal('50')),
        ('PRIMER-ACRIL-18L',     Decimal('7'),  Decimal('3'),  Decimal('2'),  Decimal('15')),
        ('VERNIZ-MAD-0.9L',      Decimal('22'), Decimal('8'),  Decimal('5'),  Decimal('40')),
        ('VERNIZ-MAD-3.6L',      Decimal('14'), Decimal('5'),  Decimal('4'),  Decimal('25')),
        ('ROLO-PINTURA-UN',      Decimal('80'), Decimal('30'), Decimal('20'), Decimal('150')),
        ('PINCEL-2POL-UN',       Decimal('50'), Decimal('20'), Decimal('15'), Decimal('100')),
        ('AGUARRAS-500ML',       Decimal('40'), Decimal('15'), Decimal('10'), Decimal('80')),
        ('AGUARRAS-1L',          Decimal('25'), Decimal('10'), Decimal('8'),  Decimal('50')),
        ('FITA-CREPE-UN',        Decimal('100'),Decimal('40'), Decimal('20'), Decimal('200')),
    ]

    for cod_var, qtd_sp, qtd_abc, est_min, est_max in estoque_dados:
        if cod_var not in variacoes:
            continue
        var = variacoes[cod_var]

        EstoqueLoja.objects.get_or_create(
            loja=loja_sp, produto_variacao=var,
            defaults=dict(quantidade_atual=qtd_sp)
        )
        EstoqueLoja.objects.get_or_create(
            loja=loja_abc, produto_variacao=var,
            defaults=dict(quantidade_atual=qtd_abc)
        )

    print(f"   ✅ {len(estoque_dados)} variações × 2 lojas")


# ══════════════════════════════════════════════════════════════════════════════
# 7. TINTOMETRIA
# ══════════════════════════════════════════════════════════════════════════════
def criar_tintometria(loja_sp, admin, variacoes):
    print("\n🎨 Tintometria...")

    # 7.1 Pigmentos
    # (codigo, nome, cor_base, r, g, b, densidade, poder_tintorial, fornecedor, conc_max)
    pigmentos_dados = [
        ('PIG-BRANCO',   'Dioxído de Titânio Branco', 'Branco',   255, 255, 255, Decimal('1.8200'), Decimal('100.00'), 'Kronos', Decimal('100.00')),
        ('PIG-PRETO',    'Negro de Fumo',              'Preto',      20,  20,  20, Decimal('1.8000'), Decimal('95.00'), 'Cabot',  Decimal('5.00')),
        ('PIG-VERMELHO', 'Óxido de Ferro Vermelho',    'Vermelho',  220,  30,  30, Decimal('4.9000'), Decimal('80.00'), 'Lanxess',Decimal('30.00')),
        ('PIG-AMARELO',  'Azo Amarelo Limão',          'Amarelo',   255, 230,   0, Decimal('1.5500'), Decimal('70.00'), 'Clariant',Decimal('15.00')),
        ('PIG-AZUL',     'Ftalocianina Azul',          'Azul',        0,  80, 200, Decimal('1.6000'), Decimal('85.00'), 'BASF',   Decimal('10.00')),
        ('PIG-VERDE',    'Ftalocianina Verde',         'Verde',      20, 160,  80, Decimal('1.5800'), Decimal('82.00'), 'BASF',   Decimal('10.00')),
        ('PIG-LARANJA',  'Molibdato Laranja',          'Laranja',   255, 100,   0, Decimal('4.2000'), Decimal('75.00'), 'Ferro',  Decimal('20.00')),
        ('PIG-MARROM',   'Óxido de Ferro Marrom',      'Marrom',    140,  70,  20, Decimal('4.7000'), Decimal('78.00'), 'Lanxess',Decimal('25.00')),
        ('PIG-ROXO',     'Violeta de Manganês',        'Roxo',      140,  30, 180, Decimal('3.8000'), Decimal('65.00'), 'Shepherd',Decimal('8.00')),
    ]

    pigmentos = {}
    for cod, nome, cor_base, r, g, b, den, pt, forn, conc_max in pigmentos_dados:
        pig, _ = Pigmento.objects.get_or_create(
            codigo=cod,
            defaults=dict(
                nome=nome,
                cor_base=cor_base,
                r=r, g=g, b=b,
                densidade=den,
                poder_tintorial=pt,
                fornecedor=forn,
                concentracao_maxima=conc_max,
                ativo=True,
            )
        )
        pigmentos[cod] = pig

        EstoquePigmento.objects.get_or_create(
            loja=loja_sp, pigmento=pig,
            defaults=dict(
                saldo_ml=Decimal('5000'),
                saldo_minimo=Decimal('500'),
                custo_ml=Decimal('0.0350'),
            )
        )
    print(f"   ✅ {len(pigmentos_dados)} pigmentos + estoques")

    # 7.2 Cores do leque
    # (codigo_cor, nome_cor, familia_cor, linha_produto, r, g, b, L, a, b_lab)
    cores_dados = [
        ('COR-BRANCO-GELO',  'Branco Gelo',   'BRANCO',   'Standard', 240, 240, 240, Decimal('95.000'), Decimal('0.100'), Decimal('1.200')),
        ('COR-MARFIM',       'Marfim',         'AMARELO',  'Standard', 255, 250, 205, Decimal('97.000'), Decimal('1.200'), Decimal('10.500')),
        ('COR-AREIA',        'Areia',          'AMARELO',  'Standard', 244, 228, 193, Decimal('91.000'), Decimal('3.200'), Decimal('18.000')),
        ('COR-VERDE-MENTA',  'Verde Menta',    'VERDE',    'Premium',  168, 223, 188, Decimal('85.000'), Decimal('-15.00'), Decimal('12.500')),
        ('COR-AZUL-CEU',     'Azul Céu',       'AZUL',     'Premium',  135, 206, 235, Decimal('79.000'), Decimal('-5.500'), Decimal('-25.00')),
        ('COR-ROSA-QUARTZO', 'Rosa Quartzo',   'ROSA',     'Standard', 245, 193, 200, Decimal('82.000'), Decimal('18.000'), Decimal('5.000')),
        ('COR-AMARELO-SOL',  'Amarelo Sol',    'AMARELO',  'Premium',  255, 215,   0, Decimal('88.000'), Decimal('5.000'), Decimal('75.000')),
        ('COR-TERRACOTA',    'Terracota',      'VERMELHO', 'Standard', 198,  93,  42, Decimal('46.000'), Decimal('29.000'), Decimal('30.000')),
        ('COR-CINZA-PRATA',  'Cinza Prata',    'CINZA',    'Standard', 192, 192, 192, Decimal('78.000'), Decimal('0.000'), Decimal('-0.200')),
        ('COR-VERDE-OLIVA',  'Verde Oliva',    'VERDE',    'Premium',  107, 142,  35, Decimal('54.000'), Decimal('-15.00'), Decimal('35.000')),
    ]

    cores = {}
    for cod_cor, nome_cor, familia, linha, r, g, b, lv, av, bv in cores_dados:
        cor, _ = LequeCorDefinida.objects.get_or_create(
            codigo_cor=cod_cor,
            defaults=dict(
                nome_cor=nome_cor,
                familia_cor=familia,
                linha_produto=linha,
                r=r, g=g, b=b,
                l_value=lv, a_value=av, b_value=bv,
                ativo=True,
            )
        )
        cores[cod_cor] = cor
    print(f"   ✅ {len(cores_dados)} cores no leque")

    # 7.3 Fórmulas tintométricas
    base_var = variacoes.get('BASE-TINT-BRANCA-3.6L')
    if not base_var:
        print("   ⚠️  Base tintométrica não encontrada, pulando fórmulas")
        return pigmentos, cores

    # (codigo_formula, nome_formula, cod_cor, [(cod_pig, ml, seq)])
    formulas_dados = [
        (
            'FRM-BRANCO-GELO', 'Fórmula Branco Gelo', 'COR-BRANCO-GELO',
            [('PIG-BRANCO', Decimal('950'), 1), ('PIG-AMARELO', Decimal('3'), 2)]
        ),
        (
            'FRM-MARFIM', 'Fórmula Marfim', 'COR-MARFIM',
            [('PIG-BRANCO', Decimal('920'), 1), ('PIG-AMARELO', Decimal('60'), 2), ('PIG-VERMELHO', Decimal('5'), 3)]
        ),
        (
            'FRM-VERDE-MENTA', 'Fórmula Verde Menta', 'COR-VERDE-MENTA',
            [('PIG-BRANCO', Decimal('800'), 1), ('PIG-VERDE', Decimal('150'), 2), ('PIG-AMARELO', Decimal('25'), 3)]
        ),
        (
            'FRM-AZUL-CEU', 'Fórmula Azul Céu', 'COR-AZUL-CEU',
            [('PIG-BRANCO', Decimal('850'), 1), ('PIG-AZUL', Decimal('130'), 2), ('PIG-PRETO', Decimal('5'), 3)]
        ),
        (
            'FRM-TERRACOTA', 'Fórmula Terracota', 'COR-TERRACOTA',
            [('PIG-VERMELHO', Decimal('400'), 1), ('PIG-AMARELO', Decimal('200'), 2), ('PIG-MARROM', Decimal('150'), 3), ('PIG-PRETO', Decimal('20'), 4)]
        ),
    ]

    formulas = {}
    for cod_frm, nome_frm, cod_cor, itens in formulas_dados:
        cor = cores[cod_cor]
        # unique_together = ['cor_definida', 'base_produto']
        frm, _ = FormulaTintometrica.objects.get_or_create(
            codigo_formula=cod_frm,
            defaults=dict(
                nome_formula=nome_frm,
                cor_definida=cor,
                base_produto=base_var,
                aprovada=True,
                testada=True,
                ativa=True,
            )
        )
        formulas[cod_frm] = frm

        for cod_pig, ml, seq in itens:
            ItemFormula.objects.get_or_create(
                formula=frm,
                pigmento=pigmentos[cod_pig],
                defaults=dict(
                    quantidade=ml,
                    sequencia=seq,
                )
            )
    print(f"   ✅ {len(formulas_dados)} fórmulas tintométricas")

    # 7.4 Misturas realizadas (usando código automático)
    misturas_dados = [
        ('Condomínio Branco Gelo', 'FRM-BRANCO-GELO', Decimal('18'), 'PRODUZIDA'),
        ('Marfim Quarto Casal',    'FRM-MARFIM',      Decimal('3.6'), 'ENTREGUE'),
        ('Verde Menta Fachada',    'FRM-VERDE-MENTA', Decimal('36'),  'PRODUZIDA'),
        ('Azul Céu Infantil',      'FRM-AZUL-CEU',    Decimal('7.2'), 'ENTREGUE'),
        ('Terracota Sala',         'FRM-TERRACOTA',   Decimal('14.4'),'PRODUZIDA'),
    ]

    for cliente_nome, cod_frm, vol, situacao in misturas_dados:
        frm = formulas[cod_frm]
        custo_pig = sum(
            it.quantidade * Decimal('0.0350')
            for it in frm.itens.all()
        )
        custo_base = vol * Decimal('10.00')
        custo_total = custo_base + custo_pig

        mistura, m_created = MisturaTinta.objects.get_or_create(
            formula=frm,
            cliente_nome=cliente_nome,
            defaults=dict(
                loja=loja_sp,
                usuario_operacao=admin,
                volume_solicitado=vol,
                volume_produzido=vol,
                custo_base=custo_base,
                custo_pigmentos=custo_pig,
                custo_total=custo_total,
                situacao=situacao,
                cor_aprovada_cliente=True,
            )
        )

        if m_created:
            for seq_i, item_frm in enumerate(frm.itens.all(), start=1):
                qtd_calc = (item_frm.quantidade / Decimal('1000')) * vol
                custo_u = Decimal('0.0350')
                ItemMistura.objects.get_or_create(
                    mistura=mistura,
                    pigmento=item_frm.pigmento,
                    defaults=dict(
                        quantidade_calculada=qtd_calc,
                        quantidade_executada=qtd_calc,
                        custo_unitario=custo_u,
                        custo_total=qtd_calc * custo_u,
                        sequencia=seq_i,
                    )
                )

    print(f"   ✅ {len(misturas_dados)} misturas")
    return pigmentos, cores


# ══════════════════════════════════════════════════════════════════════════════
# 8. CLIENTES
# ══════════════════════════════════════════════════════════════════════════════
def criar_clientes(vendedor):
    print("\n👥 Clientes...")

    clientes_dados = [
        # PF
        dict(
            codigo_cliente='CLI001',
            tipo_cliente='PF',
            nome='João da Silva Santos',
            cpf='12345678901',
            rg='345678900',
            data_nascimento=date(1985, 3, 15),
            telefone_principal='11987654321',
            email='joao.silva@email.com',
            cep='01310100',
            endereco='Rua Augusta', numero='500', bairro='Consolação',
            cidade='São Paulo', uf='SP',
            limite_credito=Decimal('2000.00'),
            categoria_cliente='REGULAR',
        ),
        dict(
            codigo_cliente='CLI002',
            tipo_cliente='PF',
            nome='Maria Aparecida Oliveira',
            cpf='98765432100',
            rg='123456789',
            data_nascimento=date(1978, 8, 22),
            telefone_principal='11912345678',
            telefone_secundario='1133221100',
            email='maria.oliveira@email.com',
            cep='04538133',
            endereco='Rua Joaquim Floriano', numero='100', bairro='Itaim Bibi',
            cidade='São Paulo', uf='SP',
            limite_credito=Decimal('5000.00'),
            categoria_cliente='VIP',
        ),
        dict(
            codigo_cliente='CLI003',
            tipo_cliente='PF',
            nome='Pedro Henrique Costa',
            cpf='45678912300',
            data_nascimento=date(1992, 11, 5),
            telefone_principal='11956789123',
            email='pedro.costa@email.com',
            cep='09210380',
            endereco='Av. Industrial', numero='1200', bairro='Vila Curuçá',
            cidade='Santo André', uf='SP',
            limite_credito=Decimal('1000.00'),
            categoria_cliente='NOVO',
        ),
        # PJ
        dict(
            codigo_cliente='CLI004',
            tipo_cliente='PJ',
            nome='Construtora ABC',
            razao_social='Construtora ABC LTDA',
            nome_fantasia='ABC Construções',
            cnpj='11222333000181',
            inscricao_estadual='999888777',
            telefone_principal='1133445566',
            email='financeiro@abcconstrucoes.com.br',
            cep='01415001',
            endereco='Rua Haddock Lobo', numero='595', bairro='Cerqueira César',
            cidade='São Paulo', uf='SP',
            limite_credito=Decimal('20000.00'),
            categoria_cliente='CONSTRUTORA',
        ),
        dict(
            codigo_cliente='CLI005',
            tipo_cliente='PJ',
            nome='Pinturas Express ME',
            razao_social='Pinturas Express Serviços ME',
            nome_fantasia='Pinturas Express',
            cnpj='55666777000190',
            inscricao_estadual='444333222',
            telefone_principal='1199887766',
            email='contato@pinturasexpress.com',
            cep='02010000',
            endereco='Rua Voluntários da Pátria', numero='4400', bairro='Santana',
            cidade='São Paulo', uf='SP',
            limite_credito=Decimal('8000.00'),
            categoria_cliente='PROFISSIONAL',
        ),
        # Cliente sem crédito (bloqueado)
        dict(
            codigo_cliente='CLI006',
            tipo_cliente='PF',
            nome='Antônio Carlos Pereira',
            cpf='11122233344',
            telefone_principal='11977665544',
            cep='08040000',
            endereco='Rua dos Ipês', numero='45', bairro='Penha',
            cidade='São Paulo', uf='SP',
            limite_credito=Decimal('0.00'),
            bloqueado_credito=True,
            motivo_bloqueio='Inadimplência anterior',
            categoria_cliente='BLOQUEADO',
        ),
    ]

    from django.db import IntegrityError

    clientes = {}
    for dados in clientes_dados:
        cod = dados.pop('codigo_cliente')
        tipo = dados.get('tipo_cliente')
        dados['vendedor_responsavel'] = vendedor

        try:
            cliente, _ = Cliente.objects.update_or_create(
                codigo_cliente=cod,
                defaults=dados,
            )
        except IntegrityError:
            # CPF/CNPJ already belongs to another record — fetch or create without unique fields
            cpf  = dados.pop('cpf', None)
            cnpj = dados.pop('cnpj', None)
            if cpf:
                cliente = Cliente.objects.filter(cpf=cpf).first()
            elif cnpj:
                cliente = Cliente.objects.filter(cnpj=cnpj).first()
            else:
                cliente = Cliente.objects.filter(codigo_cliente=cod).first()
            if not cliente:
                # Last resort: create without cpf/cnpj to avoid constraint
                cliente = Cliente.objects.create(codigo_cliente=cod, **dados)

        clientes[cod] = cliente
        print(f"   ✅ {cod} — {cliente.nome} ({tipo})")

    return clientes


# ══════════════════════════════════════════════════════════════════════════════
# 9. PEDIDOS, VENDAS, PAGAMENTOS E RECEBÍVEIS
# ══════════════════════════════════════════════════════════════════════════════
def criar_vendas(loja_sp, admin, vendedor, clientes, variacoes):
    print("\n🛒 Pedidos e Vendas...")

    # Definição dos pedidos
    # (numero, cliente_cod, situacao, forma_pagto, itens: [(cod_var, qtd, preco)], obs)
    pedidos_dados = [
        (
            'PED001', 'CLI001', 'ENTREGUE', 'DINHEIRO',
            [
                ('TINTA-ACRIL-INT-3.6L', Decimal('2'), Decimal('49.90')),
                ('ROLO-PINTURA-UN',      Decimal('1'), Decimal('15.90')),
            ],
            'Reforma sala de estar'
        ),
        (
            'PED002', 'CLI002', 'ENTREGUE', 'PIX',
            [
                ('BASE-TINT-BRANCA-3.6L', Decimal('4'), Decimal('75.00')),
                ('BASE-TINT-MEDIA-3.6L',  Decimal('2'), Decimal('78.00')),
                ('PINCEL-2POL-UN',         Decimal('3'), Decimal('9.90')),
            ],
            'Tintometria apartamento'
        ),
        (
            'PED003', 'CLI004', 'ENTREGUE', 'CREDIARIO',
            [
                ('TINTA-ACRIL-EXT-18L',   Decimal('3'), Decimal('249.90')),
                ('PRIMER-ACRIL-18L',       Decimal('2'), Decimal('159.00')),
                ('TINTA-ACRIL-INT-18L',    Decimal('5'), Decimal('219.90')),
            ],
            'Obra residencial 400m²'
        ),
        (
            'PED004', 'CLI005', 'ENTREGUE', 'CARTAO_CREDITO',
            [
                ('VERNIZ-MAD-3.6L',  Decimal('6'), Decimal('59.90')),
                ('AGUARRAS-1L',      Decimal('4'), Decimal('21.90')),
                ('FITA-CREPE-UN',    Decimal('10'), Decimal('5.90')),
            ],
            'Acabamento marcenaria'
        ),
        (
            'PED005', 'CLI001', 'APROVADO', 'PIX',
            [
                ('TINTA-ACRIL-INT-3.6L', Decimal('1'), Decimal('49.90')),
                ('PRIMER-ACRIL-3.6L',    Decimal('1'), Decimal('35.00')),
            ],
            'Quarto de hóspedes'
        ),
        (
            'PED006', 'CLI003', 'ORCAMENTO', 'DINHEIRO',
            [
                ('TINTA-ACRIL-EXT-3.6L', Decimal('3'), Decimal('55.90')),
                ('ROLO-PINTURA-UN',      Decimal('2'), Decimal('15.90')),
            ],
            'Orçamento fachada'
        ),
        (
            'PED007', 'CLI002', 'ENTREGUE', 'FIADO',
            [
                ('TINTA-ACRIL-INT-3.6L', Decimal('2'), Decimal('49.90')),
                ('PINCEL-2POL-UN',        Decimal('2'), Decimal('9.90')),
            ],
            'Pintura corredor'
        ),
        (
            'PED008', 'CLI004', 'PRODUCAO', 'CARTAO_DEBITO',
            [
                ('BASE-TINT-BRANCA-18L',  Decimal('4'), Decimal('350.00')),
                ('BASE-TINT-MEDIA-3.6L',  Decimal('6'), Decimal('78.00')),
            ],
            'Grande encomenda tintométrica'
        ),
    ]

    vendas_criadas = 0
    recebiveis_criados = 0

    for (num_ped, cli_cod, situacao, forma_pag, itens_dados, obs) in pedidos_dados:
        cliente = clientes[cli_cod]

        subtotal = sum(qtd * preco for _, qtd, preco in itens_dados)

        pedido, ped_created = PedidoVenda.objects.get_or_create(
            numero_pedido=num_ped,
            defaults=dict(
                loja=loja_sp,
                cliente=cliente,
                vendedor=vendedor,
                situacao=situacao,
                valor_subtotal=subtotal,
                valor_desconto=Decimal('0.00'),
                valor_total=subtotal,
                forma_pagamento=forma_pag,
                tipo_entrega='BALCAO',
                observacoes=obs,
            )
        )

        if ped_created:
            for seq, (cod_var, qtd, preco) in enumerate(itens_dados, start=1):
                var = variacoes[cod_var]
                ItemPedidoVenda.objects.create(
                    pedido=pedido,
                    produto_variacao=var,
                    quantidade=qtd,
                    preco_unitario=preco,
                    preco_total=qtd * preco,
                    sequencia=seq,
                )

        print(f"   ✅ Pedido {num_ped} ({situacao}) R$ {subtotal:.2f}")

        # Cria Venda para pedidos entregues
        if situacao == 'ENTREGUE':
            num_venda = num_ped.replace('PED', 'VDA')
            venda, v_created = Venda.objects.get_or_create(
                numero_venda=num_venda,
                defaults=dict(
                    pedido_origem=pedido,
                    loja=loja_sp,
                    cliente=cliente,
                    vendedor=vendedor,
                    valor_total=subtotal,
                    valor_desconto=Decimal('0.00'),
                    valor_liquido=subtotal,
                    nfe_situacao='NAO_APLICAVEL',
                    cancelada=False,
                )
            )

            if v_created:
                vendas_criadas += 1
                if forma_pag == 'CREDIARIO':
                    entrada = round(subtotal * Decimal('0.30'), 2)
                    saldo = subtotal - entrada
                    PagamentoVenda.objects.create(
                        venda=venda, forma='DINHEIRO',
                        valor=entrada, valor_recebido=entrada, troco=Decimal('0')
                    )
                    PagamentoVenda.objects.create(
                        venda=venda, forma='CREDIARIO', valor=saldo
                    )
                    venc = date.today() + timedelta(days=30)
                    Recebivel.objects.create(
                        cliente=cliente, venda=venda, loja=loja_sp,
                        valor_original=saldo,
                        valor_pago=Decimal('0.00'),
                        valor_saldo=saldo,
                        data_vencimento=venc,
                        situacao='ABERTO',
                    )
                    recebiveis_criados += 1
                    print(f"      💳 Crediário: entrada R$ {entrada:.2f}, saldo R$ {saldo:.2f}")

                elif forma_pag == 'FIADO':
                    PagamentoVenda.objects.create(
                        venda=venda, forma='FIADO', valor=subtotal
                    )
                    venc = date.today() + timedelta(days=15)
                    Recebivel.objects.create(
                        cliente=cliente, venda=venda, loja=loja_sp,
                        valor_original=subtotal,
                        valor_pago=Decimal('0.00'),
                        valor_saldo=subtotal,
                        data_vencimento=venc,
                        situacao='ABERTO',
                    )
                    recebiveis_criados += 1
                    print(f"      📋 Fiado: R$ {subtotal:.2f} vence {venc}")

                elif forma_pag == 'DINHEIRO':
                    troco = Decimal('10.00')
                    PagamentoVenda.objects.create(
                        venda=venda, forma='DINHEIRO',
                        valor=subtotal,
                        valor_recebido=subtotal + troco,
                        troco=troco,
                    )
                else:
                    PagamentoVenda.objects.create(
                        venda=venda, forma=forma_pag, valor=subtotal
                    )

                print(f"      ✅ Venda {num_venda} R$ {subtotal:.2f} [{forma_pag}]")

    print(f"   ✅ {vendas_criadas} vendas criadas, {recebiveis_criados} recebíveis")


# ══════════════════════════════════════════════════════════════════════════════
# 10. CONFIGURAÇÃO FISCAL + NOTAS FISCAIS
# ══════════════════════════════════════════════════════════════════════════════
def criar_fiscal(empresa, loja_sp):
    print("\n🧾 Dados Fiscais...")

    # 10.1 Configuração fiscal
    config, _ = ConfiguracaoFiscal.objects.get_or_create(
        empresa=empresa,
        loja=loja_sp,
        defaults=dict(
            regime_tributario='SIMPLES_NACIONAL',
            nfe_ativo=True,
            nfe_ambiente='HOMOLOGACAO',
            nfe_serie=1,
            nfe_numero_atual=10,
            nfce_ativo=True,
            nfce_ambiente='HOMOLOGACAO',
            nfce_serie=1,
            nfce_numero_atual=5,
            sat_ativo=False,
        )
    )
    print("   ✅ ConfiguracaoFiscal: Simples Nacional / Homologação")

    # 10.2 Notas fiscais — vinculadas às vendas criadas
    vendas = list(Venda.objects.filter(loja=loja_sp).order_by('created_at')[:3])
    if not vendas:
        print("   ⚠️  Nenhuma venda encontrada para vincular NF")
        return

    nf_dados = [
        # (venda_idx, tipo, serie, numero, situacao, chave)
        (0, 'NFCE', 1, 1, 'AUTORIZADA', '35240112345678000195650010000000011234567890'),
        (1, 'NFCE', 1, 2, 'AUTORIZADA', '35240112345678000195650010000000021234567891'),
        (2, 'NFE',  1, 1, 'AUTORIZADA', '35240112345678000195550010000000011234567892'),
    ]

    for venda_idx, tipo, serie, numero, situacao, chave in nf_dados:
        if venda_idx >= len(vendas):
            continue

        venda = vendas[venda_idx]
        valor = venda.valor_liquido

        nf, nf_created = NotaFiscal.objects.get_or_create(
            loja=loja_sp,
            tipo_nota=tipo,
            serie=serie,
            numero=numero,
            defaults=dict(
                venda=venda,
                chave_acesso=chave,
                situacao=situacao,
                data_autorizacao=timezone.now(),
                protocolo_autorizacao=f'1350240{numero:010d}',
                valor_total_produtos=valor,
                valor_total_nota=valor,
                valor_desconto=Decimal('0.00'),
                base_calculo_icms=valor,
                valor_icms=round(valor * Decimal('0.04'), 2),
                valor_pis=round(valor * Decimal('0.0065'), 2),
                valor_cofins=round(valor * Decimal('0.03'), 2),
                informacoes_adicionais='Documento emitido em ambiente de homologação. Sem valor fiscal.',
            )
        )

        if nf_created:
            # Itens da NF (1 item resumido)
            ItemNotaFiscal.objects.create(
                nota_fiscal=nf,
                codigo_produto='VARIOS',
                descricao='Produtos de pintura conforme pedido',
                ncm='32091010',   # NCM Tintas base água
                cfop='5102',      # Venda de mercadoria industrializada
                quantidade=Decimal('1'),
                unidade='CJ',
                valor_unitario=valor,
                valor_total=valor,
                valor_desconto=Decimal('0.00'),
                cst_icms='102',
                aliquota_icms=Decimal('4.00'),
                base_calculo_icms=valor,
                valor_icms=round(valor * Decimal('0.04'), 2),
                cst_pis='07',
                aliquota_pis=Decimal('0.65'),
                base_calculo_pis=valor,
                valor_pis=round(valor * Decimal('0.0065'), 2),
                cst_cofins='07',
                aliquota_cofins=Decimal('3.00'),
                base_calculo_cofins=valor,
                valor_cofins=round(valor * Decimal('0.03'), 2),
                numero_item=1,
            )
            print(f"   ✅ {tipo} {serie}/{numero} — R$ {valor:.2f} [{situacao}]")

    print("   ✅ Notas fiscais criadas")


# ══════════════════════════════════════════════════════════════════════════════
# MAIN
# ══════════════════════════════════════════════════════════════════════════════
def main():
    parser = argparse.ArgumentParser(description='Seed completo Atalaia Tintas')
    parser.add_argument('--limpar', action='store_true',
                        help='Remove todos os dados antes de recriar (⚠️  irreversível!)')
    args = parser.parse_args()

    print("=" * 65)
    print("🚀  SEED COMPLETO — ATALAIA TINTAS")
    print("=" * 65)

    if args.limpar:
        confirm = input("\n⚠️  ATENÇÃO: --limpar apagará TODOS os dados. Digite 'CONFIRMAR': ")
        if confirm != 'CONFIRMAR':
            print("Operação cancelada.")
            sys.exit(0)
        limpar_dados()

    try:
        admin, gerente, vendedor, caixa = criar_usuarios()
        empresa, loja_sp, loja_abc = criar_empresa_loja(admin, gerente, vendedor, caixa)
        unidades = criar_unidades()
        cats, marcas = criar_categorias_marcas()
        produtos_base, variacoes = criar_produtos(cats, marcas, unidades)
        criar_estoque(loja_sp, loja_abc, variacoes)
        criar_tintometria(loja_sp, admin, variacoes)
        clientes = criar_clientes(vendedor)
        criar_vendas(loja_sp, admin, vendedor, clientes, variacoes)
        criar_fiscal(empresa, loja_sp)

        print("\n" + "=" * 65)
        print("✨  CARGA FINALIZADA COM SUCESSO!")
        print("=" * 65)
        print()
        print("🌐  Admin:    http://127.0.0.1:8000/admin/")
        print("   • admin    / admin123     [superuser]")
        print("   • gerente  / gerente123   [staff]")
        print("   • vendedor / vendedor123")
        print("   • caixa    / caixa123")
        print()
        print("📊  API:      http://127.0.0.1:8000/api/v1/")
        print("🖥️   Frontend: http://localhost:3002/")
        print()
        print("📦  Resumo dos dados criados:")
        from apps.inventory.models import ProdutoVariacao, EstoqueLoja
        from apps.sales.models import Venda, Recebivel
        from apps.fiscal.models import NotaFiscal
        print(f"   • Usuários:        {User.objects.count()}")
        print(f"   • Produtos (var.): {ProdutoVariacao.objects.count()}")
        print(f"   • Estoque (entr.): {EstoqueLoja.objects.count()}")
        print(f"   • Clientes:        {Cliente.objects.count()}")
        print(f"   • Pedidos:         {PedidoVenda.objects.count()}")
        print(f"   • Vendas:          {Venda.objects.count()}")
        print(f"   • Recebíveis:      {Recebivel.objects.count()}")
        print(f"   • Notas Fiscais:   {NotaFiscal.objects.count()}")

    except Exception as exc:
        import traceback
        print(f"\n❌ ERRO: {exc}")
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()

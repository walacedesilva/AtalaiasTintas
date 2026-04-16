"""
Seed script: carga de dados de demonstração visual para cliente.
Execução:
    cd C:\Atalaia\AtalaiasTintas\backend
    C:\Atalaia\AtalaiasTintas\.venv\Scripts\python.exe seed_demo_visual.py
"""
import sys
import os
from decimal import Decimal
from datetime import date, timedelta

# Setup Django
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

User = get_user_model()


# ──────────────────────────────────────────────────────────────────────────────
# 1. USUARIOS
# ──────────────────────────────────────────────────────────────────────────────
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
    print(f"   ✅ admin / admin123")

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
    print(f"   ✅ vendedor / vendedor123")

    return admin, vendedor


# ──────────────────────────────────────────────────────────────────────────────
# 2. EMPRESA + LOJA + USUARIO_LOJA
# ──────────────────────────────────────────────────────────────────────────────
def criar_empresa_loja(admin, vendedor):
    print("\n🏢 Empresa e Loja...")

    empresa, _ = Empresa.objects.get_or_create(
        cnpj='12345678000199',
        defaults=dict(
            razao_social='Atalaia Tintas LTDA',
            nome_fantasia='Atalaia Tintas',
            ativa=True,
        )
    )
    print(f"   ✅ Empresa: {empresa.nome_fantasia}")

    # Usa a primeira loja ativa da empresa (ou cria se não existir)
    loja = Loja.objects.filter(empresa=empresa, ativa=True).order_by('id').first()
    if not loja:
        loja = Loja.objects.create(
            empresa=empresa,
            codigo='LJ001',
            nome='Loja Principal',
            cidade='São Paulo',
            uf='SP',
            cep='01310000',
            endereco='Av. Paulista',
            numero='1000',
            bairro='Bela Vista',
            ativa=True,
        )
    print(f"   ✅ Loja: {loja.nome} (id={loja.id})")

    for usuario in (admin, vendedor):
        UsuarioLoja.objects.get_or_create(
            usuario=usuario,
            loja=loja,
            defaults=dict(
                empresa=empresa,
                pode_vender=True,
                pode_gerenciar_estoque=True,
                pode_acessar_caixa=True,
                pode_dar_desconto=True,
                limite_desconto_percentual=Decimal('15.00'),
                ativo=True,
            )
        )
        print(f"   ✅ UsuarioLoja: {usuario.username} ↔ {loja.codigo}")

    return empresa, loja


# ──────────────────────────────────────────────────────────────────────────────
# 3. UNIDADES DE MEDIDA
# ──────────────────────────────────────────────────────────────────────────────
def criar_unidades():
    print("\n📏 Unidades de medida...")

    dados = [
        ('L',    'Litro',      'L',   'VOLUME'),
        ('ML',   'Mililitro',  'ml',  'VOLUME'),
        ('LATA', 'Lata',       'lt',  'UNIDADE'),
        ('GL',   'Galão',      'gl',  'VOLUME'),
        ('KG',   'Quilograma', 'kg',  'PESO'),
        ('UN',   'Unidade',    'un',  'UNIDADE'),
    ]
    unidades = {}
    for codigo, nome, sigla, tipo in dados:
        u, _ = UnidadeMedida.objects.get_or_create(
            codigo=codigo,
            defaults=dict(nome=nome, sigla=sigla, tipo=tipo)
        )
        unidades[codigo] = u
        print(f"   ✅ {u}")
    return unidades


# ──────────────────────────────────────────────────────────────────────────────
# 4. CATEGORIAS E MARCAS
# ──────────────────────────────────────────────────────────────────────────────
def criar_categorias_marcas():
    print("\n🗂️ Categorias e marcas...")

    cats = {}
    for codigo, nome, tint in [
        ('TINTAS',      'Tintas',              False),
        ('BASES-TINT',  'Bases Tintométricas', True),
        ('PRIMERS',     'Primers e Fundos',    False),
        ('VERNIZES',    'Vernizes e Seladores', False),
        ('FERRAMENTAS', 'Ferramentas',          False),
        ('ACESSORIOS',  'Acessórios',           False),
    ]:
        c, _ = Categoria.objects.get_or_create(
            codigo=codigo,
            defaults=dict(nome=nome, permite_tintometria=tint, ativa=True)
        )
        cats[codigo] = c
        print(f"   ✅ Categoria: {nome}")

    marcas = {}
    for codigo, nome in [
        ('TINTASYS',  'TintaSystem'),
        ('SUVINIL',   'Suvinil'),
        ('CORAL',     'Coral'),
        ('SHERWIN',   'Sherwin-Williams'),
        ('GENERICO',  'Genérico'),
    ]:
        m, _ = Marca.objects.get_or_create(
            codigo=codigo,
            defaults=dict(nome=nome, ativa=True)
        )
        marcas[codigo] = m
        print(f"   ✅ Marca: {nome}")

    return cats, marcas


# ──────────────────────────────────────────────────────────────────────────────
# 5. PRODUTOS
# ──────────────────────────────────────────────────────────────────────────────
def criar_produtos(cats, marcas, unidades):
    print("\n🎨 Produtos...")

    produtos_base_dados = [
        # (codigo, nome, tipo, categoria, marca)
        ('BASE-ACR-PRE', 'Base Acrílica Premium',     'INSUMO',  'BASES-TINT',  'TINTASYS'),
        ('TINTA-ACR-18', 'Tinta Acrílica Premium 18L','SIMPLES', 'TINTAS',      'SUVINIL'),
        ('TINTA-ACR-36', 'Tinta Acrílica Premium 3,6L','SIMPLES','TINTAS',      'SUVINIL'),
        ('PRIMER-BASE',  'Primer Selador Acrílico',    'SIMPLES', 'PRIMERS',     'CORAL'),
        ('VERNIZ-ANT',   'Verniz Antioxidante',        'SIMPLES', 'VERNIZES',    'SHERWIN'),
        ('ROLO-MOUTON',  'Rolo de Lã de Carneiro 23cm','SIMPLES', 'FERRAMENTAS', 'GENERICO'),
        ('PINCEL-3',     'Pincel Nylon 3"',             'SIMPLES', 'FERRAMENTAS', 'GENERICO'),
    ]

    variacoes_dados = [
        # (codigo_base, codigo_var, nome_var, tamanho, preco_custo, preco_venda, unid_venda, unid_estoque)
        ('BASE-ACR-PRE', '3.6L',  'Base Acrílica Premium 3,6L',  '3.6L',  22.00, 35.00, 'L',    'L'),
        ('BASE-ACR-PRE', '18L',   'Base Acrílica Premium 18L',   '18L',   95.00, 145.00,'L',    'L'),
        ('TINTA-ACR-18', 'BRANCO-18L', 'Tinta Acrílica Branco 18L', '18L', 85.00, 135.00,'L',    'L'),
        ('TINTA-ACR-18', 'AREIA-18L',  'Tinta Acrílica Areia 18L',  '18L', 85.00, 135.00,'L',    'L'),
        ('TINTA-ACR-36', 'BRANCO-36L', 'Tinta Acrílica Branco 3,6L', '3,6L', 19.00, 32.00,'L',   'L'),
        ('PRIMER-BASE',  '18L',   'Primer Selador 18L',           '18L',  72.00, 110.00, 'L',    'L'),
        ('VERNIZ-ANT',   '900ML', 'Verniz Antioxidante 900ml',    '900ml', 28.00, 45.00, 'ML',   'ML'),
        ('ROLO-MOUTON',  'UN',    'Rolo de Lã de Carneiro 23cm',  'UN',    12.50, 22.00,  'UN',   'UN'),
        ('PINCEL-3',     'UN',    'Pincel Nylon 3"',               'UN',    6.00,  12.00,  'UN',   'UN'),
    ]

    produtos_base = {}
    for codigo, nome, tipo, cat_cod, marca_cod in produtos_base_dados:
        pb, _ = ProdutoBase.objects.get_or_create(
            codigo=codigo,
            defaults=dict(
                nome=nome,
                tipo_produto=tipo,
                categoria=cats[cat_cod],
                marca=marcas[marca_cod],
                base_tintometrica='ACRILICO' if tipo == 'INSUMO' else None,
                ativo=True,
            )
        )
        produtos_base[codigo] = pb
        print(f"   ✅ ProdutoBase: {nome}")

    variacoes = {}
    for cod_base, cod_var, nome_var, tamanho, custo, venda, unid_v, unid_e in variacoes_dados:
        pv, _ = ProdutoVariacao.objects.get_or_create(
            produto_base=produtos_base[cod_base],
            codigo_variacao=cod_var,
            defaults=dict(
                nome_variacao=nome_var,
                tamanho=tamanho,
                unidade_venda=unidades[unid_v],
                unidade_estoque=unidades[unid_e],
                preco_custo=Decimal(str(custo)),
                preco_venda=Decimal(str(venda)),
                margem_lucro=round((venda - custo) / custo * 100, 2),
                estoque_minimo=Decimal('5.00'),
                ncm='32081099',
                ativo=True,
            )
        )
        variacoes[f"{cod_base}_{cod_var}"] = pv
        print(f"   ✅ Variação: {nome_var}")

    return produtos_base, variacoes


# ──────────────────────────────────────────────────────────────────────────────
# 6. ESTOQUE
# ──────────────────────────────────────────────────────────────────────────────
def criar_estoque(loja, variacoes):
    print("\n📦 Estoque...")

    estoques = {
        'BASE-ACR-PRE_3.6L':    120.0,
        'BASE-ACR-PRE_18L':      54.0,
        'TINTA-ACR-18_BRANCO-18L': 36.0,
        'TINTA-ACR-18_AREIA-18L':  18.0,
        'TINTA-ACR-36_BRANCO-36L': 72.0,
        'PRIMER-BASE_18L':         24.0,
        'VERNIZ-ANT_900ML':        48.0,
        'ROLO-MOUTON_UN':          30.0,
        'PINCEL-3_UN':             50.0,
    }

    for chave, qtd in estoques.items():
        if chave not in variacoes:
            continue
        el, created = EstoqueLoja.objects.get_or_create(
            loja=loja,
            produto_variacao=variacoes[chave],
            defaults=dict(quantidade_atual=Decimal(str(qtd)))
        )
        if not created:
            el.quantidade_atual = Decimal(str(qtd))
            el.save()
        print(f"   ✅ Estoque {chave}: {qtd}")


# ──────────────────────────────────────────────────────────────────────────────
# 7. TINTOMETRIA
# ──────────────────────────────────────────────────────────────────────────────
def criar_tintometria(loja, admin, variacoes):
    print("\n🔬 Tintometria...")

    # (codigo, nome, cor_base, r, g, b, densidade, poder_tintorial, concentracao_maxima, custo_ml)
    pig_dados = [
        ('PIG001', 'Azul Ftalocianina', 'Azul',    0,  0,  255, '1.1200', '95.00', '30.00', '0.0800'),
        ('PIG002', 'Vermelho Óxido',    'Vermelho', 220, 60, 60, '1.3500', '88.00', '25.00', '0.1200'),
        ('PIG003', 'Amarelo Cromo',     'Amarelo',  255,204,  0, '1.2800', '90.00', '20.00', '0.1000'),
        ('PIG004', 'Preto Carbono',     'Preto',     30, 30, 30, '1.8000', '99.00', '10.00', '0.1500'),
        ('PIG005', 'Branco Titânio',    'Branco',   255,255, 255,'3.9000', '100.0', '50.00', '0.0600'),
    ]
    pigmentos = []
    for cod, nome, cor_base, r, g, b, dens, poder, conc_max, custo_ml in pig_dados:
        p, _ = Pigmento.objects.get_or_create(
            codigo=cod,
            defaults=dict(
                nome=nome,
                cor_base=cor_base,
                r=r, g=g, b=b,
                densidade=Decimal(dens),
                poder_tintorial=Decimal(poder),
                concentracao_maxima=Decimal(conc_max),
                fornecedor='Pigmentos Brasil LTDA',
                ativo=True,
            )
        )
        pigmentos.append(p)
        print(f"   ✅ Pigmento: {nome}")

    for pig, (_, _, _, _, _, _, _, _, _, custo_ml) in zip(pigmentos, pig_dados):
        EstoquePigmento.objects.get_or_create(
            pigmento=pig,
            loja=loja,
            defaults=dict(
                saldo_ml=Decimal('5000.00'),
                saldo_minimo=Decimal('500.00'),
                saldo_maximo=Decimal('10000.00'),
                custo_ml=Decimal(custo_ml),
                lote_atual='LOTE2026001',
                ativo=True,
            )
        )

    # (codigo, nome, familia, linha, r, g, b, l, a, b_val)
    cores_dados = [
        ('AZ2026.001', 'Azul Real Premium',  'Azuis',     'Premium', 30,  64, 175, '15.200', '-45.800', '-30.100'),
        ('VD2026.001', 'Verde Esmeralda',    'Verdes',    'Premium', 16, 185,  65, '28.500', '-50.200',  '20.300'),
        ('AM2026.001', 'Amarelo Ouro',       'Amarelos',  'Standard',255,204,   0, '85.200',  '70.100',  '75.400'),
        ('VI2026.001', 'Violeta Intenso',    'Roxos',     'Premium', 138, 43, 226, '22.300', '-15.600', '-40.500'),
        ('BR2026.001', 'Branco Puro',        'Neutros',   'Standard',255,255, 255, '95.000',   '0.500',   '1.200'),
    ]
    cores = {}
    for cod, nome, familia, linha, r, g, b, l_val, a_val, b_val in cores_dados:
        cor, _ = LequeCorDefinida.objects.get_or_create(
            codigo_cor=cod,
            defaults=dict(
                nome_cor=nome,
                familia_cor=familia,
                linha_produto=linha,
                r=r, g=g, b=b,
                l_value=Decimal(l_val),
                a_value=Decimal(a_val),
                b_value=Decimal(b_val),
                ativo=True,
            )
        )
        cores[cod] = cor
        print(f"   ✅ Cor: {nome}")

    # Fórmula principal (Azul Real, base 3.6L)
    variacao_base = variacoes.get('BASE-ACR-PRE_3.6L')
    if variacao_base:
        formula, created = FormulaTintometrica.objects.get_or_create(
            codigo_formula='FRM001',
            defaults=dict(
                nome_formula='Azul Real - 3,6L',
                cor_definida=cores['AZ2026.001'],
                base_produto=variacao_base,
                volume_base=Decimal('3.6'),
                versao='1.0',
                aprovada=True,
                testada=True,
                ativa=True,
            )
        )
        if created:
            ItemFormula.objects.create(formula=formula, pigmento=pigmentos[0], quantidade=Decimal('32.5'))
            ItemFormula.objects.create(formula=formula, pigmento=pigmentos[3], quantidade=Decimal('2.8'))
        print(f"   ✅ Fórmula: {formula.nome_formula}")

        # Misturas de demonstração
        for i, (cod, cliente_nome, situacao) in enumerate([
            ('MIX2026001', 'João da Silva',    'CONFIRMADA'),
            ('MIX2026002', 'Maria Oliveira',   'CONFIRMADA'),
            ('MIX2026003', 'Pedro Construções','CALCULADA'),
        ], 1):
            mistura, _ = MisturaTinta.objects.get_or_create(
                codigo_mistura=cod,
                defaults=dict(
                    formula=formula,
                    loja=loja,
                    usuario_operacao=admin,
                    situacao=situacao,
                    volume_solicitado=Decimal('3.6'),
                    volume_produzido=Decimal('3.6') if situacao == 'CONFIRMADA' else Decimal('0'),
                    custo_total=Decimal('92.50'),
                    custo_base=Decimal('25.50'),
                    custo_pigmentos=Decimal('67.00'),
                    cliente_nome=cliente_nome,
                    cliente_telefone=f'(11) 9876{i}-432{i}',
                    observacoes_cliente='Cor igual à amostra apresentada',
                )
            )
            print(f"   ✅ Mistura: {cod} ({cliente_nome})")


# ──────────────────────────────────────────────────────────────────────────────
# 8. CLIENTES
# ──────────────────────────────────────────────────────────────────────────────
def criar_clientes():
    print("\n👥 Clientes...")

    clientes_dados = [
        dict(
            codigo_cliente='CLI001', tipo_cliente='PF',
            nome='João da Silva', cpf='12345678901',
            telefone_principal='(11) 98765-4321',
            email='joao.silva@email.com',
            endereco='Rua das Flores', numero='123', bairro='Centro',
            cidade='São Paulo', uf='SP', cep='01310100',
            limite_credito=Decimal('500.00'),
        ),
        dict(
            codigo_cliente='CLI002', tipo_cliente='PF',
            nome='Maria Oliveira Santos', cpf='98765432100',
            telefone_principal='(11) 91234-5678',
            email='maria.oliveira@email.com',
            endereco='Av. Paulista', numero='1578', bairro='Bela Vista',
            cidade='São Paulo', uf='SP', cep='01310200',
            limite_credito=Decimal('1000.00'),
        ),
        dict(
            codigo_cliente='CLI003', tipo_cliente='PJ',
            nome='Pedro Construções', razao_social='Pedro Construções LTDA',
            nome_fantasia='Pedro Construções',
            cnpj='98765432000100',
            telefone_principal='(11) 3345-6789',
            email='contato@pedroconstrucoes.com.br',
            endereco='Rua Industrial', numero='500', bairro='Distrito Industrial',
            cidade='São Paulo', uf='SP', cep='04310200',
            limite_credito=Decimal('5000.00'),
        ),
        dict(
            codigo_cliente='CLI004', tipo_cliente='PF',
            nome='Ana Paula Rodrigues', cpf='11122233344',
            telefone_principal='(11) 94567-8901',
            email='ana.rodrigues@email.com',
            endereco='Rua dos Pinheiros', numero='88', bairro='Pinheiros',
            cidade='São Paulo', uf='SP', cep='05422020',
            limite_credito=Decimal('300.00'),
        ),
    ]

    clientes = {}
    for dados in clientes_dados:
        # Usa cpf/cnpj como lookup único; codigo_cliente fica nos defaults
        if dados.get('cpf'):
            lookup = {'cpf': dados['cpf']}
        else:
            lookup = {'cnpj': dados['cnpj']}
        defaults = {k: v for k, v in dados.items() if k not in lookup}
        c, created = Cliente.objects.update_or_create(
            **lookup,
            defaults=defaults,
        )
        clientes[dados['codigo_cliente']] = c
        print(f"   ✅ Cliente: {c.nome} ({'criado' if created else 'atualizado'})")
    return clientes


# ──────────────────────────────────────────────────────────────────────────────
# 9. PEDIDOS, VENDAS, PAGAMENTOS, RECEBIVEIS
# ──────────────────────────────────────────────────────────────────────────────
def criar_vendas(loja, admin, vendedor, clientes, variacoes):
    print("\n🛒 Pedidos e vendas...")

    v36 = variacoes.get('TINTA-ACR-36_BRANCO-36L')
    v18 = variacoes.get('TINTA-ACR-18_BRANCO-18L')
    areia18 = variacoes.get('TINTA-ACR-18_AREIA-18L')
    primer = variacoes.get('PRIMER-BASE_18L')
    rolo = variacoes.get('ROLO-MOUTON_UN')
    pincel = variacoes.get('PINCEL-3_UN')

    pedidos_dados = [
        # Pedido entregue + venda finalizada (PIX)
        dict(
            numero_pedido='PED-DEMO-001',
            cliente=clientes['CLI001'],
            vendedor=admin,
            situacao='ENTREGUE',
            forma_pagamento='PIX',
            itens=[
                (v36, Decimal('3.6'), Decimal('32.00')),
                (rolo, Decimal('1'),  Decimal('22.00')),
            ]
        ),
        # Pedido entregue + venda finalizada (DINHEIRO)
        dict(
            numero_pedido='PED-DEMO-002',
            cliente=clientes['CLI002'],
            vendedor=vendedor,
            situacao='ENTREGUE',
            forma_pagamento='DINHEIRO',
            itens=[
                (v18,    Decimal('18'), Decimal('135.00')),
                (areia18, Decimal('18'), Decimal('135.00')),
                (primer, Decimal('18'), Decimal('110.00')),
                (pincel, Decimal('2'),  Decimal('12.00')),
            ]
        ),
        # Pedido aprovado (CARTAO_CREDITO)
        dict(
            numero_pedido='PED-DEMO-003',
            cliente=clientes['CLI003'],
            vendedor=vendedor,
            situacao='APROVADO',
            forma_pagamento='CARTAO_CREDITO',
            itens=[
                (v18,    Decimal('54'), Decimal('135.00')),
                (primer, Decimal('36'), Decimal('110.00')),
            ]
        ),
        # Orçamento em aberto
        dict(
            numero_pedido='PED-DEMO-004',
            cliente=clientes['CLI004'],
            vendedor=admin,
            situacao='ORCAMENTO',
            forma_pagamento='PIX',
            itens=[
                (v36,  Decimal('3.6'), Decimal('32.00')),
                (rolo, Decimal('2'),   Decimal('22.00')),
                (pincel, Decimal('1'), Decimal('12.00')),
            ]
        ),
        # Pedido com crediário
        dict(
            numero_pedido='PED-DEMO-005',
            cliente=clientes['CLI001'],
            vendedor=vendedor,
            situacao='ENTREGUE',
            forma_pagamento='CREDIARIO',
            itens=[
                (v18, Decimal('18'), Decimal('135.00')),
                (rolo, Decimal('1'), Decimal('22.00')),
            ]
        ),
    ]

    for dados in pedidos_dados:
        itens = dados.pop('itens')
        subtotal = sum(
            qtd * preco
            for _, qtd, preco in itens
            if _ is not None
        )

        pedido, created = PedidoVenda.objects.get_or_create(
            numero_pedido=dados['numero_pedido'],
            defaults=dict(
                loja=loja,
                cliente=dados['cliente'],
                vendedor=dados['vendedor'],
                situacao=dados['situacao'],
                forma_pagamento=dados['forma_pagamento'],
                valor_subtotal=subtotal,
                valor_total=subtotal,
                parcelas=1,
                tipo_entrega='BALCAO',
                data_aprovacao=timezone.now() if dados['situacao'] != 'ORCAMENTO' else None,
                data_entrega_real=timezone.now() if dados['situacao'] == 'ENTREGUE' else None,
            )
        )
        print(f"   ✅ Pedido: {pedido.numero_pedido} [{pedido.situacao}] R$ {subtotal:.2f}")

        if created:
            for seq, (variacao, qtd, preco) in enumerate(itens, 1):
                if variacao is None:
                    continue
                ItemPedidoVenda.objects.create(
                    pedido=pedido,
                    produto_variacao=variacao,
                    quantidade=qtd,
                    preco_unitario=preco,
                    preco_total=qtd * preco,
                    sequencia=seq,
                )

        # Criar Venda para pedidos ENTREGUE
        if dados['situacao'] == 'ENTREGUE':
            num_venda = pedido.numero_pedido.replace('PED-', 'VND-')
            venda, v_created = Venda.objects.get_or_create(
                numero_venda=num_venda,
                defaults=dict(
                    pedido_origem=pedido,
                    loja=loja,
                    cliente=pedido.cliente,
                    vendedor=pedido.vendedor,
                    valor_total=subtotal,
                    valor_desconto=Decimal('0.00'),
                    valor_liquido=subtotal,
                    nfe_situacao='NAO_APLICAVEL',
                    cancelada=False,
                )
            )
            print(f"      ✅ Venda: {venda.numero_venda} R$ {subtotal:.2f}")

            if v_created:
                forma = dados['forma_pagamento']
                if forma == 'CREDIARIO':
                    # Entrada 30% + crediário
                    entrada = round(subtotal * Decimal('0.30'), 2)
                    saldo_cred = subtotal - entrada
                    PagamentoVenda.objects.create(
                        venda=venda, forma='DINHEIRO',
                        valor=entrada, valor_recebido=entrada, troco=Decimal('0')
                    )
                    PagamentoVenda.objects.create(
                        venda=venda, forma='CREDIARIO', valor=saldo_cred
                    )
                    # Recebível
                    vencimento = date.today() + timedelta(days=30)
                    Recebivel.objects.create(
                        cliente=pedido.cliente,
                        venda=venda,
                        loja=loja,
                        valor_original=saldo_cred,
                        valor_pago=Decimal('0.00'),
                        valor_saldo=saldo_cred,
                        data_vencimento=vencimento,
                        situacao='ABERTO',
                    )
                    print(f"      ✅ Recebível: R$ {saldo_cred:.2f} vence {vencimento}")
                elif forma == 'DINHEIRO':
                    PagamentoVenda.objects.create(
                        venda=venda, forma='DINHEIRO',
                        valor=subtotal, valor_recebido=round(subtotal + 10, 2),
                        troco=Decimal('10.00')
                    )
                else:
                    PagamentoVenda.objects.create(
                        venda=venda, forma=forma, valor=subtotal
                    )


# ──────────────────────────────────────────────────────────────────────────────
# MAIN
# ──────────────────────────────────────────────────────────────────────────────
def main():
    print("=" * 60)
    print("🚀  SEED DEMO VISUAL — ATALAIA TINTAS")
    print("=" * 60)

    try:
        admin, vendedor = criar_usuarios()
        empresa, loja = criar_empresa_loja(admin, vendedor)
        unidades = criar_unidades()
        cats, marcas = criar_categorias_marcas()
        produtos_base, variacoes = criar_produtos(cats, marcas, unidades)
        criar_estoque(loja, variacoes)
        criar_tintometria(loja, admin, variacoes)
        clientes = criar_clientes()
        criar_vendas(loja, admin, vendedor, clientes, variacoes)

        print("\n" + "=" * 60)
        print("✨  CARGA FINALIZADA COM SUCESSO!")
        print("=" * 60)
        print(f"\n🌐  Admin: http://127.0.0.1:8000/admin/")
        print(f"   • login: admin  /  admin123")
        print(f"   • login: vendedor  /  vendedor123")
        print(f"\n📊  API: http://127.0.0.1:8000/api/v1/")
        print(f"\n🖥️  Frontend: http://localhost:3002/")

    except Exception as exc:
        import traceback
        print(f"\n❌ ERRO: {exc}")
        traceback.print_exc()


if __name__ == '__main__':
    main()

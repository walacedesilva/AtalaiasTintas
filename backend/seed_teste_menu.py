"""
Seed de dados de teste para as funcionalidades do menu:
  Vendas, Pedidos, Clientes, Fiscal/NFe, Relatórios, Monitoramento e Configurações.

Execução:
    cd E:\\SIAFIC\\AtalaiasTintas\\backend
    python seed_teste_menu.py
"""
import sys
import os
from decimal import Decimal
from datetime import date, timedelta

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

# ─── Setup Django ─────────────────────────────────────────────────────────────
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'tintas_system.settings')

import django
django.setup()

from django.contrib.auth import get_user_model
from django.utils import timezone

from apps.companies.models import Empresa, Loja, UsuarioLoja
from apps.sales.models import Cliente, PedidoVenda, ItemPedidoVenda, Venda, PagamentoVenda, Recebivel
from apps.fiscal.models import ConfiguracaoFiscal, NotaFiscal, ItemNotaFiscal
from apps.monitoring.models import SystemHealth, AlertNotification
from apps.inventory.models import UnidadeMedida, Categoria, Marca, ProdutoBase, ProdutoVariacao, EstoqueLoja

User = get_user_model()


# ══════════════════════════════════════════════════════════════════════════════
# 1. USUÁRIOS
# ══════════════════════════════════════════════════════════════════════════════
def criar_usuarios():
    print("\n👤 Usuários...")

    admin, _ = User.objects.get_or_create(username='admin', defaults=dict(
        email='admin@atalaiatingas.com.br',
        first_name='Administrador', last_name='Sistema',
        is_staff=True, is_superuser=True,
    ))
    admin.set_password('admin123')
    admin.save()
    print("   ✅ admin / admin123  [superuser]")

    vendedor, _ = User.objects.get_or_create(username='vendedor', defaults=dict(
        email='vendedor@atalaiatingas.com.br',
        first_name='Carlos', last_name='Vendedor',
        is_staff=False,
    ))
    vendedor.set_password('vendedor123')
    vendedor.save()
    print("   ✅ vendedor / vendedor123")

    return admin, vendedor


# ══════════════════════════════════════════════════════════════════════════════
# 2. EMPRESA + LOJA
# ══════════════════════════════════════════════════════════════════════════════
def criar_empresa_loja(admin, vendedor):
    print("\n🏢 Empresa e Loja...")

    empresa, _ = Empresa.objects.get_or_create(
        cnpj='12345678000195',
        defaults=dict(
            razao_social='Atalaia Tintas LTDA',
            nome_fantasia='Atalaia Tintas',
            inscricao_estadual='111222333444',
            telefone='1133334444',
            email='contato@atalaiatingas.com.br',
            cep='01310200',
            endereco='Av. Paulista', numero='1578',
            bairro='Bela Vista', cidade='São Paulo', uf='SP',
            ativa=True,
        )
    )
    print(f"   ✅ Empresa: {empresa.razao_social}")

    loja, _ = Loja.objects.get_or_create(
        codigo='LJ001',
        defaults=dict(
            empresa=empresa,
            nome='Loja Principal SP',
            telefone='1133334444',
            email='sp@atalaiatingas.com.br',
            cep='01310200',
            endereco='Av. Paulista', numero='1578',
            bairro='Bela Vista', cidade='São Paulo', uf='SP',
            ativa=True,
        )
    )
    print(f"   ✅ Loja: {loja.nome}")

    for user in [admin, vendedor]:
        UsuarioLoja.objects.get_or_create(
            usuario=user, loja=loja,
            defaults=dict(empresa=empresa, pode_vender=True, pode_gerenciar_estoque=True, pode_acessar_caixa=True),
        )

    return empresa, loja


# ══════════════════════════════════════════════════════════════════════════════
# 3. PRODUTOS (necessário para pedidos/vendas)
# ══════════════════════════════════════════════════════════════════════════════
def criar_produtos(loja):
    print("\n📦 Produtos...")

    un, _ = UnidadeMedida.objects.get_or_create(codigo='UN', defaults=dict(nome='Unidade', sigla='UN', tipo='UNIDADE'))
    lt, _ = UnidadeMedida.objects.get_or_create(codigo='LT', defaults=dict(nome='Litro', sigla='LT', tipo='VOLUME'))

    cat, _ = Categoria.objects.get_or_create(nome='Tintas', defaults=dict(descricao='Tintas em geral'))
    marca, _ = Marca.objects.get_or_create(nome='Suvinil', defaults=dict(descricao='Suvinil'))

    produtos = []
    dados = [
        ('TINT-3.6L',  'Tinta Acrílica Branca 3,6L',   Decimal('89.90'),  'LT'),
        ('TINT-18L',   'Tinta Acrílica Branca 18L',     Decimal('349.90'), 'LT'),
        ('MASSA-25KG', 'Massa Corrida PVA 25kg',         Decimal('74.90'),  'UN'),
        ('LIXA-80',    'Lixa Grão 80',                   Decimal('4.50'),   'UN'),
        ('ROLO-23',    'Rolo de Lã 23cm',                Decimal('18.90'),  'UN'),
    ]

    for sku, nome, preco, unidade_sigla in dados:
        un_obj = lt if unidade_sigla == 'LT' else un
        base, _ = ProdutoBase.objects.get_or_create(
            codigo=sku,
            defaults=dict(
                nome=nome, categoria=cat, marca=marca,
                descricao=nome, tipo_produto='SIMPLES', ativo=True,
            )
        )
        variacao, _ = ProdutoVariacao.objects.get_or_create(
            codigo_variacao=sku,
            defaults=dict(
                produto_base=base,
                nome_variacao='Padrão',
                unidade_venda=un_obj, unidade_estoque=un_obj,
                preco_custo=preco * Decimal('0.6'),
                preco_venda=preco,
                ativo=True,
            )
        )
        EstoqueLoja.objects.get_or_create(
            produto_variacao=variacao, loja=loja,
            defaults=dict(quantidade_atual=Decimal('50')),
        )
        produtos.append(variacao)
        print(f"   ✅ {sku} - {nome}")

    return produtos


# ══════════════════════════════════════════════════════════════════════════════
# 4. CLIENTES
# ══════════════════════════════════════════════════════════════════════════════
def criar_clientes(vendedor):
    print("\n👥 Clientes...")

    clientes_dados = [
        dict(codigo_cliente='CLI001', tipo_cliente='PF', nome='João da Silva',
             cpf='11122233344', telefone_principal='11999990001',
             email='joao.silva@email.com', cidade='São Paulo', uf='SP',
             limite_credito=Decimal('5000.00')),
        dict(codigo_cliente='CLI002', tipo_cliente='PF', nome='Maria Oliveira',
             cpf='22233344455', telefone_principal='11999990002',
             email='maria.oliveira@email.com', cidade='São Paulo', uf='SP',
             limite_credito=Decimal('3000.00')),
        dict(codigo_cliente='CLI003', tipo_cliente='PJ',
             nome='Construtora ABC',
             razao_social='Construtora ABC LTDA',
             nome_fantasia='Construtora ABC',
             cnpj='98765432000100',
             telefone_principal='1133330001',
             email='compras@construtorabc.com.br',
             cidade='São Paulo', uf='SP',
             limite_credito=Decimal('50000.00')),
        dict(codigo_cliente='CLI004', tipo_cliente='PF', nome='Pedro Souza',
             cpf='33344455566', telefone_principal='11999990003',
             email='pedro.souza@email.com', cidade='Guarulhos', uf='SP',
             limite_credito=Decimal('2000.00')),
        dict(codigo_cliente='CLI005', tipo_cliente='PJ',
             nome='Pintura Rápida ME',
             razao_social='Pintura Rápida Serviços ME',
             nome_fantasia='Pintura Rápida',
             cnpj='11223344000155',
             telefone_principal='1144440001',
             email='contato@pinturapida.com.br',
             cidade='Santo André', uf='SP',
             limite_credito=Decimal('15000.00')),
    ]

    clientes = []
    for d in clientes_dados:
        cli, created = Cliente.objects.get_or_create(
            codigo_cliente=d['codigo_cliente'],
            defaults=dict(
                tipo_cliente=d['tipo_cliente'],
                nome=d['nome'],
                cpf=d.get('cpf'),
                razao_social=d.get('razao_social'),
                nome_fantasia=d.get('nome_fantasia'),
                cnpj=d.get('cnpj'),
                telefone_principal=d.get('telefone_principal'),
                email=d.get('email'),
                cidade=d.get('cidade'),
                uf=d.get('uf'),
                limite_credito=d['limite_credito'],
                vendedor_responsavel=vendedor,
                ativo=True,
            )
        )
        clientes.append(cli)
        status = 'criado' if created else 'já existe'
        print(f"   ✅ {cli.codigo_cliente} - {cli.nome}  [{status}]")

    return clientes


# ══════════════════════════════════════════════════════════════════════════════
# 5. PEDIDOS DE VENDA
# ══════════════════════════════════════════════════════════════════════════════
def criar_pedidos(loja, clientes, produtos, vendedor):
    print("\n📋 Pedidos...")

    pedidos_dados = [
        dict(numero='PED-2026-001', cliente=clientes[0], situacao='APROVADO',
             forma='PIX', obs='Entrega na obra'),
        dict(numero='PED-2026-002', cliente=clientes[2], situacao='PRODUCAO',
             forma='CARTAO_CREDITO', obs='Cliente corporativo'),
        dict(numero='PED-2026-003', cliente=clientes[1], situacao='ORCAMENTO',
             forma='DINHEIRO', obs=''),
        dict(numero='PED-2026-004', cliente=clientes[4], situacao='PRONTO',
             forma='TRANSFERENCIA', obs='Aguardando retirada'),
        dict(numero='PED-2026-005', cliente=clientes[3], situacao='ENTREGUE',
             forma='PIX', obs='Entregue ontem'),
    ]

    pedidos = []
    for d in pedidos_dados:
        if PedidoVenda.objects.filter(numero_pedido=d['numero']).exists():
            pedido = PedidoVenda.objects.get(numero_pedido=d['numero'])
            print(f"   ⏭  {d['numero']} já existe")
        else:
            pedido = PedidoVenda.objects.create(
                numero_pedido=d['numero'],
                loja=loja,
                cliente=d['cliente'],
                vendedor=vendedor,
                situacao=d['situacao'],
                forma_pagamento=d['forma'],
                observacoes=d['obs'],
            )
            # Adicionar 2 itens por pedido
            for i, prod in enumerate(produtos[:2]):
                qty = Decimal(str((i + 1) * 2))
                ItemPedidoVenda.objects.create(
                    pedido=pedido,
                    produto_variacao=prod,
                    sequencia=i + 1,
                    quantidade=qty,
                    preco_unitario=prod.preco_venda,
                    preco_total=prod.preco_venda * qty,
                    desconto_percentual=Decimal('0.00'),
                )
            print(f"   ✅ {d['numero']} [{d['situacao']}] - {d['cliente'].nome}")
        pedidos.append(pedido)

    return pedidos


# ══════════════════════════════════════════════════════════════════════════════
# 6. VENDAS
# ══════════════════════════════════════════════════════════════════════════════
def criar_vendas(loja, clientes, produtos, pedidos, vendedor):
    print("\n💰 Vendas...")

    vendas = []
    for i, (cli, ped) in enumerate(zip(clientes[:3], pedidos[:3])):
        num = f'VDA-2026-{i+1:03d}'
        if Venda.objects.filter(numero_venda=num).exists():
            v = Venda.objects.get(numero_venda=num)
            print(f"   ⏭  {num} já existe")
        else:
            total = sum(
                p.preco_venda * Decimal('2') for p in produtos[:2]
            )
            v = Venda.objects.create(
                numero_venda=num,
                loja=loja,
                cliente=cli,
                vendedor=vendedor,
                pedido_origem=ped,
                valor_total=total,
                valor_desconto=Decimal('0.00'),
                valor_liquido=total,
            )
            # Pagamento
            PagamentoVenda.objects.create(
                venda=v,
                forma=ped.forma_pagamento,
                valor=total,
            )
            # Recebível quitado
            Recebivel.objects.create(
                venda=v,
                cliente=cli,
                loja=loja,
                valor_original=total,
                valor_saldo=Decimal('0.00'),
                data_vencimento=date.today(),
                situacao='PAGO',
            )
            print(f"   ✅ {num} - R$ {total:.2f} [{cli.nome}]")
        vendas.append(v)

    # Venda em aberto (recebível pendente)
    num_aberto = 'VDA-2026-004'
    if not Venda.objects.filter(numero_venda=num_aberto).exists():
        total = produtos[2].preco_venda * Decimal('3')
        v_aberto = Venda.objects.create(
            numero_venda=num_aberto,
            loja=loja,
            cliente=clientes[3],
            vendedor=vendedor,
            pedido_origem=pedidos[3] if len(pedidos) > 3 else pedidos[-1],
            valor_total=total,
            valor_desconto=Decimal('0.00'),
            valor_liquido=total,
        )
        Recebivel.objects.create(
            venda=v_aberto,
            cliente=clientes[3],
            loja=loja,
            valor_original=total / 2,
            valor_saldo=total / 2,
            data_vencimento=date.today() + timedelta(days=30),
            situacao='ABERTO',
        )
        Recebivel.objects.create(
            venda=v_aberto,
            cliente=clientes[3],
            loja=loja,
            valor_original=total / 2,
            valor_saldo=total / 2,
            data_vencimento=date.today() + timedelta(days=60),
            situacao='ABERTO',
        )
        print(f"   ✅ {num_aberto} - Crediário com recebíveis pendentes [{clientes[3].nome}]")
        vendas.append(v_aberto)
    else:
        print(f"   ⏭  {num_aberto} já existe")

    return vendas


# ══════════════════════════════════════════════════════════════════════════════
# 7. FISCAL / NFe
# ══════════════════════════════════════════════════════════════════════════════
def criar_fiscal(empresa, loja, vendas):
    print("\n🧾 Fiscal / NFe...")

    # Configuração fiscal
    cfg, created = ConfiguracaoFiscal.objects.get_or_create(
        empresa=empresa, loja=loja,
        defaults=dict(
            regime_tributario='SIMPLES_NACIONAL',
            nfe_ativo=True,
            nfe_ambiente='HOMOLOGACAO',
            nfe_serie=1,
            nfe_numero_atual=1,
            nfce_ativo=True,
            nfce_ambiente='HOMOLOGACAO',
            nfce_serie=1,
            nfce_numero_atual=1,
        )
    )
    print(f"   ✅ ConfiguracaoFiscal [{'criada' if created else 'já existe'}]")

    situacoes = ['AUTORIZADA', 'PENDENTE', 'CANCELADA']
    for i, (venda, sit) in enumerate(zip(vendas[:3], situacoes)):
        import uuid
        chave = f"{'3' * 44}"[:44] if sit == 'AUTORIZADA' else None
        nf_num = i + 1
        if not NotaFiscal.objects.filter(loja=loja, numero=nf_num, serie=1).exists():
            nf = NotaFiscal.objects.create(
                loja=loja,
                venda=venda,
                tipo_nota='NFE',
                serie=1,
                numero=nf_num,
                chave_acesso=f"{str(uuid.uuid4()).replace('-','')[:44]}" if sit == 'AUTORIZADA' else None,
                situacao=sit,
                valor_total_produtos=venda.valor_liquido,
                valor_total_nota=venda.valor_liquido,
                data_autorizacao=timezone.now() if sit == 'AUTORIZADA' else None,
                data_cancelamento=timezone.now() if sit == 'CANCELADA' else None,
            )
            print(f"   ✅ NFe #{nf_num} [{sit}] - R$ {venda.valor_liquido:.2f}")
        else:
            print(f"   ⏭  NFe #{nf_num} já existe")


# ══════════════════════════════════════════════════════════════════════════════
# 8. MONITORAMENTO
# ══════════════════════════════════════════════════════════════════════════════
def criar_monitoramento():
    print("\n📊 Monitoramento...")

    componentes = [
        ('DATABASE', 'HEALTHY', 12.5),
        ('API',      'HEALTHY', 45.3),
        ('DISK',     'WARNING', None),
        ('MEMORY',   'HEALTHY', None),
        ('CELERY',   'CRITICAL', None),
    ]

    for comp, status, response_time in componentes:
        SystemHealth.objects.create(
            component=comp,
            status=status,
            response_time=response_time,
            error_message=f'Verificação automática - {comp}' if status != 'HEALTHY' else None,
        )
        print(f"   ✅ SystemHealth: {comp} [{status}]")

    # Alertas
    User = django.contrib.auth.get_user_model() if False else __import__('django.contrib.auth', fromlist=['get_user_model']).get_user_model()
    admin = User.objects.filter(is_superuser=True).first()

    alertas = [
        ('DISK_SPACE',      'WARNING',  'Disco quase cheio',       'Uso de disco acima de 80%'),
        ('SYSTEM_HEALTH',   'CRITICAL', 'Celery inativo',           'Workers Celery não respondem'),
        ('BACKUP_FAILURE',  'INFO',     'Backup concluído',         'Backup diário realizado com sucesso'),
    ]
    for alert_type, severity, titulo, msg in alertas:
        AlertNotification.objects.create(
            alert_type=alert_type,
            severity=severity,
            title=titulo,
            message=msg,
        )
        print(f"   ✅ Alerta [{severity}]: {titulo}")


# ══════════════════════════════════════════════════════════════════════════════
# MAIN
# ══════════════════════════════════════════════════════════════════════════════
if __name__ == '__main__':
    print("=" * 60)
    print("  SEED: Dados de teste - Menu Atalaia Tintas")
    print("=" * 60)

    admin, vendedor = criar_usuarios()
    empresa, loja = criar_empresa_loja(admin, vendedor)
    produtos = criar_produtos(loja)
    clientes = criar_clientes(vendedor)
    pedidos = criar_pedidos(loja, clientes, produtos, vendedor)
    vendas = criar_vendas(loja, clientes, produtos, pedidos, vendedor)
    criar_fiscal(empresa, loja, vendas)
    criar_monitoramento()

    print("\n" + "=" * 60)
    print("  ✅ Seed concluído com sucesso!")
    print("=" * 60)
    print("\nLogins disponíveis:")
    print("  admin    / admin123")
    print("  vendedor / vendedor123")
    print("\nDados criados:")
    print(f"  👥 {len(clientes)} clientes")
    print(f"  📋 {len(pedidos)} pedidos")
    print(f"  💰 {len(vendas)} vendas")
    print("  🧾 NFes (autorizada, pendente, cancelada)")
    print("  📊 5 registros de saúde do sistema + 3 alertas")

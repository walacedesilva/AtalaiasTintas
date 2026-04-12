"""
Dados de Teste - Sistema de Etiquetas

Cria dados mínimos para testar o sistema completo:
- Loja de teste
- Pigmentos básicos
- Cor do leque
- Fórmula tintométrica
- Mistura de teste
"""

import os
import sys
import django
from decimal import Decimal
from datetime import datetime

# Setup Django
sys.path.append('e:/SIAFIC/AtalaiasTintas/backend')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'tintas_system.settings')
django.setup()

from django.contrib.auth.models import User
from apps.companies.models import Loja
from apps.inventory.models import Categoria, Marca, UnidadeMedida, ProdutoBase, ProdutoVariacao  
from apps.tintometry.models import *

def criar_dados_teste():
    """Cria dados mínimos para teste"""
    print("🏗️ Criando dados de teste para sistema de etiquetas...")
    
    try:
        # 1. Criar usuário admin se não existir
        if not User.objects.filter(username='admin').exists():
            admin = User.objects.create_superuser('admin', 'admin@teste.com', 'admin123')
            print("   ✅ Usuário admin criado")
        else:
            admin = User.objects.get(username='admin')
            print("   ✅ Usuário admin já existe")
        
        # 2. Criar empresa de teste primeiro
        from apps.companies.models import Empresa
        empresa, created = Empresa.objects.get_or_create(
            cnpj="12345678000199",
            defaults={
                'razao_social': 'Empresa Teste de Tintas LTDA',
                'nome_fantasia': 'TintasTeste',
                'telefone': '(11) 9999-9999',
                'email': 'contato@tintasteste.com',
                'cidade': 'São Paulo',
                'uf': 'SP',
                'ativa': True
            }
        )
        print(f"   ✅ Empresa {'criada' if created else 'já existe'}: {empresa.nome_fantasia}")
        
        # 3. Criar loja de teste
        loja, created = Loja.objects.get_or_create(
            codigo="LJ001",
            defaults={
                'empresa': empresa,
                'nome': "Loja Teste - Etiquetas",
                'descricao': 'Loja de teste para sistema de etiquetas',
                'telefone': '(11) 9999-9999',
                'email': 'loja@tintasteste.com',
                'cep': '01234567',
                'endereco': 'Rua das Tintas',
                'numero': '123',
                'bairro': 'Centro',
                'cidade': 'São Paulo',
                'uf': 'SP',
                'latitude': Decimal('-23.5505'),
                'longitude': Decimal('-46.6333'),
                'aceita_delivery': True,
                'raio_delivery_km': Decimal('10.0'),
                'ativa': True
            }
        )
        print(f"   ✅ Loja {'criada' if created else 'já existe'}: {loja.nome}")
        
        # 3. Criar pigmentos básicos  
        pigmentos_data = [
            {'codigo': 'PIG001', 'nome': 'Azul Ftalocianina', 'cor_base': 'AZUL', 'densidade': Decimal('1.05')},
            {'codigo': 'PIG002', 'nome': 'Vermelho Óxido', 'cor_base': 'VERMELHO', 'densidade': Decimal('1.12')},
            {'codigo': 'PIG003', 'nome': 'Amarelo Cromo', 'cor_base': 'AMARELO', 'densidade': Decimal('1.08')},
            {'codigo': 'PIG004', 'nome': 'Preto Carbono', 'cor_base': 'PRETO', 'densidade': Decimal('1.15')}
        ]
        
        pigmentos = []
        for pig_data in pigmentos_data:
            pigmento, created = Pigmento.objects.get_or_create(
                codigo=pig_data['codigo'],
                defaults={
                    'nome': pig_data['nome'],
                    'cor_base': pig_data['cor_base'],
                    'densidade': pig_data['densidade'],
                    'poder_tintorial': Decimal('85.0'),
                    'preco_ml': Decimal('0.15'),
                    'fornecedor': 'Fornecedor Teste',
                    'ativo': True
                }
            )
            pigmentos.append(pigmento)
            print(f"   ✅ Pigmento {'criado' if created else 'já existe'}: {pigmento.codigo}")
        
        # 4. Criar estoque dos pigmentos
        for pigmento in pigmentos:
            estoque, created = EstoquePigmento.objects.get_or_create(
                pigmento=pigmento,
                loja=loja,
                defaults={
                    'saldo_ml': Decimal('5000.0'),  # 5L de cada pigmento
                    'saldo_minimo': Decimal('500.0'),
                    'custo_ml': Decimal('0.12'),
                    'lote_atual': 'LOTE2026001',
                    'validade_lote': datetime(2026, 12, 31).date(),
                    'ativo': True
                }
            )
            print(f"   ✅ Estoque {'criado' if created else 'já existe'}: {pigmento.codigo} - {estoque.saldo_ml}ml")
        
        # 5. Criar unidades de medida primeiro
        unidade_l, _ = UnidadeMedida.objects.get_or_create(
            sigla='L',
            defaults={'nome': 'Litro', 'tipo': 'volume'}
        )
        unidade_ml, _ = UnidadeMedida.objects.get_or_create(
            sigla='ML',
            defaults={
                'nome': 'Mililitro', 
                'tipo': 'volume',
                'unidade_base': unidade_l,
                'fator_conversao': Decimal('0.001')
            }
        )
        
        # 5.1. Criar categoria e marca
        categoria, _ = Categoria.objects.get_or_create(
            codigo='BASES-TINT',
            defaults={
                'nome': 'Bases Tintométricas',
                'permite_tintometria': True,
                'exige_formula': True,
                'ativa': True
            }
        )
        marca, _ = Marca.objects.get_or_create(
            codigo='TINTASYS',
            defaults={
                'nome': 'TintaSystem',
                'ativa': True
            }
        )
        
        # 5.2. Criar base de produto
        base, created = ProdutoBase.objects.get_or_create(
            codigo="BASE-ACR-PRE",
            defaults={
                'nome': "Base Acrílica Premium",
                'descricao': 'Base acrílica premium para tintometria',
                'categoria': categoria,
                'marca': marca,
                'tipo_produto': 'INSUMO',
                'base_tintometrica': 'BRANCO',
                'linha_produto': 'PREMIUM',
                'ativo': True
            }
        )
        print(f"   ✅ Base {'criada' if created else 'já existe'}: {base.nome}")
        
        # 5.3. Criar variação da base (produto específico)
        variacao, created = ProdutoVariacao.objects.get_or_create(
            produto_base=base,
            codigo_variacao="3.6L",
            defaults={
                'nome_variacao': 'Base Acrílica Premium 3,6L',
                'cor': 'BRANCO',
                'tamanho': 'G',
                'unidade_estoque': unidade_l,
                'unidade_venda': unidade_l,
                'preco_custo': Decimal('25.50'),
                'preco_venda': Decimal('35.00'),
                'rendimento_por_litro': Decimal('3.6'),
                'ativo': True
            }
        )
        print(f"   ✅ Variação {'criada' if created else 'já existe'}: {variacao.nome_variacao}")
        
        # 6. Criar cor do leque
        cor, created = LequeCorDefinida.objects.get_or_create(
            codigo_cor="AZ2026.001", 
            defaults={
                'nome_cor': 'Azul Real Premium',
                'familia_cor': 'AZUIS',
                'linha_produto': 'PREMIUM',
                'r': 30,
                'g': 64,
                'b': 175,
                'l_value': Decimal('25.5'),
                'a_value': Decimal('15.2'),
                'b_value': Decimal('-45.8'),
                'ativo': True
            }
        )
        print(f"   ✅ Cor {'criada' if created else 'já existe'}: {cor.nome_cor}")
        
        # 7. Criar fórmula tintométrica
        formula, created = FormulaTintometrica.objects.get_or_create(
            codigo_formula="FRM001",
            defaults={
                'nome_formula': 'Azul Real - 3,6L',
                'cor_definida': cor,
                'base_produto': variacao,
                'volume_base': Decimal('3.6'),
                'versao': '1.0',
                'aprovada': True,
                'testada': True,
                'ativa': True
            }
        )
        print(f"   ✅ Fórmula {'criada' if created else 'já existe'}: {formula.nome_formula}")
        
        # 8. Criar itens da fórmula (pigmentos + quantidades)
        if created:  # Só criar itens se fórmula for nova
            itens_formula = [
                {'pigmento': pigmentos[0], 'quantidade': Decimal('32.5')},  # Azul Ftalocianina
                {'pigmento': pigmentos[3], 'quantidade': Decimal('2.8')},    # Preto Carbono
            ]
            
            for item_data in itens_formula:
                ItemFormula.objects.create(
                    formula=formula,
                    pigmento=item_data['pigmento'],
                    quantidade=item_data['quantidade']
                )
                print(f"   ✅ Item fórmula criado: {item_data['pigmento'].codigo} - {item_data['quantidade']}ml")
        
        # 9. Criar mistura de teste
        mistura, created = MisturaTinta.objects.get_or_create(
            codigo_mistura="MIX2026001",
            defaults={
                'formula': formula,
                'loja': loja,
                'usuario_operacao': admin,
                'situacao': 'CONFIRMADA',
                'volume_solicitado': Decimal('3.6'),
                'volume_produzido': Decimal('3.6'),
                'custo_total': Decimal('92.50'),
                'custo_base': Decimal('25.50'),
                'custo_pigmentos': Decimal('67.00'),
                'cliente_nome': 'João Silva',
                'cliente_telefone': '(11) 98765-4321',
                'observacoes_cliente': 'Cliente quer cor exatamente igual à amostra',
                'observacoes_internas': 'Mistura para teste do sistema de etiquetas'
            }
        )
        print(f"   ✅ Mistura {'criada' if created else 'já existe'}: {mistura.codigo_mistura}")
        
        # 10. Criar itens da mistura
        if created:
            itens_mistura = [
                {'pigmento': pigmentos[0], 'quantidade': Decimal('117.0')},  # 32.5 * 3.6
                {'pigmento': pigmentos[3], 'quantidade': Decimal('10.08')},  # 2.8 * 3.6
            ]
            
            for item_data in itens_mistura:
                ItemMistura.objects.create(
                    mistura=mistura,
                    pigmento=item_data['pigmento'],
                    quantidade_calculada=item_data['quantidade'],
                    quantidade_executada=item_data['quantidade'],
                    custo_unitario=Decimal('0.12'),
                    custo_total=item_data['quantidade'] * Decimal('0.12')
                )
                print(f"   ✅ Item mistura criado: {item_data['pigmento'].codigo} - {item_data['quantidade']}ml")
        
        print("\\n🎉 DADOS DE TESTE CRIADOS COM SUCESSO!")
        print(f"\\n📋 RESUMO:")
        print(f"   • Loja: {loja.nome}")
        print(f"   • Pigmentos: {len(pigmentos)} tipos")
        print(f"   • Cor: {cor.codigo_cor} - {cor.nome_cor}")  
        print(f"   • Fórmula: {formula.codigo_formula}")
        print(f"   • Mistura: {mistura.codigo_mistura} ({mistura.situacao})")
        print(f"\\n🔗 Agora você pode testar:")
        print(f"   • POST /api/v1/tintometry/labels/generate/")
        print(f"   • POST /api/v1/tintometry/labels/preview/")
        print(f"   • GET  /api/v1/tintometry/etiquetas/")
        
        return mistura
        
    except Exception as e:
        print(f"❌ Erro criando dados: {str(e)}")
        import traceback
        traceback.print_exc()
        return None

def testar_geracao_etiqueta():
    """Testa geração de etiqueta com dados reais"""
    print("\\n🏷️ Testando geração de etiqueta com dados reais...")
    
    try:
        from apps.tintometry.labels.services import LabelGeneratorService
        from apps.tintometry.labels.renderers import LabelPDFRenderer
        from apps.tintometry.labels.templates import TemplateManager
        
        # Buscar mistura de teste
        mistura = MisturaTinta.objects.filter(codigo_mistura="MIX2026001").first()
        
        if not mistura:
            print("   ❌ Mistura de teste não encontrada")
            return False
        
        # Gerar dados da etiqueta
        service = LabelGeneratorService()
        label_data = service.generate_label_data(str(mistura.id), 'default')
        
        print(f"   ✅ Dados gerados: {label_data['mistura']['codigo']}")
        print(f"   ✅ QR Code: {len(label_data['qr_code']['image_base64'])} chars")
        print(f"   ✅ Barcode: {label_data['barcode']['code']}")
        print(f"   ✅ Pigmentos: {len(label_data['pigmentos'])} tipos")
        
        # Gerar PDF
        renderer = LabelPDFRenderer()
        template_manager = TemplateManager()
        template = template_manager.load_template('compact')
        
        try:
            pdf_bytes = renderer.render_label_pdf(label_data, template)
            print(f"   ✅ PDF gerado: {len(pdf_bytes):,} bytes")
            
            # Salvar PDF para visualização (opcional)
            with open('e:/SIAFIC/AtalaiasTintas/etiqueta_teste.pdf', 'wb') as f:
                f.write(pdf_bytes)
            print(f"   ✅ PDF salvo: e:/SIAFIC/AtalaiasTintas/etiqueta_teste.pdf")
            
        except Exception as pdf_error:
            print(f"   ⚠️ Erro PDF: {pdf_error}")
        
        # Gerar preview HTML
        html_preview = renderer.generate_preview_html(label_data, template)
        
        # Salvar preview para visualização
        with open('e:/SIAFIC/AtalaiasTintas/etiqueta_preview.html', 'w', encoding='utf-8') as f:
            f.write(html_preview)
        print(f"   ✅ Preview HTML salvo: e:/SIAFIC/AtalaiasTintas/etiqueta_preview.html")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Erro: {str(e)}")
        return False

def main():
    print("🚀 SETUP COMPLETO - SISTEMA DE ETIQUETAS")
    print("=" * 50)
    
    # Criar dados
    mistura = criar_dados_teste()
    
    if mistura:
        # Testar geração
        testar_geracao_etiqueta()
        
        print("\\n" + "=" * 50)
        print("✨ SISTEMA PRONTO PARA USO!")
        print("=" * 50)
        print("\\n🌐 Acesse: http://localhost:8000/admin/")
        print("   • User: admin")
        print("   • Pass: admin123")
        print("\\n📡 API Endpoints:")
        print("   • http://localhost:8000/api/v1/tintometry/labels/")
        print("   • http://localhost:8000/api/v1/tintometry/misturas/")
        print("   • http://localhost:8000/api/v1/tintometry/etiquetas/")

if __name__ == '__main__':
    main()
"""
Dados iniciais para teste do sistema tintométrico
Criação de pigmentos, cores e fórmulas básicas
"""

from django.core.management.base import BaseCommand
from django.db import transaction
from apps.tintometry.models import (
    Pigmento, LequeCorDefinida, FormulaTintometrica, 
    ItemFormula, EstoquePigmento
)
from apps.companies.models import Loja
from apps.inventory.models import ProdutoVariacao
from decimal import Decimal


class Command(BaseCommand):
    help = 'Cria dados iniciais para o sistema tintométrico'
    
    def handle(self, *args, **options):
        with transaction.atomic():
            self.stdout.write('Criando dados iniciais do sistema tintométrico...')
            
            # Criar pigmentos básicos
            pigmentos = self.create_pigmentos()
            self.stdout.write(f'✓ Criados {len(pigmentos)} pigmentos')
            
            # Criar cores do leque
            cores = self.create_cores_leque()
            self.stdout.write(f'✓ Criadas {len(cores)} cores do leque')
            
            # Criar fórmulas básicas
            formulas = self.create_formulas_basicas(pigmentos, cores)
            self.stdout.write(f'✓ Criadas {len(formulas)} fórmulas')
            
            # Configurar estoque inicial
            self.setup_estoque_inicial(pigmentos)
            self.stdout.write('✓ Configurado estoque inicial')
            
            self.stdout.write(
                self.style.SUCCESS('Sistema tintométrico configurado com sucesso!')
            )
    
    def create_pigmentos(self):
        """Cria pigmentos básicos para tintometria"""
        pigmentos_data = [
            {
                'codigo': 'PIG001',
                'nome': 'Azul Ftalocianina',
                'cor_base': 'Azul',
                'densidade': Decimal('1.2500'),
                'poder_tintorial': Decimal('95.00'),
                'concentracao_maxima': Decimal('15.00'),
                'fornecedor': 'Cromatos Brasil',
                'r': 0, 'g': 100, 'b': 200
            },
            {
                'codigo': 'PIG002', 
                'nome': 'Vermelho Óxido de Ferro',
                'cor_base': 'Vermelho',
                'densidade': Decimal('1.1800'),
                'poder_tintorial': Decimal('88.50'),
                'concentracao_maxima': Decimal('20.00'),
                'fornecedor': 'Cromatos Brasil',
                'r': 180, 'g': 20, 'b': 20
            },
            {
                'codigo': 'PIG003',
                'nome': 'Amarelo Cromo',
                'cor_base': 'Amarelo', 
                'densidade': Decimal('1.3400'),
                'poder_tintorial': Decimal('92.00'),
                'concentracao_maxima': Decimal('18.00'),
                'fornecedor': 'Pigmentos São Paulo',
                'r': 255, 'g': 215, 'b': 0
            },
            {
                'codigo': 'PIG004',
                'nome': 'Preto Carbono',
                'cor_base': 'Preto',
                'densidade': Decimal('1.1000'),
                'poder_tintorial': Decimal('98.50'),
                'concentracao_maxima': Decimal('8.00'),
                'fornecedor': 'Cromatos Brasil',
                'r': 20, 'g': 20, 'b': 20
            },
            {
                'codigo': 'PIG005',
                'nome': 'Verde Óxido de Cromo',
                'cor_base': 'Verde',
                'densidade': Decimal('1.4200'),
                'poder_tintorial': Decimal('85.00'),
                'concentracao_maxima': Decimal('25.00'),
                'fornecedor': 'Pigmentos São Paulo', 
                'r': 50, 'g': 150, 'b': 50
            },
            {
                'codigo': 'PIG006',
                'nome': 'Laranja Molibdato',
                'cor_base': 'Laranja',
                'densidade': Decimal('1.2800'),
                'poder_tintorial': Decimal('91.00'),
                'concentracao_maxima': Decimal('16.00'),
                'fornecedor': 'Tintas & Cores',
                'r': 255, 'g': 140, 'b': 0
            }
        ]
        
        pigmentos = []
        for data in pigmentos_data:
            pigmento, created = Pigmento.objects.get_or_create(
                codigo=data['codigo'],
                defaults=data
            )
            pigmentos.append(pigmento)
        
        return pigmentos
    
    def create_cores_leque(self):
        """Cria cores básicas do leque"""
        cores_data = [
            {
                'codigo_cor': 'AZ001',
                'nome_cor': 'Azul Céu',
                'familia_cor': 'Azuis',
                'linha_produto': 'Standard',
                'l_value': Decimal('65.500'),
                'a_value': Decimal('-12.800'),
                'b_value': Decimal('-45.200'),
                'r': 135, 'g': 206, 'b': 235
            },
            {
                'codigo_cor': 'VM001', 
                'nome_cor': 'Vermelho Cardinal',
                'familia_cor': 'Vermelhos',
                'linha_produto': 'Premium',
                'l_value': Decimal('42.300'),
                'a_value': Decimal('58.600'),
                'b_value': Decimal('28.400'),
                'r': 196, 'g': 30, 'b': 58
            },
            {
                'codigo_cor': 'AM001',
                'nome_cor': 'Amarelo Canário',
                'familia_cor': 'Amarelos', 
                'linha_produto': 'Standard',
                'l_value': Decimal('88.200'),
                'a_value': Decimal('-8.500'),
                'b_value': Decimal('85.600'),
                'r': 255, 'g': 255, 'b': 0
            },
            {
                'codigo_cor': 'VD001',
                'nome_cor': 'Verde Floresta',
                'familia_cor': 'Verdes',
                'linha_produto': 'Premium',
                'l_value': Decimal('35.800'),
                'a_value': Decimal('-28.500'),
                'b_value': Decimal('15.200'),
                'r': 34, 'g': 139, 'b': 34
            },
            {
                'codigo_cor': 'LR001',
                'nome_cor': 'Laranja Intenso', 
                'familia_cor': 'Laranjas',
                'linha_produto': 'Standard',
                'l_value': Decimal('68.400'),
                'a_value': Decimal('42.800'),
                'b_value': Decimal('65.200'),
                'r': 255, 'g': 165, 'b': 0
            }
        ]
        
        cores = []
        for data in cores_data:
            cor, created = LequeCorDefinida.objects.get_or_create(
                codigo_cor=data['codigo_cor'],
                defaults=data
            )
            cores.append(cor)
        
        return cores
    
    def create_formulas_basicas(self, pigmentos, cores):
        """Cria fórmulas básicas para as cores"""
        formulas = []
        
        # Obter base branca (assumindo que existe)
        try:
            base_branca = ProdutoVariacao.objects.filter(
                nome_variacao__icontains='branca'
            ).first()
            
            if not base_branca:
                # Criar uma base padrão se não existir
                from apps.inventory.models import ProdutoBase, Categoria, Marca
                marca, _ = Marca.objects.get_or_create(nome='Tintas Padrão')
                categoria, _ = Categoria.objects.get_or_create(nome='Bases', defaults={'descricao': 'Bases para tinta'})
                
                produto_base, _ = ProdutoBase.objects.get_or_create(
                    nome='Base Branca Standard',
                    defaults={
                        'categoria': categoria,
                        'marca': marca,
                        'descricao': 'Base branca para tintometria'
                    }
                )
                
                base_branca, _ = ProdutoVariacao.objects.get_or_create(
                    produto_base=produto_base,
                    nome_variacao='Base Branca 1L',
                    defaults={
                        'codigo_variacao': 'BASE001',
                        'preco_custo': Decimal('12.50'),
                        'preco_venda': Decimal('18.90'),
                        'margem_lucro': Decimal('51.20'),
                        'estoque_minimo': Decimal('10.00'),
                        'fator_conversao_venda': Decimal('1.00')
                    }
                )
        except Exception:
            self.stdout.write(
                self.style.WARNING('Não foi possível criar/encontrar base branca')
            )
            return []
        
        # Fórmulas específicas para cada cor
        formulas_data = [
            {
                'cor': cores[0],  # Azul Céu
                'codigo': 'FORM_AZ001',
                'nome': 'Fórmula Azul Céu Standard',
                'itens': [
                    {'pigmento': pigmentos[0], 'quantidade': Decimal('8.5')},  # Azul Ftalocianina
                ]
            },
            {
                'cor': cores[1],  # Vermelho Cardinal  
                'codigo': 'FORM_VM001',
                'nome': 'Fórmula Vermelho Cardinal Premium',
                'itens': [
                    {'pigmento': pigmentos[1], 'quantidade': Decimal('12.5')},  # Vermelho Óxido
                    {'pigmento': pigmentos[3], 'quantidade': Decimal('0.8')},   # Preto (para intensificar)
                ]
            },
            {
                'cor': cores[2],  # Amarelo Canário
                'codigo': 'FORM_AM001', 
                'nome': 'Fórmula Amarelo Canário Standard',
                'itens': [
                    {'pigmento': pigmentos[2], 'quantidade': Decimal('15.2')},  # Amarelo Cromo
                ]
            },
            {
                'cor': cores[3],  # Verde Floresta
                'codigo': 'FORM_VD001',
                'nome': 'Fórmula Verde Floresta Premium', 
                'itens': [
                    {'pigmento': pigmentos[4], 'quantidade': Decimal('18.5')},  # Verde Óxido
                    {'pigmento': pigmentos[3], 'quantidade': Decimal('1.2')},   # Preto (para escurecer)
                ]
            },
            {
                'cor': cores[4],  # Laranja Intenso
                'codigo': 'FORM_LR001',
                'nome': 'Fórmula Laranja Intenso Standard',
                'itens': [
                    {'pigmento': pigmentos[5], 'quantidade': Decimal('14.8')},  # Laranja Molibdato
                    {'pigmento': pigmentos[2], 'quantidade': Decimal('2.5')},   # Amarelo (para brilho)
                ]
            }
        ]
        
        for data in formulas_data:
            formula, created = FormulaTintometrica.objects.get_or_create(
                codigo_formula=data['codigo'],
                defaults={
                    'cor_definida': data['cor'],
                    'base_produto': base_branca,
                    'nome_formula': data['nome'],
                    'volume_base': Decimal('1.00'),
                    'instrucoes': f"Adicionar pigmentos na ordem, misturar por 5 minutos",
                    'tempo_mistura_minutos': 5,
                    'aprovada': True,
                    'testada': True,
                    'ativa': True
                }
            )
            
            # Criar itens da fórmula
            for idx, item_data in enumerate(data['itens'], 1):
                ItemFormula.objects.get_or_create(
                    formula=formula,
                    pigmento=item_data['pigmento'],
                    defaults={
                        'quantidade': item_data['quantidade'],
                        'sequencia': idx
                    }
                )
            
            formulas.append(formula)
        
        return formulas
    
    def setup_estoque_inicial(self, pigmentos):
        """Configura estoque inicial para os pigmentos"""
        try:
            # Obter a primeira loja ou criar uma padrão
            loja = Loja.objects.first()
            if not loja:
                from apps.companies.models import Empresa
                empresa, _ = Empresa.objects.get_or_create(
                    nome='Loja Teste',
                    defaults={
                        'cnpj': '12345678000100',
                        'telefone_principal': '1140001000'
                    }
                )
                loja, _ = Loja.objects.get_or_create(
                    empresa=empresa,
                    nome='Loja Principal',
                    defaults={
                        'endereco_completo': 'Rua Teste, 123',
                        'telefone': '1140001001'
                    }
                )
            
            # Configurar estoque para cada pigmento
            for pigmento in pigmentos:
                EstoquePigmento.objects.get_or_create(
                    pigmento=pigmento,
                    loja=loja,
                    defaults={
                        'saldo_ml': Decimal('2500.0'),      # 2.5L inicial
                        'saldo_minimo': Decimal('200.0'),    # Mínimo 200ml 
                        'saldo_maximo': Decimal('5000.0'),   # Máximo 5L
                        'custo_ml': Decimal('0.125'),        # R$ 0,125 por ml
                        'lote_atual': f'LOTE2026{pigmento.codigo[-3:]}',
                        'ativo': True
                    }
                )
        except Exception as e:
            self.stdout.write(
                self.style.WARNING(f'Erro ao configurar estoque: {str(e)}')
            )
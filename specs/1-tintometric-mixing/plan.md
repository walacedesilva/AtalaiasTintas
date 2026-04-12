# Technical Implementation Plan: Tintometric Mixing System

**Feature**: Sistema de Mistura de Tintas Tintométrica  
**Created**: 2026-04-12  
**Status**: Ready for Implementation  

## 1. Architecture & Design Decisions

### 1.1 Database Schema Evolution

The current `apps/tintometry/models.py` already provides a solid foundation. We need to extend it with the following enhancements:

#### Core Entity Relationships
```
Cliente (sales) ←→ MisturaTinta ←→ FormulaTintometrica (tintometry)  
                     ↓                    ↓
                EstoquePigmento ←→ ItemFormula ←→ Pigmento (existing)
                (inventory)         (existing)     (existing)
```

#### New Models Required
- **`MisturaTinta`** - Records of executed paint mixtures with customer history
- **`EstoquePigmento`** - Extended inventory management specific to pigments
- **`HistoricoCorCliente`** - Customer color history and preferences
- **`EtiquetaMistura`** - Label generation and tracking

### 1.2 API Design Strategy

Following REST principles with the existing Django structure:

- **Resource-based URLs**: `/api/v1/tintometry/formulas/`, `/api/v1/tintometry/mixtures/`
- **HTTP verbs**: GET (list, retrieve), POST (create), PUT/PATCH (update), DELETE (remove)
- **Nested resources**: `/api/v1/tintometry/mixtures/{id}/label/` for label generation
- **Query parameters**: Filter by customer, date range, color family
- **JSON response format**: Consistent with existing API patterns

### 1.3 Integration Architecture

#### Stock Management Integration
- **Real-time sync**: Use Django signals to trigger stock updates on mixture confirmation
- **Atomic transactions**: Ensure stock consistency with database transactions
- **Conflict resolution**: Handle concurrent mixture requests through pessimistic locking

#### Customer History Integration
- **Extend sales.Cliente**: Add foreign keys to track color preferences
- **Cross-app queries**: Use Django ORM select_related/prefetch_related for performance
- **Data aggregation**: Summarize customer color history at model level

### 1.4 Scientific Calculation Architecture

#### Color Science Library Integration
```python
# Primary library: colour-science (most comprehensive)
# Backup: colorspacious (lighter weight)
# Custom: Internal RGB<->Lab conversion utilities
```

#### Formula Calculation Engine
- **Input**: Target color (Lab values), desired volume
- **Process**: Proportional scaling with density correction
- **Output**: Exact pigment quantities in ml with precision to 0.1ml
- **Validation**: Stock availability check before calculation completion

## 2. Technical Implementation Details

### 2.1 Enhanced Django Models

#### Extended Models (apps/tintometry/models.py)

```python
class MisturaTinta(TimeStampedModel):
    """Registro de misturas executadas com histórico completo"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    codigo_mistura = models.CharField(max_length=20, unique=True)  # Auto-generated
    
    # Relacionamentos
    cliente = models.ForeignKey('sales.Cliente', on_delete=models.PROTECT, related_name='misturas')
    formula = models.ForeignKey(FormulaTintometrica, on_delete=models.PROTECT)
    loja = models.ForeignKey('companies.Loja', on_delete=models.PROTECT)
    usuario_operacao = models.ForeignKey('core.User', on_delete=models.PROTECT)
    
    # Volume e custos
    volume_solicitado = models.DecimalField(max_digits=8, decimal_places=2)
    volume_produzido = models.DecimalField(max_digits=8, decimal_places=2, null=True)
    custo_total = models.DecimalField(max_digits=10, decimal_places=4)
    custo_base = models.DecimalField(max_digits=10, decimal_places=4)
    custo_pigmentos = models.DecimalField(max_digits=10, decimal_places=4)
    
    # Status e controle
    SITUACAO_CHOICES = [
        ('CALCULADA', 'Fórmula Calculada'),
        ('CONFIRMADA', 'Mistura Confirmada'),
        ('ETIQUETADA', 'Etiqueta Gerada'),
        ('CANCELADA', 'Cancelada')
    ]
    situacao = models.CharField(max_length=20, choices=SITUACAO_CHOICES, default='CALCULADA')
    data_confirmacao = models.DateTimeField(null=True, blank=True)
    data_cancelamento = models.DateTimeField(null=True, blank=True)
    motivo_cancelamento = models.CharField(max_length=200, null=True, blank=True)
    
    # Observações
    observacoes_cliente = models.TextField(null=True, blank=True)
    observacoes_internas = models.TextField(null=True, blank=True)
    
    # Rastreabilidade de qualidade
    cor_aprovada_cliente = models.BooleanField(null=True)
    data_aprovacao_cor = models.DateTimeField(null=True, blank=True)


class ItemMistura(TimeStampedModel):
    """Itens utilizados em cada mistura com quantidades exatas"""
    
    mistura = models.ForeignKey(MisturaTinta, on_delete=models.CASCADE, related_name='itens')
    pigmento = models.ForeignKey(Pigmento, on_delete=models.PROTECT)
    
    # Quantidades calculadas vs executadas
    quantidade_calculada = models.DecimalField(max_digits=8, decimal_places=4)
    quantidade_executada = models.DecimalField(max_digits=8, decimal_places=4, null=True)
    
    # Custos por item
    custo_unitario = models.DecimalField(max_digits=10, decimal_places=4)
    custo_total = models.DecimalField(max_digits=10, decimal_places=4)
    
    # Controle de estoque
    lote_utilizado = models.CharField(max_length=50, null=True, blank=True)
    estoque_antes = models.DecimalField(max_digits=10, decimal_places=4, null=True)
    estoque_depois = models.DecimalField(max_digits=10, decimal_places=4, null=True)


class EstoquePigmento(TimeStampedModel):
    """Controle específico de estoque para pigmentos tintométricos"""
    
    pigmento = models.ForeignKey(Pigmento, on_delete=models.CASCADE)
    loja = models.ForeignKey('companies.Loja', on_delete=models.CASCADE)
    
    # Saldos atuais
    saldo_ml = models.DecimalField(max_digits=10, decimal_places=4, default=0)
    saldo_minimo = models.DecimalField(max_digits=10, decimal_places=4, default=100)
    saldo_maximo = models.DecimalField(max_digits=10, decimal_places=4, default=5000)
    
    # Custos
    custo_ml = models.DecimalField(max_digits=8, decimal_places=4)
    data_ultimo_custo = models.DateTimeField(auto_now_add=True)
    
    # Lote atual
    lote_atual = models.CharField(max_length=50, null=True, blank=True)
    validade_lote = models.DateField(null=True, blank=True)
    
    # Alertas automáticos
    reposicao_solicitada = models.BooleanField(default=False)
    data_solicitacao_reposicao = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        unique_together = ['pigmento', 'loja']


class EtiquetaMistura(TimeStampedModel):
    """Etiquetas geradas para identificação das misturas"""
    
    mistura = models.OneToOneField(MisturaTinta, on_delete=models.CASCADE)
    codigo_etiqueta = models.CharField(max_length=30, unique=True)
    
    # Dados da etiqueta
    qr_code = models.CharField(max_length=200)  # QR code data
    data_impressao = models.DateTimeField(null=True, blank=True)
    usuario_impressao = models.ForeignKey('core.User', on_delete=models.SET_NULL, null=True)
    
    # Status
    impressa = models.BooleanField(default=False)
    reimpressoes = models.IntegerField(default=0)
```

### 2.2 API Views and Serializers

#### Core API Views (apps/tintometry/views.py)

```python
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db import transaction
from django.utils import timezone
from .models import FormulaTintometrica, MisturaTinta, EstoquePigmento
from .serializers import FormulaCalculationSerializer, MixtureSerializer
from .services import FormulaCalculatorService, StockManagerService

class FormulaViewSet(viewsets.ModelViewSet):
    """API para gerenciamento de fórmulas tintométricas"""
    
    queryset = FormulaTintometrica.objects.filter(ativa=True)
    serializer_class = FormulaSerializer
    
    @action(detail=True, methods=['post'])
    def calculate(self, request, pk=None):
        """Calcula quantidades de pigmentos para volume específico"""
        formula = self.get_object()
        volume = request.data.get('volume', 0)
        loja_id = request.data.get('loja_id')
        
        calculator = FormulaCalculatorService()
        calculation_result = calculator.calculate_pigment_quantities(
            formula=formula,
            volume=volume,
            loja_id=loja_id
        )
        
        if calculation_result['has_stock_issues']:
            return Response(
                calculation_result, 
                status=status.HTTP_409_CONFLICT
            )
        
        return Response(calculation_result)

class MixtureViewSet(viewsets.ModelViewSet):
    """API para registro e controle de misturas"""
    
    queryset = MisturaTinta.objects.all()
    serializer_class = MixtureSerializer
    
    @action(detail=False, methods=['post'])
    def create_from_calculation(self, request):
        """Cria mistura a partir de cálculo de fórmula"""
        with transaction.atomic():
            mixer = MixtureService()
            mixture = mixer.create_mixture_from_calculation(
                formula_id=request.data.get('formula_id'),
                volume=request.data.get('volume'),
                cliente_id=request.data.get('cliente_id'),
                loja_id=request.data.get('loja_id'),
                usuario_id=request.user.id,
                observacoes=request.data.get('observacoes', '')
            )
            
        serializer = self.get_serializer(mixture)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    
    @action(detail=True, methods=['post'])
    def confirm_production(self, request, pk=None):
        """Confirma produção e executa baixa no estoque"""
        mixture = self.get_object()
        
        with transaction.atomic():
            stock_manager = StockManagerService()
            stock_manager.execute_stock_reduction(mixture)
            
            mixture.situacao = 'CONFIRMADA'
            mixture.data_confirmacao = timezone.now()
            mixture.save()
        
        return Response({'status': 'confirmed', 'mixture_id': str(mixture.id)})
    
    @action(detail=True, methods=['get'])
    def generate_label(self, request, pk=None):
        """Gera dados para etiqueta da mistura"""
        mixture = self.get_object()
        label_service = LabelService()
        label_data = label_service.generate_label_data(mixture)
        
        return Response(label_data)

class CustomerHistoryViewSet(viewsets.ReadOnlyModelViewSet):
    """API para histórico de cores por cliente"""
    
    def get_queryset(self):
        cliente_id = self.request.query_params.get('cliente_id')
        if cliente_id:
            return MisturaTinta.objects.filter(
                cliente_id=cliente_id,
                situacao='CONFIRMADA'
            ).order_by('-data_confirmacao')
        return MisturaTinta.objects.none()
    
    @action(detail=False, methods=['get'])
    def search_by_phone(self, request):
        """Busca histórico por telefone do cliente"""
        phone = request.query_params.get('phone')
        if phone:
            from apps.sales.models import Cliente
            clientes = Cliente.objects.filter(
                telefone_principal__contains=phone
            )
            historia_completa = []
            for cliente in clientes:
                misturas = MisturaTinta.objects.filter(
                    cliente=cliente,
                    situacao='CONFIRMADA'
                ).order_by('-data_confirmacao')[:10]  # Últimas 10 misturas
                
                historia_completa.extend([{
                    'cliente': cliente.nome,
                    'codigo_mistura': m.codigo_mistura,
                    'cor': m.formula.cor_definida.nome_cor,
                    'data_mistura': m.data_confirmacao,
                    'volume': m.volume_produzido,
                    'observacoes': m.observacoes_cliente
                } for m in misturas])
        
        return Response(historia_completa)

class PigmentStockViewSet(viewsets.ModelViewSet):
    """API para controle de estoque de pigmentos"""
    
    queryset = EstoquePigmento.objects.all()
    
    @action(detail=False, methods=['get'])
    def low_stock_alerts(self, request):
        """Retorna pigmentos com estoque baixo"""
        loja_id = request.query_params.get('loja_id')
        low_stock = EstoquePigmento.objects.filter(
            loja_id=loja_id,
            saldo_ml__lte=models.F('saldo_minimo')
        ).select_related('pigmento')
        
        alerts = [{
            'pigmento': item.pigmento.nome,
            'codigo': item.pigmento.codigo,
            'saldo_atual': item.saldo_ml,
            'saldo_minimo': item.saldo_minimo,
            'percentual': (item.saldo_ml / item.saldo_minimo * 100) if item.saldo_minimo > 0 else 0
        } for item in low_stock]
        
        return Response(alerts)
```

### 2.3 Business Logic Services

#### Formula Calculator Service (apps/tintometry/services.py)

```python
from decimal import Decimal, ROUND_HALF_UP
from django.db.models import F
import colour
import numpy as np

class FormulaCalculatorService:
    """Serviço para cálculos de fórmulas tintométricas"""
    
    def calculate_pigment_quantities(self, formula, volume, loja_id):
        """
        Calcula quantidades exatas de pigmentos para volume específico
        
        Args:
            formula: FormulaTintometrica instance
            volume: Volume desejado em litros
            loja_id: ID da loja para verificação de estoque
            
        Returns:
            dict: Resultado com quantidades calculadas e disponibilidade
        """
        result = {
            'formula_id': str(formula.id),
            'volume_solicitado': volume,
            'volume_base_formula': formula.volume_base,
            'itens_calculados': [],
            'custo_total': Decimal('0'),
            'has_stock_issues': False,
            'stock_alerts': []
        }
        
        # Fator de proporção baseado no volume base da fórmula
        fator_proporcao = Decimal(str(volume)) / formula.volume_base
        
        for item_formula in formula.itens.all():
            # Quantidade calculada com precisão de 0.1ml
            quantidade = (item_formula.quantidade * fator_proporcao).quantize(
                Decimal('0.1'), 
                rounding=ROUND_HALF_UP
            )
            
            # Verificar disponibilidade em estoque
            try:
                estoque = EstoquePigmento.objects.get(
                    pigmento=item_formula.pigmento,
                    loja_id=loja_id
                )
                disponivel = estoque.saldo_ml >= quantidade
                saldo_atual = estoque.saldo_ml
                custo_item = quantidade * estoque.custo_ml
                
                if not disponivel:
                    result['has_stock_issues'] = True
                    result['stock_alerts'].append({
                        'pigmento': item_formula.pigmento.nome,
                        'necessario': quantidade,
                        'disponivel': saldo_atual,
                        'faltante': quantidade - saldo_atual
                    })
                    
            except EstoquePigmento.DoesNotExist:
                disponivel = False
                saldo_atual = Decimal('0')
                custo_item = Decimal('0')
                result['has_stock_issues'] = True
                result['stock_alerts'].append({
                    'pigmento': item_formula.pigmento.nome,
                    'erro': 'Estoque não configurado para esta loja'
                })
            
            item_resultado = {
                'pigmento_id': item_formula.pigmento.id,
                'pigmento_nome': item_formula.pigmento.nome,
                'pigmento_codigo': item_formula.pigmento.codigo,
                'quantidade_ml': quantidade,
                'custo_unitario_ml': estoque.custo_ml if 'estoque' in locals() else Decimal('0'),
                'custo_total': custo_item,
                'disponivel_estoque': disponivel,
                'saldo_atual': saldo_atual,
                'cor_hex': item_formula.pigmento.cor_hex,
                'sequencia': item_formula.sequencia,
                'observacoes': item_formula.observacoes
            }
            
            result['itens_calculados'].append(item_resultado)
            result['custo_total'] += custo_item
        
        # Calcular custo da base (produto tintável)
        try:
            from apps.inventory.models import EstoqueLoja
            estoque_base = EstoqueLoja.objects.get(
                produto_variacao=formula.base_produto,
                loja_id=loja_id
            )
            custo_base = Decimal(str(volume)) * estoque_base.custo_medio
            result['custo_base'] = custo_base
            result['custo_total'] += custo_base
        except:
            result['custo_base'] = Decimal('0')
        
        # Ordenar itens por sequência
        result['itens_calculados'].sort(key=lambda x: x['sequencia'])
        
        return result

class StockManagerService:
    """Serviço para gerenciamento automático de estoque"""
    
    def execute_stock_reduction(self, mixture):
        """
        Executa baixa automática no estoque após confirmação da mistura
        
        Args:
            mixture: MisturaTinta instance
        """
        for item in mixture.itens.all():
            estoque = EstoquePigmento.objects.select_for_update().get(
                pigmento=item.pigmento,
                loja=mixture.loja
            )
            
            # Registrar estado antes da baixa
            item.estoque_antes = estoque.saldo_ml
            
            # Executar baixa
            estoque.saldo_ml -= item.quantidade_executada or item.quantidade_calculada
            estoque.save()
            
            # Registrar estado após baixa
            item.estoque_depois = estoque.saldo_ml
            item.save()
            
            # Verificar se atingiu estoque mínimo
            if estoque.saldo_ml <= estoque.saldo_minimo:
                self._create_restock_alert(estoque)
    
    def _create_restock_alert(self, estoque_pigmento):
        """Criar alerta de reposição para pigmento com estoque baixo"""
        if not estoque_pigmento.reposicao_solicitada:
            estoque_pigmento.reposicao_solicitada = True
            estoque_pigmento.data_solicitacao_reposicao = timezone.now()
            estoque_pigmento.save()
            
            # Aqui poderia integrar com sistema de compras ou notifications
            self._send_restock_notification(estoque_pigmento)

class ColorScienceService:
    """Serviço para cálculos científicos de cor"""
    
    def rgb_to_lab(self, r, g, b):
        """Converte RGB para CIE Lab"""
        rgb = np.array([r/255.0, g/255.0, b/255.0])
        lab = colour.XYZ_to_Lab(colour.sRGB_to_XYZ(rgb))
        return lab[0], lab[1], lab[2]  # L, a, b
    
    def lab_to_rgb(self, l, a, b):
        """Converte CIE Lab para RGB"""
        lab = np.array([l, a, b])
        rgb = colour.XYZ_to_sRGB(colour.Lab_to_XYZ(lab))
        # Clamp values to 0-255 range
        rgb = np.clip(rgb * 255, 0, 255).astype(int)
        return rgb[0], rgb[1], rgb[2]
    
    def calculate_color_difference(self, color1_lab, color2_lab):
        """Calcula diferença de cor usando Delta E CIE76"""
        return colour.delta_E(color1_lab, color2_lab)
    
    def find_similar_colors(self, target_lab, tolerance=3.0):
        """Encontra cores similares no banco de dados"""
        from .models import LequeCorDefinida
        
        similar_colors = []
        cores = LequeCorDefinida.objects.filter(ativo=True)
        
        for cor in cores:
            cor_lab = [cor.l_value, cor.a_value, cor.b_value]
            delta_e = self.calculate_color_difference(target_lab, cor_lab)
            
            if delta_e <= tolerance:
                similar_colors.append({
                    'cor': cor,
                    'delta_e': float(delta_e),
                    'similarity_percent': max(0, 100 - (delta_e / tolerance * 100))
                })
        
        return sorted(similar_colors, key=lambda x: x['delta_e'])
```

### 2.4 URL Patterns

#### Updated URLs (apps/tintometry/urls.py)

```python
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    FormulaViewSet, MixtureViewSet, CustomerHistoryViewSet, 
    PigmentStockViewSet, ColorDefinitionViewSet
)

router = DefaultRouter()
router.register(r'formulas', FormulaViewSet)
router.register(r'mixtures', MixtureViewSet)
router.register(r'customer-history', CustomerHistoryViewSet, basename='customer-history')
router.register(r'pigment-stock', PigmentStockViewSet)
router.register(r'colors', ColorDefinitionViewSet)

app_name = 'tintometry'

urlpatterns = [
    # Quick calculation endpoint for POS integration
    path('quick-calculate/', views.quick_formula_calculation, name='quick-calculate'),
    
    # Bulk operations
    path('bulk-stock-update/', views.bulk_pigment_stock_update, name='bulk-stock-update'),
    
    # Reporting endpoints
    path('reports/daily-production/', views.daily_production_report, name='daily-production'),
    path('reports/pigment-usage/', views.pigment_usage_report, name='pigment-usage'),
    
    # Label generation
    path('labels/generate/<uuid:mixture_id>/', views.generate_mixture_label, name='generate-label'),
    path('labels/print/<str:label_code>/', views.print_mixture_label, name='print-label'),
    
] + router.urls
```

## 3. File Structure Implementation

### 3.1 Files to Create

```
backend/
├── apps/tintometry/
│   ├── migrations/
│   │   └── 0002_add_mixture_system.py
│   ├── services/
│   │   ├── __init__.py
│   │   ├── formula_calculator.py
│   │   ├── stock_manager.py
│   │   ├── color_science.py
│   │   └── label_generator.py
│   ├── serializers/
│   │   ├── __init__.py
│   │   ├── formula_serializers.py
│   │   ├── mixture_serializers.py
│   │   └── stock_serializers.py
│   ├── utils/
│   │   ├── __init__.py
│   │   ├── color_calculations.py
│   │   └── qr_generator.py
│   └── templatetags/
│       ├── __init__.py
│       └── tintometry_tags.py
└── requirements/
    └── tintometry.txt  # New dependencies
```

### 3.2 Files to Modify

```
backend/apps/tintometry/models.py     # Add MisturaTinta, EstoquePigmento
backend/apps/tintometry/views.py      # Add ViewSets and API endpoints  
backend/apps/tintometry/urls.py       # Add new URL patterns
backend/apps/tintometry/admin.py      # Admin interface for new models
```

### 3.3 Database Migrations

#### Migration 0002_add_mixture_system.py

```python
from django.db import migrations, models
import django.db.models.deletion
import uuid

class Migration(migrations.Migration):
    dependencies = [
        ('tintometry', '0001_initial'),
        ('sales', '0001_initial'),
        ('companies', '0001_initial'),
        ('core', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='MisturaTinta',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, primary_key=True, serialize=False, editable=False)),
                ('codigo_mistura', models.CharField(unique=True, max_length=20)),
                ('volume_solicitado', models.DecimalField(max_digits=8, decimal_places=2)),
                ('volume_produzido', models.DecimalField(max_digits=8, decimal_places=2, null=True)),
                ('custo_total', models.DecimalField(max_digits=10, decimal_places=4)),
                ('situacao', models.CharField(choices=[('CALCULADA', 'Fórmula Calculada'), ('CONFIRMADA', 'Mistura Confirmada'), ('ETIQUETADA', 'Etiqueta Gerada'), ('CANCELADA', 'Cancelada')], default='CALCULADA', max_length=20)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('cliente', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='misturas', to='sales.cliente')),
                ('formula', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='tintometry.formulatinotmetrica')),
                ('loja', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='companies.loja')),
                ('usuario_operacao', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='core.user')),
            ],
            options={'abstract': False,},
        ),
        migrations.CreateModel(
            name='EstoquePigmento',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('saldo_ml', models.DecimalField(decimal_places=4, default=0, max_digits=10)),
                ('saldo_minimo', models.DecimalField(decimal_places=4, default=100, max_digits=10)),
                ('custo_ml', models.DecimalField(decimal_places=4, max_digits=8)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('loja', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='companies.loja')),
                ('pigmento', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='tintometry.pigmento')),
            ],
            options={'unique_together': {('pigmento', 'loja')},},
        ),
        # Additional models...
    ]
```

## 4. Dependencies & Integration

### 4.1 New Python Dependencies

```python
# requirements/tintometry.txt
colour-science==0.4.2    # Comprehensive color science library
colorspacious==1.1.2     # Fast colorspace conversions 
qrcode[pil]==7.4.2       # QR code generation for labels
reportlab==4.0.4         # PDF generation for labels and reports
pillow==10.0.1          # Image processing (enhance existing version)
numpy>=1.24.0           # Mathematical operations (may already exist)
```

### 4.2 Settings Configuration

#### Add to settings.py

```python
# Tintometry specific settings
TINTOMETRY_CONFIG = {
    'DEFAULT_FORMULA_VOLUME': 1.0,  # Litros
    'MINIMUM_MIXTURE_VOLUME': 0.1,  # 100ml
    'MAXIMUM_MIXTURE_VOLUME': 20.0,  # 20L
    'PIGMENT_PRECISION_ML': 0.1,
    'AUTO_GENERATE_MIXTURE_CODE': True,
    'ENABLE_STOCK_ALERTS': True,
    'LABEL_PRINTER_DPI': 300,
    'COLOR_TOLERANCE_DELTA_E': 3.0,
}

# QR Code settings
QR_CODE_CONFIG = {
    'ERROR_CORRECT': 'M',  # Medium error correction
    'BORDER': 4,
    'BOX_SIZE': 10,
}
```

### 4.3 Integration with Existing Apps

#### Core Authentication Integration
- Use existing `User` model for operation tracking
- Extend permissions: `'tintometry.can_calculate_formulas'`, `'tintometry.can_confirm_mixtures'`
- API authentication via existing token system

#### Inventory System Integration
- `EstoquePigmento` extends inventory concepts for pigment-specific management
- Integration with `apps.inventory.models.EstoqueLoja` for base products
- Automatic cost calculations using existing costing methods

#### Sales Integration
- Foreign key to `sales.Cliente` for customer history
- Integration with `sales.PedidoVenda` for mixture orders
- Cross-referencing with customer purchase patterns

#### Companies Integration  
- Multi-store support via `companies.Loja` foreign keys
- Store-specific stock management and formula access
- Centralized formula management with distributed execution

## 5. Quality & Testing Strategy

### 5.1 Unit Test Structure

#### Test Files to Create

```
backend/apps/tintometry/tests/
├── __init__.py
├── test_models.py           # Model validation and business rules
├── test_services.py         # Business logic and calculations
├── test_views.py           # API endpoint functionality  
├── test_integrations.py    # Cross-app integration tests
├── fixtures/
│   ├── formulas.json       # Sample formulas for testing
│   ├── pigments.json       # Standard pigment catalog
│   └── colors.json         # Color definitions
└── utils/
    ├── test_helpers.py     # Common test utilities
    └── color_test_data.py  # Scientific color data for validation
```

#### Key Test Cases

```python
# test_services.py - Formula calculation accuracy
def test_formula_calculation_precision():
    """Test that formula calculations maintain 0.1ml precision"""
    
def test_proportional_scaling():
    """Test volume scaling maintains correct proportions"""
    
def test_stock_validation():
    """Test stock availability checking before calculation"""

# test_models.py - Data integrity
def test_mixture_code_uniqueness():
    """Ensure mixture codes are unique across system"""
    
def test_stock_consistency():
    """Test that stock levels remain consistent after operations"""

# test_integrations.py - Cross-system functionality  
def test_customer_history_integration():
    """Test mixture history appears in customer records"""
    
def test_inventory_stock_updates():
    """Test automatic stock reductions trigger correctly"""
```

### 5.2 Performance Considerations

#### Database Optimization
- **Indexes**: Create composite indexes on frequently queried fields
  - `MisturaTinta`: (cliente_id, created_at)
  - `EstoquePigmento`: (loja_id, pigmento_id)
  - `ItemMistura`: (mistura_id, pigmento_id)

#### Query Optimization
- Use `select_related()` for formula calculations to reduce database hits
- `prefetch_related()` for customer history with multiple mixtures  
- Database-level stock locking prevents race conditions

#### Caching Strategy
- Cache frequently accessed formulas using Django's cache framework
- Cache calculated color differences for similar color suggestions
- Cache customer recent history for faster POS access

### 5.3 Real-time Performance Requirements

#### Stock Update Performance
- Target: < 500ms for mixture confirmation including stock updates
- Use database transactions to ensure consistency
- Implement pessimistic locking for concurrent access handling

#### Formula Calculation Performance
- Target: < 2 seconds for formula calculation with stock validation
- Pre-calculate common volume conversions
- Optimize color science calculations with numpy vectorization

### 5.4 Error Handling & Data Validation

#### Input Validation
```python
# Volume validation
def validate_mixture_volume(volume):
    min_vol = settings.TINTOMETRY_CONFIG['MINIMUM_MIXTURE_VOLUME'] 
    max_vol = settings.TINTOMETRY_CONFIG['MAXIMUM_MIXTURE_VOLUME']
    if not min_vol <= volume <= max_vol:
        raise ValidationError(f'Volume deve estar entre {min_vol}L e {max_vol}L')

# Formula validation  
def validate_formula_completeness(formula):
    if not formula.itens.exists():
        raise ValidationError('Fórmula deve ter pelo menos um pigmento')
    
    total_concentration = sum(item.quantidade for item in formula.itens.all())
    if total_concentration > formula.volume_base * 50:  # 5% max concentration  
        raise ValidationError('Concentração total de pigmentos muito alta')
```

#### Error Recovery
- **Stock conflicts**: Provide alternative formulas when pigments unavailable
- **Calculation errors**: Fall back to manual entry mode with validation
- **Network/database errors**: Queue operations for retry with user notification

## 6. Implementation Roadmap

### 6.1 Phase 1: Core Models & Database (Week 1)
- [ ] Create enhanced models: `MisturaTinta`, `EstoquePigmento`, `ItemMistura`
- [ ] Generate and apply database migrations  
- [ ] Create basic admin interface for data management
- [ ] Set up unit tests for model validation

### 6.2 Phase 2: Formula Calculation Engine (Week 2)
- [ ] Implement `FormulaCalculatorService` with volume scaling
- [ ] Add stock validation and availability checking  
- [ ] Create color science utilities with lab/rgb conversions
- [ ] Test calculation accuracy and edge cases

### 6.3 Phase 3: API Development (Week 3)  
- [ ] Create formula calculation API endpoints
- [ ] Implement mixture recording and confirmation APIs
- [ ] Add customer history retrieval endpoints
- [ ] Build stock management and alert APIs

### 6.4 Phase 4: Stock Management Integration (Week 4)
- [ ] Implement automatic stock reduction service
- [ ] Create low stock alerting system
- [ ] Add batch operations for stock updates
- [ ] Test concurrent access and consistency

### 6.5 Phase 5: Label & Reporting System (Week 5)
- [ ] Build QR code and label generation system
- [ ] Create daily/weekly production reports
- [ ] Add pigment usage analytics
- [ ] Implement customer color preference analytics

### 6.6 Phase 6: Testing & Polish (Week 6)
- [ ] Complete end-to-end integration testing
- [ ] Performance optimization and load testing
- [ ] Documentation and API specification completion
- [ ] User acceptance testing setup

## 7. Success Metrics & Acceptance Criteria

### 7.1 Functional Acceptance
- [ ] Formula calculation completes in < 30 seconds for any registered color
- [ ] Stock accuracy maintains 99.5% precision compared to physical counts
- [ ] Customer color history retrieval shows 95% successful exact reproductions
- [ ] System handles 50 concurrent mixture calculations without conflicts
- [ ] Stock alerts trigger before pigment depletion prevents sales

### 7.2 Performance Benchmarks  
- [ ] API response time < 2 seconds for all calculation endpoints
- [ ] Database transactions complete < 500ms for stock updates  
- [ ] Search customer history by phone < 1 second response time
- [ ] Generate mixture labels < 3 seconds including QR code creation
- [ ] Handle 100+ daily mixtures per store without performance degradation

### 7.3 Integration Success
- [ ] Zero data inconsistencies between tintometry and inventory systems
- [ ] Customer data synchronizes correctly with sales module  
- [ ] Multi-store operations maintain isolated stock while sharing formulas
- [ ] Admin interface allows complete system management without technical knowledge
- [ ] Backup/restore procedures preserve all mixture history and relationships

This comprehensive technical implementation plan provides the complete roadmap for building the tintometric mixing system while maintaining integration with the existing Django architecture and following established best practices.
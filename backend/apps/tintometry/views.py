"""
Tintometry API Views

REST API views for tintometric system:
- CRUD operations for all tintometric entities
- Custom actions for business workflows  
- Scientific calculations and color analysis
- Stock management operations
"""

from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from django.db import transaction
from django.utils import timezone
from django.db.models import Q, Sum
from decimal import Decimal

import logging

from .models import (
    Pigmento,
    LequeCorDefinida,
    FormulaTintometrica,
    MisturaTinta,
    EstoquePigmento,
    EtiquetaMistura
)
from .serializers import (
    PigmentoSerializer,
    LequeCorDefinidaSerializer,
    FormulaTintometricaSerializer,
    MisturaTintaSerializer,
    EstoquePigmentoSerializer,
    EtiquetaMisturaSerializer,
    MisturaCalculationRequestSerializer,
    MistureConfirmationSerializer,
    MixtureExecutionSerializer,
    StockMovementSerializer,
    ColorAnalysisSerializer,
    StockAlertSerializer,
    ColorMatchSerializer
)
from .services import (
    FormulaCalculatorService,
    StockManagerService,
    ColorScienceService,
    MixtureService
)

logger = logging.getLogger(__name__)


class PigmentoViewSet(viewsets.ModelViewSet):
    """ViewSet para pigmentos tintométricos"""
    
    queryset = Pigmento.objects.all()
    serializer_class = PigmentoSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['cor_base', 'fornecedor', 'ativo']
    search_fields = ['nome', 'codigo', 'fornecedor']
    ordering_fields = ['nome', 'codigo', 'densidade', 'poder_tintorial']
    ordering = ['nome']
    
    def get_queryset(self):
        """Personaliza queryset baseado em parâmetros"""
        queryset = super().get_queryset()
        
        # Filtrar apenas ativos por padrão
        if not self.request.query_params.get('include_inactive'):
            queryset = queryset.filter(ativo=True)
        
        return queryset
    
    @action(detail=True, methods=['get'])
    def stock_status(self, request, pk=None):
        """Retorna status de estoque do pigmento em todas as lojas"""
        pigmento = self.get_object()
        
        # Obter estoque em todas as lojas
        estoques = EstoquePigmento.objects.filter(
            pigmento=pigmento,
            ativo=True
        ).select_related('loja')
        
        stock_data = []
        for estoque in estoques:
            stock_data.append({
                'loja': {
                    'id': estoque.loja.id,
                    'nome': estoque.loja.nome
                },
                'saldo_ml': float(estoque.saldo_ml),
                'estoque_critico': estoque.estoque_critico,
                'valor_estoque': float(estoque.valor_total_estoque),
                'lote_atual': estoque.lote_atual,
                'validade': estoque.validade_lote.isoformat() if estoque.validade_lote else None
            })
        
        return Response({
            'pigmento': PigmentoSerializer(pigmento).data,
            'estoques': stock_data,
            'total_lojas': len(stock_data),
            'valor_total': sum(item['valor_estoque'] for item in stock_data)
        })
    
    @action(detail=True, methods=['get'])
    def usage_history(self, request, pk=None):
        """Retorna histórico de uso do pigmento"""
        pigmento = self.get_object()
        days_back = int(request.query_params.get('days', 30))
        
        stock_service = StockManagerService()
        loja_id = request.query_params.get('loja_id')
        
        if loja_id:
            history = stock_service.get_stock_movement_history(
                loja_id=int(loja_id),
                pigmento_id=pigmento.id,
                days_back=days_back
            )
        else:
            # Buscar histórico de todas as lojas
            history = []
            # Implementar busca multi-loja se necessário
        
        return Response({
            'pigmento': PigmentoSerializer(pigmento).data,
            'periodo_dias': days_back,
            'movimentacoes': history,
            'total_movimentacoes': len(history)
        })


class LequeCorDefinidaViewSet(viewsets.ModelViewSet):
    """ViewSet para cores do leque"""
    
    queryset = LequeCorDefinida.objects.all()
    serializer_class = LequeCorDefinidaSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['familia_cor', 'linha_produto', 'ativo']
    search_fields = ['nome_cor', 'codigo_cor', 'familia_cor']
    ordering_fields = ['nome_cor', 'codigo_cor', 'data_criacao']
    ordering = ['familia_cor', 'nome_cor']
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        if not self.request.query_params.get('include_inactive'):
            queryset = queryset.filter(ativo=True)
        
        return queryset
    
    @action(detail=False, methods=['post'])
    def find_similar_colors(self, request):
        """Encontra cores similares baseadas em Lab ou RGB"""
        serializer = ColorMatchSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        color_service = ColorScienceService()
        
        # Converter RGB para Lab se necessário
        if serializer.validated_data.get('target_rgb'):
            r, g, b = serializer.validated_data['target_rgb']
            target_lab = color_service.rgb_to_lab(r, g, b)
        else:
            target_lab = tuple(serializer.validated_data['target_lab'])
        
        # Buscar cores na biblioteca
        colors = self.get_queryset()
        color_library = []
        
        for color in colors:
            color_library.append({
                'id': color.id,
                'codigo_cor': color.codigo_cor,
                'nome': color.nome_cor,
                'familia': color.familia_cor,
                'lab': (color.l_value, color.a_value, color.b_value),
                'rgb': (color.r, color.g, color.b)
            })
        
        # Encontrar matches
        matches = color_service.find_closest_color_match(
            target_lab=target_lab,
            color_library=color_library,
            max_results=serializer.validated_data['max_results']
        )
        
        return Response({
            'target_color': {
                'lab': list(target_lab),
                'rgb': color_service.lab_to_rgb(*target_lab) if serializer.validated_data.get('target_lab') else serializer.validated_data.get('target_rgb')
            },
            'matches': matches,
            'total_found': len(matches),
            'tolerance_level': serializer.validated_data['tolerance_level']
        })
    
    @action(detail=True, methods=['get'])
    def available_formulas(self, request, pk=None):
        """Lista fórmulas disponíveis para esta cor"""
        cor = self.get_object()
        
        formulas = FormulaTintometrica.objects.filter(
            cor_definida=cor,
            ativa=True
        ).select_related('base_produto').prefetch_related('itens__pigmento')
        
        return Response({
            'cor': LequeCorDefinidaSerializer(cor).data,
            'formulas': FormulaTintometricaSerializer(formulas, many=True).data,
            'total_formulas': formulas.count()
        })


class FormulaTintometricaViewSet(viewsets.ModelViewSet):
    """ViewSet para fórmulas tintométricas"""
    
    queryset = FormulaTintometrica.objects.select_related(
        'cor_definida', 'base_produto'
    ).prefetch_related('itens__pigmento')
    serializer_class = FormulaTintometricaSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['aprovada', 'testada', 'ativa']
    search_fields = ['nome_formula', 'codigo_formula']
    ordering_fields = ['nome_formula', 'codigo_formula', 'created_at']
    ordering = ['-created_at']
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        if not self.request.query_params.get('include_inactive'):
            queryset = queryset.filter(ativa=True)
        
        return queryset
    
    @action(detail=True, methods=['post'])
    def calculate_mixture(self, request, pk=None):
        """Calcula mistura para volume específico"""
        formula = self.get_object()
        
        # Validar dados de entrada
        data = {
            'formula_id': str(formula.id),
            'volume_requested': request.data.get('volume_requested'),
            'loja_id': request.data.get('loja_id'),
            'customer_data': request.data.get('customer_data', {}),
            'observations': request.data.get('observations', ''),
            'validate_stock': request.data.get('validate_stock', True)
        }
        
        calc_serializer = MisturaCalculationRequestSerializer(data=data)
        calc_serializer.is_valid(raise_exception=True)
        
        try:
            calculator_service = FormulaCalculatorService()
            
            # Calcular quantidades
            calculation_result = calculator_service.calculate_mixture_quantities(
                formula=formula,
                target_volume=Decimal(str(calc_serializer.validated_data['volume_requested'])),
                loja_id=calc_serializer.validated_data['loja_id'],
                validate_stock=calc_serializer.validated_data['validate_stock']
            )
            
            # Análise de custos detalhada
            cost_breakdown = calculator_service.calculate_cost_breakdown(calculation_result)
            
            return Response({
                'success': True,
                'formula': FormulaTintometricaSerializer(formula).data,
                'calculation': calculation_result,
                'cost_breakdown': cost_breakdown,
                'recommendations': self._generate_mixing_recommendations(calculation_result)
            })
            
        except Exception as e:
            logger.error(f"Erro no cálculo da fórmula {formula.codigo_formula}: {str(e)}")
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['get'])
    def cost_analysis(self, request, pk=None):
        """Análise de custos da fórmula para diferentes volumes"""
        formula = self.get_object()
        loja_id = request.query_params.get('loja_id')
        
        if not loja_id:
            return Response({
                'error': 'loja_id é obrigatório'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        calculator_service = FormulaCalculatorService()
        volumes = [Decimal('0.5'), Decimal('1.0'), Decimal('3.6'), Decimal('18.0')]  # Volumes comuns
        
        analysis = []
        
        for volume in volumes:
            try:
                result = calculator_service.calculate_mixture_quantities(
                    formula=formula,
                    target_volume=volume,
                    loja_id=int(loja_id),
                    validate_stock=False
                )
                
                analysis.append({
                    'volume_litros': float(volume),
                    'custo_total': result['custos']['total'],
                    'custo_por_litro': result['custos']['total'] / volume,
                    'custo_base': result['custos']['base'],
                    'custo_pigmentos': result['custos']['pigmentos']
                })
                
            except Exception as e:
                logger.warning(f"Erro no cálculo para volume {volume}: {str(e)}")
        
        return Response({
            'formula': FormulaTintometricaSerializer(formula).data,
            'cost_analysis': analysis,
            'loja_id': int(loja_id)
        })
    
    def _generate_mixing_recommendations(self, calculation_result):
        """Gera recomendações para a mistura"""
        recommendations = []
        
        # Verificar alertas de estoque
        if calculation_result['validacao']['warnings']:
            recommendations.extend(calculation_result['validacao']['warnings'])
        
        # Recomendações baseadas no número de pigmentos
        num_pigments = len(calculation_result['pigmentos'])
        if num_pigments > 5:
            recommendations.append("Fórmula complexa com muitos pigmentos - misturar em sequência cuidadosa")
        
        # Recomendações baseadas no custo
        if calculation_result['custos']['total'] > 100:
            recommendations.append("Mistura de alto custo - confirmar aprovação do cliente")
        
        return recommendations


class MisturaTintaViewSet(viewsets.ModelViewSet):
    """ViewSet para misturas de tinta"""
    
    queryset = MisturaTinta.objects.select_related(
        'formula', 'formula__cor_definida', 'loja', 'usuario_operacao'
    ).prefetch_related('itens__pigmento', 'etiqueta')
    serializer_class = MisturaTintaSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['situacao', 'loja', 'cor_aprovada_cliente']
    search_fields = ['codigo_mistura', 'cliente_nome', 'cliente_telefone']
    ordering_fields = ['created_at', 'data_confirmacao', 'custo_total']
    ordering = ['-created_at']
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Filtros por data
        date_from = self.request.query_params.get('date_from')
        date_to = self.request.query_params.get('date_to')
        
        if date_from:
            queryset = queryset.filter(created_at__date__gte=date_from)
        if date_to:
            queryset = queryset.filter(created_at__date__lte=date_to)
        
        # Filtro por telefone do cliente
        phone = self.request.query_params.get('customer_phone')
        if phone:
            queryset = queryset.filter(cliente_telefone__icontains=phone)
        
        return queryset
    
    @action(detail=False, methods=['post'])
    def create_calculation(self, request):
        """Cria nova mistura com cálculo completo"""
        serializer = MisturaCalculationRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        mixture_service = MixtureService()
        
        try:
            result = mixture_service.create_mixture_calculation(
                formula_id=str(serializer.validated_data['formula_id']),
                volume_requested=serializer.validated_data['volume_requested'],
                loja_id=serializer.validated_data['loja_id'],
                user_id=str(request.user.id),
                customer_data=serializer.validated_data['customer_data'],
                observations=serializer.validated_data.get('observations'),
                validate_stock=serializer.validated_data['validate_stock']
            )
            
            return Response(result, status=status.HTTP_201_CREATED if result['success'] else status.HTTP_400_BAD_REQUEST)
            
        except Exception as e:
            logger.error(f"Erro na criação da mistura: {str(e)}")
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['post'])
    def confirm(self, request, pk=None):
        """Confirma mistura e reserva estoque"""
        mistura = self.get_object()
        
        serializer = MistureConfirmationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        mixture_service = MixtureService()
        
        try:
            result = mixture_service.confirm_mixture(
                mixture_id=str(mistura.id),
                user_id=str(request.user.id),
                reserve_stock=serializer.validated_data['reserve_stock']
            )
            
            return Response(result, status=status.HTTP_200_OK if result['success'] else status.HTTP_400_BAD_REQUEST)
            
        except Exception as e:
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['post'])
    def execute(self, request, pk=None):
        """Registra execução física da mistura"""
        mistura = self.get_object()
        
        serializer = MixtureExecutionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        mixture_service = MixtureService()
        
        try:
            result = mixture_service.execute_mixture(
                mixture_id=str(mistura.id),
                user_id=str(request.user.id),
                actual_quantities=serializer.validated_data.get('actual_quantities'),
                actual_volume=serializer.validated_data.get('actual_volume'),
                quality_approved=serializer.validated_data['quality_approved'],
                observations=serializer.validated_data.get('observations')
            )
            
            return Response(result)
            
        except Exception as e:
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['post'])
    def complete(self, request, pk=None):
        """Finaliza mistura marcando como entregue"""
        mistura = self.get_object()
        
        mixture_service = MixtureService()
        
        try:
            result = mixture_service.complete_mixture(
                mixture_id=str(mistura.id),
                user_id=str(request.user.id),
                delivery_confirmed=request.data.get('delivery_confirmed', True),
                customer_feedback=request.data.get('customer_feedback')
            )
            
            return Response(result)
            
        except Exception as e:
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        """Cancela mistura e restaura estoque reservado.

        Aceita: { "motivo": "..." }
        Apenas misturas CALCULADA ou CONFIRMADA podem ser canceladas.
        """
        mistura = self.get_object()
        motivo = request.data.get('motivo', '').strip()

        if not motivo:
            return Response(
                {'success': False, 'error': 'O campo "motivo" é obrigatório.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        mixture_service = MixtureService()

        try:
            result = mixture_service.cancel_mixture(
                mixture_id=str(mistura.id),
                motivo=motivo,
                user_id=str(request.user.id),
            )
            return Response(result, status=status.HTTP_200_OK)

        except Exception as e:
            return Response(
                {'success': False, 'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST,
            )

    @action(detail=True, methods=['get'])
    def detailed_status(self, request, pk=None):
        """Status detalhado da mistura"""
        mistura = self.get_object()
        
        mixture_service = MixtureService()
        status_data = mixture_service.get_mixture_status(str(mistura.id))
        
        return Response(status_data)
    
    @action(detail=False, methods=['get'])
    def dashboard_summary(self, request):
        """Resumo para dashboard"""
        loja_id = request.query_params.get('loja_id')
        
        queryset = self.get_queryset()
        if loja_id:
            queryset = queryset.filter(loja_id=loja_id)
        
        # Resumo por situação
        summary = {
            'total_misturas': queryset.count(),
            'por_situacao': {},
            'receita_total': 0,
            'misturas_hoje': 0,
            'misturas_pendentes': 0
        }
        
        # Contar por situação
        situacoes = queryset.values_list('situacao', flat=True)
        for situacao in ['CALCULADA', 'CONFIRMADA', 'PRODUZIDA', 'ENTREGUE', 'CANCELADA']:
            summary['por_situacao'][situacao] = situacoes.filter(situacao=situacao).count()
        
        # Receita total (apenas entregues)
        receita = queryset.filter(situacao='ENTREGUE').aggregate(
            total=Sum('custo_total')
        )['total'] or 0
        summary['receita_total'] = float(receita)
        
        # Misturas hoje
        hoje = timezone.now().date()
        summary['misturas_hoje'] = queryset.filter(created_at__date=hoje).count()
        
        # Pendentes
        summary['misturas_pendentes'] = queryset.filter(
            situacao__in=['CALCULADA', 'CONFIRMADA', 'PRODUZIDA']
        ).count()
        
        return Response(summary)


class EstoquePigmentoViewSet(viewsets.ModelViewSet):
    """ViewSet para estoque de pigmentos"""
    
    queryset = EstoquePigmento.objects.select_related('pigmento', 'loja')
    serializer_class = EstoquePigmentoSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['loja', 'estoque_critico', 'alerta_ativo', 'ativo']
    search_fields = ['pigmento__nome', 'pigmento__codigo', 'lote_atual']
    ordering_fields = ['saldo_ml', 'percentual_estoque', 'validade_lote']
    ordering = ['pigmento__nome']
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        if not self.request.query_params.get('include_inactive'):
            queryset = queryset.filter(ativo=True)
        
        return queryset
    
    @action(detail=False, methods=['get'])
    def low_stock_alerts(self, request):
        """Lista alertas de estoque baixo"""
        loja_id = request.query_params.get('loja_id')
        
        stock_service = StockManagerService()
        alerts = stock_service.get_low_stock_alerts(loja_id=int(loja_id) if loja_id else None)
        
        return Response(alerts)
    
    @action(detail=False, methods=['get'])
    def stock_summary(self, request):
        """Resumo geral de estoque"""
        loja_id = request.query_params.get('loja_id')
        
        stock_service = StockManagerService()
        
        if loja_id:
            summary = stock_service.get_stock_status(loja_id=int(loja_id))
        else:
            # Resumo geral de todas as lojas
            summary = {'error': 'loja_id obrigatório para resumo de estoque'}
        
        return Response(summary)
    
    @action(detail=True, methods=['post'])
    def add_stock(self, request, pk=None):
        """Adiciona estoque para o pigmento"""
        estoque = self.get_object()
        
        serializer = StockMovementSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        stock_service = StockManagerService()
        
        success, message = stock_service.add_stock(
            loja_id=estoque.loja.id,
            pigmento_id=estoque.pigmento.id,
            quantidade=serializer.validated_data['quantidade'],
            custo_unitario=serializer.validated_data['custo_unitario'],
            lote=serializer.validated_data.get('lote'),
            validade=serializer.validated_data.get('validade'),
            observacoes=serializer.validated_data.get('observacoes')
        )
        
        if success:
            # Retornar estoque atualizado
            estoque.refresh_from_db()
            return Response({
                'success': True,
                'message': message,
                'estoque': EstoquePigmentoSerializer(estoque).data
            })
        else:
            return Response({
                'success': False,
                'error': message
            }, status=status.HTTP_400_BAD_REQUEST)


class ColorAnalysisAPIView(viewsets.GenericViewSet):
    """API para análise científica de cores"""
    
    permission_classes = [IsAuthenticated]
    
    @action(detail=False, methods=['post'])
    def compare_colors(self, request):
        """Compara duas cores e calcula Delta E"""
        serializer = ColorAnalysisSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        color_service = ColorScienceService()
        
        target_lab = tuple(serializer.validated_data['target_lab'])
        achieved_lab = tuple(serializer.validated_data['achieved_lab'])
        tolerance_level = serializer.validated_data['tolerance_level']
        
        evaluation = color_service.evaluate_color_match(
            target_lab, achieved_lab, tolerance_level
        )
        
        return Response(evaluation)
    
    @action(detail=False, methods=['post'])
    def rgb_to_lab(self, request):
        """Converte RGB para Lab"""
        r = int(request.data.get('r', 0))
        g = int(request.data.get('g', 0))
        b = int(request.data.get('b', 0))
        
        if not all(0 <= val <= 255 for val in [r, g, b]):
            return Response({
                'error': 'Valores RGB devem estar entre 0 e 255'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        color_service = ColorScienceService()
        L, a, b_lab = color_service.rgb_to_lab(r, g, b)
        
        return Response({
            'rgb': {'r': r, 'g': g, 'b': b},
            'lab': {'L': float(L), 'a': float(a), 'b': float(b_lab)}
        })
    
    @action(detail=False, methods=['post'])
    def lab_to_rgb(self, request):
        """Converte Lab para RGB"""
        L = Decimal(str(request.data.get('L', 0)))
        a = Decimal(str(request.data.get('a', 0)))
        b = Decimal(str(request.data.get('b', 0)))
        
        color_service = ColorScienceService()
        r, g, b_rgb = color_service.lab_to_rgb(L, a, b)
        
        return Response({
            'lab': {'L': float(L), 'a': float(a), 'b': float(b)},
            'rgb': {'r': r, 'g': g, 'b': b_rgb}
        })

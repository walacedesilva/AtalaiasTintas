"""
Label API Views

API completa para geração e gerenciamento de etiquetas:
- Geração de etiquetas PDF em tempo real
- Gestão de templates customizados
- Preview HTML para visualização  
- Validação de QR Codes
- Histórico de etiquetas geradas
- Configuração de impressoras
"""

import base64
import json
import logging
from typing import Dict, Any

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.parsers import MultiPartParser, JSONParser
from django_filters.rest_framework import DjangoFilterBackend
from django.http import HttpResponse
from django.utils import timezone
from django.core.cache import cache
from django.db import transaction

from ..models import MisturaTinta, EtiquetaMistura
from .services import LabelGeneratorService, QRCodeService
from .renderers import LabelPDFRenderer
from .templates import TemplateManager, EtiquetaTemplate
from .serializers import (
    LabelGenerationRequestSerializer,
    LabelResponseSerializer,
    LabelTemplateSerializer,
    LabelTemplateListSerializer,
    EtiquetaMisturaSerializer,
    QRCodeValidationSerializer,
    QRCodeValidationResponseSerializer
)

logger = logging.getLogger(__name__)


class LabelGenerationViewSet(viewsets.GenericViewSet):
    """
    ViewSet principal para geração de etiquetas
    
    Endpoints:
    - POST /generate/ - Gerar etiqueta
    - POST /preview/ - Preview HTML  
    - GET /templates/ - Listar templates
    - POST /templates/ - Criar template customizado
    - POST /validate_qr/ - Validar QR Code
    """
    
    permission_classes = [IsAuthenticated]
    parser_classes = [JSONParser, MultiPartParser]
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.label_service = LabelGeneratorService()
        self.pdf_renderer = LabelPDFRenderer()
        self.template_manager = TemplateManager()
        self.qr_service = QRCodeService()
    
    @action(detail=False, methods=['post'])
    def generate(self, request):
        """
        Gera etiqueta completa para mistura
        
        Body:
        {
          "mistura_id": "uuid",
          "template_id": "default",
          "output_format": "pdf",
          "auto_print": false
        }
        """
        serializer = LabelGenerationRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        try:
            # Extrair dados validados
            mistura_id = str(serializer.validated_data['mistura_id'])
            template_id = serializer.validated_data['template_id']
            output_format = serializer.validated_data['output_format']
            custom_template = serializer.validated_data.get('custom_template')
            
            # Buscar loja do usuário (assumindo que existe relação)
            loja_id = getattr(request.user, 'loja_id', None)
            
            # Usar template customizado ou buscar por ID
            if custom_template:
                template = custom_template
            else:
                template = self.template_manager.load_template(template_id, loja_id)
            
            # Gerar dados da etiqueta
            label_data = self.label_service.generate_label_data(mistura_id, template_id)
            
            # Crear registro no banco
            etiqueta_record = self.label_service.create_label_record(mistura_id, template_id)
            
            # Preparar resposta baseada no formato
            response_data = {
                'success': True,
                'mistura_id': mistura_id,
                'etiqueta_id': str(etiqueta_record.id),
                'template_used': template_id,
                'generation_time': timezone.now(),
                'qr_data_summary': label_data['qr_code']['data_summary'],
                'barcode': label_data['barcode']['code'],
                'warnings': []
            }
            
            if output_format == 'pdf':
                # Gerar PDF
                pdf_bytes = self.pdf_renderer.render_label_pdf(label_data, template)
                pdf_b64 = base64.b64encode(pdf_bytes).decode('utf-8')
                
                response_data.update({
                    'pdf_base64': pdf_b64,
                    'file_size_bytes': len(pdf_bytes)
                })
                
                # Auto-impressão se solicitada
                if serializer.validated_data.get('auto_print'):
                    printer_name = serializer.validated_data.get('printer_name')
                    # TODO: Implementar fila de impressão
                    response_data['print_queue_id'] = 1  # Placeholder
                
            elif output_format == 'preview_html':
                # Gerar preview HTML
                html_preview = self.pdf_renderer.generate_preview_html(label_data, template)
                response_data['preview_html'] = html_preview
                
            elif output_format == 'data_only':
                # Retornar apenas dados estruturados
                response_data['label_data'] = label_data
            
            # Atualizar registro da etiqueta  
            etiqueta_record.data_geracao = timezone.now()
            etiqueta_record.save()
            
            return Response(response_data, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            logger.error(f"Erro gerando etiqueta para mistura {mistura_id}: {str(e)}")
            return Response({
                'success': False,
                'error': str(e),
                'mistura_id': mistura_id if 'mistura_id' in locals() else None
            }, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['post'])
    def preview(self, request):
        """
        Gera preview HTML rápido da etiqueta
        
        Usado para visualização antes da geração final
        """
        serializer = LabelGenerationRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        try:
            mistura_id = str(serializer.validated_data['mistura_id'])
            template_id = serializer.validated_data['template_id']
            custom_template = serializer.validated_data.get('custom_template')
            
            loja_id = getattr(request.user, 'loja_id', None)
            
            # Carregar template
            if custom_template:
                template = custom_template
            else:
                template = self.template_manager.load_template(template_id, loja_id)
            
            # Buscar dados do cache ou gerar novos
            label_data = self.label_service.get_cached_label_data(mistura_id, template_id)
            
            # Gerar HTML preview
            html_preview = self.pdf_renderer.generate_preview_html(label_data, template)
            
            return Response({
                'success': True,
                'preview_html': html_preview,
                'template_used': template_id,
                'cached_data': 'label_data' in cache.get(f"label_data_{mistura_id}_{template_id}", {})
            })
            
        except Exception as e:
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['get'])
    def templates(self, request):
        """
        Lista todos os templates disponíveis
        
        Query params:
        - loja_id: ID da loja (inclui templates customizados)
        """
        loja_id = request.query_params.get('loja_id')
        if loja_id:
            loja_id = int(loja_id)
        
        try:
            templates_list = self.template_manager.list_templates(loja_id)
            
            serializer = LabelTemplateListSerializer(templates_list, many=True)
            
            return Response({
                'success': True,
                'templates': serializer.data,
                'total_count': len(templates_list),
                'loja_id': loja_id
            })
            
        except Exception as e:
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['post'])
    def create_template(self, request):
        """
        Cria template customizado para loja
        
        Body: Dados do LabelTemplateSerializer
        """
        serializer = LabelTemplateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        try:
            # Converter para objeto EtiquetaTemplate
            template = serializer.validated_data
            
            # Validar template
            is_valid, errors = self.template_manager.validate_template(template)
            if not is_valid:
                return Response({
                    'success': False,
                    'validation_errors': errors
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Salvar template (assumir loja do usuário)
            loja_id = getattr(request.user, 'loja_id', 1)  # Default loja 1
            
            success = self.template_manager.save_custom_template(template, loja_id)
            
            if success:
                return Response({
                    'success': True,
                    'template_id': template.id,
                    'message': f'Template "{template.name}" criado com sucesso',
                    'loja_id': loja_id
                }, status=status.HTTP_201_CREATED)
            else:
                return Response({
                    'success': False,
                    'error': 'Erro salvando template'
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
                
        except Exception as e:
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['post'])
    def validate_qr(self, request):
        """
        Valida QR Code de etiqueta
        
        Body:
        {
          "qr_content": "json_string_from_qr"
        }
        """
        serializer = QRCodeValidationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        try:
            qr_content = serializer.validated_data['qr_content']
            
            # Validar QR Code
            is_valid, qr_data = self.qr_service.validate_qr_data(qr_content)
            
            response_data = {
                'valid': is_valid,
                'qr_data': qr_data if is_valid else None,
                'warnings': []
            }
            
            if is_valid:
                # Tentar encontrar mistura no sistema
                try:
                    mistura_id = qr_data.get('id')
                    mistura = MisturaTinta.objects.get(id=mistura_id)
                    
                    response_data.update({
                        'mistura_found': True,
                        'mistura_data': {
                            'id': str(mistura.id),
                            'codigo': mistura.codigo_mistura,
                            'situacao': mistura.situacao,
                            'cor_nome': mistura.formula.cor_definida.nome_cor,
                            'volume_ml': float(mistura.volume_calculado_ml),
                            'data_criacao': mistura.created_at.isoformat()
                        }
                    })
                    
                    # Calcular idade do QR
                    qr_timestamp = timezone.datetime.fromisoformat(
                        qr_data['timestamp'].replace('Z', '+00:00')
                    )
                    age_days = (timezone.now() - qr_timestamp).days
                    response_data['age_days'] = age_days
                    
                    # Avisos baseados na idade
                    if age_days > 7:
                        response_data['warnings'].append(f'QR Code antigo ({age_days} dias)')
                    if age_days > 30:
                        response_data['warnings'].append('QR Code pode estar expirado')
                        
                except MisturaTinta.DoesNotExist:
                    response_data.update({
                        'mistura_found': False,
                        'warnings': ['Mistura não encontrada no sistema atual']
                    })
            else:
                response_data['error'] = qr_data.get('error', 'QR Code inválido')
            
            return Response(response_data)
            
        except Exception as e:
            return Response({
                'valid': False,
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['get'])
    def download_pdf(self, request):
        """
        Download direto de PDF de etiqueta
        
        Query params:
        - etiqueta_id: ID da etiqueta 
        """
        etiqueta_id = request.query_params.get('etiqueta_id')
        
        if not etiqueta_id:
            return Response({
                'error': 'etiqueta_id é obrigatório'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            # Buscar registro da etiqueta
            etiqueta = EtiquetaMistura.objects.select_related(
                'mistura__formula__cor_definida'
            ).get(id=etiqueta_id)
            
            # Gerar dados da etiqueta novamente
            label_data = self.label_service.generate_label_data(
                str(etiqueta.mistura.id),
                etiqueta.template_usado
            )
            
            # Carregar template
            loja_id = etiqueta.mistura.loja.id
            template = self.template_manager.load_template(etiqueta.template_usado, loja_id)
            
            # Renderizar PDF  
            pdf_bytes = self.pdf_renderer.render_label_pdf(label_data, template)
            
            # Retornar como download
            response = HttpResponse(pdf_bytes, content_type='application/pdf')
            filename = f"etiqueta_{etiqueta.codigo_rastreamento}.pdf"
            response['Content-Disposition'] = f'attachment; filename="{filename}"'
            response['Content-Length'] = len(pdf_bytes)
            
            # Incrementar contador de impressões
            etiqueta.contador_impressao += 1
            etiqueta.data_impressao = timezone.now()
            etiqueta.save()
            
            return response
            
        except EtiquetaMistura.DoesNotExist:
            return Response({
                'error': 'Etiqueta não encontrada'
            }, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class EtiquetaHistoryViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet para histórico de etiquetas geradas
    
    Endpoints:
    - GET / - Listar etiquetas
    - GET /{id}/ - Detalhes da etiqueta
    - GET /stats/ - Estatísticas de impressões
    """
    
    queryset = EtiquetaMistura.objects.select_related(
        'mistura__formula__cor_definida',
        'mistura__loja'
    ).order_by('-created_at')
    
    serializer_class = EtiquetaMisturaSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['status', 'template_usado', 'mistura__loja']
    search_fields = ['codigo_rastreamento', 'mistura__codigo_mistura']
    
    def get_queryset(self):
        """Filtrar por loja do usuário se aplicável"""
        queryset = super().get_queryset()
        
        # Filtro por data
        data_inicio = self.request.query_params.get('data_inicio')
        data_fim = self.request.query_params.get('data_fim')
        
        if data_inicio:
            queryset = queryset.filter(created_at__date__gte=data_inicio)
        if data_fim:
            queryset = queryset.filter(created_at__date__lte=data_fim)
        
        return queryset
    
    @action(detail=False, methods=['get'])
    def stats(self, request):
        """
        Estatísticas de etiquetas e impressões
        """
        queryset = self.get_queryset()
        
        # Estatísticas gerais
        stats = {
            'total_etiquetas': queryset.count(),
            'total_impressoes': sum(etq.contador_impressao for etq in queryset),
            'etiquetas_hoje': queryset.filter(
                created_at__date=timezone.now().date()
            ).count(),
            'templates_mais_usados': {},
            'status_distribution': {},
            'impressoes_por_dia': {}
        }
        
        # Templates mais usados
        templates = queryset.values_list('template_usado', flat=True)
        for template in set(templates):
            stats['templates_mais_usados'][template] = templates.filter(
                template_usado=template
            ).count()
        
        # Distribuição por status
        for status_choice in EtiquetaMistura.STATUS_CHOICES:
            status_value = status_choice[0]
            stats['status_distribution'][status_value] = queryset.filter(
                status=status_value
            ).count()
        
        return Response(stats)
    
    @action(detail=True, methods=['post'])
    def regenerate(self, request, pk=None):
        """
        Regenera etiqueta existente com novos parâmetros
        """
        etiqueta = self.get_object()
        
        try:
            # Usar serviço de geração
            label_service = LabelGeneratorService()
            pdf_renderer = LabelPDFRenderer()
            template_manager = TemplateManager()
            
            # Parâmetros opcionais
            template_id = request.data.get('template_id', etiqueta.template_usado)
            output_format = request.data.get('output_format', 'pdf')
            
            # Carregar template
            loja_id = etiqueta.mistura.loja.id
            template = template_manager.load_template(template_id, loja_id)
            
            # Gerar dados atualizados
            label_data = label_service.generate_label_data(
                str(etiqueta.mistura.id),
                template_id
            )
            
            if output_format == 'pdf':
                # Gerar PDF
                pdf_bytes = pdf_renderer.render_label_pdf(label_data, template)
                pdf_b64 = base64.b64encode(pdf_bytes).decode('utf-8')
                
                # Atualizar registro
                etiqueta.template_usado = template_id
                etiqueta.contador_impressao += 1
                etiqueta.save()
                
                return Response({
                    'success': True,
                    'etiqueta_id': str(etiqueta.id),
                    'pdf_base64': pdf_b64,
                    'template_used': template_id,
                    'regeneration_time': timezone.now()
                })
            
            elif output_format == 'preview_html':
                html_preview = pdf_renderer.generate_preview_html(label_data, template)
                
                return Response({
                    'success': True,
                    'preview_html': html_preview,
                    'template_used': template_id
                })
            
            else:
                return Response({
                    'success': True,
                    'label_data': label_data,
                    'template_used': template_id
                })
                
        except Exception as e:
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)
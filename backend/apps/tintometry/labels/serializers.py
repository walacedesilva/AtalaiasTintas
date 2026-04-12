"""
Label API Serializers

Serializers para API de geração e gerenciamento de etiquetas:
- Validação de dados de entrada
- Configuração de templates
- Parâmetros de renderização
- Metadados de etiquetas geradas
- Preview e download de PDFs
"""

from rest_framework import serializers
from rest_framework.fields import SerializerMethodField
from django.core.validators import RegexValidator
from typing import Dict, Any
import json

from ..models import MisturaTinta, EtiquetaMistura
from .templates import EtiquetaTemplate, LabelSize, LabelOrientation, ColorScheme, FontConfig, LayoutConfig


class ColorSchemeSerializer(serializers.Serializer):
    """Serializer para esquema de cores"""
    
    primary = serializers.CharField(
        max_length=7,
        validators=[RegexValidator(r'^#[0-9A-Fa-f]{6}$', 'Cor deve estar no formato #RRGGBB')],
        help_text="Cor primária (ex: #1e3a8a)"
    )
    secondary = serializers.CharField(
        max_length=7,
        validators=[RegexValidator(r'^#[0-9A-Fa-f]{6}$')],
        help_text="Cor secundária"
    )
    accent = serializers.CharField(
        max_length=7,
        validators=[RegexValidator(r'^#[0-9A-Fa-f]{6}$')],
        help_text="Cor de destaque"
    )
    background = serializers.CharField(
        max_length=7,
        validators=[RegexValidator(r'^#[0-9A-Fa-f]{6}$')], 
        help_text="Cor de fundo"
    )
    text_primary = serializers.CharField(
        max_length=7,
        validators=[RegexValidator(r'^#[0-9A-Fa-f]{6}$')],
        help_text="Cor do texto principal"
    )
    text_secondary = serializers.CharField(
        max_length=7,
        validators=[RegexValidator(r'^#[0-9A-Fa-f]{6}$')],
        help_text="Cor do texto secundário"
    )


class FontConfigSerializer(serializers.Serializer):
    """Serializer para configuração de fontes"""
    
    family_primary = serializers.CharField(
        max_length=50,
        default="Arial",
        help_text="Família da fonte primária"
    )
    family_secondary = serializers.CharField(
        max_length=50,
        default="Arial",
        help_text="Família da fonte secundária"
    )
    size_title = serializers.IntegerField(
        min_value=8,
        max_value=24,
        default=14,
        help_text="Tamanho da fonte do título (8-24pt)"
    )
    size_subtitle = serializers.IntegerField(
        min_value=6,
        max_value=18,
        default=10,
        help_text="Tamanho da fonte do subtítulo (6-18pt)"
    )
    size_body = serializers.IntegerField(
        min_value=6,
        max_value=16,
        default=8,
        help_text="Tamanho da fonte do corpo (6-16pt)"
    )
    size_small = serializers.IntegerField(
        min_value=4,
        max_value=12,
        default=6,
        help_text="Tamanho da fonte pequena (4-12pt)"
    )


class LayoutConfigSerializer(serializers.Serializer):
    """Serializer para configuração de layout"""
    
    padding = serializers.IntegerField(
        min_value=0,
        max_value=15,
        default=5,
        help_text="Padding interno em mm (0-15mm)"
    )
    margin = serializers.IntegerField(
        min_value=0,
        max_value=10,
        default=2,
        help_text="Margem externa em mm (0-10mm)"
    )
    qr_size = serializers.IntegerField(
        min_value=10,
        max_value=30,
        default=20,
        help_text="Tamanho do QR Code em mm (10-30mm)"
    )
    barcode_height = serializers.IntegerField(
        min_value=5,
        max_value=15,
        default=8,
        help_text="Altura do código de barras em mm (5-15mm)"
    )
    logo_max_height = serializers.IntegerField(
        min_value=8,
        max_value=20,
        default=12,
        help_text="Altura máxima do logo em mm (8-20mm)"
    )
    element_spacing = serializers.IntegerField(
        min_value=1,
        max_value=8,
        default=2,
        help_text="Espaçamento entre elementos em mm (1-8mm)"
    )


class LabelTemplateSerializer(serializers.Serializer):
    """Serializer para templates de etiquetas"""
    
    id = serializers.CharField(
        max_length=50,
        help_text="ID único do template"
    )
    name = serializers.CharField(
        max_length=100,
        help_text="Nome amigável do template"
    )
    description = serializers.CharField(
        max_length=255,
        required=False,
        allow_blank=True,
        help_text="Descrição do template"
    )
    
    # Dimensões
    size = serializers.ChoiceField(
        choices=[size.value for size in LabelSize],
        default=LabelSize.MEDIUM.value,
        help_text="Tamanho padrão da etiqueta"
    )
    orientation = serializers.ChoiceField(
        choices=[orient.value for orient in LabelOrientation],
        default=LabelOrientation.LANDSCAPE.value,
        help_text="Orientação da etiqueta"
    )
    custom_width = serializers.IntegerField(
        min_value=30,
        max_value=200,
        required=False,
        allow_null=True,
        help_text="Largura customizada em mm (apenas para size=custom)"
    )
    custom_height = serializers.IntegerField(
        min_value=15,
        max_value=150,
        required=False,
        allow_null=True,
        help_text="Altura customizada em mm (apenas para size=custom)"
    )
    
    # Configurações visuais
    colors = ColorSchemeSerializer(required=False)
    fonts = FontConfigSerializer(required=False)
    layout = LayoutConfigSerializer(required=False)
    
    # Elementos visíveis
    show_logo = serializers.BooleanField(default=True)
    show_qr_code = serializers.BooleanField(default=True)
    show_barcode = serializers.BooleanField(default=True)
    show_color_preview = serializers.BooleanField(default=True)
    show_formula_details = serializers.BooleanField(default=True)
    show_pigment_list = serializers.BooleanField(default=True)
    show_technical_info = serializers.BooleanField(default=True)
    show_client_info = serializers.BooleanField(default=True)
    
    # Textos customizáveis
    header_text = serializers.CharField(
        max_length=100,
        default="SISTEMA DE TINTAS",
        help_text="Texto do cabeçalho"
    )
    footer_text = serializers.CharField(
        max_length=100,
        default="Qualidade e Precisão",
        help_text="Texto do rodapé"
    )
    
    # Posicionamento
    logo_position = serializers.ChoiceField(
        choices=['top-left', 'top-right', 'center'],
        default='top-left',
        help_text="Posição do logo"
    )
    qr_position = serializers.ChoiceField(
        choices=['bottom-left', 'bottom-right', 'top-right'],
        default='bottom-right',
        help_text="Posição do QR Code"
    )
    
    # Template HTML opcional
    template_path = serializers.CharField(
        max_length=255,
        required=False,
        allow_null=True,
        help_text="Caminho para template HTML customizado"
    )
    
    def validate(self, attrs):
        """Validações customizadas"""
        # Validar dimensões customizadas
        if attrs.get('size') == LabelSize.CUSTOM.value:
            if not attrs.get('custom_width') or not attrs.get('custom_height'):
                raise serializers.ValidationError(
                    "custom_width e custom_height são obrigatórios quando size='custom'"
                )
        
        # Validar se pelo menos um elemento está visível
        element_fields = [
            'show_logo', 'show_qr_code', 'show_barcode', 'show_color_preview',
            'show_formula_details', 'show_pigment_list', 'show_technical_info', 'show_client_info'
        ]
        
        if not any(attrs.get(field, True) for field in element_fields):
            raise serializers.ValidationError(
                "Pelo menos um elemento deve estar visível na etiqueta"
            )
        
        return attrs
    
    def to_internal_value(self, data):
        """Converte dados para objetos internos"""
        validated_data = super().to_internal_value(data)
        
        # Criar objeto EtiquetaTemplate
        return EtiquetaTemplate(
            id=validated_data['id'],
            name=validated_data['name'],
            description=validated_data.get('description', ''),
            size=LabelSize(validated_data['size']),
            orientation=LabelOrientation(validated_data['orientation']),
            custom_width=validated_data.get('custom_width'),
            custom_height=validated_data.get('custom_height'),
            colors=ColorScheme(**validated_data.get('colors', {})),
            fonts=FontConfig(**validated_data.get('fonts', {})),
            layout=LayoutConfig(**validated_data.get('layout', {})),
            show_logo=validated_data.get('show_logo', True),
            show_qr_code=validated_data.get('show_qr_code', True),
            show_barcode=validated_data.get('show_barcode', True),
            show_color_preview=validated_data.get('show_color_preview', True),
            show_formula_details=validated_data.get('show_formula_details', True),
            show_pigment_list=validated_data.get('show_pigment_list', True),
            show_technical_info=validated_data.get('show_technical_info', True),
            show_client_info=validated_data.get('show_client_info', True),
            header_text=validated_data.get('header_text', 'SISTEMA DE TINTAS'),
            footer_text=validated_data.get('footer_text', 'Qualidade e Precisão'),
            logo_position=validated_data.get('logo_position', 'top-left'),
            qr_position=validated_data.get('qr_position', 'bottom-right'),
            template_path=validated_data.get('template_path')
        )


class LabelGenerationRequestSerializer(serializers.Serializer):
    """Serializer para requisição de geração de etiqueta"""
    
    mistura_id = serializers.UUIDField(
        help_text="ID da mistura para gerar etiqueta"
    )
    template_id = serializers.CharField(
        max_length=50,
        default="default",
        help_text="ID do template a usar (default, compact, premium, eco)"
    )
    custom_template = LabelTemplateSerializer(
        required=False,
        help_text="Template customizado (opcional)"
    )
    output_format = serializers.ChoiceField(
        choices=['pdf', 'preview_html', 'data_only'],
        default='pdf',
        help_text="Formato de saída"
    )
    dpi = serializers.IntegerField(
        min_value=150,
        max_value=600,
        default=300,
        help_text="DPI para geração PDF (150-600)"
    )
    auto_print = serializers.BooleanField(
        default=False,
        help_text="Enviar automaticamente para impressão"
    )
    printer_name = serializers.CharField(
        max_length=100,
        required=False,
        allow_blank=True,
        help_text="Nome da impressora (se auto_print=True)"
    )
    
    def validate_mistura_id(self, value):
        """Valida se a mistura existe e está em situação apropriada"""
        try:
            mistura = MisturaTinta.objects.get(id=value)
            
            # Verificar se mistura está em situação adequada para etiqueta
            situacoes_validas = ['CONFIRMADA', 'PRODUZIDA', 'ENTREGUE']
            if mistura.situacao not in situacoes_validas:
                raise serializers.ValidationError(
                    f"Mistura deve estar em uma das situações: {', '.join(situacoes_validas)}"
                )
            
            return value
            
        except MisturaTinta.DoesNotExist:
            raise serializers.ValidationError("Mistura não encontrada")


class LabelResponseSerializer(serializers.Serializer):
    """Serializer para resposta de geração de etiqueta"""
    
    success = serializers.BooleanField(help_text="Sucesso da operação")
    mistura_id = serializers.UUIDField(help_text="ID da mistura")
    etiqueta_id = serializers.UUIDField(
        required=False,
        help_text="ID do registro da etiqueta criado"
    )
    template_used = serializers.CharField(
        max_length=50,
        help_text="Template utilizado"
    )
    generation_time = serializers.DateTimeField(
        help_text="Timestamp da geração"
    )
    
    # Dados da resposta baseados no formato solicitado
    pdf_base64 = serializers.CharField(
        required=False,
        help_text="PDF codificado em base64 (se output_format=pdf)"
    )
    preview_html = serializers.CharField(
        required=False,
        help_text="HTML do preview (se output_format=preview_html)"
    )
    label_data = serializers.DictField(
        required=False,
        help_text="Dados estruturados da etiqueta (se output_format=data_only)"
    )
    
    # Metadados
    file_size_bytes = serializers.IntegerField(
        required=False,
        help_text="Tamanho do PDF gerado em bytes"
    )
    qr_data_summary = serializers.CharField(
        required=False,
        help_text="Resumo dos dados no QR Code"
    )
    barcode = serializers.CharField(
        required=False,
        help_text="Código de barras gerado"
    )
    print_queue_id = serializers.IntegerField(
        required=False,
        help_text="ID na fila de impressão (se auto_print=True)"
    )
    
    # Informações de erro
    error = serializers.CharField(
        required=False,
        help_text="Mensagem de erro (se success=False)"
    )
    warnings = serializers.ListField(
        child=serializers.CharField(),
        required=False,
        help_text="Lista de avisos durante a geração"
    )


class EtiquetaMisturaSerializer(serializers.ModelSerializer):
    """Serializer para modelo EtiquetaMistura"""
    
    mistura_codigo = SerializerMethodField()
    mistura_cor = SerializerMethodField()
    qr_data_preview = SerializerMethodField()
    
    class Meta:
        model = EtiquetaMistura
        fields = [
            'id', 'mistura', 'mistura_codigo', 'mistura_cor',
            'codigo_rastreamento', 'template_usado', 'qr_data_preview',
            'data_geracao', 'data_impressao', 'contador_impressao',
            'status', 'observacoes', 'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'codigo_rastreamento', 'data_geracao', 
            'created_at', 'updated_at'
        ]
    
    def get_mistura_codigo(self, obj):
        """Código da mistura associada"""
        return obj.mistura.codigo_mistura
    
    def get_mistura_cor(self, obj):
        """Nome da cor da mistura"""
        return obj.mistura.formula.cor_definida.nome_cor
    
    def get_qr_data_preview(self, obj):
        """Preview dos dados do QR Code"""
        try:
            if obj.dados_qr_code:
                qr_data = json.loads(obj.dados_qr_code)
                return {
                    'mistura_id': qr_data.get('id'),
                    'cor_nome': qr_data.get('cor_nome'),
                    'volume_ml': qr_data.get('volume_ml'),
                    'data_criacao': qr_data.get('data_criacao')
                }
        except:
            pass
        return None


class LabelTemplateListSerializer(serializers.Serializer):
    """Serializer para listagem de templates"""
    
    id = serializers.CharField(help_text="ID do template")
    name = serializers.CharField(help_text="Nome do template")
    description = serializers.CharField(help_text="Descrição")
    size = serializers.CharField(help_text="Tamanho (small, medium, large, custom)")
    orientation = serializers.CharField(help_text="Orientação (portrait, landscape)")
    type = serializers.CharField(help_text="Tipo (default, custom)")
    preview_available = serializers.BooleanField(help_text="Preview disponível")
    created_by_loja = serializers.IntegerField(
        required=False,
        help_text="ID da loja que criou (para templates customizados)"
    )


class QRCodeValidationSerializer(serializers.Serializer):
    """Serializer para validação de QR Codes"""
    
    qr_content = serializers.CharField(
        help_text="Conteúdo do QR Code lido"
    )
    
    def validate_qr_content(self, value):
        """Valida formato do conteúdo do QR"""
        try:
            # Tentar fazer parse do JSON
            qr_data = json.loads(value)
            
            # Campos obrigatórios
            required_fields = ['id', 'codigo', 'timestamp', 'version']
            missing_fields = [field for field in required_fields if field not in qr_data]
            
            if missing_fields:
                raise serializers.ValidationError(
                    f"Campos obrigatórios ausentes no QR: {', '.join(missing_fields)}"
                )
            
            return value
            
        except json.JSONDecodeError:
            raise serializers.ValidationError("QR Code não contém JSON válido")


class QRCodeValidationResponseSerializer(serializers.Serializer):
    """Serializer para resposta de validação de QR Code"""
    
    valid = serializers.BooleanField(help_text="QR Code é válido")
    mistura_found = serializers.BooleanField(help_text="Mistura encontrada no sistema")
    qr_data = serializers.DictField(
        required=False,
        help_text="Dados decodificados do QR"
    )
    mistura_data = serializers.DictField(
        required=False,
        help_text="Dados atuais da mistura no sistema"
    )
    age_days = serializers.IntegerField(
        required=False,
        help_text="Idade do QR em dias"
    )
    warnings = serializers.ListField(
        child=serializers.CharField(),
        required=False,
        help_text="Avisos sobre o QR Code"
    )
    error = serializers.CharField(
        required=False,
        help_text="Erro na validação"
    )
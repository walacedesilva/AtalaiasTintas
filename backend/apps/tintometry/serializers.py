"""
Tintometry API Serializers

Handles serialization/deserialization for tintometric REST API:
- Data validation and transformation
- Complex nested relationships
- Custom business logic validation
- Scientific precision handling
"""

from rest_framework import serializers
from decimal import Decimal, InvalidOperation
from django.core.exceptions import ValidationError
from django.utils import timezone

from .models import (
    Pigmento,
    LequeCorDefinida,
    FormulaTintometrica,
    ItemFormula,
    MisturaTinta,
    ItemMistura,
    EstoquePigmento,
    EtiquetaMistura,
    ProducaoTinta,
    CorPersonalizada
)
from apps.companies.models import Loja
from apps.core.models import User


class PigmentoSerializer(serializers.ModelSerializer):
    """Serializer para pigmentos tintométricos"""
    
    cor_hex = serializers.ReadOnlyField()
    
    class Meta:
        model = Pigmento
        fields = [
            'id', 'codigo', 'nome', 'cor_base', 'densidade', 'poder_tintorial',
            'fornecedor', 'codigo_fornecedor', 'concentracao_maxima',
            'r', 'g', 'b', 'cor_hex', 'ativo', 'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at', 'cor_hex']
    
    def validate_densidade(self, value):
        """Valida densidade do pigmento"""
        if value <= 0 or value > 10:
            raise serializers.ValidationError("Densidade deve estar entre 0.01 e 10.0 g/ml")
        return value
    
    def validate_poder_tintorial(self, value):
        """Valida poder tintorial"""
        if value <= 0 or value > 100:
            raise serializers.ValidationError("Poder tintorial deve estar entre 0.01 e 100%")
        return value


class LequeCorDefinidaSerializer(serializers.ModelSerializer):
    """Serializer para cores do leque"""
    
    cor_hex = serializers.ReadOnlyField()
    
    class Meta:
        model = LequeCorDefinida
        fields = [
            'id', 'codigo_cor', 'nome_cor', 'descricao', 'familia_cor', 'linha_produto',
            'l_value', 'a_value', 'b_value', 'r', 'g', 'b', 'cor_hex',
            'amostra_cor', 'ativo', 'data_criacao'
        ]
        read_only_fields = ['data_criacao', 'cor_hex']
    
    def validate(self, data):
        """Validação cruzada dos valores Lab e RGB"""
        # Validar valores Lab
        l_value = data.get('l_value')
        if l_value is not None and (l_value < 0 or l_value > 100):
            raise serializers.ValidationError("L value deve estar entre 0 e 100")
        
        a_value = data.get('a_value')
        if a_value is not None and (a_value < -128 or a_value > 127):
            raise serializers.ValidationError("a value deve estar entre -128 e 127")
        
        b_value = data.get('b_value')
        if b_value is not None and (b_value < -128 or b_value > 127):
            raise serializers.ValidationError("b value deve estar entre -128 e 127")
        
        return data


class ItemFormulaSerializer(serializers.ModelSerializer):
    """Serializer para itens de fórmula"""
    
    pigmento_details = PigmentoSerializer(source='pigmento', read_only=True)
    
    class Meta:
        model = ItemFormula
        fields = [
            'id', 'pigmento', 'pigmento_details', 'quantidade', 'sequencia', 'observacoes'
        ]
    
    def validate_quantidade(self, value):
        """Valida quantidade do pigmento na fórmula"""
        if value <= 0:
            raise serializers.ValidationError("Quantidade deve ser positiva")
        if value > 1000:  # 1L = 1000ml
            raise serializers.ValidationError("Quantidade muito alta (máximo 1000ml)")
        return value


class FormulaTintometricaSerializer(serializers.ModelSerializer):
    """Serializer para fórmulas tintométricas"""
    
    itens = ItemFormulaSerializer(many=True, read_only=True)
    cor_definida_details = LequeCorDefinidaSerializer(source='cor_definida', read_only=True)
    total_pigmentos = serializers.SerializerMethodField()
    quantidade_total_pigmentos = serializers.SerializerMethodField()
    
    class Meta:
        model = FormulaTintometrica
        fields = [
            'id', 'cor_definida', 'cor_definida_details', 'base_produto',
            'codigo_formula', 'nome_formula', 'versao', 'volume_base',
            'instrucoes', 'tempo_mistura_minutos', 'aprovada', 'testada',
            'data_aprovacao', 'usuario_aprovacao', 'ativa',
            'itens', 'total_pigmentos', 'quantidade_total_pigmentos',
            'created_at', 'updated_at'
        ]
        read_only_fields = [
            'created_at', 'updated_at', 'total_pigmentos', 
            'quantidade_total_pigmentos', 'data_aprovacao'
        ]
    
    def get_total_pigmentos(self, obj):
        """Retorna número total de pigmentos na fórmula"""
        return obj.itens.count()
    
    def get_quantidade_total_pigmentos(self, obj):
        """Retorna soma total das quantidades de pigmentos"""
        total = sum(item.quantidade for item in obj.itens.all())
        return float(total)


class EstoquePigmentoSerializer(serializers.ModelSerializer):
    """Serializer para estoque de pigmentos"""
    
    pigmento_details = PigmentoSerializer(source='pigmento', read_only=True)
    percentual_estoque = serializers.ReadOnlyField()
    estoque_critico = serializers.ReadOnlyField()
    valor_total_estoque = serializers.ReadOnlyField()
    dias_para_vencer = serializers.SerializerMethodField()
    
    class Meta:
        model = EstoquePigmento
        fields = [
            'id', 'pigmento', 'pigmento_details', 'loja', 'saldo_ml', 
            'saldo_minimo', 'saldo_maximo', 'custo_ml', 'data_ultimo_custo',
            'lote_atual', 'validade_lote', 'alerta_ativo', 'data_ultimo_alerta',
            'reposicao_solicitada', 'data_solicitacao_reposicao', 'quantidade_solicitada',
            'ativo', 'percentual_estoque', 'estoque_critico', 'valor_total_estoque',
            'dias_para_vencer', 'created_at', 'updated_at'
        ]
        read_only_fields = [
            'created_at', 'updated_at', 'percentual_estoque', 'estoque_critico',
            'valor_total_estoque', 'dias_para_vencer', 'data_ultimo_custo',
            'data_ultimo_alerta'
        ]
    
    def get_dias_para_vencer(self, obj):
        """Calcula dias restantes para vencimento"""
        if not obj.validade_lote:
            return None
        
        hoje = timezone.now().date()
        dias_restantes = (obj.validade_lote - hoje).days
        return dias_restantes if dias_restantes >= 0 else 0
    
    def validate_saldo_ml(self, value):
        """Valida saldo de estoque"""
        if value < 0:
            raise serializers.ValidationError("Saldo não pode ser negativo")
        return value
    
    def validate_custo_ml(self, value):
        """Valida custo por ml"""
        if value < 0:
            raise serializers.ValidationError("Custo não pode ser negativo")
        return value


class ItemMisturaSerializer(serializers.ModelSerializer):
    """Serializer para itens de mistura"""
    
    pigmento_details = PigmentoSerializer(source='pigmento', read_only=True)
    variacao_percentual = serializers.ReadOnlyField()
    quantidade_final = serializers.ReadOnlyField()
    
    class Meta:
        model = ItemMistura
        fields = [
            'id', 'pigmento', 'pigmento_details', 'quantidade_calculada',
            'quantidade_executada', 'custo_unitario', 'custo_total',
            'lote_utilizado', 'estoque_antes', 'estoque_depois', 'sequencia',
            'variacao_percentual', 'quantidade_final'
        ]


class EtiquetaMisturaSerializer(serializers.ModelSerializer):
    """Serializer para etiquetas de mistura"""
    
    dados_qr_formatados = serializers.ReadOnlyField()
    
    class Meta:
        model = EtiquetaMistura
        fields = [
            'id', 'codigo_etiqueta', 'qr_code_data', 'codigo_barras',
            'impressa', 'data_impressao', 'usuario_impressao', 'reimpressoes',
            'historico_reimpressoes', 'titulo_personalizado', 'observacoes_etiqueta',
            'dados_qr_formatados', 'created_at'
        ]
        read_only_fields = [
            'created_at', 'codigo_etiqueta', 'qr_code_data', 'dados_qr_formatados',
            'data_impressao', 'reimpressoes', 'historico_reimpressoes'
        ]


class MisturaTintaSerializer(serializers.ModelSerializer):
    """Serializer para misturas de tinta"""
    
    itens = ItemMisturaSerializer(many=True, read_only=True)
    formula_details = FormulaTintometricaSerializer(source='formula', read_only=True)
    etiqueta = EtiquetaMisturaSerializer(read_only=True)
    fator_proporcao = serializers.ReadOnlyField()
    economia = serializers.ReadOnlyField()
    
    class Meta:
        model = MisturaTinta
        fields = [
            'id', 'codigo_mistura', 'formula', 'formula_details', 'loja',
            'usuario_operacao', 'cliente_nome', 'cliente_documento', 
            'cliente_telefone', 'cliente_email', 'volume_solicitado', 
            'volume_produzido', 'custo_total', 'custo_base', 'custo_pigmentos',
            'situacao', 'data_confirmacao', 'data_producao', 'data_entrega',
            'data_cancelamento', 'motivo_cancelamento', 'observacoes_cliente',
            'observacoes_internas', 'cor_aprovada_cliente', 'data_aprovacao_cor',
            'pedido_venda_id', 'itens', 'etiqueta', 'fator_proporcao', 'economia',
            'created_at', 'updated_at'
        ]
        read_only_fields = [
            'created_at', 'updated_at', 'codigo_mistura', 'fator_proporcao',
            'economia', 'data_confirmacao', 'data_producao', 'data_entrega'
        ]
    
    def validate_volume_solicitado(self, value):
        """Valida volume solicitado"""
        if value <= 0:
            raise serializers.ValidationError("Volume deve ser positivo")
        if value > 1000:  # 1000 litros
            raise serializers.ValidationError("Volume muito alto (máximo 1000L)")
        return value
    
    def validate_cliente_nome(self, value):
        """Valida nome do cliente"""
        if len(value.strip()) < 2:
            raise serializers.ValidationError("Nome do cliente deve ter pelo menos 2 caracteres")
        return value.strip()


class MisturaCalculationRequestSerializer(serializers.Serializer):
    """Serializer para requisição de cálculo de mistura"""
    
    formula_id = serializers.UUIDField()
    volume_requested = serializers.DecimalField(max_digits=8, decimal_places=2)
    loja_id = serializers.IntegerField()
    customer_data = serializers.DictField()
    observations = serializers.CharField(required=False, allow_blank=True)
    validate_stock = serializers.BooleanField(default=True)
    
    def validate_volume_requested(self, value):
        """Valida volume solicitado"""
        if value <= 0:
            raise serializers.ValidationError("Volume deve ser positivo")
        if value > 1000:
            raise serializers.ValidationError("Volume muito alto (máximo 1000L)")
        return value
    
    def validate_customer_data(self, value):
        """Valida dados do cliente"""
        required_fields = ['nome']
        for field in required_fields:
            if field not in value or not value[field]:
                raise serializers.ValidationError(f"Campo obrigatório: {field}")
        
        # Validar nome
        if len(value['nome'].strip()) < 2:
            raise serializers.ValidationError("Nome deve ter pelo menos 2 caracteres")
        
        return value


class MistureConfirmationSerializer(serializers.Serializer):
    """Serializer para confirmação de mistura"""
    
    reserve_stock = serializers.BooleanField(default=True)
    observations = serializers.CharField(required=False, allow_blank=True)


class MixtureExecutionSerializer(serializers.Serializer):
    """Serializer para execução de mistura"""
    
    actual_quantities = serializers.ListField(
        child=serializers.DictField(),
        required=False
    )
    actual_volume = serializers.DecimalField(
        max_digits=8, 
        decimal_places=2, 
        required=False
    )
    quality_approved = serializers.BooleanField(default=True)
    observations = serializers.CharField(required=False, allow_blank=True)
    
    def validate_actual_quantities(self, value):
        """Valida quantidades executadas"""
        if not value:
            return value
        
        for qty_data in value:
            if 'pigmento_id' not in qty_data or 'quantidade' not in qty_data:
                raise serializers.ValidationError(
                    "Cada quantidade deve ter 'pigmento_id' e 'quantidade'"
                )
            
            try:
                quantidade = Decimal(str(qty_data['quantidade']))
                if quantidade < 0:
                    raise serializers.ValidationError("Quantidade não pode ser negativa")
            except (ValueError, InvalidOperation):
                raise serializers.ValidationError("Quantidade inválida")
        
        return value


class StockMovementSerializer(serializers.Serializer):
    """Serializer para movimentação de estoque"""
    
    pigmento_id = serializers.IntegerField()
    quantidade = serializers.DecimalField(max_digits=10, decimal_places=4)
    custo_unitario = serializers.DecimalField(max_digits=8, decimal_places=4)
    lote = serializers.CharField(required=False, allow_blank=True)
    validade = serializers.DateField(required=False)
    observacoes = serializers.CharField(required=False, allow_blank=True)
    
    def validate_quantidade(self, value):
        """Valida quantidade de movimento"""
        if value <= 0:
            raise serializers.ValidationError("Quantidade deve ser positiva")
        return value
    
    def validate_custo_unitario(self, value):
        """Valida custo unitário"""
        if value < 0:
            raise serializers.ValidationError("Custo não pode ser negativo")
        return value


class ColorAnalysisSerializer(serializers.Serializer):
    """Serializer para análise de cores"""
    
    target_lab = serializers.ListField(
        child=serializers.DecimalField(max_digits=6, decimal_places=3),
        min_length=3,
        max_length=3
    )
    achieved_lab = serializers.ListField(
        child=serializers.DecimalField(max_digits=6, decimal_places=3),
        min_length=3,
        max_length=3
    )
    tolerance_level = serializers.ChoiceField(
        choices=['CRITICA', 'COMERCIAL', 'INDUSTRIAL', 'ACEITAVEL'],
        default='COMERCIAL'
    )
    
    def validate_target_lab(self, value):
        """Valida valores Lab da cor alvo"""
        L, a, b = value
        if L < 0 or L > 100:
            raise serializers.ValidationError("L deve estar entre 0 e 100")
        if a < -128 or a > 127:
            raise serializers.ValidationError("a deve estar entre -128 e 127")
        if b < -128 or b > 127:
            raise serializers.ValidationError("b deve estar entre -128 e 127")
        return value
    
    def validate_achieved_lab(self, value):
        """Valida valores Lab da cor alcançada"""
        return self.validate_target_lab(value)


class StockAlertSerializer(serializers.ModelSerializer):
    """Serializer para alertas de estoque"""
    
    pigmento_nome = serializers.CharField(source='pigmento.nome', read_only=True)
    loja_nome = serializers.CharField(source='loja.nome', read_only=True)
    dias_para_vencer = serializers.SerializerMethodField()
    quantidade_sugerida_reposicao = serializers.SerializerMethodField()
    
    class Meta:
        model = EstoquePigmento
        fields = [
            'id', 'pigmento_nome', 'loja_nome', 'saldo_ml', 'saldo_minimo',
            'estoque_critico', 'alerta_ativo', 'data_ultimo_alerta',
            'validade_lote', 'dias_para_vencer', 'quantidade_sugerida_reposicao'
        ]
    
    def get_dias_para_vencer(self, obj):
        """Calcula dias para vencimento"""
        if not obj.validade_lote:
            return None
        hoje = timezone.now().date()
        return (obj.validade_lote - hoje).days
    
    def get_quantidade_sugerida_reposicao(self, obj):
        """Calcula quantidade sugerida para reposição"""
        return float(obj.saldo_maximo - obj.saldo_ml)


class ColorMatchSerializer(serializers.Serializer):
    """Serializer para busca de cores similares"""
    
    target_rgb = serializers.ListField(
        child=serializers.IntegerField(min_value=0, max_value=255),
        min_length=3,
        max_length=3,
        required=False
    )
    target_lab = serializers.ListField(
        child=serializers.DecimalField(max_digits=6, decimal_places=3),
        min_length=3,
        max_length=3,
        required=False
    )
    max_results = serializers.IntegerField(default=5, min_value=1, max_value=20)
    tolerance_level = serializers.ChoiceField(
        choices=['CRITICA', 'COMERCIAL', 'INDUSTRIAL', 'ACEITAVEL'],
        default='COMERCIAL'
    )
    
    def validate(self, data):
        """Validação cruzada - deve ter RGB ou Lab"""
        if not data.get('target_rgb') and not data.get('target_lab'):
            raise serializers.ValidationError(
                "Deve fornecer target_rgb ou target_lab"
            )
        return data
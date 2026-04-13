"""
Django Admin configuration for Tintometry app
Comprehensive management interface for paint mixing system
"""

from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils import timezone
from django import forms
from django.db import transaction

from .models import (
    Pigmento, LequeCorDefinida, FormulaTintometrica, ItemFormula,
    MisturaTinta, ItemMistura, EstoquePigmento, EtiquetaMistura,
    ProducaoTinta, ConsumoProducao, CorPersonalizada
)


class ItemFormulaInline(admin.TabularInline):
    """Inline para itens da fórmula"""
    model = ItemFormula
    extra = 1
    fields = ['pigmento', 'quantidade', 'sequencia', 'observacoes']
    ordering = ['sequencia']


class ItemMisturaInline(admin.TabularInline):
    """Inline para itens utilizados na mistura"""
    model = ItemMistura
    extra = 0
    readonly_fields = ['custo_unitario', 'custo_total', 'estoque_antes', 'estoque_depois']
    fields = [
        'pigmento', 'quantidade_calculada', 'quantidade_executada', 
        'custo_unitario', 'custo_total', 'sequencia'
    ]
    ordering = ['sequencia']


@admin.register(Pigmento)
class PigmentoAdmin(admin.ModelAdmin):
    """Interface administrativa para pigmentos"""
    
    list_display = [
        'codigo', 'nome', 'cor_base', 'cor_display', 'densidade', 
        'poder_tintorial', 'concentracao_maxima', 'ativo'
    ]
    list_filter = ['ativo', 'cor_base', 'fornecedor']
    search_fields = ['codigo', 'nome', 'fornecedor']
    
    fieldsets = (
        ('Identificação', {
            'fields': ('codigo', 'nome', 'cor_base', 'ativo')
        }),
        ('Características Técnicas', {
            'fields': ('densidade', 'poder_tintorial', 'concentracao_maxima')
        }),
        ('Fornecedor', {
            'fields': ('fornecedor', 'codigo_fornecedor')
        }),
        ('Cor RGB', {
            'fields': ('r', 'g', 'b'),
            'classes': ['collapse']
        })
    )
    
    def cor_display(self, obj):
        """Mostra uma amostra da cor"""
        return format_html(
            '<div style="width: 30px; height: 20px; background-color: {}; border: 1px solid #ccc;"></div>',
            obj.cor_hex
        )
    cor_display.short_description = 'Cor'


@admin.register(LequeCorDefinida)
class LequeCorDefinidaAdmin(admin.ModelAdmin):
    """Interface administrativa para cores do leque"""
    
    list_display = [
        'codigo_cor', 'nome_cor', 'familia_cor', 'linha_produto',
        'cor_display', 'ativo'
    ]
    list_filter = ['ativo', 'familia_cor', 'linha_produto']
    search_fields = ['codigo_cor', 'nome_cor', 'descricao']
    
    fieldsets = (
        ('Identificação', {
            'fields': ('codigo_cor', 'nome_cor', 'descricao', 'ativo')
        }),
        ('Classificação', {
            'fields': ('familia_cor', 'linha_produto')
        }),
        ('Valores Colorimétricos Lab', {
            'fields': ('l_value', 'a_value', 'b_value')
        }),
        ('Valores RGB', {
            'fields': ('r', 'g', 'b')
        }),
        ('Imagem', {
            'fields': ('amostra_cor',)
        })
    )
    
    def cor_display(self, obj):
        return format_html(
            '<div style="width: 40px; height: 25px; background-color: {}; border: 1px solid #ccc; border-radius: 3px;"></div>',
            obj.cor_hex
        )
    cor_display.short_description = 'Amostra'


@admin.register(FormulaTintometrica)
class FormulaTintometricaAdmin(admin.ModelAdmin):
    """Interface administrativa para fórmulas"""
    
    list_display = [
        'codigo_formula', 'nome_formula', 'cor_definida', 'base_produto',
        'volume_base', 'aprovada', 'testada', 'ativa'
    ]
    list_filter = ['aprovada', 'testada', 'ativa', 'cor_definida__familia_cor']
    search_fields = ['codigo_formula', 'nome_formula', 'cor_definida__nome_cor']
    
    inlines = [ItemFormulaInline]
    
    fieldsets = (
        ('Identificação', {
            'fields': ('codigo_formula', 'nome_formula', 'versao')
        }),
        ('Produto e Cor', {
            'fields': ('cor_definida', 'base_produto', 'volume_base')
        }),
        ('Processo', {
            'fields': ('instrucoes', 'tempo_mistura_minutos')
        }),
        ('Controle de Qualidade', {
            'fields': ('aprovada', 'testada', 'data_aprovacao', 'usuario_aprovacao', 'ativa')
        })
    )
    
    readonly_fields = ['data_aprovacao']
    
    actions = ['aprovar_formulas', 'desativar_formulas']
    
    def aprovar_formulas(self, request, queryset):
        """Aprovar fórmulas selecionadas"""
        updated = queryset.update(
            aprovada=True,
            data_aprovacao=timezone.now(),
            usuario_aprovacao=request.user
        )
        self.message_user(request, f'{updated} fórmulas foram aprovadas.')
    aprovar_formulas.short_description = "Aprovar fórmulas selecionadas"


@admin.register(MisturaTinta)
class MisturaTintaAdmin(admin.ModelAdmin):
    """Interface administrativa para misturas de tinta"""
    
    list_display = [
        'codigo_mistura', 'cliente_nome', 'formula', 'volume_solicitado',
        'situacao_display', 'custo_total', 'data_confirmacao'
    ]
    list_filter = ['situacao', 'loja', 'created_at']
    search_fields = [
        'codigo_mistura', 'cliente_nome', 'cliente_telefone', 
        'formula__nome_formula', 'formula__cor_definida__nome_cor'
    ]
    
    inlines = [ItemMisturaInline]
    
    fieldsets = (
        ('Identificação', {
            'fields': ('codigo_mistura', 'situacao')
        }),
        ('Cliente', {
            'fields': ('cliente_nome', 'cliente_documento', 'cliente_telefone', 'cliente_email')
        }),
        ('Fórmula e Produto', {
            'fields': ('formula', 'loja', 'usuario_operacao')
        }),
        ('Volume e Custos', {
            'fields': (
                ('volume_solicitado', 'volume_produzido'),
                ('custo_total', 'custo_base', 'custo_pigmentos')
            )
        }),
        ('Controle de Datas', {
            'fields': (
                'data_confirmacao', 'data_producao', 'data_entrega',
                ('data_cancelamento', 'motivo_cancelamento')
            ),
            'classes': ['collapse']
        }),
        ('Observações', {
            'fields': ('observacoes_cliente', 'observacoes_internas'),
            'classes': ['collapse']
        }),
        ('Qualidade', {
            'fields': ('cor_aprovada_cliente', 'data_aprovacao_cor'),
            'classes': ['collapse']
        })
    )
    
    readonly_fields = ['codigo_mistura', 'custo_total', 'custo_base', 'custo_pigmentos']
    
    def situacao_display(self, obj):
        """Display colorido do status"""
        colors = {
            'CALCULADA': '#ffc107',    # Amarelo
            'CONFIRMADA': '#007bff',   # Azul  
            'PRODUZIDA': '#28a745',    # Verde
            'ENTREGUE': '#6c757d',     # Cinza
            'CANCELADA': '#dc3545'     # Vermelho
        }
        color = colors.get(obj.situacao, '#6c757d')
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color,
            obj.get_situacao_display()
        )
    situacao_display.short_description = 'Situação'
    
    actions = ['confirmar_misturas', 'cancelar_misturas']
    
    def confirmar_misturas(self, request, queryset):
        """Confirmar misturas selecionadas"""
        confirmadas = 0
        for mistura in queryset.filter(situacao='CALCULADA'):
            mistura.situacao = 'CONFIRMADA'
            mistura.data_confirmacao = timezone.now()
            mistura.save()
            confirmadas += 1
        
        self.message_user(request, f'{confirmadas} misturas foram confirmadas.')
    confirmar_misturas.short_description = "Confirmar misturas calculadas"


@admin.register(EstoquePigmento)
class EstoquePigmentoAdmin(admin.ModelAdmin):
    """Interface administrativa para estoque de pigmentos"""
    
    list_display = [
        'pigmento', 'loja', 'saldo_ml', 'saldo_minimo',
        'status_estoque', 'custo_ml', 'alerta_ativo', 'lote_atual'
    ]
    list_filter = ['alerta_ativo', 'loja', 'pigmento__cor_base']
    search_fields = ['pigmento__nome', 'pigmento__codigo', 'lote_atual']
    
    fieldsets = (
        ('Produto e Local', {
            'fields': ('pigmento', 'loja', 'ativo')
        }),
        ('Saldos', {
            'fields': ('saldo_ml', 'saldo_minimo', 'saldo_maximo')
        }),
        ('Custos', {
            'fields': ('custo_ml', 'data_ultimo_custo')
        }),
        ('Lote Atual', {
            'fields': ('lote_atual', 'validade_lote')
        }),
        ('Alertas e Reposição', {
            'fields': (
                'alerta_ativo', 'data_ultimo_alerta',
                'reposicao_solicitada', 'data_solicitacao_reposicao', 'quantidade_solicitada'
            ),
            'classes': ['collapse']
        })
    )
    
    readonly_fields = ['data_ultimo_custo', 'data_ultimo_alerta']
    
    def status_estoque(self, obj):
        """Indicador visual do status do estoque"""
        if obj.estoque_critico:
            return format_html(
                '<span style="color: red; font-weight: bold;">⚠️ CRÍTICO</span>'
            )
        elif obj.percentual_estoque < 50:
            return format_html(
                '<span style="color: orange; font-weight: bold;">⚡ BAIXO</span>'
            )
        else:
            return format_html(
                '<span style="color: green;">✓ OK</span>'
            )
    status_estoque.short_description = 'Situação do Estoque'
    
    actions = ['solicitar_reposicao', 'desativar_alertas']
    
    def solicitar_reposicao(self, request, queryset):
        """Solicitar reposição para itens selecionados"""
        for item in queryset:
            if item.estoque_critico and not item.reposicao_solicitada:
                item.reposicao_solicitada = True
                item.data_solicitacao_reposicao = timezone.now()
                item.quantidade_solicitada = item.saldo_maximo - item.saldo_ml
                item.save()
        
        self.message_user(request, "Reposições solicitadas para itens críticos.")
    solicitar_reposicao.short_description = "Solicitar reposição"


@admin.register(EtiquetaMistura)
class EtiquetaMisturaAdmin(admin.ModelAdmin):
    """Interface administrativa para etiquetas"""
    
    list_display = [
        'codigo_etiqueta', 'mistura', 'impressa', 'reimpressoes',
        'data_impressao', 'usuario_impressao'
    ]
    list_filter = ['impressa', 'data_impressao']
    search_fields = ['codigo_etiqueta', 'mistura__codigo_mistura', 'mistura__cliente_nome']
    
    fieldsets = (
        ('Identificação', {
            'fields': ('codigo_etiqueta', 'mistura')
        }),
        ('Dados da Etiqueta', {
            'fields': ('qr_code_data', 'codigo_barras', 'titulo_personalizado', 'observacoes_etiqueta')
        }),
        ('Controle de Impressão', {
            'fields': ('impressa', 'data_impressao', 'usuario_impressao', 'reimpressoes')
        })
    )
    
    readonly_fields = ['codigo_etiqueta', 'qr_code_data', 'data_impressao', 'reimpressoes']
    
    actions = ['marcar_impressas']
    
    def marcar_impressas(self, request, queryset):
        """Marcar etiquetas como impressas"""
        for etiqueta in queryset.filter(impressa=False):
            etiqueta.marcar_impressa(request.user)
        
        self.message_user(request, "Etiquetas marcadas como impressas.")
    marcar_impressas.short_description = "Marcar como impressas"


@admin.register(CorPersonalizada)
class CorPersonalizadaAdmin(admin.ModelAdmin):
    """Interface administrativa para cores personalizadas"""
    
    list_display = [
        'codigo_cor_personalizada', 'nome_cor', 'cliente_nome',
        'cor_display', 'total_producoes', 'data_ultima_producao'
    ]
    search_fields = [
        'codigo_cor_personalizada', 'nome_cor', 'cliente_nome', 
        'cliente_documento', 'telefone_cliente'
    ]
    
    fieldsets = (
        ('Identificação', {
            'fields': ('codigo_cor_personalizada', 'nome_cor', 'descricao')
        }),
        ('Cliente', {
            'fields': ('cliente_nome', 'cliente_documento', 'telefone_cliente')
        }),
        ('Valores Colorimétricos', {
            'fields': ('l_value', 'a_value', 'b_value')
        }),
        ('Valores RGB', {
            'fields': ('r', 'g', 'b')
        }),
        ('Fórmula e Histórico', {
            'fields': (
                'formula_desenvolvida', 'total_producoes',
                'data_primeira_producao', 'data_ultima_producao'
            )
        })
    )
    
    readonly_fields = ['total_producoes', 'data_primeira_producao', 'data_ultima_producao']
    
    def cor_display(self, obj):
        return format_html(
            '<div style="width: 40px; height: 25px; background-color: {}; border: 1px solid #ccc; border-radius: 3px;"></div>',
            obj.cor_hex
        )
    cor_display.short_description = 'Amostra'


@admin.register(ProducaoTinta)
class ProducaoTintaAdmin(admin.ModelAdmin):
    """Interface administrativa para produções de tinta"""
    
    list_display = [
        'numero_producao', 'formula', 'volume_solicitado', 'situacao',
        'operador', 'cor_aprovada', 'data_fim_producao'
    ]
    list_filter = ['situacao', 'cor_aprovada', 'loja']
    search_fields = [
        'numero_producao', 'formula__nome_formula', 'cliente_nome', 'operador__username'
    ]


# Customização do site admin para tintometria
admin.site.site_header = "Sistema de Tintas - Tintometria"

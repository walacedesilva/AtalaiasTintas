from django.contrib import admin
from django.utils.html import format_html
from django.utils import timezone
from .models import (
    Categoria,
    Marca,
    ProdutoBase,
    ProdutoUnidade,
    ProdutoVariacao,
    UnidadeMedida,
    EstoqueLoja,
    EstoqueReserva,
    MovimentacaoEstoque,
    LoteProduto,
    EntradaMercadoria,
    EntradaMercadoriaItem,
)


@admin.register(Categoria)
class CategoriaAdmin(admin.ModelAdmin):
    list_display = ['codigo', 'nome', 'nivel', 'parent', 'permite_tintometria', 'exige_formula', 'ativa']
    list_filter = ['nivel', 'ativa', 'permite_tintometria', 'exige_formula']
    search_fields = ['codigo', 'nome']
    list_select_related = ['parent']
    ordering = ['nivel', 'ordem', 'nome']
    list_per_page = 25


@admin.register(Marca)
class MarcaAdmin(admin.ModelAdmin):
    list_display = ['codigo', 'nome', 'fornecedor_principal', 'ativa']
    list_filter = ['ativa']
    search_fields = ['codigo', 'nome', 'fornecedor_principal']
    list_per_page = 25


@admin.register(ProdutoBase)
class ProdutoBaseAdmin(admin.ModelAdmin):
    list_display = ['codigo', 'nome', 'categoria', 'marca', 'tipo_produto', 'ativo']
    list_filter = ['tipo_produto', 'ativo', 'categoria', 'marca']
    search_fields = ['codigo', 'nome']
    list_select_related = ['categoria', 'marca']
    list_per_page = 25

    fieldsets = (
        ('Identificação', {
            'fields': ('codigo', 'nome', 'descricao'),
        }),
        ('Classificação', {
            'fields': ('categoria', 'marca', 'tipo_produto'),
        }),
        ('Status', {
            'fields': ('ativo',),
        }),
    )


@admin.register(UnidadeMedida)
class UnidadeMedidaAdmin(admin.ModelAdmin):
    list_display = ['codigo', 'nome', 'sigla', 'tipo']
    list_filter = ['tipo']
    search_fields = ['codigo', 'nome', 'sigla']


# ---------------------------------------------------------------------------
# ProdutoUnidade — T022: unit conversion admin interface
# ---------------------------------------------------------------------------

class ProdutoUnidadeInline(admin.TabularInline):
    model = ProdutoUnidade
    extra = 0
    fields = ['unidade', 'unidade_base', 'fator_conversao', 'preco_diferenciado', 'ativa']


@admin.register(ProdutoVariacao)
class ProdutoVariacaoAdmin(admin.ModelAdmin):
    list_display = ['codigo_variacao', 'nome_variacao', 'produto_base', 'unidade_venda', 'preco_venda', 'estoque_minimo', 'ativo']
    list_filter = ['ativo', 'produto_base__categoria', 'produto_base__marca']
    search_fields = ['codigo_variacao', 'nome_variacao', 'produto_base__nome']
    list_select_related = ['produto_base', 'unidade_venda']
    inlines = [ProdutoUnidadeInline]
    list_per_page = 30


@admin.register(ProdutoUnidade)
class ProdutoUnidadeAdmin(admin.ModelAdmin):
    list_display = ['produto', 'unidade', 'unidade_base', 'fator_conversao', 'preco_diferenciado', 'ativa']
    list_filter = ['unidade_base', 'ativa', 'unidade__tipo']
    search_fields = ['produto__codigo_variacao', 'produto__nome_variacao']
    list_select_related = ['produto', 'unidade']
    list_per_page = 30


# ---------------------------------------------------------------------------
# EstoqueLoja
# ---------------------------------------------------------------------------

@admin.register(EstoqueLoja)
class EstoqueLojaAdmin(admin.ModelAdmin):
    list_display = ['loja', 'produto_variacao', 'quantidade_atual', 'quantidade_reservada', 'quantidade_disponivel_display', 'bloqueado_venda']
    list_filter = ['loja', 'bloqueado_venda']
    search_fields = ['produto_variacao__codigo_variacao', 'produto_variacao__nome_variacao']
    list_select_related = ['loja', 'produto_variacao']
    readonly_fields = ['data_ultima_movimentacao']
    list_per_page = 50

    def quantidade_disponivel_display(self, obj):
        qtd = obj.quantidade_disponivel
        color = 'green' if qtd > 0 else 'red'
        return format_html('<span style="color: {};">{}</span>', color, qtd)
    quantidade_disponivel_display.short_description = 'Disponível'


# ---------------------------------------------------------------------------
# MovimentacaoEstoque — T033
# ---------------------------------------------------------------------------

@admin.register(MovimentacaoEstoque)
class MovimentacaoEstoqueAdmin(admin.ModelAdmin):
    list_display = ['created_at', 'produto', 'tipo_movimentacao', 'quantidade_original',
                    'unidade_original', 'quantidade_base', 'estoque_antes', 'estoque_depois', 'usuario']
    list_filter = ['tipo_movimentacao', 'created_at']
    search_fields = ['produto__codigo_variacao', 'produto__nome_variacao', 'documento_referencia']
    list_select_related = ['produto', 'unidade_original', 'usuario']
    readonly_fields = ['id', 'created_at', 'updated_at']
    date_hierarchy = 'created_at'
    list_per_page = 50

    def has_add_permission(self, request):
        return False  # Movements only created via service layer

    def has_change_permission(self, request, obj=None):
        return False  # Audit trail — read only


# ---------------------------------------------------------------------------
# EstoqueReserva
# ---------------------------------------------------------------------------

@admin.register(EstoqueReserva)
class EstoqueReservaAdmin(admin.ModelAdmin):
    list_display = ['produto', 'quantidade_reservada', 'unidade', 'sessao_checkout', 'expira_em', 'status_display', 'usuario']
    list_filter = ['status', 'created_at']
    search_fields = ['produto__codigo_variacao', 'sessao_checkout']
    list_select_related = ['produto', 'unidade', 'usuario']
    readonly_fields = ['id', 'created_at']
    list_per_page = 50

    def status_display(self, obj):
        colors = {'ATIVA': 'green', 'CONFIRMADA': 'blue', 'EXPIRADA': 'gray', 'CANCELADA': 'red'}
        color = colors.get(obj.status, 'black')
        return format_html('<span style="color: {};">{}</span>', color, obj.status)
    status_display.short_description = 'Status'


# ---------------------------------------------------------------------------
# LoteProduto — new: batch / expiry admin
# ---------------------------------------------------------------------------

@admin.register(LoteProduto)
class LoteProdutoAdmin(admin.ModelAdmin):
    list_display = ['numero_lote', 'produto', 'loja', 'data_validade', 'quantidade_atual',
                    'unidade', 'status_validade_display', 'status', 'dias_para_vencer']
    list_filter = ['status', 'loja', 'data_validade']
    search_fields = ['numero_lote', 'produto__codigo_variacao', 'produto__nome_variacao', 'documento_entrada']
    list_select_related = ['produto__produto_base', 'loja', 'unidade']
    readonly_fields = ['id', 'esta_vencido', 'dias_para_vencer', 'created_at', 'updated_at']
    date_hierarchy = 'data_validade'
    list_per_page = 40

    fieldsets = (
        ('Identificação', {'fields': ('id', 'produto', 'loja', 'numero_lote', 'codigo_barras_lote')}),
        ('Datas', {'fields': ('data_fabricacao', 'data_validade', 'data_entrada', 'esta_vencido', 'dias_para_vencer')}),
        ('Quantidades', {'fields': ('quantidade_inicial', 'quantidade_atual', 'unidade', 'custo_unitario')}),
        ('Status', {'fields': ('status', 'motivo_bloqueio', 'documento_entrada', 'observacoes')}),
    )

    def status_validade_display(self, obj):
        if obj.esta_vencido:
            return format_html('<span style="color: red; font-weight: bold;">VENCIDO</span>')
        dias = obj.dias_para_vencer
        if dias is not None and dias <= 30:
            return format_html('<span style="color: orange;">Vence em {} dias</span>', dias)
        return format_html('<span style="color: green;">OK</span>')
    status_validade_display.short_description = 'Validade'


# ---------------------------------------------------------------------------
# EntradaMercadoria — T034: goods receipt + XML import
# ---------------------------------------------------------------------------

class EntradaMercadoriaItemInline(admin.TabularInline):
    model = EntradaMercadoriaItem
    extra = 0
    fields = ['descricao_nfe', 'codigo_nfe', 'quantidade', 'unidade_nfe', 'valor_unitario',
              'valor_total', 'produto', 'unidade', 'status']
    readonly_fields = ['descricao_nfe', 'codigo_nfe', 'quantidade', 'unidade_nfe', 'valor_unitario', 'valor_total']


@admin.register(EntradaMercadoria)
class EntradaMercadoriaAdmin(admin.ModelAdmin):
    list_display = ['data_entrada', 'fornecedor_nome', 'fornecedor_cnpj', 'numero_nfe',
                    'valor_total_nfe', 'status', 'loja', 'usuario']
    list_filter = ['status', 'tipo_entrada', 'loja', 'data_entrada']
    search_fields = ['fornecedor_nome', 'fornecedor_cnpj', 'chave_acesso_nfe', 'numero_nfe']
    list_select_related = ['loja', 'usuario']
    readonly_fields = ['id', 'chave_acesso_nfe', 'xml_nfe', 'data_conferencia', 'created_at', 'updated_at']
    date_hierarchy = 'data_entrada'
    inlines = [EntradaMercadoriaItemInline]
    list_per_page = 25

    fieldsets = (
        ('Dados da Entrada', {'fields': ('id', 'loja', 'tipo_entrada', 'usuario', 'data_entrada', 'status', 'observacoes')}),
        ('Fornecedor', {'fields': ('fornecedor_nome', 'fornecedor_cnpj', 'fornecedor_uf')}),
        ('NF-e do Fornecedor', {'fields': ('chave_acesso_nfe', 'numero_nfe', 'serie_nfe', 'data_emissao_nfe')}),
        ('Valores', {'fields': ('valor_total_nfe', 'valor_total_entrada', 'data_conferencia')}),
        ('XML', {'fields': ('xml_nfe',), 'classes': ('collapse',)}),
    )


from django.contrib import admin
from django.utils.html import format_html
from .models import Cliente, PedidoVenda, Venda, PagamentoVenda, Recebivel, DescontoAuditLog


@admin.register(Cliente)
class ClienteAdmin(admin.ModelAdmin):
    list_display = ['codigo_cliente', 'nome', 'tipo_cliente', 'cpf_cnpj', 'telefone_principal', 'cidade_uf', 'ativo']
    list_filter = ['tipo_cliente', 'ativo', 'bloqueado_credito', 'uf']
    search_fields = ['codigo_cliente', 'nome', 'cpf', 'cnpj', 'email']
    list_select_related = ['vendedor_responsavel']
    list_per_page = 25

    fieldsets = (
        ('Identificação', {
            'fields': ('codigo_cliente', 'tipo_cliente', 'nome', 'cpf', 'rg', 'data_nascimento',
                       'razao_social', 'nome_fantasia', 'cnpj', 'inscricao_estadual'),
        }),
        ('Contato', {
            'fields': ('telefone_principal', 'telefone_secundario', 'email'),
        }),
        ('Endereço', {
            'fields': ('cep', 'endereco', 'numero', 'complemento', 'bairro', 'cidade', 'uf'),
            'classes': ('collapse',),
        }),
        ('Comercial', {
            'fields': ('limite_credito', 'bloqueado_credito', 'motivo_bloqueio',
                       'categoria_cliente', 'vendedor_responsavel'),
        }),
        ('Status', {
            'fields': ('ativo',),
        }),
    )

    @admin.display(description='CPF/CNPJ')
    def cpf_cnpj(self, obj):
        return obj.cpf or obj.cnpj or '—'

    @admin.display(description='Cidade/UF')
    def cidade_uf(self, obj):
        if obj.cidade and obj.uf:
            return f'{obj.cidade}/{obj.uf}'
        return '—'


@admin.register(PedidoVenda)
class PedidoVendaAdmin(admin.ModelAdmin):
    list_display = ['numero_pedido', 'cliente', 'loja', 'situacao_badge', 'valor_total', 'forma_pagamento', 'data_pedido']
    list_filter = ['situacao', 'forma_pagamento', 'tipo_entrega', 'loja']
    search_fields = ['numero_pedido', 'cliente__nome', 'cliente__cpf', 'cliente__cnpj']
    list_select_related = ['cliente', 'loja', 'vendedor']
    date_hierarchy = 'data_pedido'
    readonly_fields = ['data_pedido', 'numero_pedido']
    list_per_page = 25

    fieldsets = (
        ('Pedido', {
            'fields': ('numero_pedido', 'loja', 'cliente', 'vendedor', 'situacao'),
        }),
        ('Valores', {
            'fields': ('valor_subtotal', 'valor_desconto', 'percentual_desconto', 'valor_total'),
        }),
        ('Pagamento', {
            'fields': ('forma_pagamento', 'parcelas', 'valor_entrada'),
        }),
        ('Entrega', {
            'fields': ('tipo_entrega', 'endereco_entrega', 'valor_frete',
                       'data_entrega_prevista', 'data_entrega_real'),
            'classes': ('collapse',),
        }),
        ('Observações', {
            'fields': ('observacoes', 'observacoes_internas'),
            'classes': ('collapse',),
        }),
    )

    SITUACAO_COLORS = {
        'ORCAMENTO': '#6c757d',
        'APROVADO': '#0d6efd',
        'PRODUCAO': '#ffc107',
        'PRONTO': '#20c997',
        'ENTREGUE': '#198754',
        'CANCELADO': '#dc3545',
    }

    @admin.display(description='Situação')
    def situacao_badge(self, obj):
        color = self.SITUACAO_COLORS.get(obj.situacao, '#6c757d')
        return format_html(
            '<span style="background:{};color:#fff;padding:2px 8px;border-radius:4px;font-size:11px">{}</span>',
            color, obj.get_situacao_display()
        )


# ---------------------------------------------------------------------------
# T008 — VendaAdmin + PagamentoVenda inline
# ---------------------------------------------------------------------------

class PagamentoVendaInline(admin.TabularInline):
    model = PagamentoVenda
    extra = 0
    readonly_fields = ['troco']
    fields = ['forma', 'valor', 'valor_recebido', 'troco', 'referencia_externa', 'observacoes']


@admin.register(Venda)
class VendaAdmin(admin.ModelAdmin):
    list_display = ['numero_venda', 'cliente', 'loja', 'valor_liquido', 'data_venda', 'cancelada']
    list_filter = ['cancelada', 'tem_devolucao', 'loja', 'nfe_situacao']
    search_fields = ['numero_venda', 'cliente__nome', 'cliente__cpf', 'cliente__cnpj']
    list_select_related = ['cliente', 'loja', 'vendedor']
    date_hierarchy = 'data_venda'
    readonly_fields = ['numero_venda', 'data_venda', 'created_at', 'updated_at']
    list_per_page = 25
    inlines = [PagamentoVendaInline]

    fieldsets = (
        ('Venda', {
            'fields': ('numero_venda', 'loja', 'cliente', 'vendedor', 'data_venda', 'pedido_origem'),
        }),
        ('Valores', {
            'fields': ('valor_total', 'valor_desconto', 'valor_liquido'),
        }),
        ('Status', {
            'fields': ('cancelada', 'motivo_cancelamento', 'data_cancelamento', 'cancelado_por',
                       'tem_devolucao'),
        }),
        ('NFe', {
            'fields': ('nfe_situacao', 'nfe_tipo_emissao', 'nfe_chave_acesso', 'nfe_protocolo'),
            'classes': ('collapse',),
        }),
    )


# ---------------------------------------------------------------------------
# T008 — RecebivelAdmin
# ---------------------------------------------------------------------------

@admin.register(Recebivel)
class RecebivelAdmin(admin.ModelAdmin):
    list_display = ['id', 'cliente', 'venda', 'valor_original', 'valor_pago', 'valor_saldo',
                    'situacao', 'data_vencimento', 'loja']
    list_filter = ['situacao', 'loja', 'criado_com_override']
    search_fields = ['cliente__nome', 'cliente__cpf', 'cliente__cnpj', 'venda__numero_venda']
    list_select_related = ['cliente', 'venda', 'loja']
    date_hierarchy = 'data_vencimento'
    readonly_fields = ['valor_saldo', 'created_at', 'updated_at']
    list_per_page = 25

    fieldsets = (
        ('Recebível', {
            'fields': ('cliente', 'venda', 'loja', 'data_vencimento', 'situacao'),
        }),
        ('Valores', {
            'fields': ('valor_original', 'valor_pago', 'valor_saldo'),
        }),
        ('Override de Crédito', {
            'fields': ('criado_com_override', 'aprovador_override'),
            'classes': ('collapse',),
        }),
        ('Cancelamento', {
            'fields': ('cancelado_por', 'data_cancelamento', 'motivo_cancelamento'),
            'classes': ('collapse',),
        }),
        ('Observações', {
            'fields': ('observacoes',),
            'classes': ('collapse',),
        }),
    )


# ---------------------------------------------------------------------------
# T008 — DescontoAuditLogAdmin (read-only — SEC-4)
# ---------------------------------------------------------------------------

@admin.register(DescontoAuditLog)
class DescontoAuditLogAdmin(admin.ModelAdmin):
    list_display = ['id', 'pedido', 'tipo_desconto', 'percentual', 'valor_antes', 'valor_depois',
                    'solicitante', 'aprovador', 'aprovado_com_pin', 'created_at']
    list_filter = ['tipo_desconto', 'aprovado_com_pin']
    search_fields = ['pedido__numero_pedido', 'solicitante__username', 'aprovador__username']
    list_select_related = ['pedido', 'solicitante', 'aprovador', 'item']
    readonly_fields = ['pedido', 'solicitante', 'aprovador', 'tipo_desconto', 'item',
                       'valor_antes', 'valor_depois', 'percentual', 'motivo',
                       'aprovado_com_pin', 'created_at', 'updated_at']
    list_per_page = 50

    # Audit log: no add / change / delete via Admin (SEC-4)
    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


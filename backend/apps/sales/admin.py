from django.contrib import admin
from django.utils.html import format_html
from .models import Cliente, PedidoVenda


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

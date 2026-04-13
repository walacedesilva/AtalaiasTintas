from django.contrib import admin
from django.utils.html import format_html
from .models import Empresa, Loja


@admin.register(Empresa)
class EmpresaAdmin(admin.ModelAdmin):
    list_display = ['razao_social', 'nome_fantasia', 'cnpj_formatado', 'tipo_empresa', 'ativa']
    list_filter = ['tipo_empresa', 'ativa', 'uf']
    search_fields = ['razao_social', 'nome_fantasia', 'cnpj']
    list_select_related = ['empresa_matriz']
    list_per_page = 20

    fieldsets = (
        ('Identificação', {
            'fields': ('razao_social', 'nome_fantasia', 'cnpj', 'inscricao_estadual', 'inscricao_municipal'),
        }),
        ('Tipo', {
            'fields': ('tipo_empresa', 'empresa_matriz'),
        }),
        ('Contato', {
            'fields': ('telefone', 'email', 'website'),
            'classes': ('collapse',),
        }),
        ('Endereço', {
            'fields': ('cep', 'endereco', 'numero', 'complemento', 'bairro', 'cidade', 'uf'),
            'classes': ('collapse',),
        }),
        ('Status', {
            'fields': ('ativa',),
        }),
    )

    @admin.display(description='CNPJ')
    def cnpj_formatado(self, obj):
        c = obj.cnpj
        if len(c) == 14:
            return f'{c[:2]}.{c[2:5]}.{c[5:8]}/{c[8:12]}-{c[12:]}'
        return c


@admin.register(Loja)
class LojaAdmin(admin.ModelAdmin):
    list_display = ['codigo', 'nome', 'empresa', 'cidade_uf', 'ativa']
    list_filter = ['ativa', 'empresa']
    search_fields = ['codigo', 'nome', 'empresa__razao_social']
    list_select_related = ['empresa', 'responsavel']
    list_per_page = 20

    fieldsets = (
        ('Identificação', {
            'fields': ('codigo', 'nome', 'descricao', 'empresa'),
        }),
        ('Contato', {
            'fields': ('telefone', 'email', 'responsavel'),
        }),
        ('Endereço', {
            'fields': ('cep', 'endereco', 'numero', 'complemento', 'bairro', 'cidade', 'uf'),
            'classes': ('collapse',),
        }),
        ('Status', {
            'fields': ('ativa',),
        }),
    )

    @admin.display(description='Cidade/UF')
    def cidade_uf(self, obj):
        if obj.cidade and obj.uf:
            return f'{obj.cidade}/{obj.uf}'
        return '—'

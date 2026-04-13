from django.contrib import admin
from django.utils.html import format_html
from .models import Categoria, Marca, ProdutoBase, UnidadeMedida


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

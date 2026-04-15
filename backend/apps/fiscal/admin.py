"""Enhanced fiscal admin — T054."""
from __future__ import annotations

from django.contrib import admin
from django.utils.html import format_html
from django.utils.safestring import mark_safe

from apps.fiscal.models import (
    ConfiguracaoFiscal,
    NotaFiscal,
    ItemNotaFiscal,
    TabelaNCM,
)


# ---------------------------------------------------------------------------
# Inlines
# ---------------------------------------------------------------------------

class ItemNotaFiscalInline(admin.TabularInline):
    model = ItemNotaFiscal
    extra = 0
    readonly_fields = ('numero_item', 'codigo_produto', 'descricao', 'ncm', 'cfop',
                       'quantidade', 'unidade', 'valor_unitario', 'valor_total',
                       'aliquota_icms', 'valor_icms', 'valor_pis', 'valor_cofins')
    fields = readonly_fields
    can_delete = False

    def has_add_permission(self, request, obj=None):
        return False


# ---------------------------------------------------------------------------
# NotaFiscalAdmin
# ---------------------------------------------------------------------------

@admin.register(NotaFiscal)
class NotaFiscalAdmin(admin.ModelAdmin):
    list_display  = ('__str__', 'situacao_badge', 'loja', 'chave_acesso_curta',
                     'valor_total_nota', 'data_emissao', 'data_autorizacao')
    list_filter   = ('situacao', 'tipo_nota', 'loja', 'data_emissao')
    search_fields = ('chave_acesso', 'venda__numero_venda',
                     'venda__cliente__nome', 'protocolo_autorizacao')
    readonly_fields = ('id', 'chave_acesso', 'protocolo_autorizacao',
                       'data_emissao', 'data_envio', 'data_autorizacao',
                       'data_cancelamento', 'xml_viewer_envio',
                       'xml_viewer_retorno', 'xml_viewer_cancelamento')
    fieldsets = (
        ('Identificação', {
            'fields': ('id', 'loja', 'venda', 'tipo_nota', 'serie', 'numero',
                       'chave_acesso', 'protocolo_autorizacao')
        }),
        ('Status e Datas', {
            'fields': ('situacao', 'data_emissao', 'data_envio',
                       'data_autorizacao', 'data_cancelamento')
        }),
        ('Valores e Tributos', {
            'fields': ('valor_total_produtos', 'valor_desconto', 'valor_total_nota',
                       'base_calculo_icms', 'valor_icms', 'valor_pis', 'valor_cofins'),
            'classes': ('collapse',),
        }),
        ('XMLs', {
            'fields': ('xml_viewer_envio', 'xml_viewer_retorno', 'xml_viewer_cancelamento'),
            'classes': ('collapse',),
        }),
        ('Observações', {
            'fields': ('informacoes_adicionais', 'motivo_cancelamento'),
            'classes': ('collapse',),
        }),
    )
    inlines = [ItemNotaFiscalInline]
    date_hierarchy = 'data_emissao'
    ordering = ('-data_emissao',)

    def situacao_badge(self, obj):
        colors = {
            'AUTORIZADA':  ('#d1fae5', '#065f46'),
            'CANCELADA':   ('#fee2e2', '#991b1b'),
            'REJEITADA':   ('#fee2e2', '#991b1b'),
            'PENDENTE':    ('#fef9c3', '#854d0e'),
            'ENVIADA':     ('#dbeafe', '#1e3a8a'),
            'RASCUNHO':    ('#f3f4f6', '#374151'),
            'INUTILIZADA': ('#f3f4f6', '#374151'),
        }
        bg, fg = colors.get(obj.situacao, ('#f3f4f6', '#374151'))
        return format_html(
            '<span style="background:{};color:{};padding:2px 8px;border-radius:4px;font-size:.85em">{}</span>',
            bg, fg, obj.get_situacao_display()
        )
    situacao_badge.short_description = 'Situação'
    situacao_badge.admin_order_field = 'situacao'

    def chave_acesso_curta(self, obj):
        if obj.chave_acesso:
            return f'{obj.chave_acesso[:10]}…'
        return '—'
    chave_acesso_curta.short_description = 'Chave Acesso'

    def _xml_viewer(self, xml_field):
        if not xml_field:
            return mark_safe('<em>Não disponível</em>')
        escaped = xml_field.replace('<', '&lt;').replace('>', '&gt;')
        return format_html(
            '<details><summary>Ver XML</summary>'
            '<pre style="font-size:.75rem;max-height:300px;overflow:auto;'
            'background:#f8fafc;padding:1rem;border-radius:.375rem">{}</pre></details>',
            mark_safe(escaped)
        )

    def xml_viewer_envio(self, obj):
        return self._xml_viewer(obj.xml_envio)
    xml_viewer_envio.short_description = 'XML Envio'

    def xml_viewer_retorno(self, obj):
        return self._xml_viewer(obj.xml_retorno)
    xml_viewer_retorno.short_description = 'XML Retorno'

    def xml_viewer_cancelamento(self, obj):
        return self._xml_viewer(obj.xml_cancelamento)
    xml_viewer_cancelamento.short_description = 'XML Cancelamento'


# ---------------------------------------------------------------------------
# ConfiguracaoFiscalAdmin
# ---------------------------------------------------------------------------

@admin.register(ConfiguracaoFiscal)
class ConfiguracaoFiscalAdmin(admin.ModelAdmin):
    list_display  = ('empresa', 'loja', 'regime_tributario', 'nfe_ativo',
                     'nfce_ativo', 'nfe_ambiente', 'certificado_validade')
    list_filter   = ('regime_tributario', 'nfe_ativo', 'nfe_ambiente', 'empresa')
    search_fields = ('empresa__nome', 'loja__nome')
    fieldsets = (
        ('Empresa / Loja', {'fields': ('empresa', 'loja', 'regime_tributario')}),
        ('NF-e', {
            'fields': ('nfe_ativo', 'nfe_ambiente', 'nfe_serie', 'nfe_numero_atual'),
        }),
        ('NFCe', {
            'fields': ('nfce_ativo', 'nfce_ambiente', 'nfce_serie', 'nfce_numero_atual'),
            'classes': ('collapse',),
        }),
        ('SAT', {
            'fields': ('sat_ativo', 'sat_codigo_ativacao', 'sat_numero_caixa'),
            'classes': ('collapse',),
        }),
        ('Certificado Digital', {
            'fields': ('certificado_a1_arquivo', 'certificado_senha', 'certificado_validade'),
            'classes': ('collapse',),
            'description': 'Mantenha a senha do certificado segura. Não compartilhe este arquivo.',
        }),
    )


# ---------------------------------------------------------------------------
# TabelaNCMAdmin
# ---------------------------------------------------------------------------

@admin.register(TabelaNCM)
class TabelaNCMAdmin(admin.ModelAdmin):
    list_display  = ('codigo_ncm', 'descricao', 'categoria', 'aliquota_nacional', 'ativo')
    list_filter   = ('ativo', 'categoria')
    search_fields = ('codigo_ncm', 'descricao', 'categoria')
    list_editable = ('ativo',)
    ordering      = ('codigo_ncm',)


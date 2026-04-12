"""
Configuração do Django Admin para o sistema de etiquetas
"""
from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from .models import LabelTemplate, LabelPrintJob, LabelPrintQueue, PrinterConfiguration


@admin.register(LabelTemplate)
class LabelTemplateAdmin(admin.ModelAdmin):
    list_display = [
        'name', 'category', 'status', 'dimensions_display', 
        'is_default', 'is_active', 'usage_count_display', 'created_at'
    ]
    list_filter = ['category', 'status', 'is_active', 'is_default', 'created_at']
    search_fields = ['name', 'description']
    readonly_fields = ['created_at', 'updated_at', 'usage_count_display']
    
    fieldsets = (
        ('Informações Básicas', {
            'fields': ('name', 'description', 'category', 'status', 'is_default', 'is_active')
        }),
        ('Dimensões', {
            'fields': ('width', 'height', 'margin'),
            'classes': ('collapse',)
        }),
        ('Cores', {
            'fields': ('background_color', 'text_color', 'accent_color'),
            'classes': ('collapse',)
        }),
        ('Fonte', {
            'fields': ('font_family', 'font_size_base'),
            'classes': ('collapse',)
        }),
        ('Elementos', {
            'fields': (
                'include_qr_code', 'include_barcode', 'include_logo',
                'include_formula', 'include_customer', 'include_cost'
            ),
            'classes': ('collapse',)
        }),
        ('Configuração Avançada', {
            'fields': ('layout_config',),
            'classes': ('collapse', 'wide')
        }),
        ('Metadados', {
            'fields': ('created_by', 'created_at', 'updated_at', 'usage_count_display'),
            'classes': ('collapse',)
        }),
    )
    
    def usage_count_display(self, obj):
        """Exibe contagem de uso do template"""
        count = obj.usage_count
        if count > 0:
            url = reverse('admin:tintometry_labels_labelprintjob_changelist')
            return format_html(
                '<a href="{}?template_id={}">{} uso{}</a>',
                url, obj.id, count, 's' if count > 1 else ''
            )
        return '0 usos'
    usage_count_display.short_description = 'Uso'
    
    def save_model(self, request, obj, form, change):
        """Salva o modelo definindo o criador se necessário"""
        if not change and not obj.created_by:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(LabelPrintJob)
class LabelPrintJobAdmin(admin.ModelAdmin):
    list_display = [
        'job_id_short', 'template', 'output_type', 'status', 
        'misturas_count_display', 'copies_count', 'created_by', 'created_at'
    ]
    list_filter = [
        'status', 'output_type', 'template', 'paper_size', 
        'print_quality', 'color_mode', 'created_at'
    ]
    search_fields = ['job_id', 'template__name']
    readonly_fields = [
        'job_id', 'created_at', 'started_at', 'completed_at', 
        'duration_display', 'file_size_display'
    ]
    
    fieldsets = (
        ('Identificação', {
            'fields': ('job_id', 'template', 'status', 'progress')
        }),
        ('Configurações', {
            'fields': (
                'output_type', 'copies_count', 'paper_size', 
                'print_quality', 'color_mode'
            ),
            'classes': ('collapse',)
        }),
        ('Resultado', {
            'fields': (
                'output_file_path', 'file_size_display', 'error_message'
            ),
            'classes': ('collapse',)
        }),
        ('Configuração Avançada', {
            'fields': ('print_config',),
            'classes': ('collapse', 'wide')
        }),
        ('Metadados', {
            'fields': (
                'created_by', 'created_at', 'started_at', 
                'completed_at', 'duration_display'
            ),
            'classes': ('collapse',)
        }),
    )
    
    def job_id_short(self, obj):
        """Exibe versão curta do job_id"""
        return obj.job_id.hex[:8]
    job_id_short.short_description = 'Job ID'
    
    def misturas_count_display(self, obj):
        """Exibe contagem de misturas"""
        count = obj.misturas_count
        if count > 0:
            return f"{count} mistura{'s' if count > 1 else ''}"
        return 'Nenhuma'
    misturas_count_display.short_description = 'Misturas'
    
    def duration_display(self, obj):
        """Exibe duração formatada"""
        duration = obj.duration
        if duration:
            seconds = duration.total_seconds()
            if seconds < 60:
                return f"{seconds:.1f}s"
            elif seconds < 3600:
                return f"{seconds // 60:.0f}m {seconds % 60:.0f}s"
            else:
                hours = seconds // 3600
                minutes = (seconds % 3600) // 60
                return f"{hours:.0f}h {minutes:.0f}m"
        return '-'
    duration_display.short_description = 'Duração'
    
    def file_size_display(self, obj):
        """Exibe tamanho do arquivo formatado"""
        if obj.file_size:
            size = obj.file_size
            if size < 1024:
                return f"{size} bytes"
            elif size < 1024 * 1024:
                return f"{size / 1024:.1f} KB"
            else:
                return f"{size / (1024 * 1024):.1f} MB"
        return '-'
    file_size_display.short_description = 'Tamanho'


@admin.register(LabelPrintQueue)
class LabelPrintQueueAdmin(admin.ModelAdmin):
    list_display = [
        'print_job_id', 'priority', 'scheduled_for', 'attempts', 
        'max_attempts', 'can_retry_display', 'last_attempt'
    ]
    list_filter = ['priority', 'scheduled_for', 'attempts']
    search_fields = ['print_job__job_id']
    readonly_fields = ['last_attempt']
    
    fieldsets = (
        ('Trabalho', {
            'fields': ('print_job', 'priority', 'scheduled_for')
        }),
        ('Controle de Tentativas', {
            'fields': ('attempts', 'max_attempts', 'last_attempt'),
            'classes': ('collapse',)
        }),
        ('Worker', {
            'fields': ('worker_id',),
            'classes': ('collapse',)
        }),
    )
    
    def print_job_id(self, obj):
        """Exibe ID do trabalho de impressão"""
        return obj.print_job.job_id.hex[:8]
    print_job_id.short_description = 'Job ID'
    
    def can_retry_display(self, obj):
        """Indica se pode tentar novamente"""
        if obj.can_retry():
            return format_html('<span style="color: green;">✓ Sim</span>')
        return format_html('<span style="color: red;">✗ Não</span>')
    can_retry_display.short_description = 'Pode Tentar'


@admin.register(PrinterConfiguration)
class PrinterConfigurationAdmin(admin.ModelAdmin):
    list_display = [
        'name', 'printer_type', 'system_name', 'max_dimensions_display',
        'dpi', 'supports_color', 'is_active', 'is_default'
    ]
    list_filter = ['printer_type', 'supports_color', 'is_active', 'is_default']
    search_fields = ['name', 'system_name']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Informações Básicas', {
            'fields': ('name', 'printer_type', 'system_name', 'is_active', 'is_default')
        }),
        ('Especificações Técnicas', {
            'fields': ('max_width_mm', 'max_height_mm', 'dpi', 'supports_color'),
            'classes': ('collapse',)
        }),
        ('Configurações do Driver', {
            'fields': ('driver_config',),
            'classes': ('collapse', 'wide')
        }),
        ('Metadados', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def max_dimensions_display(self, obj):
        """Exibe dimensões máximas formatadas"""
        return f"{obj.max_width_mm} x {obj.max_height_mm}mm"
    max_dimensions_display.short_description = 'Dimensões Máx.'
    
    actions = ['make_default', 'activate_printers', 'deactivate_printers']
    
    def make_default(self, request, queryset):
        """Torna uma impressora padrão"""
        if queryset.count() != 1:
            self.message_user(
                request, 
                "Selecione exatamente uma impressora para tornar padrão.",
                level='error'
            )
            return
        
        printer = queryset.first()
        PrinterConfiguration.objects.update(is_default=False)
        printer.is_default = True
        printer.save()
        
        self.message_user(
            request,
            f"'{printer.name}' definida como impressora padrão."
        )
    make_default.short_description = "Definir como padrão"
    
    def activate_printers(self, request, queryset):
        """Ativa impressoras selecionadas"""
        count = queryset.update(is_active=True)
        self.message_user(
            request,
            f"{count} impressora{'s' if count > 1 else ''} ativada{'s' if count > 1 else ''}."
        )
    activate_printers.short_description = "Ativar impressoras selecionadas"
    
    def deactivate_printers(self, request, queryset):
        """Desativa impressoras selecionadas"""
        count = queryset.update(is_active=False)
        self.message_user(
            request,
            f"{count} impressora{'s' if count > 1 else ''} desativada{'s' if count > 1 else ''}."
        )
    deactivate_printers.short_description = "Desativar impressoras selecionadas"


# Customização do site admin
admin.site.site_header = 'Sistema de Tintas - Administração'
admin.site.site_title = 'Admin Tintas'
admin.site.index_title = 'Administração do Sistema'
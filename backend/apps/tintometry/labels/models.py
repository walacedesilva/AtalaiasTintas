"""
Modelos para o sistema de templates e geração de etiquetas
"""
from django.db import models
from django.conf import settings
from django.utils import timezone
import uuid


class LabelTemplate(models.Model):
    """Template de etiqueta personalizável"""
    
    CATEGORY_CHOICES = [
        ('standard', 'Padrão'),
        ('compact', 'Compacto'),
        ('premium', 'Premium'),
        ('custom', 'Personalizado'),
    ]
    
    STATUS_CHOICES = [
        ('active', 'Ativo'),
        ('inactive', 'Inativo'),
        ('draft', 'Rascunho'),
    ]
    
    # Identificação
    name = models.CharField('Nome', max_length=100)
    description = models.TextField('Descrição', blank=True)
    category = models.CharField('Categoria', max_length=20, choices=CATEGORY_CHOICES, default='standard')
    status = models.CharField('Status', max_length=20, choices=STATUS_CHOICES, default='active')
    is_default = models.BooleanField('Template Padrão', default=False)
    is_active = models.BooleanField('Ativo', default=True)
    
    # Dimensões (em mm)
    width = models.PositiveIntegerField('Largura (mm)', default=100)
    height = models.PositiveIntegerField('Altura (mm)', default=150)
    margin = models.PositiveIntegerField('Margem (mm)', default=5)
    
    # Configurações de cor
    background_color = models.CharField('Cor de Fundo', max_length=7, default='#FFFFFF')
    text_color = models.CharField('Cor do Texto', max_length=7, default='#000000')
    accent_color = models.CharField('Cor de Destaque', max_length=7, default='#2563EB')
    
    # Configurações de fonte
    font_family = models.CharField('Família da Fonte', max_length=50, default='Arial')
    font_size_base = models.PositiveIntegerField('Tamanho Base da Fonte', default=12)
    
    # Elementos incluídos
    include_qr_code = models.BooleanField('Incluir QR Code', default=True)
    include_barcode = models.BooleanField('Incluir Código de Barras', default=True)
    include_logo = models.BooleanField('Incluir Logo', default=True)
    include_formula = models.BooleanField('Incluir Lista de Pigmentos', default=True)
    include_customer = models.BooleanField('Incluir Dados do Cliente', default=True)
    include_cost = models.BooleanField('Incluir Informações de Custo', default=False)
    
    # Layout específico (JSON com configurações customizadas)
    layout_config = models.JSONField('Configuração de Layout', default=dict, blank=True)
    
    # Metadados
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, 
                                   related_name='created_templates')
    created_at = models.DateTimeField('Criado em', auto_now_add=True)
    updated_at = models.DateTimeField('Atualizado em', auto_now=True)
    
    class Meta:
        verbose_name = 'Template de Etiqueta'
        verbose_name_plural = 'Templates de Etiquetas'
        ordering = ['name']
    
    def __str__(self):
        return f"{self.name} ({self.get_category_display()})"
    
    def save(self, *args, **kwargs):
        # Garantir que apenas um template seja o padrão por categoria
        if self.is_default:
            LabelTemplate.objects.filter(
                category=self.category, 
                is_default=True
            ).exclude(id=self.id).update(is_default=False)
        
        super().save(*args, **kwargs)
    
    @property
    def dimensions_display(self):
        """Retorna as dimensões formatadas"""
        return f"{self.width} x {self.height}mm"
    
    @property
    def usage_count(self):
        """Conta quantas vezes o template foi usado"""
        return self.labelprintjob_set.count()


class LabelPrintJob(models.Model):
    """Registro de trabalho de impressão de etiquetas"""
    
    STATUS_CHOICES = [
        ('pending', 'Pendente'),
        ('processing', 'Processando'),
        ('completed', 'Concluído'),
        ('failed', 'Falhou'),
        ('cancelled', 'Cancelado'),
    ]
    
    OUTPUT_CHOICES = [
        ('pdf', 'PDF'),
        ('print', 'Impressão Direta'),
        ('preview', 'Preview'),
    ]
    
    # Identificação
    job_id = models.UUIDField('ID do Trabalho', default=uuid.uuid4, unique=True)
    template = models.ForeignKey(LabelTemplate, on_delete=models.PROTECT, 
                                verbose_name='Template Usado')
    
    # Misturas incluídas
    misturas = models.ManyToManyField('tintometry.MisturaTinta', 
                                      verbose_name='Misturas',
                                      related_name='print_jobs')
    
    # Configurações do trabalho
    output_type = models.CharField('Tipo de Saída', max_length=20, 
                                  choices=OUTPUT_CHOICES, default='pdf')
    copies_count = models.PositiveIntegerField('Número de Cópias', default=1)
    paper_size = models.CharField('Tamanho do Papel', max_length=20, default='a4')
    print_quality = models.CharField('Qualidade', max_length=20, default='medium')
    color_mode = models.CharField('Modo de Cor', max_length=20, default='color')
    
    # Configurações específicas (JSON)
    print_config = models.JSONField('Configurações de Impressão', default=dict, blank=True)
    
    # Status e resultado
    status = models.CharField('Status', max_length=20, choices=STATUS_CHOICES, default='pending')
    progress = models.PositiveIntegerField('Progresso (%)', default=0)
    error_message = models.TextField('Mensagem de Erro', blank=True)
    
    # Arquivos gerados
    output_file_path = models.CharField('Caminho do Arquivo', max_length=500, blank=True)
    file_size = models.PositiveIntegerField('Tamanho do Arquivo (bytes)', null=True, blank=True)
    
    # Metadados
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField('Criado em', auto_now_add=True)
    started_at = models.DateTimeField('Iniciado em', null=True, blank=True)
    completed_at = models.DateTimeField('Concluído em', null=True, blank=True)
    
    class Meta:
        verbose_name = 'Trabalho de Impressão'
        verbose_name_plural = 'Trabalhos de Impressão'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Job {self.job_id.hex[:8]} - {self.template.name}"
    
    def start_processing(self):
        """Marca o trabalho como iniciado"""
        self.status = 'processing'
        self.started_at = timezone.now()
        self.save()
    
    def complete_successfully(self, output_path=None, file_size=None):
        """Marca o trabalho como concluído com sucesso"""
        self.status = 'completed'
        self.progress = 100
        self.completed_at = timezone.now()
        if output_path:
            self.output_file_path = output_path
        if file_size:
            self.file_size = file_size
        self.save()
    
    def fail_with_error(self, error_message):
        """Marca o trabalho como falhou"""
        self.status = 'failed'
        self.error_message = error_message
        self.completed_at = timezone.now()
        self.save()
    
    @property
    def duration(self):
        """Retorna a duração do trabalho se concluído"""
        if self.started_at and self.completed_at:
            return self.completed_at - self.started_at
        return None
    
    @property
    def misturas_count(self):
        """Conta o número de misturas no trabalho"""
        return self.misturas.count()


class LabelPrintQueue(models.Model):
    """Fila de impressão para processamento assíncrono"""
    
    PRIORITY_CHOICES = [
        ('low', 'Baixa'),
        ('normal', 'Normal'),
        ('high', 'Alta'),
        ('urgent', 'Urgente'),
    ]
    
    print_job = models.OneToOneField(LabelPrintJob, on_delete=models.CASCADE,
                                    verbose_name='Trabalho de Impressão')
    priority = models.CharField('Prioridade', max_length=20, 
                               choices=PRIORITY_CHOICES, default='normal')
    scheduled_for = models.DateTimeField('Agendado para', default=timezone.now)
    attempts = models.PositiveIntegerField('Tentativas', default=0)
    max_attempts = models.PositiveIntegerField('Máximo de Tentativas', default=3)
    
    # Metadados de processamento
    worker_id = models.CharField('ID do Worker', max_length=100, blank=True)
    last_attempt = models.DateTimeField('Última Tentativa', null=True, blank=True)
    
    class Meta:
        verbose_name = 'Item da Fila de Impressão'
        verbose_name_plural = 'Fila de Impressão'
        ordering = ['priority', 'scheduled_for']
    
    def __str__(self):
        return f"Fila: {self.print_job.job_id.hex[:8]} ({self.get_priority_display()})"
    
    def can_retry(self):
        """Verifica se ainda pode tentar processar"""
        return self.attempts < self.max_attempts
    
    def increment_attempts(self):
        """Incrementa o contador de tentativas"""
        self.attempts += 1
        self.last_attempt = timezone.now()
        self.save()


class PrinterConfiguration(models.Model):
    """Configuração de impressora para etiquetas"""
    
    PRINTER_TYPES = [
        ('thermal', 'Térmica'),
        ('inkjet', 'Jato de Tinta'),
        ('laser', 'Laser'),
        ('label', 'Etiquetadora'),
    ]
    
    name = models.CharField('Nome da Impressora', max_length=100)
    printer_type = models.CharField('Tipo', max_length=20, choices=PRINTER_TYPES)
    system_name = models.CharField('Nome no Sistema', max_length=200, 
                                  help_text='Nome da impressora no sistema operacional')
    
    # Configurações técnicas
    max_width_mm = models.PositiveIntegerField('Largura Máxima (mm)', default=100)
    max_height_mm = models.PositiveIntegerField('Altura Máxima (mm)', default=150)
    dpi = models.PositiveIntegerField('DPI', default=300)
    supports_color = models.BooleanField('Suporta Cor', default=True)
    
    # Status
    is_active = models.BooleanField('Ativo', default=True)
    is_default = models.BooleanField('Padrão', default=False)
    
    # Configurações específicas (JSON)
    driver_config = models.JSONField('Configurações do Driver', default=dict, blank=True)
    
    created_at = models.DateTimeField('Criado em', auto_now_add=True)
    updated_at = models.DateTimeField('Atualizado em', auto_now=True)
    
    class Meta:
        verbose_name = 'Configuração de Impressora'
        verbose_name_plural = 'Configurações de Impressoras'
        ordering = ['name']
    
    def __str__(self):
        return f"{self.name} ({self.get_printer_type_display()})"
    
    def save(self, *args, **kwargs):
        # Garantir que apenas uma impressora seja padrão
        if self.is_default:
            PrinterConfiguration.objects.filter(
                is_default=True
            ).exclude(id=self.id).update(is_default=False)
        
        super().save(*args, **kwargs)
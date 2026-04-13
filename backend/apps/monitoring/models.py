"""
Monitoring models for system health tracking and alerting
User Story 2: Data Integrity and Backup
Tasks: T034-T037 - Monitoring models implementation
"""

from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.core.validators import MinValueValidator, MaxValueValidator
import json

User = get_user_model()


class TimeStampedModel(models.Model):
    """Base model with automatic timestamps"""
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        abstract = True


class SystemHealth(TimeStampedModel):
    """
    Model to track system health metrics and performance indicators
    Task: T034 - SystemHealth model for health metrics
    """
    
    # Health status levels
    STATUS_HEALTHY = 'HEALTHY'
    STATUS_WARNING = 'WARNING'
    STATUS_CRITICAL = 'CRITICAL'
    STATUS_DOWN = 'DOWN'
    
    STATUS_CHOICES = [
        (STATUS_HEALTHY, 'Saudável'),
        (STATUS_WARNING, 'Aviso'),
        (STATUS_CRITICAL, 'Crítico'),
        (STATUS_DOWN, 'Inativo'),
    ]
    
    # System component types
    COMPONENT_DATABASE = 'DATABASE'
    COMPONENT_REDIS = 'REDIS'
    COMPONENT_API = 'API'
    COMPONENT_CELERY = 'CELERY'
    COMPONENT_DISK = 'DISK'
    COMPONENT_MEMORY = 'MEMORY'
    COMPONENT_CPU = 'CPU'
    COMPONENT_EXTERNAL_API = 'EXTERNAL_API'
    
    COMPONENT_CHOICES = [
        (COMPONENT_DATABASE, 'Banco de Dados'),
        (COMPONENT_REDIS, 'Cache Redis'),
        (COMPONENT_API, 'Serviços de API'),
        (COMPONENT_CELERY, 'Tarefas em Segundo Plano'),
        (COMPONENT_DISK, 'Armazenamento em Disco'),
        (COMPONENT_MEMORY, 'Uso de Memória'),
        (COMPONENT_CPU, 'Uso de CPU'),
        (COMPONENT_EXTERNAL_API, 'APIs Externas'),
    ]
    
    # Core fields
    component = models.CharField(
        max_length=50,
        choices=COMPONENT_CHOICES,
        help_text="Componente do sistema sendo monitorado"
    )
    
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        help_text="Status de saúde atual"
    )
    
    # Performance metrics
    response_time = models.FloatField(
        null=True, blank=True,
        validators=[MinValueValidator(0.0)],
        help_text="Tempo de resposta em milissegundos"
    )
    
    cpu_usage = models.FloatField(
        null=True, blank=True,
        validators=[MinValueValidator(0.0), MaxValueValidator(100.0)],
        help_text="Percentual de uso de CPU"
    )
    
    memory_usage = models.FloatField(
        null=True, blank=True,
        validators=[MinValueValidator(0.0), MaxValueValidator(100.0)],
        help_text="Percentual de uso de memória"
    )
    
    disk_usage = models.FloatField(
        null=True, blank=True,
        validators=[MinValueValidator(0.0), MaxValueValidator(100.0)],
        help_text="Percentual de uso de disco"
    )
    
    # Connection metrics
    active_connections = models.IntegerField(
        null=True, blank=True,
        validators=[MinValueValidator(0)],
        help_text="Número de conexões ativas"
    )
    
    queue_size = models.IntegerField(
        null=True, blank=True,
        validators=[MinValueValidator(0)],
        help_text="Tamanho da fila de tarefas em segundo plano"
    )
    
    # Error tracking
    error_count = models.IntegerField(
        default=0,
        validators=[MinValueValidator(0)],
        help_text="Número de erros neste intervalo de verificação"
    )
    
    error_message = models.TextField(
        null=True, blank=True,
        help_text="Última mensagem de erro, se houver"
    )
    
    # Additional metadata
    check_timestamp = models.DateTimeField(
        default=timezone.now,
        help_text="Quando esta verificação de saúde foi realizada"
    )
    
    additional_data = models.JSONField(
        null=True, blank=True,
        help_text="Métricas adicionais e metadados"
    )
    
    class Meta:
        ordering = ['-check_timestamp']
        indexes = [
            models.Index(fields=['component', 'check_timestamp']),
            models.Index(fields=['status', 'check_timestamp']),
            models.Index(fields=['check_timestamp']),
        ]
        verbose_name = 'Verificação de Saúde'
        verbose_name_plural = 'Verificações de Saúde'
    
    def __str__(self):
        return f"{self.get_component_display()} - {self.get_status_display()} ({self.check_timestamp})"
    
    @property
    def is_healthy(self):
        """Check if component is healthy"""
        return self.status == self.STATUS_HEALTHY
    
    @property
    def needs_attention(self):
        """Check if component needs attention"""
        return self.status in [self.STATUS_WARNING, self.STATUS_CRITICAL]
    
    @classmethod
    def get_current_status(cls, component):
        """Get the latest health status for a component"""
        return cls.objects.filter(component=component).first()
    
    @classmethod
    def get_system_overview(cls):
        """Get overview of all system components"""
        components = {}
        for component_code, component_name in cls.COMPONENT_CHOICES:
            latest_check = cls.get_current_status(component_code)
            components[component_code] = {
                'name': component_name,
                'status': latest_check.status if latest_check else 'UNKNOWN',
                'last_check': latest_check.check_timestamp if latest_check else None
            }
        return components


class AlertNotification(TimeStampedModel):
    """
    Model to track system alerts and notifications
    Task: T035 - AlertNotification model for alert tracking
    """
    
    # Alert severity levels
    SEVERITY_INFO = 'INFO'
    SEVERITY_WARNING = 'WARNING'
    SEVERITY_ERROR = 'ERROR'
    SEVERITY_CRITICAL = 'CRITICAL'
    
    SEVERITY_CHOICES = [
        (SEVERITY_INFO, 'Informação'),
        (SEVERITY_WARNING, 'Aviso'),
        (SEVERITY_ERROR, 'Erro'),
        (SEVERITY_CRITICAL, 'Crítico'),
    ]
    
    # Alert types
    TYPE_SYSTEM_HEALTH = 'SYSTEM_HEALTH'
    TYPE_BACKUP_FAILURE = 'BACKUP_FAILURE'
    TYPE_SECURITY_ALERT = 'SECURITY_ALERT'
    TYPE_PERFORMANCE = 'PERFORMANCE'
    TYPE_DISK_SPACE = 'DISK_SPACE'
    TYPE_DATABASE_ERROR = 'DATABASE_ERROR'
    TYPE_API_ERROR = 'API_ERROR'
    
    TYPE_CHOICES = [
        (TYPE_SYSTEM_HEALTH, 'Saúde do Sistema'),
        (TYPE_BACKUP_FAILURE, 'Falha de Backup'),
        (TYPE_SECURITY_ALERT, 'Alerta de Segurança'),
        (TYPE_PERFORMANCE, 'Problema de Desempenho'),
        (TYPE_DISK_SPACE, 'Espaço em Disco'),
        (TYPE_DATABASE_ERROR, 'Erro no Banco de Dados'),
        (TYPE_API_ERROR, 'Erro de API'),
    ]
    
    # Alert status
    STATUS_ACTIVE = 'ACTIVE'
    STATUS_ACKNOWLEDGED = 'ACKNOWLEDGED'
    STATUS_RESOLVED = 'RESOLVED'
    STATUS_SUPPRESSED = 'SUPPRESSED'
    
    STATUS_CHOICES = [
        (STATUS_ACTIVE, 'Ativo'), 
        (STATUS_ACKNOWLEDGED, 'Reconhecido'),
        (STATUS_RESOLVED, 'Resolvido'),
        (STATUS_SUPPRESSED, 'Suprimido'),
    ]
    
    # Core fields
    title = models.CharField(
        max_length=200,
        help_text="Título breve do alerta"
    )
    
    message = models.TextField(
        help_text="Mensagem detalhada do alerta"
    )
    
    alert_type = models.CharField(
        max_length=50,
        choices=TYPE_CHOICES,
        help_text="Tipo de alerta"
    )
    
    severity = models.CharField(
        max_length=20,
        choices=SEVERITY_CHOICES,
        help_text="Nível de severidade do alerta"
    )
    
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default=STATUS_ACTIVE,
        help_text="Status atual do alerta"
    )
    
    # Related objects
    health_check = models.ForeignKey(
        SystemHealth,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='alerts',
        help_text="Verificação de saúde relacionada, se aplicável"
    )
    
    affected_user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='alerts_received',
        help_text="Usuário afetado por este alerta"
    )
    
    # Alert management
    acknowledged_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='alerts_acknowledged',
        help_text="Usuário que reconheceu o alerta"
    )
    
    acknowledged_at = models.DateTimeField(
        null=True, blank=True,
        help_text="Quando o alerta foi reconhecido"
    )
    
    resolved_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='alerts_resolved',
        help_text="Usuário que resolveu o alerta"
    )
    
    resolved_at = models.DateTimeField(
        null=True, blank=True,
        help_text="Quando o alerta foi resolvido"
    )
    
    resolution_notes = models.TextField(
        null=True, blank=True,
        help_text="Notas sobre como o alerta foi resolvido"
    )
    
    # Metadata
    source_component = models.CharField(
        max_length=100,
        null=True, blank=True,
        help_text="Componente do sistema que gerou este alerta"
    )
    
    metadata = models.JSONField(
        null=True, blank=True,
        help_text="Metadados adicionais do alerta"
    )
    
    # Notification flags
    email_sent = models.BooleanField(
        default=False,
        help_text="Se a notificação por e-mail foi enviada"
    )
    
    sms_sent = models.BooleanField(
        default=False,
        help_text="Se a notificação por SMS foi enviada"
    )
    
    push_sent = models.BooleanField(
        default=False,
        help_text="Se a notificação push foi enviada"
    )
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['alert_type', 'created_at']),
            models.Index(fields=['severity', 'status']),
            models.Index(fields=['status', 'created_at']),
            models.Index(fields=['affected_user', 'status']),
        ]
        verbose_name = 'Notificação de Alerta'
        verbose_name_plural = 'Notificações de Alerta'
    
    def __str__(self):
        return f"{self.get_severity_display()}: {self.title}"
    
    def acknowledge(self, user, notes=None):
        """Acknowledge this alert"""
        self.status = self.STATUS_ACKNOWLEDGED
        self.acknowledged_by = user
        self.acknowledged_at = timezone.now()
        if notes:
            self.resolution_notes = notes
        self.save(update_fields=[
            'status', 'acknowledged_by', 'acknowledged_at', 'resolution_notes'
        ])
    
    def resolve(self, user, notes=None):
        """Resolve this alert"""
        self.status = self.STATUS_RESOLVED
        self.resolved_by = user
        self.resolved_at = timezone.now()
        if notes:
            self.resolution_notes = notes
        self.save(update_fields=[
            'status', 'resolved_by', 'resolved_at', 'resolution_notes'
        ])
    
    @property
    def is_active(self):
        """Check if alert is still active"""
        return self.status == self.STATUS_ACTIVE
    
    @property
    def age(self):
        """Get alert age as timedelta"""
        return timezone.now() - self.created_at
    
    @classmethod
    def create_alert(cls, title, message, alert_type, severity, **kwargs):
        """Helper method to create new alerts"""
        return cls.objects.create(
            title=title,
            message=message,
            alert_type=alert_type,
            severity=severity,
            **kwargs
        )
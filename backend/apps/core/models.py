from django.db import models
from django.core.exceptions import ValidationError
from django.conf import settings
import json


class UserPreferences(models.Model):
    """
    Model to store user interface preferences for personalized experience.
    
    Feature: 3-modern-web-interface
    Task: T006 - User Preferences Model
    """
    
    # Choices for theme preference
    THEME_CHOICES = [
        ('light', 'Light Theme'),
        ('dark', 'Dark Theme'),
        ('auto', 'System Preference'),
    ]
    
    # Choices for interface density
    DENSITY_CHOICES = [
        ('compact', 'Compact (High density)'),
        ('comfortable', 'Comfortable (Default)'),
        ('spacious', 'Spacious (Low density)'),
    ]
    
    # Core relationship
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name='preferences',
        help_text="User account associated with these preferences"
    )
    
    # Theme preferences
    theme = models.CharField(
        max_length=10,
        choices=THEME_CHOICES,
        default='light',
        help_text="Visual theme preference for the interface"
    )
    
    # Layout preferences
    density = models.CharField(
        max_length=15,
        choices=DENSITY_CHOICES,
        default='comfortable',
        help_text="Interface density/spacing preference"
    )
    
    # Quick actions configuration (stored as JSON)
    quick_actions = models.JSONField(
        default=list,
        blank=True,
        help_text="JSON array of quick action button configurations"
    )
    
    # Additional preferences for future expansion
    sidebar_collapsed = models.BooleanField(
        default=False,
        help_text="Whether the navigation sidebar is collapsed by default"
    )
    
    show_breadcrumbs = models.BooleanField(
        default=True,
        help_text="Whether to display breadcrumb navigation"
    )
    
    # Accessibility preferences
    high_contrast = models.BooleanField(
        default=False,
        help_text="Enable high contrast mode for better accessibility"
    )
    
    reduce_motion = models.BooleanField(
        default=False,
        help_text="Reduce animations and motion effects"
    )
    
    # Timestamps
    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text="When these preferences were first created"
    )
    
    updated_at = models.DateTimeField(
        auto_now=True,
        help_text="When these preferences were last modified"
    )
    
    class Meta:
        verbose_name = "User Preferences"
        verbose_name_plural = "User Preferences"
        ordering = ['-updated_at']
    
    def __str__(self):
        return f"{self.user.username} - {self.theme}/{self.density}"
    
    def clean(self):
        """Validate quick_actions JSON field"""
        if self.quick_actions and not isinstance(self.quick_actions, list):
            raise ValidationError({
                'quick_actions': 'Quick actions must be a list of action configurations'
            })
    
    def get_default_quick_actions(self):
        """Return default quick actions configuration"""
        return [
            {'action': 'create_label', 'label': 'Nova Etiqueta', 'icon': 'bi-tag'},
            {'action': 'inventory_count', 'label': 'Contagem', 'icon': 'bi-clipboard-check'},
            {'action': 'sales_report', 'label': 'Vendas', 'icon': 'bi-graph-up'},
            {'action': 'tint_mix', 'label': 'Misturar Tinta', 'icon': 'bi-palette'},
        ]
    
    def save(self, *args, **kwargs):
        # Set default quick actions if none provided
        if not self.quick_actions:
            self.quick_actions = self.get_default_quick_actions()
        
        # Validate before saving
        self.clean()
        
        super().save(*args, **kwargs)
    
    @classmethod
    def get_or_create_for_user(cls, user):
        """
        Get or create preferences for a user with sensible defaults.
        
        Args:
            user: User instance
            
        Returns:
            tuple: (UserPreferences instance, created boolean)
        """
        preferences, created = cls.objects.get_or_create(
            user=user,
            defaults={
                'theme': 'light',
                'density': 'comfortable',
                'quick_actions': cls().get_default_quick_actions(),
                'sidebar_collapsed': False,
                'show_breadcrumbs': True,
                'high_contrast': False,
                'reduce_motion': False,
            }
        )
        return preferences, created


def create_user_preferences(sender, instance, created, **kwargs):
    """
    Signal receiver to automatically create UserPreferences when a User is created.
    """
    if created:
        UserPreferences.objects.create(user=instance)


def create_user_preferences(sender, instance, created, **kwargs):
    """
    Signal receiver to automatically create UserPreferences when a User is created.
    This will be connected after all models are loaded to avoid circular imports.
    """
    if created:
        UserPreferences.objects.create(user=instance)
from django.contrib.auth.models import AbstractUser
from django.core.validators import ValidationError
import uuid


class TimeStampedModel(models.Model):
    """Modelo base com timestamps automáticos"""
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        abstract = True


class User(AbstractUser):
    """Usuário customizado do sistema"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    cpf = models.CharField(max_length=11, unique=True, null=True, blank=True)
    telefone = models.CharField(max_length=15, null=True, blank=True)
    data_nascimento = models.DateField(null=True, blank=True)
    
    # Configurações de perfil
    foto_perfil = models.ImageField(upload_to='perfis/', null=True, blank=True)
    ativo = models.BooleanField(default=True)
    
    # Permissões específicas do sistema
    pode_vender = models.BooleanField(default=False)
    pode_gerenciar_estoque = models.BooleanField(default=False)
    pode_acessar_financeiro = models.BooleanField(default=False)
    pode_administrar = models.BooleanField(default=False)
    
    class Meta:
        db_table = 'auth_user'


class UserProfile(TimeStampedModel):
    """Perfil estendido do usuário"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    
    # Dados profissionais
    cargo = models.CharField(max_length=100, null=True, blank=True)
    setor = models.CharField(max_length=100, null=True, blank=True)
    data_admissao = models.DateField(null=True, blank=True)
    
    # Configurações de trabalho
    meta_vendas_mensal = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    comissao_percentual = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    
    # Configurações de sistema
    tema_sistema = models.CharField(max_length=20, choices=[
        ('claro', 'Claro'),
        ('escuro', 'Escuro'),
        ('auto', 'Automático')
    ], default='claro')
    
    notificacoes_email = models.BooleanField(default=True)
    notificacoes_push = models.BooleanField(default=True)


class Configuracao(TimeStampedModel):
    """Configurações globais do sistema"""
    chave = models.CharField(max_length=100, unique=True)
    valor = models.TextField()
    tipo = models.CharField(max_length=20, choices=[
        ('string', 'Texto'),
        ('integer', 'Número Inteiro'),
        ('float', 'Número Decimal'),
        ('boolean', 'Verdadeiro/Falso'),
        ('json', 'JSON')
    ])
    descricao = models.TextField(null=True, blank=True)
    categoria = models.CharField(max_length=50, null=True, blank=True)
    
    def get_valor(self):
        """Retorna o valor convertido para o tipo apropriado"""
        if self.tipo == 'integer':
            return int(self.valor)
        elif self.tipo == 'float':
            return float(self.valor)
        elif self.tipo == 'boolean':
            return self.valor.lower() in ['true', '1', 'sim', 'yes']
        elif self.tipo == 'json':
            import json
            return json.loads(self.valor)
        else:
            return self.valor
    
    def __str__(self):
        return f"{self.chave}: {self.valor}"


class LogSistema(TimeStampedModel):
    """Log de atividades do sistema"""
    usuario = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    acao = models.CharField(max_length=100)
    modelo = models.CharField(max_length=100, null=True, blank=True)
    objeto_id = models.CharField(max_length=100, null=True, blank=True)
    detalhes = models.JSONField(null=True, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(null=True, blank=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['usuario', 'created_at']),
            models.Index(fields=['modelo', 'objeto_id']),
        ]


class UserSession(TimeStampedModel):
    """Modelo para rastreamento de sessões de usuário"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sessions')
    session_key = models.CharField(max_length=40, unique=True)
    ip_address = models.GenericIPAddressField()
    user_agent = models.TextField(null=True, blank=True)
    browser_info = models.JSONField(null=True, blank=True)
    
    # Session status
    is_active = models.BooleanField(default=True)
    last_activity = models.DateTimeField(auto_now=True)
    login_time = models.DateTimeField(auto_now_add=True)
    logout_time = models.DateTimeField(null=True, blank=True)
    
    # Security tracking
    location_city = models.CharField(max_length=100, null=True, blank=True)
    location_country = models.CharField(max_length=100, null=True, blank=True)
    is_suspicious = models.BooleanField(default=False)
    
    class Meta:
        ordering = ['-login_time']
        indexes = [
            models.Index(fields=['user', 'is_active']),
            models.Index(fields=['session_key']),
            models.Index(fields=['last_activity']),
        ]
    
    def __str__(self):
        return f"{self.user.username} - {self.login_time} ({'Ativo' if self.is_active else 'Inativo'})"
    
    def duration(self):
        """Retorna a duração da sessão"""
        end_time = self.logout_time or timezone.now()
        return end_time - self.login_time
    
    def mark_logout(self):
        """Marca a sessão como finalizada"""
        from django.utils import timezone
        self.logout_time = timezone.now()
        self.is_active = False
        self.save(update_fields=['logout_time', 'is_active'])


class AuditLog(TimeStampedModel):
    """Log robusto para auditoria de ações críticas do sistema"""
    
    # Action types
    ACTION_LOGIN = 'LOGIN'
    ACTION_LOGOUT = 'LOGOUT'
    ACTION_CREATE = 'CREATE'
    ACTION_UPDATE = 'UPDATE'
    ACTION_DELETE = 'DELETE'
    ACTION_VIEW = 'VIEW'
    ACTION_EXPORT = 'EXPORT'
    ACTION_IMPORT = 'IMPORT'
    ACTION_ACCESS_DENIED = 'ACCESS_DENIED'
    ACTION_SECURITY_ALERT = 'SECURITY_ALERT'
    
    ACTION_CHOICES = [
        (ACTION_LOGIN, 'Login'),
        (ACTION_LOGOUT, 'Logout'),
        (ACTION_CREATE, 'Criar'),
        (ACTION_UPDATE, 'Atualizar'),
        (ACTION_DELETE, 'Excluir'),
        (ACTION_VIEW, 'Visualizar'),
        (ACTION_EXPORT, 'Exportar'),
        (ACTION_IMPORT, 'Importar'),
        (ACTION_ACCESS_DENIED, 'Acesso Negado'),
        (ACTION_SECURITY_ALERT, 'Alerta de Segurança'),
    ]
    
    # Risk levels
    RISK_LOW = 'LOW'
    RISK_MEDIUM = 'MEDIUM'
    RISK_HIGH = 'HIGH'
    RISK_CRITICAL = 'CRITICAL'
    
    RISK_CHOICES = [
        (RISK_LOW, 'Baixo'),
        (RISK_MEDIUM, 'Médio'), 
        (RISK_HIGH, 'Alto'),
        (RISK_CRITICAL, 'Crítico'),
    ]
    
    # Core fields
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    session = models.ForeignKey(UserSession, on_delete=models.SET_NULL, null=True, blank=True)
    action = models.CharField(max_length=20, choices=ACTION_CHOICES)
    resource = models.CharField(max_length=100, help_text="Recurso afetado (modelo.campo)")
    resource_id = models.CharField(max_length=100, null=True, blank=True)
    
    # Audit details
    description = models.TextField(help_text="Descrição da ação")
    risk_level = models.CharField(max_length=10, choices=RISK_CHOICES, default=RISK_LOW)
    success = models.BooleanField(default=True)
    error_message = models.TextField(null=True, blank=True)
    
    # Context information
    ip_address = models.GenericIPAddressField()
    user_agent = models.TextField(null=True, blank=True)
    request_path = models.URLField(max_length=200, null=True, blank=True)
    request_method = models.CharField(max_length=10, null=True, blank=True)
    
    # Before/after data for critical actions
    old_values = models.JSONField(null=True, blank=True, help_text="Valores anteriores")
    new_values = models.JSONField(null=True, blank=True, help_text="Novos valores")
    
    # Additional metadata
    extra_data = models.JSONField(null=True, blank=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'created_at']),
            models.Index(fields=['action', 'created_at']),
            models.Index(fields=['resource', 'resource_id']),
            models.Index(fields=['risk_level', 'created_at']),
            models.Index(fields=['success']),
        ]
        verbose_name = 'Log de Auditoria'
        verbose_name_plural = 'Logs de Auditoria'
    
    def __str__(self):
        user_str = self.user.username if self.user else 'Sistema'
        return f"{user_str} - {self.get_action_display()} - {self.resource} ({self.created_at})"
    
    @classmethod
    def log_action(cls, user, action, resource, resource_id=None, description="", 
                   risk_level=RISK_LOW, success=True, error_message=None,
                   old_values=None, new_values=None, extra_data=None,
                   request=None, session=None):
        """
        Helper method para criar logs de auditoria
        """
        audit_data = {
            'user': user,
            'session': session,
            'action': action,
            'resource': resource,
            'resource_id': str(resource_id) if resource_id else None,
            'description': description,
            'risk_level': risk_level,
            'success': success,
            'error_message': error_message,
            'old_values': old_values,
            'new_values': new_values,
            'extra_data': extra_data,
        }
        
        if request:
            audit_data.update({
                'ip_address': cls._get_client_ip(request),
                'user_agent': request.META.get('HTTP_USER_AGENT', ''),
                'request_path': request.path,
                'request_method': request.method,
            })
        
        return cls.objects.create(**audit_data)
    
    @staticmethod
    def _get_client_ip(request):
        """Extrai o IP real do cliente considerando proxies"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip

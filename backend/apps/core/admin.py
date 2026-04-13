"""
Django Admin configuration for Core app
Provides comprehensive user and audit management interface
"""

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.forms import UserChangeForm, UserCreationForm
from django.utils.html import format_html
from django.urls import reverse
from django.utils import timezone
from django import forms

from .models import User, UserProfile, UserSession, AuditLog, UserPreferences


class TintasUserCreationForm(UserCreationForm):
    """Custom user creation form with business fields"""
    
    email = forms.EmailField(required=True)
    
    class Meta:
        model = User
        fields = ('username', 'email', 'password1', 'password2')
    
    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        if commit:
            user.save()
        return user


class TintasUserChangeForm(UserChangeForm):
    """Custom user change form with business fields"""
    
    class Meta:
        model = User
        fields = '__all__'


class UserProfileInline(admin.StackedInline):
    """Inline for UserProfile"""
    model = UserProfile
    can_delete = False
    verbose_name = "Perfil do Usuário"
    verbose_name_plural = "Perfis dos Usuários"
    
    fieldsets = (
        ('Informações Profissionais', {
            'fields': ('cargo', 'setor', 'data_admissao')
        }),
        ('Configurações de Trabalho', {
            'fields': ('meta_vendas_mensal', 'comissao_percentual')
        }),
        ('Configurações de Sistema', {
            'fields': ('tema_sistema', 'notificacoes_email', 'notificacoes_push')
        }),
    )


class UserSessionInline(admin.TabularInline):
    """Inline for active user sessions"""
    model = UserSession
    extra = 0
    can_delete = False
    readonly_fields = ('session_key', 'ip_address', 'user_agent', 'login_time', 'last_activity', 'is_active')
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.filter(is_active=True)
    
    verbose_name = "Sessão Ativa"
    verbose_name_plural = "Sessões Ativas"


class UserPreferencesInline(admin.StackedInline):
    """
    Inline admin to show UserPreferences directly in the User admin page.
    """
    model = UserPreferences
    can_delete = False
    verbose_name = "Preferências de Interface"
    verbose_name_plural = "Preferências de Interface"
    
    fieldsets = (
        ('Tema Visual', {
            'fields': ('theme', 'density', 'high_contrast'),
            'classes': ('wide',)
        }),
        ('Layout', {
            'fields': ('sidebar_collapsed', 'show_breadcrumbs', 'reduce_motion'),
            'classes': ('wide',)
        }),
        ('Ações Rápidas', {
            'fields': ('quick_actions',),
            'classes': ('collapse', 'wide'),
            'description': 'Configuração JSON para ações rápidas personalizadas'
        }),
    )


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """Enhanced User admin with business-specific features"""
    
    form = TintasUserChangeForm
    add_form = TintasUserCreationForm
    
    list_display = [
        'username', 'email', 'business_role_display', 
        'ativo', 'last_login', 'date_joined', 'active_sessions_count'
    ]
    
    list_filter = [
        'ativo', 'is_staff', 'is_superuser', 'date_joined', 'last_login',
        'pode_vender', 'pode_gerenciar_estoque', 'pode_acessar_financeiro', 
        'pode_administrar'
    ]
    
    search_fields = ['username', 'email']
    
    ordering = ['-date_joined']
    
    readonly_fields = ['last_login', 'date_joined']
    
    inlines = [UserProfileInline, UserSessionInline, UserPreferencesInline]
    
    fieldsets = (
        (None, {
            'fields': ('username', 'password')
        }),
        ('Informações Pessoais', {
            'fields': ('email', 'cpf', 'telefone', 'data_nascimento', 'foto_perfil')
        }),
        ('Permissões Comerciais', {
            'fields': (
                'pode_vender', 'pode_gerenciar_estoque', 'pode_acessar_financeiro',
                'pode_administrar'
            ),
            'classes': ['collapse']
        }),
        ('Permissões Django', {
            'fields': ('is_active', 'ativo', 'is_staff', 'is_superuser', 'groups', 'user_permissions'),
            'classes': ['collapse']
        }),
        ('Datas Importantes', {
            'fields': ('last_login', 'date_joined'),
            'classes': ['collapse']
        }),
    )
    
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'email', 'password1', 'password2'),
        }),
        ('Permissões Iniciais', {
            'fields': ('pode_vender', 'ativo'),
            'classes': ['collapse']
        }),
    )
    
    def business_role_display(self, obj):
        """Display user's business role"""
        from .permissions import BusinessPermissions, BusinessRole
        if obj.is_superuser or getattr(obj, 'pode_administrar', False):
            role = BusinessRole.ADMIN
        elif getattr(obj, 'pode_vender', False):
            role = BusinessRole.VENDOR
        elif getattr(obj, 'pode_gerenciar_estoque', False):
            role = BusinessRole.OPERATOR
        else:
            role = BusinessRole.VIEWER
        return role.value
    business_role_display.short_description = 'Função'
    
    def active_sessions_count(self, obj):
        """Count of active sessions"""
        count = obj.sessions.filter(is_active=True).count()
        if count > 0:
            return format_html(
                '<a href="{}?user__id__exact={}">{} sessões</a>',
                reverse('admin:core_usersession_changelist'),
                obj.id,
                count
            )
        return '0 sessões'
    active_sessions_count.short_description = 'Sessões Ativas'
    
    actions = ['activate_users', 'deactivate_users', 'force_logout_users']
    
    def activate_users(self, request, queryset):
        """Activate selected users"""
        updated = queryset.update(ativo=True)
        self.message_user(request, f'{updated} usuários foram ativados.')
    activate_users.short_description = "Ativar usuários selecionados"
    
    def deactivate_users(self, request, queryset):
        """Deactivate selected users"""
        updated = queryset.update(ativo=False)
        self.message_user(request, f'{updated} usuários foram desativados.')
    deactivate_users.short_description = "Desativar usuários selecionados"
    
    def force_logout_users(self, request, queryset):
        """Force logout all sessions for selected users"""
        total_sessions = 0
        for user in queryset:
            sessions = UserSession.objects.filter(user=user, is_active=True)
            sessions.update(is_active=False, logout_time=timezone.now())
            total_sessions += sessions.count()
        
        self.message_user(request, f'{total_sessions} sessões foram encerradas.')
    force_logout_users.short_description = "Forçar logout dos usuários selecionados"


@admin.register(UserProfile) 
class UserProfileAdmin(admin.ModelAdmin):
    """UserProfile admin interface"""
    
    list_display = ['user', 'cargo', 'setor', 'tema_sistema', 'created_at']
    list_filter = ['tema_sistema', 'setor', 'created_at']
    search_fields = ['user__username', 'cargo', 'setor']
    
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Usuário', {
            'fields': ('user',)
        }),
        ('Informações Profissionais', {
            'fields': ('cargo', 'setor', 'data_admissao')
        }),
        ('Configurações de Trabalho', {
            'fields': ('meta_vendas_mensal', 'comissao_percentual')
        }),
        ('Preferências de Sistema', {
            'fields': ('tema_sistema', 'notificacoes_email', 'notificacoes_push')
        }),
        ('Metadados', {
            'fields': ('created_at', 'updated_at'),
            'classes': ['collapse']
        }),
    )


@admin.register(UserSession)
class UserSessionAdmin(admin.ModelAdmin):
    """UserSession admin interface"""
    
    list_display = [
        'user', 'session_key_short', 'ip_address', 'login_time', 
        'last_activity', 'is_active', 'browser_display'
    ]
    
    list_filter = ['is_active', 'login_time', 'last_activity']
    search_fields = ['user__username', 'user__nome_completo', 'ip_address', 'session_key']
    
    readonly_fields = [
        'user', 'session_key', 'ip_address', 'user_agent', 
        'browser_info', 'login_time', 'last_activity', 'logout_time'
    ]
    
    date_hierarchy = 'login_time'
    
    fieldsets = (
        ('Sessão', {
            'fields': ('user', 'session_key', 'is_active')
        }),
        ('Informações de Conexão', {
            'fields': ('ip_address', 'user_agent', 'browser_info')
        }),
        ('Registros de Data', {
            'fields': ('login_time', 'last_activity', 'logout_time'),
            'classes': ['collapse']
        }),
    )
    
    def session_key_short(self, obj):
        """Display shortened session key"""
        if obj.session_key:
            return f"{obj.session_key[:8]}..."
        return "-"
    session_key_short.short_description = 'Chave de Sessão'
    
    def browser_display(self, obj):
        """Display browser info"""
        if obj.browser_info:
            user_agent = obj.browser_info.get('user_agent', '')
            if 'Chrome' in user_agent:
                return '🌐 Chrome'
            elif 'Firefox' in user_agent:
                return '🦊 Firefox'
            elif 'Safari' in user_agent:
                return '🧭 Safari'
            elif 'Edge' in user_agent:
                return '📘 Edge'
        return '❓ Desconhecido'
    browser_display.short_description = 'Navegador'
    
    actions = ['force_logout_sessions']
    
    def force_logout_sessions(self, request, queryset):
        """Force logout selected sessions"""
        active_sessions = queryset.filter(is_active=True)
        updated = active_sessions.update(is_active=False, logout_time=timezone.now())
        self.message_user(request, f'{updated} sessões foram encerradas.')
    force_logout_sessions.short_description = "Encerrar sessões selecionadas"


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    """AuditLog admin - Somente leitura para conformidade"""

    list_display = [
        'created_at', 'user_display', 'action_display', 'resource',
        'description_short', 'risk_level_display', 'success_display', 'ip_address',
    ]

    list_filter = [
        'action', 'risk_level', 'success', 'created_at',
        'user__username',
    ]

    search_fields = [
        'user__username', 'resource', 'description', 'ip_address',
    ]

    readonly_fields = [
        'user', 'session', 'action', 'resource', 'resource_id', 'description',
        'risk_level', 'success', 'ip_address', 'user_agent',
        'request_path', 'request_method', 'old_values', 'new_values',
        'error_message', 'extra_data', 'created_at',
    ]

    date_hierarchy = 'created_at'

    fieldsets = (
        ('Ação', {
            'fields': ('created_at', 'user', 'session', 'action', 'resource', 'resource_id'),
        }),
        ('Detalhes', {
            'fields': ('description', 'risk_level', 'success', 'error_message'),
        }),
        ('Solicitação HTTP', {
            'fields': ('ip_address', 'user_agent', 'request_path', 'request_method'),
            'classes': ['collapse'],
        }),
        ('Dados Alterados', {
            'fields': ('old_values', 'new_values', 'extra_data'),
            'classes': ['collapse'],
        }),
    )

    # ── Colunas coloridas ──────────────────────────────────────────────────

    _BADGE = (
        'display:inline-block;padding:2px 9px;border-radius:9999px;'
        'font-size:0.68rem;font-weight:600;letter-spacing:0.03em;'
    )

    _ACTION_STYLES = {
        'LOGIN':          'background:#dbeafe;color:#1d4ed8',
        'LOGOUT':         'background:#f1f5f9;color:#475569',
        'CREATE':         'background:#dcfce7;color:#15803d',
        'UPDATE':         'background:#fef9c3;color:#92400e',
        'DELETE':         'background:#fee2e2;color:#b91c1c',
        'VIEW':           'background:#ccfbf1;color:#0f766e',
        'EXPORT':         'background:#ede9fe;color:#6d28d9',
        'IMPORT':         'background:#e0e7ff;color:#3730a3',
        'ACCESS_DENIED':  'background:#ffedd5;color:#c2410c',
        'SECURITY_ALERT': 'background:#fce7f3;color:#9d174d',
    }

    _RISK_STYLES = {
        'LOW':      ('background:#dcfce7;color:#15803d', '🟢 Baixo'),
        'MEDIUM':   ('background:#fef9c3;color:#92400e', '🟡 Médio'),
        'HIGH':     ('background:#ffedd5;color:#c2410c', '🟠 Alto'),
        'CRITICAL': ('background:#fee2e2;color:#b91c1c', '🔴 Crítico'),
    }

    def action_display(self, obj):
        style = self._ACTION_STYLES.get(obj.action, 'background:#f1f5f9;color:#475569')
        return format_html(
            '<span style="{};{}">{}</span>',
            self._BADGE, style, obj.get_action_display(),
        )
    action_display.short_description = 'Ação'

    def description_short(self, obj):
        if not obj.description:
            return '—'
        text = obj.description
        return (text[:75] + '…') if len(text) > 75 else text
    description_short.short_description = 'Descrição'

    def user_display(self, obj):
        if obj.user:
            return format_html(
                '<a href="{}">{}</a>',
                reverse('admin:core_user_change', args=[obj.user.pk]),
                obj.user.username,
            )
        return 'Sistema'
    user_display.short_description = 'Usuário'

    def risk_level_display(self, obj):
        style, label = self._RISK_STYLES.get(
            obj.risk_level, ('background:#f1f5f9;color:#475569', obj.risk_level)
        )
        return format_html(
            '<span style="{};{}">{}</span>',
            self._BADGE, style, label,
        )
    risk_level_display.short_description = 'Risco'

    def success_display(self, obj):
        if obj.success:
            return format_html(
                '<span style="{};background:#dcfce7;color:#15803d;">✓ Sucesso</span>',
                self._BADGE,
            )
        return format_html(
            '<span style="{};background:#fee2e2;color:#b91c1c;">✗ Falha</span>',
            self._BADGE,
        )
    success_display.short_description = 'Status'

    # ── Botão "Voltar" no detalhe ────────────────────────────────────────

    def changeform_view(self, request, object_id=None, form_url='', extra_context=None):
        extra_context = extra_context or {}
        referrer = request.META.get('HTTP_REFERER', '')
        # Usa o referrer quando não é a própria página de detalhe
        if referrer and (object_id is None or f'/auditlog/{object_id}/' not in referrer):
            extra_context['auditlog_back_url'] = referrer
        else:
            extra_context['auditlog_back_url'] = '../..'
        return super().changeform_view(request, object_id, form_url, extra_context)

    # ── Permissões (somente leitura) ─────────────────────────────────────

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    def has_change_permission(self, request, obj=None):
        return False


# Customização do site admin
admin.site.site_header = "Sistema de Tintas - Administração"
admin.site.site_title = "Admin Tintas"
admin.site.index_title = "Painel Administrativo"


# ===================================
# USER PREFERENCES ADMIN
# Feature: 3-modern-web-interface  
# Task: T006 - User Preferences Model
# ===================================

@admin.register(UserPreferences)
class UserPreferencesAdmin(admin.ModelAdmin):
    """
    Admin interface for UserPreferences model.
    Provides comprehensive management of user interface preferences.
    """
    
    list_display = [
        'user', 
        'theme', 
        'density', 
        'sidebar_collapsed',
        'show_breadcrumbs',
        'high_contrast',
        'updated_at'
    ]
    
    list_filter = [
        'theme',
        'density', 
        'sidebar_collapsed',
        'show_breadcrumbs',
        'high_contrast',
        'reduce_motion',
        'created_at',
        'updated_at'
    ]
    
    search_fields = [
        'user__username',
        'user__first_name', 
        'user__last_name',
        'user__email'
    ]
    
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Informações do Usuário', {
            'fields': ('user',),
            'description': 'Conta de usuário associada a estas preferências'
        }),
        ('Preferências Visuais', {
            'fields': ('theme', 'density', 'high_contrast'),
            'description': 'Configurações de aparência e visuais'
        }),
        ('Preferências de Layout', {
            'fields': ('sidebar_collapsed', 'show_breadcrumbs'),
            'description': 'Configuração de navegação e layout'
        }),
        ('Acessibilidade', {
            'fields': ('reduce_motion',),
            'description': 'Preferências de acessibilidade e movimento'
        }),
        ('Ações Rápidas', {
            'fields': ('quick_actions',),
            'description': 'Configuração JSON para botões de ação rápida',
            'classes': ('collapse',)
        }),
        ('Registros de Data', {
            'fields': ('created_at', 'updated_at'),
            'description': 'Datas de criação e modificação',
            'classes': ('collapse',)
        }),
    )
    
    ordering = ['-updated_at']
    
    def has_delete_permission(self, request, obj=None):
        """
        Prevent deletion of UserPreferences to maintain data integrity.
        Users should only be able to modify, not delete preferences.
        """
        return False
    
    def get_queryset(self, request):
        """Optimize queries by selecting related user data"""
        return super().get_queryset(request).select_related('user')

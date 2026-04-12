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
    verbose_name = "Interface Preferences"
    verbose_name_plural = "Interface Preferences"
    
    fieldsets = (
        ('Visual Theme', {
            'fields': ('theme', 'density', 'high_contrast'),
            'classes': ('wide',)
        }),
        ('Layout', {
            'fields': ('sidebar_collapsed', 'show_breadcrumbs', 'reduce_motion'),
            'classes': ('wide',)
        }),
        ('Quick Actions', {
            'fields': ('quick_actions',),
            'classes': ('collapse', 'wide'),
            'description': 'JSON configuration for personalized quick actions'
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
        from .permissions import BusinessRole
        return BusinessRole.get_user_role(obj).value
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
        ('Metadata', {
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
        ('Timestamps', {
            'fields': ('login_time', 'last_activity', 'logout_time'),
            'classes': ['collapse']
        }),
    )
    
    def session_key_short(self, obj):
        """Display shortened session key"""
        if obj.session_key:
            return f"{obj.session_key[:8]}..."
        return "-"
    session_key_short.short_description = 'Session Key'
    
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
    """AuditLog admin interface - Read-only for compliance"""
    
    list_display = [
        'created_at', 'user_display', 'action', 'resource', 
        'risk_level_display', 'success_display', 'ip_address'
    ]
    
    list_filter = [
        'action', 'risk_level', 'success', 'created_at',
        'user__username'
    ]
    
    search_fields = [
        'user__username', 'resource', 'description', 'ip_address'
    ]
    
    readonly_fields = [
        'user', 'session', 'action', 'resource', 'resource_id', 'description',
        'risk_level', 'success', 'ip_address', 'user_agent',
        'request_path', 'request_method', 'old_values', 'new_values',
        'error_message', 'extra_data', 'created_at'
    ]
    
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('Ação', {
            'fields': ('created_at', 'user', 'session', 'action', 'resource', 'resource_id')
        }),
        ('Detalhes', {
            'fields': ('description', 'risk_level', 'success', 'error_message')
        }),
        ('Informações Técnicas', {
            'fields': ('ip_address', 'user_agent', 'request_path', 'request_method', 
                      'old_values', 'new_values', 'extra_data'),
            'classes': ['collapse']
        }),
    )
    
    def user_display(self, obj):
        """Display user with link"""
        if obj.user:
            return format_html(
                '<a href="{}">{}</a>',
                reverse('admin:core_user_change', args=[obj.user.pk]),
                obj.user.username
            )
        return 'Sistema'
    user_display.short_description = 'Usuário'
    
    def risk_level_display(self, obj):
        """Display risk level with color"""
        colors = {
            'LOW': '#28a745',      # Green
            'MEDIUM': '#ffc107',   # Yellow  
            'HIGH': '#fd7e14',     # Orange
            'CRITICAL': '#dc3545'  # Red
        }
        color = colors.get(obj.risk_level, '#6c757d')
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color,
            obj.get_risk_level_display()
        )
    risk_level_display.short_description = 'Nível de Risco'
    
    def success_display(self, obj):
        """Display success status with icon"""
        if obj.success:
            return format_html('<span style="color: green;">✓ Sucesso</span>')
        else:
            return format_html('<span style="color: red;">✗ Falha</span>')
    success_display.short_description = 'Status'
    
    def has_add_permission(self, request):
        """Audit logs cannot be manually created"""
        return False
    
    def has_delete_permission(self, request, obj=None):
        """Audit logs cannot be deleted (compliance requirement)"""
        return False
    
    def has_change_permission(self, request, obj=None):
        """Audit logs cannot be modified (compliance requirement)"""
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
        ('User Information', {
            'fields': ('user',),
            'description': 'User account associated with these preferences'
        }),
        ('Visual Preferences', {
            'fields': ('theme', 'density', 'high_contrast'),
            'description': 'Appearance and visual settings'
        }),
        ('Layout Preferences', {
            'fields': ('sidebar_collapsed', 'show_breadcrumbs'),
            'description': 'Navigation and layout configuration'
        }),
        ('Accessibility', {
            'fields': ('reduce_motion',),
            'description': 'Accessibility and motion preferences'
        }),
        ('Quick Actions', {
            'fields': ('quick_actions',),
            'description': 'JSON configuration for quick action buttons',
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'description': 'Creation and modification dates',
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

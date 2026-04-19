from django.db import models
from django.core.exceptions import ValidationError
from django.conf import settings
from django.utils import timezone
import json
import uuid

# Import managers for permission system
from .managers import (
    CustomUserManager, PermissionManager, UserGroupManager,
    PermissionAuditLogManager, GroupMembershipManager
)


class UserPreferences(models.Model):
    """
    Model to store user interface preferences for personalized experience.
    
    Feature: 3-modern-web-interface
    Task: T006 - User Preferences Model
    """
    
    # Choices for theme preference
    THEME_CHOICES = [
        ('light', 'Tema Claro'),
        ('dark', 'Tema Escuro'),
        ('auto', 'Preferência do Sistema'),
    ]
    
    # Choices for interface density
    DENSITY_CHOICES = [
        ('compact', 'Compacto (Alta densidade)'),
        ('comfortable', 'Confortável (Padrão)'),
        ('spacious', 'Espaçoso (Baixa densidade)'),
    ]
    
    # Core relationship
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name='preferences',
        help_text="Conta do usuário associada a estas preferências"
    )
    
    # Theme preferences
    theme = models.CharField(
        max_length=10,
        choices=THEME_CHOICES,
        default='light',
        help_text="Preferência de tema visual para a interface"
    )
    
    # Layout preferences
    density = models.CharField(
        max_length=15,
        choices=DENSITY_CHOICES,
        default='comfortable',
        help_text="Preferência de densidade/espaçamento da interface"
    )
    
    # Quick actions configuration (stored as JSON)
    quick_actions = models.JSONField(
        default=list,
        blank=True,
        help_text="Array JSON com configurações dos botões de ação rápida"
    )
    
    # Additional preferences for future expansion
    sidebar_collapsed = models.BooleanField(
        default=False,
        help_text="Se a barra lateral de navegação está recolhida por padrão"
    )
    
    show_breadcrumbs = models.BooleanField(
        default=True,
        help_text="Se deve exibir a navegação em trilha de migalhas"
    )
    
    # Accessibility preferences
    high_contrast = models.BooleanField(
        default=False,
        help_text="Ativar modo de alto contraste para melhor acessibilidade"
    )
    
    reduce_motion = models.BooleanField(
        default=False,
        help_text="Reduzir animações e efeitos de movimento"
    )
    
    # Timestamps
    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text="Quando estas preferências foram criadas pela primeira vez"
    )
    
    updated_at = models.DateTimeField(
        auto_now=True,
        help_text="Quando estas preferências foram modificadas pela última vez"
    )
    
    class Meta:
        verbose_name = "Preferências do Usuário"
        verbose_name_plural = "Preferências do Usuário"
        ordering = ['-updated_at']
    
    def __str__(self):
        return f"{self.user.username} - {self.theme}/{self.density}"
    
    def clean(self):
        """Validate quick_actions JSON field"""
        if self.quick_actions and not isinstance(self.quick_actions, list):
            raise ValidationError({
                'quick_actions': 'As ações rápidas devem ser uma lista de configurações'
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
    
    # Permissões específicas do sistema (legacy - mantido para compatibilidade)
    pode_vender = models.BooleanField(default=False)
    pode_gerenciar_estoque = models.BooleanField(default=False)
    pode_acessar_financeiro = models.BooleanField(default=False)
    pode_administrar = models.BooleanField(default=False)
    
    # Manager
    objects = CustomUserManager()
    
    class Meta:
        db_table = 'auth_user'
        verbose_name = 'Usuário'
        verbose_name_plural = 'Usuários'
        
    def __str__(self):
        return f"{self.username} ({self.get_full_name() or self.email})"
        
    # ========================================================================
    # MÉTODOS DO NOVO SISTEMA DE PERMISSÕES
    # ========================================================================
    
    def get_active_groups(self):
        """Retorna todos os grupos ativos do usuário"""
        return UserGroup.objects.filter(
            memberships__user=self,
            memberships__is_active=True,
            is_active=True
        ).distinct()
        
    def get_primary_group(self):
        """Retorna o grupo primário do usuário"""
        try:
            membership = self.group_memberships.get(
                is_primary=True, 
                is_active=True,
                group__is_active=True
            )
            return membership.group
        except GroupMembership.DoesNotExist:
            return None
            
    def has_permission_new(self, permission_code, check_groups=True):
        """
        Verifica se o usuário possui uma permissão específica no novo sistema
        
        Args:
            permission_code (str): Código da permissão (ex: 'tintometry.formula.create')
            check_groups (bool): Se deve verificar permissões de grupo
            
        Returns:
            bool: True se o usuário possui a permissão
        """
        from django.utils import timezone
        now = timezone.now()
        
        try:
            parts = permission_code.split('.')
            if len(parts) != 3:
                return False
            module, resource, action = parts
            
            permission = Permission.objects.get(
                module=module,
                resource=resource, 
                action=action,
                is_active=True
            )
        except Permission.DoesNotExist:
            return False
            
        # Verificar permissões diretas do usuário
        user_permission = self.user_permissions_new.filter(
            permission=permission,
            is_active=True
        ).first()
        
        if user_permission and user_permission.is_valid_now():
            return user_permission.grant_type == 'allow'
            
        # Verificar permissões de grupos se habilitado
        if check_groups:
            active_groups = self.get_active_groups()
            
            for group in active_groups:
                # Verificar permissões diretas do grupo
                group_permission = group.group_permissions.filter(
                    permission=permission,
                    is_active=True
                ).first()
                
                if group_permission:
                    return group_permission.grant_type == 'allow'
                    
                # Verificar herança hierárquica
                if self._check_inherited_permission(group, permission):
                    return True
                    
        return False
        
    def _check_inherited_permission(self, group, permission):
        """Verifica permissões herdadas de grupos pais"""
        parent = group.parent
        while parent:
            parent_permission = parent.group_permissions.filter(
                permission=permission,
                is_active=True,
                inherit_to_children=True
            ).first()
            
            if parent_permission:
                return parent_permission.grant_type == 'allow'
                
            parent = parent.parent
            
        return False
        
    def get_all_permissions_new(self):
        """Retorna todas as permissões do usuário (diretas e de grupos)"""
        permissions = set()
        
        # Permissões diretas
        user_permissions = self.user_permissions_new.filter(
            is_active=True,
            grant_type='allow'
        ).select_related('permission')
        
        for up in user_permissions:
            if up.is_valid_now():
                permissions.add(up.permission.code)
                
        # Permissões de grupos
        active_groups = self.get_active_groups()
        for group in active_groups:
            permissions.update(self._get_group_permissions(group))
            
        return list(permissions)
        
    def _get_group_permissions(self, group):
        """Retorna permissões de um grupo específico incluindo herança"""
        permissions = set()
        
        # Permissões diretas do grupo
        group_permissions = group.group_permissions.filter(
            is_active=True,
            grant_type='allow'
        ).select_related('permission')
        
        for gp in group_permissions:
            permissions.add(gp.permission.code)
            
        # Permissões herdadas
        parent = group.parent
        while parent:
            parent_permissions = parent.group_permissions.filter(
                is_active=True,
                grant_type='allow',
                inherit_to_children=True
            ).select_related('permission')
            
            for pp in parent_permissions:
                permissions.add(pp.permission.code)
                
            parent = parent.parent
            
        return permissions
        
    def add_to_group(self, group, is_primary=False, added_by=None, **kwargs):
        """Adiciona usuário a um grupo"""
        # Remove 'reason' from kwargs since GroupMembership doesn't have this field
        reason = kwargs.pop('reason', '')
        
        membership, created = GroupMembership.objects.get_or_create(
            user=self,
            group=group,
            defaults={
                'is_primary': is_primary,
                'added_by': added_by,
                **kwargs
            }
        )
        
        if created:
            # Log da ação
            PermissionAuditLog.log_action(
                action='add_to_group',
                actor=added_by or self,
                target_user=self,
                target_group=group,
                reason=reason
            )
            
        return membership
        
    def remove_from_group(self, group, removed_by=None, reason=''):
        """Remove usuário de um grupo"""
        try:
            membership = self.group_memberships.get(group=group)
            membership.is_active = False
            membership.save()
            
            # Log da ação
            PermissionAuditLog.log_action(
                action='remove_from_group',
                actor=removed_by or self,
                target_user=self,
                target_group=group,
                reason=reason
            )
            
            return True
        except GroupMembership.DoesNotExist:
            return False
            
    def grant_permission(self, permission_code, granted_by=None, **kwargs):
        """Concede uma permissão direta ao usuário"""
        try:
            permission = Permission.objects.get(
                module=permission_code.split('.')[0],
                resource=permission_code.split('.')[1],
                action=permission_code.split('.')[2],
                is_active=True
            )
        except (Permission.DoesNotExist, IndexError):
            return None
            
        # Remove 'reason' from kwargs since UserPermission has it as a field
        reason = kwargs.pop('reason', '')
        
        user_permission, created = UserPermission.objects.get_or_create(
            user=self,
            permission=permission,
            defaults={
                'granted_by': granted_by,
                'reason': reason,
                **kwargs
            }
        )
        
        if created:
            # Log da ação
            PermissionAuditLog.log_action(
                action='grant_user',
                actor=granted_by or self,
                target_user=self,
                permission=permission,
                reason=reason
            )
            
        return user_permission
        
    def revoke_permission(self, permission_code, revoked_by=None, reason=''):
        """Revoga uma permissão direta do usuário"""
        try:
            parts = permission_code.split('.')
            if len(parts) != 3:
                return False
            module, resource, action = parts
            
            permission = Permission.objects.get(
                module=module,
                resource=resource,
                action=action
            )
            user_permission = self.user_permissions_new.get(permission=permission)
            user_permission.is_active = False
            user_permission.save()
            
            # Log da ação
            PermissionAuditLog.log_action(
                action='revoke_user',
                actor=revoked_by or self,
                target_user=self,
                permission=permission,
                reason=reason
            )
            
            return True
        except (Permission.DoesNotExist, UserPermission.DoesNotExist, IndexError):
            return False
    
    # ========================================================================
    # T005: BACKWARD COMPATIBILITY AND INTEGRATION METHODS
    # ========================================================================
    
    def get_legacy_permissions(self):
        """
        Retorna as permissões legadas em formato de dicionário para compatibilidade.
        
        Returns:
            dict: Dicionário com permissões boolean legadas
        """
        return {
            'pode_vender': self.pode_vender,
            'pode_gerenciar_estoque': self.pode_gerenciar_estoque,
            'pode_acessar_financeiro': self.pode_acessar_financeiro,
            'pode_administrar': self.pode_administrar,
        }
    
    def has_legacy_permission(self, permission_name):
        """
        Verifica se o usuário possui uma permissão legada específica.
        
        Args:
            permission_name (str): Nome da permissão legada (ex: 'pode_vender')
            
        Returns:
            bool: True se possui a permissão
        """
        legacy_permissions = self.get_legacy_permissions()
        return legacy_permissions.get(permission_name, False)
    
    def has_any_permission(self, permission_code=None, legacy_name=None):
        """
        Verifica permissão tanto no novo sistema quanto no legado.
        
        Args:
            permission_code (str, optional): Código da nova permissão (ex: 'sales.order.create')
            legacy_name (str, optional): Nome da permissão legada (ex: 'pode_vender')
            
        Returns:
            bool: True se possui qualquer uma das permissões (nova ou legada)
        """
        # Verificar nova permissão primeiro
        if permission_code and self.has_permission_new(permission_code):
            return True
            
        # Fallback para permissão legada
        if legacy_name and self.has_legacy_permission(legacy_name):
            return True
            
        return False
    
    def migrate_legacy_permissions(self, migrated_by=None):
        """
        Migra as permissões boolean legadas para o novo sistema de permissões.
        
        Args:
            migrated_by (User, optional): Usuário que executou a migração
            
        Returns:
            dict: Relatório da migração com permissões criadas
        """
        migration_report = {
            'migrated_permissions': [],
            'failed_migrations': [],
            'existing_permissions': []
        }
        
        # Mapeamento de permissões legadas para novas
        legacy_mappings = {
            'pode_vender': 'sales.order.create',
            'pode_gerenciar_estoque': 'inventory.stock.manage',
            'pode_acessar_financeiro': 'financial.report.view',
            'pode_administrar': 'system.administration.manage',
        }
        
        for legacy_field, new_permission_code in legacy_mappings.items():
            # Verificar se possui a permissão legada
            if self.has_legacy_permission(legacy_field):
                # Tentar criar a nova permissão
                user_permission = self.grant_permission(
                    permission_code=new_permission_code,
                    granted_by=migrated_by,
                    reason=f'Migração automática de {legacy_field}',
                    grant_type='allow'
                )
                
                if user_permission:
                    migration_report['migrated_permissions'].append({
                        'legacy': legacy_field,
                        'new': new_permission_code,
                        'user_permission_id': str(user_permission.id)
                    })
                else:
                    # Verificar se já existe
                    if self.has_permission_new(new_permission_code):
                        migration_report['existing_permissions'].append({
                            'legacy': legacy_field,
                            'new': new_permission_code
                        })
                    else:
                        migration_report['failed_migrations'].append({
                            'legacy': legacy_field,
                            'new': new_permission_code,
                            'error': 'Failed to create permission'
                        })
        
        return migration_report
    
    def sync_legacy_permissions(self):
        """
        Sincroniza as permissões legadas com base nas novas permissões.
        Atualiza os campos boolean baseado nas permissões do novo sistema.
        """
        # Mapeamento reverso: nova permissão -> campo legado
        reverse_mappings = {
            'sales.order.create': 'pode_vender',
            'inventory.stock.manage': 'pode_gerenciar_estoque', 
            'financial.report.view': 'pode_acessar_financeiro',
            'system.administration.manage': 'pode_administrar',
        }
        
        updated_fields = []
        
        for new_permission_code, legacy_field in reverse_mappings.items():
            # Verificar se possui a nova permissão
            has_new_permission = self.has_permission_new(new_permission_code)
            
            # Sincronizar com campo legado
            current_value = getattr(self, legacy_field)
            
            if has_new_permission != current_value:
                setattr(self, legacy_field, has_new_permission)
                updated_fields.append({
                    'field': legacy_field,
                    'old_value': current_value,
                    'new_value': has_new_permission,
                    'source_permission': new_permission_code
                })
        
        # Salvar apenas se houve mudanças
        if updated_fields:
            self.save(update_fields=[item['field'] for item in updated_fields])
            
            # Log da sincronização
            PermissionAuditLog.log_action(
                action='sync_legacy',
                actor=self,
                target_user=self,
                details={
                    'updated_fields': updated_fields,
                    'sync_timestamp': timezone.now().isoformat()
                },
                reason='Sincronização automática de permissões legadas'
            )
        
        return updated_fields
    
    def get_effective_permissions(self, include_legacy=True):
        """
        Retorna todas as permissões efetivas do usuário (novas + legadas).
        
        Args:
            include_legacy (bool): Se deve incluir permissões legadas no resultado
            
        Returns:
            dict: Dicionário com permissões novas e legadas organizadas
        """
        effective_permissions = {
            'new_permissions': self.get_all_permissions_new(),
            'legacy_permissions': self.get_legacy_permissions() if include_legacy else {},
            'active_groups': [],
            'primary_group': None,
            'effective_since': timezone.now().isoformat()
        }
        
        # Adicionar informações de grupos
        active_groups = self.get_active_groups()
        for group in active_groups:
            effective_permissions['active_groups'].append({
                'id': str(group.id),
                'name': group.name,
                'full_path': group.get_full_path(),
                'is_primary': False
            })
        
        # Identificar grupo primário
        primary_group = self.get_primary_group()
        if primary_group:
            effective_permissions['primary_group'] = {
                'id': str(primary_group.id),
                'name': primary_group.name,
                'full_path': primary_group.get_full_path()
            }
            
            # Marcar grupo primário na lista de grupos ativos
            for group_info in effective_permissions['active_groups']:
                if group_info['id'] == str(primary_group.id):
                    group_info['is_primary'] = True
                    break
        
        return effective_permissions
    
    def has_module_access(self, module_name, action=None, legacy_fallback=None):
        """
        Verifica se o usuário tem acesso a um módulo específico.
        
        Args:
            module_name (str): Nome do módulo (ex: 'sales', 'inventory')
            action (str, optional): Ação específica (ex: 'create', 'view')
            legacy_fallback (str, optional): Permissão legada para fallback
            
        Returns:
            bool: True se tem acesso ao módulo
        """
        # Verificar permissões específicas primeiro
        if action:
            # Assumir recurso padrão se não especificado
            permission_patterns = [
                f'{module_name}.{action}.{action}',  # ex: sales.create.create
                f'{module_name}.any.{action}',      # ex: sales.any.create
                f'{module_name}.*.{action}',        # ex: sales.*.create
            ]
            
            for pattern in permission_patterns:
                if self.has_permission_new(pattern):
                    return True
        
        # Verificar permissões gerais do módulo
        general_patterns = [
            f'{module_name}.*.view',
            f'{module_name}.*.read', 
            f'{module_name}.*.manage',
        ]
        
        for pattern in general_patterns:
            if self.has_permission_new(pattern):
                return True
        
        # Fallback para permissão legada se especificada
        if legacy_fallback and self.has_legacy_permission(legacy_fallback):
            return True
            
        return False
    
    def get_accessible_modules(self):
        """
        Retorna lista de módulos que o usuário pode acessar.
        
        Returns:
            list: Lista de módulos acessíveis com detalhes
        """
        accessible_modules = []
        
        # Mapear permissões para módulos
        module_mappings = {
            'sales': {
                'legacy_permission': 'pode_vender',
                'display_name': 'Vendas e Pedidos',
                'icon': 'bi-cart',
                'actions': ['view', 'create', 'update', 'manage']
            },
            'inventory': {
                'legacy_permission': 'pode_gerenciar_estoque',
                'display_name': 'Controle de Estoque',
                'icon': 'bi-boxes',
                'actions': ['view', 'update', 'manage', 'count']
            },
            'financial': {
                'legacy_permission': 'pode_acessar_financeiro',
                'display_name': 'Financeiro e Relatórios',
                'icon': 'bi-graph-up',
                'actions': ['view', 'report', 'export']
            },
            'system': {
                'legacy_permission': 'pode_administrar',
                'display_name': 'Administração do Sistema',
                'icon': 'bi-gear',
                'actions': ['view', 'manage', 'configure']
            },
            'tintometry': {
                'legacy_permission': None,
                'display_name': 'Tintometria',
                'icon': 'bi-palette',
                'actions': ['view', 'mix', 'formula', 'manage']
            }
        }
        
        for module_name, module_info in module_mappings.items():
            # Verificar se tem acesso ao módulo
            has_access = False
            accessible_actions = []
            
            for action in module_info['actions']:
                if self.has_module_access(
                    module_name, 
                    action, 
                    module_info['legacy_permission']
                ):
                    has_access = True
                    accessible_actions.append(action)
            
            if has_access:
                accessible_modules.append({
                    'module': module_name,
                    'display_name': module_info['display_name'],
                    'icon': module_info['icon'],
                    'accessible_actions': accessible_actions,
                    'legacy_permission': module_info['legacy_permission'],
                    'has_legacy_access': (
                        module_info['legacy_permission'] and 
                        self.has_legacy_permission(module_info['legacy_permission'])
                    )
                })
        
        return accessible_modules


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

    class Meta:
        verbose_name = 'Perfil de Usuário'
        verbose_name_plural = 'Perfis de Usuários'


# ============================================================================
# SISTEMA DE PERMISSÕES HIERÁRQUICO
# ============================================================================

class UserGroup(TimeStampedModel):
    """
    Grupos hierárquicos de usuários para gerenciamento de permissões
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=80, unique=True, verbose_name='Nome do Grupo')
    description = models.TextField(blank=True, verbose_name='Descrição')
    
    # Hierarquia de grupos
    parent = models.ForeignKey(
        'self', 
        on_delete=models.CASCADE, 
        null=True, 
        blank=True, 
        related_name='children',
        verbose_name='Grupo Pai'
    )
    
    # Configurações
    is_active = models.BooleanField(default=True, verbose_name='Ativo')
    is_system = models.BooleanField(default=False, verbose_name='Grupo do Sistema')
    max_users = models.PositiveIntegerField(
        null=True, 
        blank=True, 
        verbose_name='Máximo de Usuários'
    )
    
    # Metadados
    created_by = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        related_name='created_groups',
        verbose_name='Criado por'
    )
    
    # Manager
    objects = UserGroupManager()
    
    class Meta:
        verbose_name = 'Grupo de Usuários'
        verbose_name_plural = 'Grupos de Usuários'
        ordering = ['name']
        
    def __str__(self):
        return self.name
        
    def get_full_path(self):
        """Retorna o caminho completo hierárquico do grupo"""
        if self.parent:
            return f"{self.parent.get_full_path()} > {self.name}"
        return self.name
        
    def get_all_children(self):
        """Retorna todos os grupos filhos recursivamente"""
        children = list(self.children.all())
        for child in self.children.all():
            children.extend(child.get_all_children())
        return children
        
    def get_user_count(self):
        """Retorna o número de usuários no grupo"""
        return self.memberships.filter(is_active=True).count()


class Permission(models.Model):
    """
    Permissões granulares do sistema com estrutura module.resource.action
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Estrutura hierárquica da permissão
    module = models.CharField(max_length=50, verbose_name='Módulo')
    resource = models.CharField(max_length=50, verbose_name='Recurso')
    action = models.CharField(max_length=50, verbose_name='Ação')
    
    # Informações da permissão
    name = models.CharField(max_length=255, verbose_name='Nome da Permissão')
    description = models.TextField(blank=True, verbose_name='Descrição')
    
    # Configurações
    is_active = models.BooleanField(default=True, verbose_name='Ativa')
    is_system = models.BooleanField(default=False, verbose_name='Permissão do Sistema')
    requires_confirmation = models.BooleanField(
        default=False, 
        verbose_name='Requer Confirmação'
    )
    
    # Metadados
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Manager
    objects = PermissionManager()
    
    class Meta:
        verbose_name = 'Permissão'
        verbose_name_plural = 'Permissões'
        unique_together = ('module', 'resource', 'action')
        ordering = ['module', 'resource', 'action']
        
    def __str__(self):
        return f"{self.module}.{self.resource}.{self.action}"
        
    @property
    def code(self):
        """Retorna o código da permissão no formato module.resource.action"""
        return f"{self.module}.{self.resource}.{self.action}"


class GroupMembership(TimeStampedModel):
    """
    Relacionamento many-to-many entre usuários e grupos com metadados
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    user = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='group_memberships',
        verbose_name='Usuário'
    )
    group = models.ForeignKey(
        UserGroup, 
        on_delete=models.CASCADE, 
        related_name='memberships',
        verbose_name='Grupo'
    )
    
    # Status da associação
    is_active = models.BooleanField(default=True, verbose_name='Ativa')
    is_primary = models.BooleanField(default=False, verbose_name='Grupo Primário')
    
    # Papel no grupo
    ROLE_CHOICES = [
        ('member', 'Membro'),
        ('admin', 'Administrador'),
        ('viewer', 'Visualizador'),
        ('editor', 'Editor')
    ]
    role = models.CharField(
        max_length=20,
        choices=ROLE_CHOICES,
        default='member',
        verbose_name='Papel no Grupo'
    )
    
    # Período de validade
    valid_from = models.DateTimeField(
        null=True, 
        blank=True, 
        verbose_name='Válido a partir de'
    )
    valid_until = models.DateTimeField(
        null=True, 
        blank=True, 
        verbose_name='Válido até'
    )
    
    # Datas importantes
    joined_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Entrou no Grupo em'
    )
    removed_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Removido do Grupo em'
    )
    
    # Metadados
    added_by = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        related_name='added_memberships',
        verbose_name='Adicionado por'
    )
    removed_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='removed_memberships',
        verbose_name='Removido por'
    )
    notes = models.TextField(blank=True, verbose_name='Observações')
    
    # Manager
    objects = GroupMembershipManager()
    
    class Meta:
        verbose_name = 'Associação ao Grupo'
        verbose_name_plural = 'Associações aos Grupos'
        unique_together = ('user', 'group')
        ordering = ['-is_primary', 'group__name']
        
    def __str__(self):
        return f"{self.user.username} -> {self.group.name}"
        
    def is_valid_now(self):
        """Verifica se a associação está válida no momento atual"""
        from django.utils import timezone
        now = timezone.now()
        
        if not self.is_active:
            return False
            
        if self.valid_from and now < self.valid_from:
            return False
            
        if self.valid_until and now > self.valid_until:
            return False
            
        return True


class UserPermission(TimeStampedModel):
    """
    Permissões diretas do usuário com suporte temporal
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    user = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='user_permissions_new',
        verbose_name='Usuário'
    )
    permission = models.ForeignKey(
        Permission, 
        on_delete=models.CASCADE, 
        related_name='user_assignments',
        verbose_name='Permissão'
    )
    
    # Tipo de permissão
    GRANT_TYPE_CHOICES = [
        ('allow', 'Permitir'),
        ('deny', 'Negar'),
    ]
    grant_type = models.CharField(
        max_length=10, 
        choices=GRANT_TYPE_CHOICES, 
        default='allow',
        verbose_name='Tipo'
    )
    
    # Status da permissão
    is_active = models.BooleanField(default=True, verbose_name='Ativa')
    is_granted = models.BooleanField(default=True, verbose_name='Concedida')
    
    # Período de validade
    valid_from = models.DateTimeField(
        null=True, 
        blank=True, 
        verbose_name='Válido a partir de'
    )
    valid_until = models.DateTimeField(
        null=True, 
        blank=True, 
        verbose_name='Válido até'
    )
    expires_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Expira em'
    )
    
    # Metadados
    granted_by = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        related_name='granted_permissions',
        verbose_name='Concedido por'
    )
    granted_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Concedido em'
    )
    revoked_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Revogado em'
    )
    revoked_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='revoked_permissions',
        verbose_name='Revogado por'
    )
    reason = models.CharField(
        max_length=255, 
        blank=True, 
        verbose_name='Justificativa'
    )
    notes = models.TextField(blank=True, verbose_name='Observações')
    
    # Delegação de permissões
    is_delegated = models.BooleanField(
        default=False,
        verbose_name='É Delegada',
        help_text='Indica se esta permissão foi delegada por outro usuário'
    )
    delegation_source_user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='delegated_permissions',
        verbose_name='Usuário que Delegou'
    )
    delegation_scope_restrictions = models.JSONField(
        null=True,
        blank=True,
        verbose_name='Restrições de Escopo da Delegação',
        help_text='Limitações de escopo para permissões delegadas'
    )
    delegation_reason = models.TextField(
        blank=True,
        verbose_name='Motivo da Delegação'
    )
    
    # Aprovação de permissões
    approval_request = models.ForeignKey(
        'PermissionApprovalRequest',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='granted_permissions',
        verbose_name='Solicitação de Aprovação'
    )
    
    class Meta:
        verbose_name = 'Permissão de Usuário'
        verbose_name_plural = 'Permissões de Usuários'
        unique_together = ('user', 'permission')
        ordering = ['user__username', 'permission__module']
        
    def __str__(self):
        return f"{self.user.username} - {self.permission.code} ({self.grant_type})"
        
    def is_valid_now(self):
        """Verifica se a permissão está válida no momento atual"""
        from django.utils import timezone
        now = timezone.now()
        
        if not self.is_active:
            return False
            
        if self.valid_from and now < self.valid_from:
            return False
            
        if self.valid_until and now > self.valid_until:
            return False
            
        return True


class GroupPermission(TimeStampedModel):
    """
    Permissões baseadas em grupo
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    group = models.ForeignKey(
        UserGroup, 
        on_delete=models.CASCADE, 
        related_name='group_permissions',
        verbose_name='Grupo'
    )
    permission = models.ForeignKey(
        Permission, 
        on_delete=models.CASCADE, 
        related_name='group_assignments',
        verbose_name='Permissão'
    )
    
    # Tipo de permissão
    GRANT_TYPE_CHOICES = [
        ('allow', 'Permitir'),
        ('deny', 'Negar'),
    ]
    grant_type = models.CharField(
        max_length=10, 
        choices=GRANT_TYPE_CHOICES, 
        default='allow',
        verbose_name='Tipo'
    )
    
    # Status da permissão
    is_active = models.BooleanField(default=True, verbose_name='Ativa')
    
    # Herança hierárquica
    inherit_to_children = models.BooleanField(
        default=True, 
        verbose_name='Herdar para Subgrupos'
    )
    
    # Metadados
    granted_by = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        related_name='granted_group_permissions',
        verbose_name='Concedido por'
    )
    reason = models.CharField(
        max_length=255, 
        blank=True, 
        verbose_name='Justificativa'
    )
    notes = models.TextField(blank=True, verbose_name='Observações')
    
    class Meta:
        verbose_name = 'Permissão de Grupo'
        verbose_name_plural = 'Permissões de Grupos'
        unique_together = ('group', 'permission')
        ordering = ['group__name', 'permission__module']
        
    def __str__(self):
        return f"{self.group.name} - {self.permission.code} ({self.grant_type})"


class PermissionAuditLog(TimeStampedModel):
    """
    Log de auditoria para todas as alterações de permissões
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Informações da ação
    ACTION_CHOICES = [
        ('grant_user', 'Conceder Permissão a Usuário'),
        ('revoke_user', 'Revogar Permissão de Usuário'),
        ('grant_group', 'Conceder Permissão a Grupo'),
        ('revoke_group', 'Revogar Permissão de Grupo'),
        ('add_to_group', 'Adicionar ao Grupo'),
        ('remove_from_group', 'Remover do Grupo'),
        ('create_group', 'Criar Grupo'),
        ('update_group', 'Atualizar Grupo'),
        ('delete_group', 'Excluir Grupo'),
        ('create_permission', 'Criar Permissão'),
        ('update_permission', 'Atualizar Permissão'),
        ('delete_permission', 'Excluir Permissão'),
    ]
    action = models.CharField(
        max_length=20, 
        choices=ACTION_CHOICES,
        verbose_name='Ação'
    )
    
    # Entidades envolvidas
    actor = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        related_name='audit_actions',
        verbose_name='Usuário que executou'
    )
    target_user = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='audit_targets',
        verbose_name='Usuário alvo'
    )
    target_group = models.ForeignKey(
        UserGroup, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='audit_targets',
        verbose_name='Grupo alvo'
    )
    permission = models.ForeignKey(
        Permission, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='audit_logs',
        verbose_name='Permissão'
    )
    
    # Detalhes da ação
    details = models.JSONField(
        default=dict, 
        blank=True, 
        verbose_name='Detalhes da Ação'
    )
    reason = models.CharField(
        max_length=255, 
        blank=True, 
        verbose_name='Justificativa'
    )
    result = models.CharField(
        max_length=20, 
        choices=[
            ('success', 'Sucesso'),
            ('failure', 'Falha'),
            ('partial', 'Parcial'),
        ],
        default='success',
        verbose_name='Resultado'
    )
    
    # Contexto técnico
    ip_address = models.GenericIPAddressField(
        null=True, 
        blank=True, 
        verbose_name='Endereço IP'
    )
    user_agent = models.TextField(blank=True, verbose_name='User Agent')
    session_key = models.CharField(
        max_length=40, 
        blank=True, 
        verbose_name='Chave de Sessão'
    )
    
    # Manager
    objects = PermissionAuditLogManager()
    
    class Meta:
        verbose_name = 'Log de Auditoria de Permissões'
        verbose_name_plural = 'Logs de Auditoria de Permissões'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['action', 'created_at']),
            models.Index(fields=['actor', 'created_at']),
            models.Index(fields=['target_user', 'created_at']),
        ]
        
    def __str__(self):
        return f"{self.action} - {self.actor} ({self.created_at})"
        
    @classmethod
    def log_action(cls, action, actor=None, target_user=None, target_group=None, 
                   permission=None, reason='', details=None, result='success', 
                   request=None, **kwargs):
        """
        Método de conveniência para registrar ações de auditoria
        """
        log_data = {
            'action': action,
            'actor': actor,
            'target_user': target_user,
            'target_group': target_group,
            'permission': permission,
            'reason': reason,
            'details': details or {},
            'result': result,
        }
        
        # Extrair informações da requisição se fornecida
        if request:
            log_data['ip_address'] = cls._get_client_ip(request)
            log_data['user_agent'] = request.META.get('HTTP_USER_AGENT', '')[:500]
            log_data['session_key'] = request.session.session_key or ''
        
        # Adicionar dados extras
        log_data.update(kwargs)
        
        return cls.objects.create(**log_data)
    
    @staticmethod
    def _get_client_ip(request):
        """Extrai o IP do cliente da requisição"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip


# ============================================================================
# T013: ENHANCED AUTHENTICATION MODELS
# ============================================================================

import hashlib
import secrets
from django.core.validators import RegexValidator


class APIKey(TimeStampedModel):
    """
    API Keys for programmatic access with advanced features.
    
    Features:
    - Secure key generation and storage
    - Scope-based permissions
    - Rate limiting support
    - Usage tracking and analytics
    - Key expiration and rotation
    """
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # User relationship
    user = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='api_keys',
        verbose_name='Usuário'
    )
    
    # Key identification
    name = models.CharField(
        max_length=100,
        verbose_name='Nome da Chave',
        help_text='Nome descritivo para identificação da chave'
    )
    description = models.TextField(
        blank=True,
        verbose_name='Descrição',
        help_text='Descrição detalhada do uso da chave'
    )
    
    # Key security
    key_prefix = models.CharField(
        max_length=8,
        verbose_name='Prefixo da Chave',
        help_text='Primeiros 8 caracteres da chave para identificação'
    )
    key_hash = models.CharField(
        max_length=64,
        unique=True,
        verbose_name='Hash da Chave',
        help_text='SHA-256 hash da chave completa'
    )
    
    # Access control
    is_active = models.BooleanField(
        default=True,
        verbose_name='Ativa'
    )
    expires_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Expira em',
        help_text='Data e hora de expiração da chave'
    )
    
    # Scope permissions (comma-separated patterns)
    scopes = models.TextField(
        blank=True,
        verbose_name='Escopos de Acesso',
        help_text='Padrões de endpoints separados por vírgula (ex: GET:/api/users/*, POST:/api/orders/*)'
    )
    
    # Rate limiting
    rate_limit_per_hour = models.PositiveIntegerField(
        null=True,
        blank=True,
        verbose_name='Limite de Requisições por Hora',
        help_text='Número máximo de requisições por hora (deixe vazio para ilimitado)'
    )
    
    # Usage tracking
    usage_count = models.PositiveIntegerField(
        default=0,
        verbose_name='Contador de Uso'
    )
    last_used_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Último Uso'
    )
    last_used_ip = models.GenericIPAddressField(
        null=True,
        blank=True,
        verbose_name='Último IP utilizado'
    )
    
    # Metadata
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_api_keys',
        verbose_name='Criado por'
    )
    
    class Meta:
        verbose_name = 'Chave de API'
        verbose_name_plural = 'Chaves de API'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['key_hash']),
            models.Index(fields=['user', 'is_active']),
            models.Index(fields=['expires_at']),
        ]
    
    def __str__(self):
        return f"{self.name} ({self.key_prefix}...)"
    
    @classmethod
    def generate_key(cls, user, name, description='', scopes='', 
                     rate_limit_per_hour=None, expires_at=None, created_by=None):
        """
        Generate a new API key with secure random generation.
        
        Returns:
            tuple: (api_key_instance, raw_key)
        """
        # Generate secure random key
        raw_key = f"ak_{secrets.token_urlsafe(32)}"
        key_prefix = raw_key[:8]
        key_hash = hashlib.sha256(raw_key.encode()).hexdigest()
        
        # Create API key instance
        api_key = cls.objects.create(
            user=user,
            name=name,
            description=description,
            key_prefix=key_prefix,
            key_hash=key_hash,
            scopes=scopes,
            rate_limit_per_hour=rate_limit_per_hour,
            expires_at=expires_at,
            created_by=created_by or user
        )
        
        return api_key, raw_key
    
    def is_expired(self):
        """Check if the API key is expired."""
        if self.expires_at:
            return timezone.now() > self.expires_at
        return False
    
    def can_access_endpoint(self, endpoint, method='GET'):
        """
        Check if this API key can access the given endpoint.
        
        Args:
            endpoint (str): API endpoint path
            method (str): HTTP method
            
        Returns:
            bool: True if access is allowed
        """
        if not self.scopes:
            return True  # No scope restrictions
        
        scope_list = [scope.strip() for scope in self.scopes.split(',')]
        
        for scope in scope_list:
            if self._scope_matches(scope, endpoint, method):
                return True
        
        return False
    
    def _scope_matches(self, scope, endpoint, method):
        """
        Check if a scope pattern matches the endpoint and method.
        
        Scope formats:
        - '*' - Full access
        - 'GET:*' - All GET requests  
        - 'POST:/api/orders/*' - POST to orders endpoints
        - '/api/users/*' - Any method to users endpoints
        """
        if scope == '*':
            return True
        
        if ':' in scope:
            scope_method, scope_pattern = scope.split(':', 1)
            if scope_method.upper() != method.upper():
                return False
        else:
            scope_pattern = scope
        
        # Simple wildcard matching
        if scope_pattern.endswith('*'):
            return endpoint.startswith(scope_pattern[:-1])
        
        return endpoint == scope_pattern
    
    def increment_usage(self, ip_address=None):
        """Increment usage counter and update last used information."""
        self.usage_count += 1
        self.last_used_at = timezone.now()
        if ip_address:
            self.last_used_ip = ip_address
        self.save(update_fields=['usage_count', 'last_used_at', 'last_used_ip'])


class APIKeyUsageLog(models.Model):
    """
    Detailed usage logging for API keys.
    """
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # API key relationship
    api_key = models.ForeignKey(
        APIKey,
        on_delete=models.CASCADE,
        related_name='usage_logs',
        verbose_name='Chave de API'
    )
    
    # Request details
    endpoint = models.CharField(
        max_length=255,
        verbose_name='Endpoint'
    )
    method = models.CharField(
        max_length=10,
        verbose_name='Método HTTP'
    )
    status_code = models.PositiveIntegerField(
        null=True,
        blank=True,
        verbose_name='Código de Status'
    )
    
    # Client information
    ip_address = models.GenericIPAddressField(
        verbose_name='Endereço IP'
    )
    user_agent = models.TextField(
        blank=True,
        verbose_name='User Agent'
    )
    
    # Timing
    timestamp = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Timestamp da Requisição'
    )
    response_time_ms = models.PositiveIntegerField(
        null=True,
        blank=True,
        verbose_name='Tempo de Resposta (ms)'
    )
    
    # Additional metadata
    request_size_bytes = models.PositiveIntegerField(
        null=True,
        blank=True,
        verbose_name='Tamanho da Requisição (bytes)'
    )
    response_size_bytes = models.PositiveIntegerField(
        null=True,
        blank=True,
        verbose_name='Tamanho da Resposta (bytes)'
    )
    
    class Meta:
        verbose_name = 'Log de Uso de API Key'
        verbose_name_plural = 'Logs de Uso de API Keys'
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['api_key', 'timestamp']),
            models.Index(fields=['timestamp']),
            models.Index(fields=['ip_address', 'timestamp']),
        ]
    
    def __str__(self):
        return f"{self.api_key.name} - {self.method} {self.endpoint}"


class LoginAttempt(TimeStampedModel):
    """
    Track login attempts for security monitoring and rate limiting.
    """
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Attempt details
    username = models.CharField(
        max_length=150,
        verbose_name='Nome de Usuário'
    )
    ip_address = models.GenericIPAddressField(
        verbose_name='Endereço IP'
    )
    user_agent = models.TextField(
        blank=True,
        verbose_name='User Agent'
    )
    
    # Result
    was_successful = models.BooleanField(
        verbose_name='Sucesso'
    )
    failure_reason = models.CharField(
        max_length=100,
        blank=True,
        verbose_name='Motivo da Falha'
    )
    
    # User reference (only for successful attempts)
    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='login_attempts',
        verbose_name='Usuário'
    )
    
    # Authentication method used
    auth_method = models.CharField(
        max_length=20,
        choices=[
            ('password', 'Senha'),
            ('api_key', 'Chave API'),
            ('jwt', 'Token JWT'),
            ('token', 'Token DRF'),
        ],
        default='password',
        verbose_name='Método de Autenticação'
    )
    
    # Additional security metadata
    session_key = models.CharField(
        max_length=40,
        blank=True,
        verbose_name='Chave da Sessão'
    )
    
    class Meta:
        verbose_name = 'Tentativa de Login'
        verbose_name_plural = 'Tentativas de Login'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['ip_address', 'created_at']),
            models.Index(fields=['username', 'created_at']),
            models.Index(fields=['was_successful', 'created_at']),
        ]
    
    def __str__(self):
        status = "Success" if self.was_successful else "Failed"
        return f"{self.username} from {self.ip_address} - {status}"
    
    @classmethod
    def log_attempt(cls, username, ip_address, was_successful, 
                    user=None, failure_reason='', auth_method='password',
                    user_agent='', session_key=''):
        """
        Log a login attempt.
        
        Args:
            username (str): Username attempted
            ip_address (str): Client IP address
            was_successful (bool): Whether login was successful
            user (User, optional): User instance if successful
            failure_reason (str): Reason for failure if unsuccessful
            auth_method (str): Authentication method used
            user_agent (str): Client user agent
            session_key (str): Session key
            
        Returns:
            LoginAttempt: Created instance
        """
        return cls.objects.create(
            username=username,
            ip_address=ip_address,
            user_agent=user_agent[:500] if user_agent else '',
            was_successful=was_successful,
            failure_reason=failure_reason,
            user=user,
            auth_method=auth_method,
            session_key=session_key
        )
    
    @classmethod
    def get_recent_failures_for_ip(cls, ip_address, minutes=15):
        """
        Get recent failed login attempts for an IP address.
        
        Args:
            ip_address (str): IP address to check
            minutes (int): Time window in minutes
            
        Returns:
            QuerySet: Recent failed attempts
        """
        from datetime import timedelta
        cutoff_time = timezone.now() - timedelta(minutes=minutes)
        
        return cls.objects.filter(
            ip_address=ip_address,
            was_successful=False,
            created_at__gte=cutoff_time
        )
    
    @classmethod
    def get_recent_failures_for_username(cls, username, minutes=15):
        """
        Get recent failed login attempts for a username.
        
        Args:
            username (str): Username to check
            minutes (int): Time window in minutes
            
        Returns:
            QuerySet: Recent failed attempts
        """
        from datetime import timedelta
        cutoff_time = timezone.now() - timedelta(minutes=minutes)
        
        return cls.objects.filter(
            username=username,
            was_successful=False,
            created_at__gte=cutoff_time
        )


class UserSession(TimeStampedModel):
    """
    Enhanced user session tracking with security features.
    """
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # User relationship
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='sessions',
        verbose_name='Usuário'
    )
    
    # Session identification
    session_key = models.CharField(
        max_length=40,
        unique=True,
        verbose_name='Chave da Sessão'
    )
    
    # Client information
    ip_address = models.GenericIPAddressField(
        verbose_name='Endereço IP'
    )
    user_agent = models.TextField(
        blank=True,
        verbose_name='User Agent'
    )
    
    # Session state
    is_active = models.BooleanField(
        default=True,
        verbose_name='Ativa'
    )
    last_activity = models.DateTimeField(
        auto_now=True,
        verbose_name='Última Atividade'
    )
    
    # Authentication method
    auth_method = models.CharField(
        max_length=20,
        choices=[
            ('password', 'Senha'),
            ('api_key', 'Chave API'),
            ('jwt', 'Token JWT'),
            ('token', 'Token DRF'),
            ('sso', 'Single Sign-On'),
        ],
        default='password',
        verbose_name='Método de Autenticação'
    )
    
    # Security flags
    requires_mfa = models.BooleanField(
        default=False,
        verbose_name='Requer MFA'
    )
    mfa_verified = models.BooleanField(
        default=False,
        verbose_name='MFA Verificado'
    )
    mfa_verified_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='MFA Verificado em'
    )
    
    # Geolocation (if available)
    country_code = models.CharField(
        max_length=2,
        blank=True,
        verbose_name='Código do País'
    )
    city = models.CharField(
        max_length=100,
        blank=True,
        verbose_name='Cidade'
    )
    
    # Session termination
    ended_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Sessão Terminada em'
    )
    end_reason = models.CharField(
        max_length=50,
        blank=True,
        choices=[
            ('logout', 'Logout Manual'),
            ('timeout', 'Timeout por Inatividade'),
            ('security', 'Terminação por Segurança'),
            ('admin', 'Terminado pelo Administrador'),
            ('password_change', 'Mudança de Senha'),
        ],
        verbose_name='Motivo do Término'
    )
    
    class Meta:
        verbose_name = 'Sessão de Usuário'
        verbose_name_plural = 'Sessões de Usuários'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'is_active']),
            models.Index(fields=['session_key']),
            models.Index(fields=['ip_address', 'created_at']),
            models.Index(fields=['last_activity']),
        ]
    
    def __str__(self):
        return f"{self.user.username} - {self.session_key[:8]}..."
    
    def is_expired(self, timeout_minutes=30):
        """
        Check if the session is expired based on inactivity.
        
        Args:
            timeout_minutes (int): Timeout in minutes
            
        Returns:
            bool: True if session is expired
        """
        from datetime import timedelta
        
        if not self.is_active:
            return True
        
        cutoff_time = timezone.now() - timedelta(minutes=timeout_minutes)
        return self.last_activity < cutoff_time
    
    def terminate(self, reason='logout', ended_by=None):
        """
        Terminate the session.
        
        Args:
            reason (str): Reason for termination
            ended_by (User, optional): User who terminated the session
        """
        self.is_active = False
        self.ended_at = timezone.now()
        self.end_reason = reason
        self.save(update_fields=['is_active', 'ended_at', 'end_reason'])
        
        # Log session termination
        PermissionAuditLog.log_action(
            action='session_terminated',
            actor=ended_by or self.user,
            target_user=self.user,
            reason=f'Session terminated: {reason}',
            details={
                'session_id': str(self.id),
                'session_key': self.session_key,
                'end_reason': reason,
                'duration_minutes': (timezone.now() - self.created_at).total_seconds() / 60
            }
        )


class MFABackupCode(TimeStampedModel):
    """
    Multi-factor authentication backup codes.
    """
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # User relationship
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='mfa_backup_codes',
        verbose_name='Usuário'
    )
    
    # Code storage
    code_hash = models.CharField(
        max_length=64,
        verbose_name='Hash do Código',
        help_text='SHA-256 hash do código de backup'
    )
    
    # Usage tracking
    is_used = models.BooleanField(
        default=False,
        verbose_name='Código Utilizado'
    )
    used_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Usado em'
    )
    used_from_ip = models.GenericIPAddressField(
        null=True,
        blank=True,
        verbose_name='Usado do IP'
    )
    
    class Meta:
        verbose_name = 'Código de Backup MFA'
        verbose_name_plural = 'Códigos de Backup MFA'
        ordering = ['created_at']
        indexes = [
            models.Index(fields=['user', 'is_used']),
            models.Index(fields=['code_hash']),
        ]
    
    def __str__(self):
        return f"Backup code for {self.user.username}"
    
    @classmethod
    def generate_codes_for_user(cls, user, count=10):
        """
        Generate backup codes for a user.
        
        Args:
            user (User): User instance
            count (int): Number of codes to generate
            
        Returns:
            list: Generated raw codes (store these securely!)
        """
        # Delete existing unused codes
        cls.objects.filter(user=user, is_used=False).delete()
        
        raw_codes = []
        backup_codes = []
        
        for _ in range(count):
            # Generate random code
            raw_code = f"{secrets.randbelow(10000):04d}-{secrets.randbelow(10000):04d}"
            code_hash = hashlib.sha256(raw_code.encode()).hexdigest()
            
            raw_codes.append(raw_code)
            backup_codes.append(cls(user=user, code_hash=code_hash))
        
        # Bulk create
        cls.objects.bulk_create(backup_codes)
        
        return raw_codes
    
    def mark_as_used(self, ip_address=None):
        """
        Mark backup code as used.
        
        Args:
            ip_address (str, optional): IP address where code was used
        """
        self.is_used = True
        self.used_at = timezone.now()
        if ip_address:
            self.used_from_ip = ip_address
        self.save(update_fields=['is_used', 'used_at', 'used_from_ip'])


class PermissionApprovalRequest(TimeStampedModel):
    """
    Solicitações de aprovação para permissões de alto risco.
    
    Feature: Permission System
    Task: T011 - User Permission Management API - Approval Workflow
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Relacionamentos principais
    requester = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='permission_requests_made',
        verbose_name='Solicitante'
    )
    target_user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='permission_requests_received',
        verbose_name='Usuário Alvo'
    )
    permission = models.ForeignKey(
        Permission,
        on_delete=models.CASCADE,
        related_name='approval_requests',
        verbose_name='Permissão'
    )
    
    # Detalhes da solicitação
    justification = models.TextField(
        verbose_name='Justificativa',
        help_text='Razão pela qual a permissão é necessária'
    )
    requested_duration_hours = models.PositiveIntegerField(
        default=24,
        verbose_name='Duração Solicitada (horas)'
    )
    
    # Status da solicitação
    STATUS_CHOICES = [
        ('pending', 'Pendente'),
        ('approved', 'Aprovado'),
        ('denied', 'Negado'),
        ('expired', 'Expirado'),
        ('cancelled', 'Cancelado')
    ]
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending',
        verbose_name='Status'
    )
    
    # Datas importantes
    request_expires_at = models.DateTimeField(
        verbose_name='Solicitação Expira em',
        help_text='Data limite para aprovação da solicitação'
    )
    completed_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Completado em'
    )
    
    # Metadados
    priority = models.CharField(
        max_length=10,
        choices=[
            ('low', 'Baixa'),
            ('normal', 'Normal'),
            ('high', 'Alta'),
            ('urgent', 'Urgente')
        ],
        default='normal',
        verbose_name='Prioridade'
    )
    
    class Meta:
        verbose_name = 'Solicitação de Aprovação de Permissão'
        verbose_name_plural = 'Solicitações de Aprovação de Permissões'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['requester', 'status', '-created_at']),
            models.Index(fields=['target_user', 'status', '-created_at']),
            models.Index(fields=['permission', 'status']),
            models.Index(fields=['status', 'request_expires_at']),
        ]
    
    def __str__(self):
        return f"Solicitação: {self.permission.code} para {self.target_user.username} ({self.status})"
    
    def is_expired(self):
        """Verifica se a solicitação está expirada"""
        return self.request_expires_at < timezone.now()
    
    def can_be_approved(self):
        """Verifica se a solicitação ainda pode ser aprovada"""
        return self.status == 'pending' and not self.is_expired()
    
    def get_pending_approvals(self):
        """Retorna aprovações pendentes para esta solicitação"""
        return self.approval_tasks.filter(status='pending')
    
    def get_required_approvals_count(self):
        """Retorna o número de aprovações necessárias"""
        if self.permission.risk_level == 'CRITICAL':
            return 2  # Críticas precisam de 2 aprovações
        elif self.permission.risk_level == 'HIGH':
            return 1  # Altas precisam de 1 aprovação
        return 0


class PermissionApprovalTask(TimeStampedModel):
    """
    Individual approval tasks within an approval request.
    """
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Relationship to approval request
    approval_request = models.ForeignKey(
        PermissionApprovalRequest,
        on_delete=models.CASCADE,
        related_name='approval_tasks',
        verbose_name='Solicitação de Aprovação'
    )
    
    # Approver
    approver = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='approval_tasks',
        verbose_name='Aprovador'
    )
    
    # Task status
    STATUS_CHOICES = [
        ('pending', 'Pendente'),
        ('approved', 'Aprovado'),
        ('denied', 'Negado'),
    ]
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending',
        verbose_name='Status'
    )
    
    # Decision details
    decision = models.CharField(
        max_length=20,
        blank=True,
        verbose_name='Decisão'
    )
    comments = models.TextField(
        blank=True,
        verbose_name='Comentários'
    )
    decided_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Decidido em'
    )
    
    class Meta:
        verbose_name = 'Tarefa de Aprovação'
        verbose_name_plural = 'Tarefas de Aprovação'
        ordering = ['-created_at']
        unique_together = ('approval_request', 'approver')
    
    def __str__(self):
        return f"{self.approver.username} - {self.approval_request}"


# ============================================================================
# ENHANCED USER MODEL EXTENSIONS FOR T013
# ============================================================================

# Add fields to User model for enhanced authentication
def extend_user_model():
    """
    Extend the User model with additional fields for enhanced authentication.
    This function adds fields dynamically to avoid migration conflicts.
    """
    # Add MFA fields
    if not hasattr(User, 'mfa_enabled'):
        User.add_to_class('mfa_enabled', models.BooleanField(
            default=False,
            verbose_name='MFA Habilitado'
        ))
    
    if not hasattr(User, 'totp_secret'):
        User.add_to_class('totp_secret', models.CharField(
            max_length=32,
            blank=True,
            verbose_name='Segredo TOTP'
        ))
    
    if not hasattr(User, 'phone_number_verified'):
        User.add_to_class('phone_number_verified', models.BooleanField(
            default=False,
            verbose_name='Telefone Verificado'
        ))
    
    if not hasattr(User, 'password_changed_at'):
        User.add_to_class('password_changed_at', models.DateTimeField(
            null=True,
            blank=True,
            verbose_name='Senha Alterada em'
        ))
    
    if not hasattr(User, 'last_activity'):
        User.add_to_class('last_activity', models.DateTimeField(
            null=True,
            blank=True,
            verbose_name='Última Atividade'
        ))
    
    # Add account security fields
    if not hasattr(User, 'account_locked_at'):
        User.add_to_class('account_locked_at', models.DateTimeField(
            null=True,
            blank=True,
            verbose_name='Conta Bloqueada em'
        ))
    
    if not hasattr(User, 'failed_login_attempts'):
        User.add_to_class('failed_login_attempts', models.PositiveIntegerField(
            default=0,
            verbose_name='Tentativas de Login Falharam'
        ))
    
    if not hasattr(User, 'security_questions_set'):
        User.add_to_class('security_questions_set', models.BooleanField(
            default=False,
            verbose_name='Perguntas de Segurança Definidas'
        ))


# Call the extension function when the module is loaded
extend_user_model()


# ============================================================================
# SIGNAL HANDLERS FOR AUTHENTICATION ENHANCEMENTS
# ============================================================================

from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver


@receiver(pre_save, sender=User)
def track_password_changes(sender, instance, **kwargs):
    """Track when user passwords are changed."""
    if instance.pk:
        try:
            old_instance = User.objects.get(pk=instance.pk)
            if old_instance.password != instance.password:
                instance.password_changed_at = timezone.now()
                instance.failed_login_attempts = 0  # Reset failed attempts on password change
        except User.DoesNotExist:
            pass


@receiver(post_save, sender=User)
def generate_mfa_backup_codes(sender, instance, created, **kwargs):
    """Generate MFA backup codes when MFA is enabled for the first time."""
    if not created and instance.mfa_enabled:
        # Check if backup codes exist
        if not MFABackupCode.objects.filter(user=instance, is_used=False).exists():
            MFABackupCode.generate_codes_for_user(instance)


# Helper classes for permissions and configurations

class Configuracao(models.Model):
    """Configurações do sistema"""
    chave = models.CharField(max_length=100, unique=True)
    valor = models.TextField()
    tipo = models.CharField(max_length=20, choices=[
        ('text', 'Texto'),
        ('number', 'Número'),
        ('boolean', 'Verdadeiro/Falso'),
        ('json', 'JSON')
    ], default='text')
    categoria = models.CharField(max_length=50, null=True, blank=True)
    descricao = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Configuração'
        verbose_name_plural = 'Configurações'
        ordering = ['categoria', 'chave']
    
    def __str__(self):
        return f"{self.chave} = {self.valor}"


# Permission Audit Log for tracking permission changes
class PermissionAuditLog(models.Model):
    actor = models.ForeignKey(User, on_delete=models.CASCADE)
    target_user = models.ForeignKey(
        User, 
        related_name='permission_audit_logs', 
        on_delete=models.CASCADE, 
        null=True, 
        blank=True
    )
    action = models.CharField(max_length=100)
    details = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'Log de Auditoria de Permissões'
        verbose_name_plural = 'Logs de Auditoria de Permissões'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['actor', '-created_at']),
            models.Index(fields=['target_user', '-created_at']),
            models.Index(fields=['action', '-created_at']),
            models.Index(fields=['created_at']),
        ]
        
    def __str__(self):
        return f"{self.action} - {self.actor} ({self.created_at.strftime('%Y-%m-%d %H:%M')})"
        
    @classmethod
    def log_action(cls, action, actor, **kwargs):
        """Método helper para criar registros de auditoria"""
        return cls.objects.create(
            action=action,
            actor=actor,
            **kwargs
        )


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
        verbose_name = 'Sessão de Usuário'
        verbose_name_plural = 'Sessões de Usuários'
    
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


class BackupRecord(TimeStampedModel):
    """
    Model to track database backup operations and audit trail
    Task: T037 - BackupRecord model for backup audit trail
    User Story 2: Data Integrity and Backup
    """
    
    # Backup types
    TYPE_FULL = 'FULL'
    TYPE_INCREMENTAL = 'INCREMENTAL'
    TYPE_DIFFERENTIAL = 'DIFFERENTIAL'
    TYPE_MANUAL = 'MANUAL'
    TYPE_EMERGENCY = 'EMERGENCY'
    
    TYPE_CHOICES = [
        (TYPE_FULL, 'Full Backup'),
        (TYPE_INCREMENTAL, 'Incremental Backup'),
        (TYPE_DIFFERENTIAL, 'Differential Backup'),
        (TYPE_MANUAL, 'Manual Backup'),
        (TYPE_EMERGENCY, 'Emergency Backup'),
    ]
    
    # Backup status
    STATUS_STARTED = 'STARTED'
    STATUS_IN_PROGRESS = 'IN_PROGRESS'
    STATUS_COMPLETED = 'COMPLETED'
    STATUS_FAILED = 'FAILED'
    STATUS_CANCELLED = 'CANCELLED'
    STATUS_CORRUPTED = 'CORRUPTED'
    
    STATUS_CHOICES = [
        (STATUS_STARTED, 'Started'),
        (STATUS_IN_PROGRESS, 'In Progress'),
        (STATUS_COMPLETED, 'Completed'),
        (STATUS_FAILED, 'Failed'),
        (STATUS_CANCELLED, 'Cancelled'),
        (STATUS_CORRUPTED, 'Corrupted'),
    ]
    
    # Core fields
    backup_type = models.CharField(
        max_length=20,
        choices=TYPE_CHOICES,
        help_text="Type of backup operation"
    )
    
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default=STATUS_STARTED,
        help_text="Current backup status"
    )
    
    # File information
    filename = models.CharField(
        max_length=255,
        help_text="Backup file name"
    )
    
    file_path = models.CharField(
        max_length=500,
        help_text="Full path to backup file"
    )
    
    file_size = models.BigIntegerField(
        null=True, blank=True,
        help_text="Backup file size in bytes"
    )
    
    checksum = models.CharField(
        max_length=64,
        null=True, blank=True,
        help_text="SHA256 checksum of backup file for integrity verification"
    )
    
    # Timing information
    started_at = models.DateTimeField(
        help_text="When backup operation started"
    )
    
    completed_at = models.DateTimeField(
        null=True, blank=True,
        help_text="When backup operation completed"
    )
    
    duration = models.DurationField(
        null=True, blank=True,
        help_text="Total backup duration"
    )
    
    # Backup details
    database_name = models.CharField(
        max_length=100,
        default='default',
        help_text="Database name that was backed up"
    )
    
    tables_included = models.JSONField(
        null=True, blank=True,
        help_text="List of tables included in backup"
    )
    
    compression_used = models.BooleanField(
        default=True,
        help_text="Whether compression was used"
    )
    
    encryption_used = models.BooleanField(
        default=False,
        help_text="Whether encryption was used"
    )
    
    # User and automation
    initiated_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='backup_records',
        help_text="User who initiated the backup (null for automated)"
    )
    
    is_automated = models.BooleanField(
        default=False,
        help_text="Whether this was an automated backup"
    )
    
    # Error handling
    error_message = models.TextField(
        null=True, blank=True,
        help_text="Error message if backup failed"
    )
    
    error_details = models.JSONField(
        null=True, blank=True,
        help_text="Detailed error information"
    )
    
    # Retention management
    retention_days = models.IntegerField(
        default=30,
        help_text="How many days to retain this backup"
    )
    
    expires_at = models.DateTimeField(
        null=True, blank=True,
        help_text="When this backup expires and can be deleted"
    )
    
    is_archived = models.BooleanField(
        default=False,
        help_text="Whether backup has been archived to long-term storage"
    )
    
    archive_location = models.CharField(
        max_length=500,
        null=True, blank=True,
        help_text="Location of archived backup"
    )
    
    # Recovery information
    last_verified = models.DateTimeField(
        null=True, blank=True,
        help_text="When backup integrity was last verified"
    )
    
    verification_result = models.BooleanField(
        null=True, blank=True,
        help_text="Result of last integrity verification"
    )
    
    restore_count = models.IntegerField(
        default=0,
        help_text="Number of times this backup has been used for restore"
    )
    
    # Metadata
    metadata = models.JSONField(
        null=True, blank=True,
        help_text="Additional backup metadata and configuration"
    )
    
    notes = models.TextField(
        null=True, blank=True,
        help_text="Administrative notes about this backup"
    )
    
    class Meta:
        ordering = ['-started_at']
        indexes = [
            models.Index(fields=['backup_type', 'started_at']),
            models.Index(fields=['status', 'started_at']),
            models.Index(fields=['database_name', 'started_at']),
            models.Index(fields=['is_automated', 'started_at']),
            models.Index(fields=['expires_at']),
        ]
        verbose_name = 'Registro de Backup'
        verbose_name_plural = 'Registros de Backup'
    
    def __str__(self):
        return f"{self.get_backup_type_display()} - {self.filename} ({self.get_status_display()})"
    
    @property
    def is_successful(self):
        """Check if backup completed successfully"""
        return self.status == self.STATUS_COMPLETED
    
    @property
    def is_expired(self):
        """Check if backup has expired"""
        if not self.expires_at:
            return False
        return timezone.now() > self.expires_at
    
    @property
    def size_formatted(self):
        """Get human-readable file size"""
        if not self.file_size:
            return "Unknown"
        
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if self.file_size < 1024.0:
                return f"{self.file_size:.1f} {unit}"
            self.file_size /= 1024.0
        return f"{self.file_size:.1f} PB"
    
    def mark_completed(self, file_size=None, checksum=None):
        """Mark backup as completed with file information"""
        from django.utils import timezone
        
        self.status = self.STATUS_COMPLETED
        self.completed_at = timezone.now()
        
        if self.started_at and self.completed_at:
            self.duration = self.completed_at - self.started_at
        
        if file_size:
            self.file_size = file_size
        
        if checksum:
            self.checksum = checksum
        
        # Set expiration date
        if self.retention_days and not self.expires_at:
            from datetime import timedelta
            self.expires_at = self.completed_at + timedelta(days=self.retention_days)
        
        self.save(update_fields=[
            'status', 'completed_at', 'duration', 'file_size', 
            'checksum', 'expires_at'
        ])
    
    def mark_failed(self, error_message, error_details=None):
        """Mark backup as failed with error information"""
        self.status = self.STATUS_FAILED
        self.completed_at = timezone.now()
        self.error_message = error_message
        
        if error_details:
            self.error_details = error_details
        
        if self.started_at and self.completed_at:
            self.duration = self.completed_at - self.started_at
        
        self.save(update_fields=[
            'status', 'completed_at', 'duration', 'error_message', 'error_details'
        ])
    
    def verify_integrity(self):
        """Verify backup file integrity using checksum"""
        import hashlib
        import os
        
        if not os.path.exists(self.file_path):
            self.verification_result = False
            self.last_verified = timezone.now()
            self.save(update_fields=['verification_result', 'last_verified'])
            return False
        
        if not self.checksum:
            # No checksum to verify against
            return None
        
        # Calculate current file checksum
        sha256_hash = hashlib.sha256()
        try:
            with open(self.file_path, "rb") as f:
                for byte_block in iter(lambda: f.read(4096), b""):
                    sha256_hash.update(byte_block)
            
            current_checksum = sha256_hash.hexdigest()
            self.verification_result = (current_checksum == self.checksum)
            self.last_verified = timezone.now()
            self.save(update_fields=['verification_result', 'last_verified'])
            
            return self.verification_result
        
        except Exception:
            self.verification_result = False
            self.last_verified = timezone.now()
            self.save(update_fields=['verification_result', 'last_verified'])
            return False
    
    @classmethod
    def create_backup_record(cls, backup_type, filename, file_path, 
                           initiated_by=None, is_automated=False, **kwargs):
        """Helper method to create new backup records"""
        return cls.objects.create(
            backup_type=backup_type,
            filename=filename,
            file_path=file_path,
            started_at=timezone.now(),
            initiated_by=initiated_by,
            is_automated=is_automated,
            **kwargs
        )
    
    @classmethod
    def get_recent_backups(cls, days=7):
        """Get backups from the last N days"""
        from datetime import timedelta
        cutoff_date = timezone.now() - timedelta(days=days)
        return cls.objects.filter(started_at__gte=cutoff_date)
    
    @classmethod
    def get_expired_backups(cls):
        """Get backups that have expired"""
        return cls.objects.filter(
            expires_at__lt=timezone.now(),
            is_archived=False
        )

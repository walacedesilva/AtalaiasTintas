"""
Serializers for user management and authentication in the paint store system.
Handles data serialization/deserialization for API endpoints.
"""

from rest_framework import serializers
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.utils import timezone
import json
import re

from .models import (
    User, UserProfile, UserSession, AuditLog, UserPreferences, BackupRecord, Configuracao,
    # Permission system models for T004
    Permission, UserGroup, UserPermission, GroupPermission, 
    PermissionAuditLog, GroupMembership
)


class UserSerializer(serializers.ModelSerializer):
    """
    Serializer for User model - public safe fields only
    """
    full_name = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'first_name', 'last_name', 'full_name',
            'cpf', 'telefone', 'data_nascimento', 'foto_perfil', 'ativo',
            'date_joined', 'last_login', 'is_active',
            # Business permissions (read-only for security)
            'pode_vender', 'pode_gerenciar_estoque', 'pode_acessar_financeiro', 'pode_administrar'
        ]
        read_only_fields = [
            'id', 'date_joined', 'last_login',
            'pode_vender', 'pode_gerenciar_estoque', 'pode_acessar_financeiro', 'pode_administrar'
        ]
    
    def get_full_name(self, obj):
        """Return user's full name"""
        return f"{obj.first_name} {obj.last_name}".strip() or obj.username


class UserProfileSerializer(serializers.ModelSerializer):
    """
    Serializer for UserProfile model
    """
    
    class Meta:
        model = UserProfile
        fields = ['cargo', 'setor', 'data_admissao', 'meta_vendas_mensal', 
                 'comissao_percentual', 'tema_sistema', 'notificacoes_email', 
                 'notificacoes_push']


class UserSessionSerializer(serializers.ModelSerializer):
    """
    Serializer for UserSession model - read only
    """
    user_name = serializers.CharField(source='user.username', read_only=True)
    
    class Meta:
        model = UserSession
        fields = [
            'id', 'user_name', 'session_key', 'ip_address', 
            'user_agent', 'is_active', 'created_at', 'last_activity'
        ]
        read_only_fields = '__all__'


class UserPreferencesSerializer(serializers.ModelSerializer):
    """
    Complete serializer for UserPreferences - includes validation
    """
    
    class Meta:
        model = UserPreferences
        fields = [
            'id', 'user', 'theme', 'density', 'quick_actions', 'sidebar_collapsed',
            'show_breadcrumbs', 'high_contrast', 'reduce_motion',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'user', 'created_at', 'updated_at']
    
    def validate_theme(self, value):
        """Validate theme choice"""
        valid_themes = ['light', 'dark', 'auto']
        if value not in valid_themes:
            raise serializers.ValidationError(f"Theme must be one of: {', '.join(valid_themes)}")
        return value
    
    def validate_density(self, value):
        """Validate density choice"""
        valid_densities = ['compact', 'comfortable', 'spacious']
        if value not in valid_densities:
            raise serializers.ValidationError(f"Density must be one of: {', '.join(valid_densities)}")
        return value
    
    def validate_quick_actions(self, value):
        """Validate quick actions list"""
        if not isinstance(value, list):
            raise serializers.ValidationError("Quick actions must be a list")
        
        # Validate structure of each action
        for action in value:
            if not isinstance(action, dict):
                raise serializers.ValidationError("Each quick action must be a dictionary")
            
            required_fields = ['action', 'label', 'icon']
            for field in required_fields:
                if field not in action:
                    raise serializers.ValidationError(f"Quick action missing required field: {field}")
                    
        return value


# ============================================================================
# PERMISSION SYSTEM SERIALIZERS - TASK T004
# ============================================================================

def validate_permission_code_format(value):
    """
    Validator para formato de código de permissão (module.resource.action)
    """
    pattern = r'^[a-z][a-z0-9_]*\.[a-z][a-z0-9_]*\.[a-z][a-z0-9_]*$'
    if not re.match(pattern, value):
        raise serializers.ValidationError(
            "Código deve seguir o formato 'module.resource.action' com letras minúsculas, "
            "números e underscores, começando sempre com letra."
        )
    return value


def validate_temporal_permission_dates(valid_from, valid_until):
    """
    Validator para dates temporais de permissões
    """
    now = timezone.now()
    
    if valid_from and valid_from < now:
        raise serializers.ValidationError({
            'valid_from': 'Data de início deve ser no futuro.'
        })
    
    if valid_until and valid_until < now:
        raise serializers.ValidationError({
            'valid_until': 'Data de término deve ser no futuro.'
        })
    
    if valid_from and valid_until and valid_from >= valid_until:
        raise serializers.ValidationError({
            'valid_until': 'Data de término deve ser posterior à data de início.'
        })


class PermissionSerializer(serializers.ModelSerializer):
    """
    Serializer para o modelo Permission com validações de formato e regras de negócio.
    
    Feature: 8-user-permissions-system
    Task: T004 - Basic Serializers and Validation
    """
    
    code = serializers.CharField(source='code', read_only=True)
    full_name = serializers.SerializerMethodField(read_only=True)
    
    class Meta:
        model = Permission
        fields = [
            'id', 'module', 'resource', 'action', 'code', 'name', 
            'description', 'full_name', 'is_active', 'is_system',
            'requires_confirmation', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'code', 'created_at', 'updated_at']
        
    def get_full_name(self, obj):
        """Retorna nome completo formatado da permissão"""
        return f"{obj.name} ({obj.code})"
    
    def validate_module(self, value):
        """Valida formato do módulo"""
        if not re.match(r'^[a-z][a-z0-9_]*$', value):
            raise serializers.ValidationError(
                "Módulo deve começar com letra minúscula e conter apenas letras, números e underscores."
            )
        return value
    
    def validate_resource(self, value):
        """Valida formato do recurso"""
        if not re.match(r'^[a-z][a-z0-9_]*$', value):
            raise serializers.ValidationError(
                "Recurso deve começar com letra minúscula e conter apenas letras, números e underscores."
            )
        return value
    
    def validate_action(self, value):
        """Valida formato da ação"""
        allowed_actions = [
            'create', 'read', 'update', 'delete', 'list', 'view',
            'manage', 'execute', 'import', 'export', 'approve', 'reject'
        ]
        
        if not re.match(r'^[a-z][a-z0-9_]*$', value):
            raise serializers.ValidationError(
                "Ação deve começar com letra minúscula e conter apenas letras, números e underscores."
            )
        
        if value not in allowed_actions:
            raise serializers.ValidationError(
                f"Ação deve ser uma das seguintes: {', '.join(allowed_actions)}"
            )
        
        return value
    
    def validate_name(self, value):
        """Valida nome da permissão"""
        if len(value.strip()) < 5:
            raise serializers.ValidationError(
                "Nome da permissão deve ter pelo menos 5 caracteres."
            )
        return value.strip()
    
    def validate(self, attrs):
        """Validação cross-field para regras de negócio"""
        # Verifica duplicação de permissão
        module = attrs.get('module')
        resource = attrs.get('resource')
        action = attrs.get('action')
        
        if module and resource and action:
            permission_exists = Permission.objects.filter(
                module=module,
                resource=resource,
                action=action
            ).exclude(pk=self.instance.pk if self.instance else None).exists()
            
            if permission_exists:
                raise serializers.ValidationError(
                    f"Permissão {module}.{resource}.{action} já existe."
                )
        
        # Validações de segurança para permissões críticas
        if action in ['delete', 'manage'] and not attrs.get('requires_confirmation'):
            attrs['requires_confirmation'] = True
        
        return attrs


class UserGroupSerializer(serializers.ModelSerializer):
    """
    Serializer para o modelo UserGroup com suporte a hierarquia e validações.
    
    Feature: 8-user-permissions-system  
    Task: T004 - Basic Serializers and Validation
    """
    
    full_path = serializers.CharField(source='get_full_path', read_only=True)
    user_count = serializers.IntegerField(source='get_user_count', read_only=True)
    children = serializers.SerializerMethodField(read_only=True)
    parent_name = serializers.CharField(source='parent.name', read_only=True)
    created_by_name = serializers.CharField(source='created_by.username', read_only=True)
    
    class Meta:
        model = UserGroup
        fields = [
            'id', 'name', 'description', 'parent', 'parent_name',
            'full_path', 'is_active', 'is_system', 'max_users', 
            'user_count', 'created_by', 'created_by_name', 'children',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'user_count', 'full_path']
        
    def get_children(self, obj):
        """Retorna grupos filhos diretos"""
        children = obj.children.filter(is_active=True)
        return [{'id': child.id, 'name': child.name, 'user_count': child.get_user_count()} 
                for child in children]
    
    def validate_name(self, value):
        """Valida nome do grupo"""
        if len(value.strip()) < 3:
            raise serializers.ValidationError(
                "Nome do grupo deve ter pelo menos 3 caracteres."
            )
        
        # Verifica caracteres especiais
        if not re.match(r'^[A-Za-z0-9\s\-_]+$', value):
            raise serializers.ValidationError(
                "Nome do grupo deve conter apenas letras, números, espaços, hífen e underscore."
            )
        
        return value.strip()
    
    def validate_max_users(self, value):
        """Valida limite máximo de usuários"""
        if value is not None and value < 1:
            raise serializers.ValidationError(
                "Limite máximo de usuários deve ser maior que zero."
            )
        return value
    
    def validate(self, attrs):
        """Validação cross-field para hierarquia e regras de negócio"""
        parent = attrs.get('parent')
        name = attrs.get('name')
        
        # Previne ciclos na hierarquia
        if parent and self.instance:
            current = parent
            while current:
                if current.pk == self.instance.pk:
                    raise serializers.ValidationError({
                        'parent': 'Não é possível criar ciclo na hierarquia de grupos.'
                    })
                current = current.parent
        
        # Verifica nome único no mesmo nível hierárquico
        if name and parent:
            sibling_exists = UserGroup.objects.filter(
                name__iexact=name,
                parent=parent
            ).exclude(pk=self.instance.pk if self.instance else None).exists()
            
            if sibling_exists:
                raise serializers.ValidationError({
                    'name': f'Já existe um grupo com nome "{name}" no mesmo nível hierárquico.'
                })
        
        # Validação de limite de usuários vs. usuários atuais
        max_users = attrs.get('max_users')
        if self.instance and max_users:
            current_users = self.instance.get_user_count()
            if current_users > max_users:
                raise serializers.ValidationError({
                    'max_users': f'Não é possível definir limite menor que o número atual de usuários ({current_users}).'
                })
        
        return attrs


class UserPermissionSerializer(serializers.ModelSerializer):
    """
    Serializer para o modelo UserPermission com validação temporal e aprovações.
    
    Feature: 8-user-permissions-system
    Task: T004 - Basic Serializers and Validation
    """
    
    user_name = serializers.CharField(source='user.username', read_only=True)
    permission_code = serializers.CharField(source='permission.code', read_only=True)
    permission_name = serializers.CharField(source='permission.name', read_only=True)
    granted_by_name = serializers.CharField(source='granted_by.username', read_only=True)
    is_currently_valid = serializers.SerializerMethodField(read_only=True)
    
    class Meta:
        model = UserPermission
        fields = [
            'id', 'user', 'user_name', 'permission', 'permission_code', 
            'permission_name', 'grant_type', 'is_active', 'valid_from', 
            'valid_until', 'is_currently_valid', 'granted_by', 'granted_by_name',
            'reason', 'notes', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
        
    def get_is_currently_valid(self, obj):
        """Verifica se a permissão está válida no momento atual"""
        return obj.is_valid_now()
    
    def validate_reason(self, value):
        """Valida justificativa obrigatória para permissões críticas"""
        if value and len(value.strip()) < 10:
            raise serializers.ValidationError(
                "Justificativa deve ter pelo menos 10 caracteres quando fornecida."
            )
        return value.strip() if value else value
    
    def validate(self, attrs):
        """Validação cross-field com regras temporais e de aprovação"""
        # Validação de datas temporais
        valid_from = attrs.get('valid_from')
        valid_until = attrs.get('valid_until')
        
        if valid_from or valid_until:
            validate_temporal_permission_dates(valid_from, valid_until)
        
        # Validação de permissões críticas
        permission = attrs.get('permission')
        reason = attrs.get('reason')
        grant_type = attrs.get('grant_type', 'allow')
        
        if permission and permission.requires_confirmation and not reason:
            raise serializers.ValidationError({
                'reason': 'Justificativa obrigatória para permissões que requerem confirmação.'
            })
        
        # Previne duplicação de permissões conflitantes
        user = attrs.get('user')
        if permission and user:
            existing = UserPermission.objects.filter(
                user=user,
                permission=permission,
                is_active=True
            ).exclude(pk=self.instance.pk if self.instance else None)
            
            if existing.exists():
                raise serializers.ValidationError(
                    'Usuário já possui esta permissão. Desative a existente antes de criar nova.'
                )
        
        # Aprovação obrigatória para permissões de 'deny'
        if grant_type == 'deny' and not attrs.get('granted_by'):
            raise serializers.ValidationError({
                'granted_by': 'Permissões de negação requerem aprovação de um superior.'
            })
            
        return attrs


class GroupPermissionSerializer(serializers.ModelSerializer):
    """
    Serializer para o modelo GroupPermission com validação de herança.
    
    Feature: 8-user-permissions-system
    Task: T004 - Basic Serializers and Validation
    """
    
    group_name = serializers.CharField(source='group.name', read_only=True)
    permission_code = serializers.CharField(source='permission.code', read_only=True)
    permission_name = serializers.CharField(source='permission.name', read_only=True)
    granted_by_name = serializers.CharField(source='granted_by.username', read_only=True)
    
    class Meta:
        model = GroupPermission
        fields = [
            'id', 'group', 'group_name', 'permission', 'permission_code',
            'permission_name', 'grant_type', 'is_active', 'inherit_to_children',
            'granted_by', 'granted_by_name', 'reason', 'notes',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
        
    def validate(self, attrs):
        """Validação de herança e conflitos hierárquicos"""
        group = attrs.get('group')
        permission = attrs.get('permission')
        inherit_to_children = attrs.get('inherit_to_children', True)
        
        # Previne duplicação de permissões no mesmo grupo
        if group and permission:
            existing = GroupPermission.objects.filter(
                group=group,
                permission=permission,
                is_active=True
            ).exclude(pk=self.instance.pk if self.instance else None)
            
            if existing.exists():
                raise serializers.ValidationError(
                    'Grupo já possui esta permissão. Desative a existente antes de criar nova.'
                )
        
        # Validação de herança hierárquica
        if group and permission and inherit_to_children:
            # Verifica se grupos pais já possuem a permissão
            parent = group.parent
            while parent:
                parent_permission = GroupPermission.objects.filter(
                    group=parent,
                    permission=permission,
                    is_active=True,
                    inherit_to_children=True
                ).first()
                
                if parent_permission:
                    raise serializers.ValidationError({
                        'inherit_to_children': 
                        f'Permissão já herdada do grupo pai "{parent.name}". '
                        'Desative herança ou revogue a permissão do grupo pai.'
                    })
                parent = parent.parent
        
        return attrs


class PermissionAuditLogSerializer(serializers.ModelSerializer):
    """
    Serializer read-only para o modelo PermissionAuditLog com filtragem de campos.
    
    Feature: 8-user-permissions-system
    Task: T004 - Basic Serializers and Validation
    """
    
    actor_name = serializers.CharField(source='actor.username', read_only=True)
    target_user_name = serializers.CharField(source='target_user.username', read_only=True)
    target_group_name = serializers.CharField(source='target_group.name', read_only=True)
    permission_code = serializers.CharField(source='permission.code', read_only=True)
    action_display = serializers.CharField(source='get_action_display', read_only=True)
    result_display = serializers.CharField(source='get_result_display', read_only=True)
    
    class Meta:
        model = PermissionAuditLog
        fields = [
            'id', 'action', 'action_display', 'actor', 'actor_name',
            'target_user', 'target_user_name', 'target_group', 'target_group_name',
            'permission', 'permission_code', 'details', 'reason', 
            'result', 'result_display', 'ip_address', 'created_at'
        ]
        read_only_fields = '__all__'  # Serializer completamente read-only
        
    def to_representation(self, instance):
        """Filtra campos sensíveis baseado no usuário atual"""
        data = super().to_representation(instance)
        
        # Remove dados técnicos sensíveis se não for admin
        request = self.context.get('request')
        if request and hasattr(request, 'user'):
            user = request.user
            if not user.is_staff:
                data.pop('ip_address', None)
                data.pop('user_agent', None)
                data.pop('session_key', None)
                
                # Filtra detalhes da ação se não envolver o usuário atual
                if (instance.actor != user and 
                    instance.target_user != user and 
                    (not instance.target_group or 
                     not instance.target_group.memberships.filter(user=user, is_active=True).exists())):
                    data.pop('details', None)
        
        return data


class GroupMembershipSerializer(serializers.ModelSerializer):
    """
    Serializer para o modelo GroupMembership para gerenciamento de associações.
    
    Feature: 8-user-permissions-system
    Task: T004 - Basic Serializers and Validation
    """
    
    user_name = serializers.CharField(source='user.username', read_only=True)
    group_name = serializers.CharField(source='group.name', read_only=True)
    added_by_name = serializers.CharField(source='added_by.username', read_only=True)
    is_currently_valid = serializers.SerializerMethodField(read_only=True)
    
    class Meta:
        model = GroupMembership
        fields = [
            'id', 'user', 'user_name', 'group', 'group_name',
            'is_active', 'is_primary', 'valid_from', 'valid_until',
            'is_currently_valid', 'added_by', 'added_by_name', 
            'notes', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
        
    def get_is_currently_valid(self, obj):
        """Verifica se a associação está válida no momento atual"""
        return obj.is_valid_now()
    
    def validate(self, attrs):
        """Validação de associações e limites"""
        user = attrs.get('user')
        group = attrs.get('group')
        is_primary = attrs.get('is_primary', False)
        
        # Validação de datas temporais
        valid_from = attrs.get('valid_from')
        valid_until = attrs.get('valid_until')
        
        if valid_from or valid_until:
            validate_temporal_permission_dates(valid_from, valid_until)
        
        # Previne múltiplas associações primárias
        if is_primary and user:
            existing_primary = GroupMembership.objects.filter(
                user=user,
                is_primary=True,
                is_active=True
            ).exclude(pk=self.instance.pk if self.instance else None)
            
            if existing_primary.exists():
                raise serializers.ValidationError({
                    'is_primary': 'Usuário já possui um grupo primário. Desative o existente primeiro.'
                })
        
        # Verifica limite de usuários no grupo
        if group and group.max_users:
            current_members = group.memberships.filter(is_active=True).count()
            
            # Se é uma nova associação
            if not self.instance and current_members >= group.max_users:
                raise serializers.ValidationError({
                    'group': 
                    f'Grupo atingiu o limite máximo de {group.max_users} usuários.'
                })
        
        # Previne duplicação de associação
        if user and group:
            existing = GroupMembership.objects.filter(
                user=user,
                group=group,
                is_active=True
            ).exclude(pk=self.instance.pk if self.instance else None)
            
            if existing.exists():
                raise serializers.ValidationError(
                    'Usuário já é membro deste grupo. Desative a associação existente primeiro.'
                )
        
        return attrs
        if len(value) > 8:  # Maximum 8 quick actions
            raise serializers.ValidationError("Maximum 8 quick actions allowed")
        
        return value
    
    def validate_default_view(self, value):
        """Validate default view choice"""
        valid_views = ['dashboard', 'sales', 'inventory', 'reports', 'clients']
        if value not in valid_views:
            raise serializers.ValidationError(f"Default view must be one of: {', '.join(valid_views)}")
        return value
    
    def validate_items_per_page(self, value):
        """Validate items per page"""
        valid_counts = [10, 25, 50, 100, 200]
        if value not in valid_counts:
            raise serializers.ValidationError(f"Items per page must be one of: {', '.join(map(str, valid_counts))}")
        return value
    
    def validate_auto_logout_time(self, value):
        """Validate auto logout time in minutes"""
        if value < 5 or value > 480:  # 5 minutes to 8 hours
            raise serializers.ValidationError("Auto logout time must be between 5 and 480 minutes")
        return value


class UserPreferencesUpdateSerializer(serializers.ModelSerializer):
    """
    Partial update serializer for UserPreferences
    """
    
    class Meta:
        model = UserPreferences
        fields = [
            'theme', 'language', 'currency', 'timezone', 'date_format', 
            'time_format', 'decimal_places', 'notifications_email', 'notifications_push',
            'notifications_sms', 'dashboard_layout', 'quick_actions', 'default_view',
            'items_per_page', 'auto_logout_time', 'show_tooltips', 'compact_mode',
            'keyboard_shortcuts'
        ]
    
    def validate_quick_actions(self, value):
        """Use parent serializer validation"""
        serializer = UserPreferencesSerializer()
        return serializer.validate_quick_actions(value)


class LoginSerializer(serializers.Serializer):
    """
    Serializer for user login
    """
    username = serializers.CharField(max_length=150, required=True)
    password = serializers.CharField(max_length=128, required=True, write_only=True)
    
    def validate_username(self, value):
        """Validate username format"""
        if not value.strip():
            raise serializers.ValidationError("Username cannot be empty.")
        return value.strip().lower()
    
    def validate_password(self, value):
        """Validate password format"""
        if not value:
            raise serializers.ValidationError("Password is required.")
        if len(value) < 3:  # Minimal validation for now
            raise serializers.ValidationError("Password too short.")
        return value


class ChangePasswordSerializer(serializers.Serializer):
    """
    Serializer for password change
    """
    old_password = serializers.CharField(max_length=128, required=True, write_only=True)
    new_password = serializers.CharField(max_length=128, required=True, write_only=True)
    confirm_password = serializers.CharField(max_length=128, required=True, write_only=True)
    
    def validate(self, data):
        """Validate password change data"""
        new_password = data.get('new_password')
        confirm_password = data.get('confirm_password')
        
        if new_password != confirm_password:
            raise serializers.ValidationError({
                'confirm_password': 'New passwords do not match.'
            })
        
        # Validate new password strength
        try:
            validate_password(new_password)
        except ValidationError as e:
            raise serializers.ValidationError({
                'new_password': list(e.messages)
            })
        
        return data


class UserCreateSerializer(serializers.ModelSerializer):
    """
    Serializer for user creation (admin only)
    """
    password = serializers.CharField(max_length=128, write_only=True)
    password_confirm = serializers.CharField(max_length=128, write_only=True)
    
    class Meta:
        model = User
        fields = [
            'username', 'email', 'first_name', 'last_name', 'cpf', 'telefone',
            'data_nascimento', 'password', 'password_confirm', 'ativo',
            'pode_vender', 'pode_gerenciar_estoque', 'pode_acessar_financeiro', 'pode_administrar'
        ]
        extra_kwargs = {
            'password': {'write_only': True},
            'password_confirm': {'write_only': True}
        }
    
    def validate_email(self, value):
        """Validate email is unique"""
        if value and User.objects.filter(email=value).exists():
            raise serializers.ValidationError("Email already in use.")
        return value
    
    def validate_cpf(self, value):
        """Validate CPF is unique if provided"""
        if value and User.objects.filter(cpf=value).exists():
            raise serializers.ValidationError("CPF already registered.")
        return value
    
    def validate(self, data):
        """Validate password confirmation"""
        password = data.get('password')
        password_confirm = data.pop('password_confirm', None)
        
        if password != password_confirm:
            raise serializers.ValidationError({
                'password_confirm': 'Passwords do not match.'
            })
        
        # Validate password strength
        try:
            validate_password(password)
        except ValidationError as e:
            raise serializers.ValidationError({
                'password': list(e.messages)
            })
        
        return data
    
    def create(self, validated_data):
        """Create user with encrypted password"""
        password = validated_data.pop('password')
        user = User.objects.create_user(password=password, **validated_data)
        
        # Create user profile
        UserProfile.objects.create(user=user)
        
        return user


class UserUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer for user updates
    """
    
    class Meta:
        model = User
        fields = [
            'first_name', 'last_name', 'email', 'cpf', 'telefone', 
            'data_nascimento', 'foto_perfil', 'ativo'
        ]
    
    def validate_email(self, value):
        """Validate email is unique (excluding current user)"""
        if value:
            existing = User.objects.filter(email=value).exclude(id=self.instance.id)
            if existing.exists():
                raise serializers.ValidationError("Email already in use.")
        return value
    
    def validate_cpf(self, value):
        """Validate CPF is unique (excluding current user)"""
        if value:
            existing = User.objects.filter(cpf=value).exclude(id=self.instance.id)
            if existing.exists():
                raise serializers.ValidationError("CPF already registered.")
        return value


class AdminUserUpdateSerializer(UserUpdateSerializer):
    """
    Serializer for admin user updates (includes permissions)
    """
    
    class Meta:
        model = User
        fields = UserUpdateSerializer.Meta.fields + [
            'pode_vender', 'pode_gerenciar_estoque', 'pode_acessar_financeiro', 'pode_administrar'
        ]


class AuditLogSerializer(serializers.ModelSerializer):
    """
    Serializer for AuditLog model (read-only)
    """
    user_name = serializers.CharField(source='user.username', read_only=True)
    action_display = serializers.CharField(source='get_action_display', read_only=True)
    risk_level_display = serializers.CharField(source='get_risk_level_display', read_only=True)
    
    class Meta:
        model = AuditLog
        fields = [
            'id', 'user_name', 'action', 'action_display', 'resource', 'resource_id',
            'description', 'risk_level', 'risk_level_display', 'success', 'error_message',
            'ip_address', 'request_path', 'request_method', 'created_at'
        ]
        read_only_fields = '__all__'


class BackupRecordSerializer(serializers.ModelSerializer):
    """
    Serializer for BackupRecord model
    """
    backup_type_display = serializers.CharField(source='get_backup_type_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    initiated_by_username = serializers.CharField(source='initiated_by.username', read_only=True)
    file_size_mb = serializers.SerializerMethodField()
    duration_display = serializers.SerializerMethodField()
    
    class Meta:
        model = BackupRecord
        fields = [
            'id', 'backup_id', 'backup_type', 'backup_type_display', 'status', 'status_display',
            'filename', 'file_path', 'file_size', 'file_size_mb', 'checksum', 'compression_type',
            'retention_days', 'initiated_by', 'initiated_by_username', 'is_automated',
            'created_at', 'started_at', 'completed_at', 'duration_seconds', 'duration_display',
            'error_message', 'error_details', 'is_archived', 'archive_location'
        ]
        read_only_fields = [
            'id', 'backup_id', 'file_size', 'checksum', 'created_at', 'started_at',
            'completed_at', 'duration_seconds', 'error_message', 'error_details'
        ]
    
    def get_file_size_mb(self, obj):
        """Return file size in MB"""
        if obj.file_size:
            return round(obj.file_size / (1024 * 1024), 2)
        return None
    
    def get_duration_display(self, obj):
        """Return human readable duration"""
        if obj.duration_seconds:
            minutes, seconds = divmod(obj.duration_seconds, 60)
            if minutes > 0:
                return f"{minutes}m {seconds}s"
            return f"{seconds}s"
        return None


class ConfiguracaoSerializer(serializers.ModelSerializer):
    """
    Serializer for Configuracao (system configuration) model
    Task: T045 - Configuration management views
    """
    tipo_display = serializers.CharField(source='get_tipo_display', read_only=True)
    valor_parsed = serializers.SerializerMethodField()
    
    class Meta:
        model = Configuracao
        fields = [
            'id', 'chave', 'valor', 'valor_parsed', 'tipo', 'tipo_display',
            'descricao', 'categoria', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_valor_parsed(self, obj):
        """Return the parsed value according to its type"""
        try:
            return obj.get_valor()
        except (ValueError, json.JSONDecodeError):
            return obj.valor
    
    def validate_valor(self, value):
        """Validate value according to its type"""
        tipo = self.initial_data.get('tipo', '')
        
        if tipo == 'integer':
            try:
                int(value)
            except (ValueError, TypeError):
                raise serializers.ValidationError("Value must be a valid integer")
        
        elif tipo == 'float':
            try:
                float(value)
            except (ValueError, TypeError):
                raise serializers.ValidationError("Value must be a valid decimal number")
        
        elif tipo == 'boolean':
            if str(value).lower() not in ['true', 'false', '1', '0', 'sim', 'não', 'yes', 'no']:
                raise serializers.ValidationError("Value must be a valid boolean (true/false)")
        
        elif tipo == 'json':
            try:
                json.loads(value)
            except json.JSONDecodeError:
                raise serializers.ValidationError("Value must be valid JSON")
        
        return value
    
    def validate_chave(self, value):
        """Validate configuration key uniqueness"""
        if self.instance:
            # Update case - exclude current instance
            if Configuracao.objects.exclude(id=self.instance.id).filter(chave=value).exists():
                raise serializers.ValidationError("Configuration key must be unique")
        else:
            # Create case
            if Configuracao.objects.filter(chave=value).exists():
                raise serializers.ValidationError("Configuration key must be unique")
        return value


class ConfiguracaoUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer for updating configuration values only
    """
    
    class Meta:
        model = Configuracao
        fields = ['valor', 'descricao']
    
    def validate_valor(self, value):
        """Validate value according to configuration type"""
        if self.instance:
            tipo = self.instance.tipo
            
            if tipo == 'integer':
                try:
                    int(value)
                except (ValueError, TypeError):
                    raise serializers.ValidationError("Value must be a valid integer")
            
            elif tipo == 'float':
                try:
                    float(value)
                except (ValueError, TypeError):
                    raise serializers.ValidationError("Value must be a valid decimal number")
            
            elif tipo == 'boolean':
                if str(value).lower() not in ['true', 'false', '1', '0', 'sim', 'não', 'yes', 'no']:
                    raise serializers.ValidationError("Value must be a valid boolean")
            
            elif tipo == 'json':
                try:
                    json.loads(value)
                except json.JSONDecodeError:
                    raise serializers.ValidationError("Value must be valid JSON")
        
        return value


# =============================================================================
# T017: ENHANCED VALIDATION SERIALIZERS
# =============================================================================

"""
T017: Enhanced validation serializers with comprehensive business rule validation.

This section extends the existing serializers with T017 validation system features:
- Advanced input validation
- Business rule enforcement
- Consistent error handling
- Field-level validation with security checks
"""

class EnhancedPermissionSerializer(PermissionSerializer):
    """
    Enhanced Permission serializer with T017 validation system.
    
    Extends the existing PermissionSerializer with advanced validation,
    security checks, and business rule enforcement.
    """
    
    def validate_code(self, value):
        """
        Enhanced permission code validation using T017 ValidationUtils.
        """
        from .exceptions import ValidationUtils, PermissionValidationError, PermissionConflictError
        
        try:
            # Use T017 validation utility for comprehensive validation
            validated_code = ValidationUtils.validate_permission_code(value)
            
            # Check for uniqueness (exclude current instance during updates)
            queryset = Permission.objects.filter(code=validated_code)
            if self.instance:
                queryset = queryset.exclude(pk=self.instance.pk)
            
            if queryset.exists():
                raise PermissionConflictError(f'Permission code "{validated_code}" already exists')
            
            return validated_code
            
        except (PermissionValidationError, PermissionConflictError) as e:
            raise serializers.ValidationError(str(e))
    
    def validate_risk_level(self, value):
        """
        Enhanced risk level validation with T017 business rules.
        """
        from .exceptions import ValidationUtils, PermissionValidationError
        
        try:
            validated_level = ValidationUtils.validate_risk_level(value)
            
            # Additional business rule: Risk level changes require authorization
            if self.instance and self.instance.risk_level != validated_level:
                request = self.context.get('request')
                if request and hasattr(request, 'user'):
                    from .exceptions import BusinessRuleValidator
                    BusinessRuleValidator.validate_risk_level_change(
                        self.instance, validated_level, request.user
                    )
            
            return validated_level
            
        except PermissionValidationError as e:
            raise serializers.ValidationError(str(e))


class EnhancedUserPermissionSerializer(UserPermissionSerializer):
    """
    Enhanced UserPermission serializer with T017 validation system.
    
    Extends existing UserPermissionSerializer with comprehensive business
    rule validation and conflict detection.
    """
    
    def validate(self, attrs):
        """
        Enhanced validation using T017 business rule validators.
        """
        # Call parent validation first
        attrs = super().validate(attrs)
        
        user = attrs.get('user') or (self.instance.user if self.instance else None)
        permission = attrs.get('permission') or (self.instance.permission if self.instance else None)
        expires_at = attrs.get('expires_at')
        is_granted = attrs.get('is_granted', True)
        
        # Enhanced validation using T017 system
        if user and permission and is_granted:
            try:
                from .exceptions import ValidationUtils
                ValidationUtils.validate_user_permission_assignment(
                    user=user, 
                    permission=permission, 
                    expires_at=expires_at
                )
            except Exception as e:
                raise serializers.ValidationError({'non_field_errors': [str(e)]})
        
        return attrs


class ValidationErrorResponseSerializer(serializers.Serializer):
    """
    T017: Serializer for consistent validation error responses.
    
    Used in API documentation to show standardized error response format.
    """
    
    error = serializers.CharField(
        help_text="Error code identifying the type of validation error"
    )
    detail = serializers.CharField(
        help_text="Human-readable description of the error"
    )
    field_errors = serializers.DictField(
        child=serializers.ListField(child=serializers.CharField()),
        required=False,
        help_text="Field-specific validation errors with detailed messages"
    )
    timestamp = serializers.DateTimeField(
        help_text="ISO timestamp when the error occurred"
    )
    request_id = serializers.CharField(
        help_text="Unique request ID for error correlation and debugging"
    )
    
    class Meta:
        ref_name = 'ValidationErrorResponse'


class RateLimitErrorResponseSerializer(serializers.Serializer):
    """
    T017: Serializer for rate limit error responses.
    
    Used in API documentation to show rate limiting error format.
    """
    
    error = serializers.CharField(
        default="rate_limit_exceeded",
        help_text="Error code for rate limiting violations"
    )
    detail = serializers.CharField(
        help_text="Description of the rate limit violation and guidance"
    )
    retry_after = serializers.IntegerField(
        help_text="Seconds to wait before retrying the request"
    )
    limit = serializers.IntegerField(
        help_text="Rate limit threshold that was exceeded"
    )
    window = serializers.IntegerField(
        help_text="Time window in seconds for the rate limit calculation"
    )
    
    class Meta:
        ref_name = 'RateLimitErrorResponse'


class BulkPermissionOperationSerializer(serializers.Serializer):
    """
    T017: Serializer for bulk permission operations with validation.
    
    Enables bulk granting/revoking permissions while maintaining
    T017 validation standards and audit trails.
    """
    
    users = serializers.ListField(
        child=serializers.IntegerField(),
        min_length=1,
        max_length=100,
        help_text="List of user IDs to update (max 100)"
    )
    permissions = serializers.ListField(
        child=serializers.IntegerField(),
        min_length=1,
        max_length=50,
        help_text="List of permission IDs to grant/revoke (max 50)"
    )
    action = serializers.ChoiceField(
        choices=[('grant', 'Grant'), ('revoke', 'Revoke')],
        help_text="Action to perform on the permissions"
    )
    expires_at = serializers.DateTimeField(
        required=False,
        help_text="Expiration date for granted permissions (grant action only)"
    )
    reason = serializers.CharField(
        max_length=500,
        required=False,
        allow_blank=True,
        help_text="Business justification for the bulk operation"
    )
    
    def validate_users(self, value):
        """
        Validate that all user IDs exist and are active using T017 validation.
        """
        from django.contrib.auth import get_user_model
        User = get_user_model()
        
        user_ids = set(value)
        existing_users = User.objects.filter(id__in=user_ids, is_active=True)
        existing_ids = set(existing_users.values_list('id', flat=True))
        
        missing_ids = user_ids - existing_ids
        if missing_ids:
            raise serializers.ValidationError(
                f'Invalid or inactive user IDs: {", ".join(map(str, sorted(missing_ids)))}'
            )
        
        return value
    
    def validate_permissions(self, value):
        """
        Validate that all permission IDs exist and are active.
        """
        permission_ids = set(value)
        existing_permissions = Permission.objects.filter(id__in=permission_ids, is_active=True)
        existing_ids = set(existing_permissions.values_list('id', flat=True))
        
        missing_ids = permission_ids - existing_ids
        if missing_ids:
            raise serializers.ValidationError(
                f'Invalid or inactive permission IDs: {", ".join(map(str, sorted(missing_ids)))}'
            )
        
        return value
    
    def validate_expires_at(self, value):
        """
        Validate expiration date using T017 business rules.
        """
        if value and value <= timezone.now():
            raise serializers.ValidationError('Expiration date must be in the future')
        
        return value
    
    def validate(self, attrs):
        """
        Cross-field validation for bulk operations with T017 business rules.
        """
        action = attrs.get('action')
        expires_at = attrs.get('expires_at')
        
        # Business rule: Expiration only applies to grant operations
        if action == 'revoke' and expires_at:
            raise serializers.ValidationError({
                'expires_at': 'Expiration date is not applicable for revoke operations'
            })
        
        # Validate that current user has permission for bulk operations
        request = self.context.get('request')
        if request and hasattr(request, 'user'):
            if not request.user.has_perm('core.bulk_manage_permissions'):
                from .exceptions import InsufficientPermissionsError
                raise serializers.ValidationError({
                    'non_field_errors': ['You do not have permission to perform bulk operations']
                })
        
        return attrs
    
    class Meta:
        ref_name = 'BulkPermissionOperation'


class HealthCheckResponseSerializer(serializers.Serializer):
    """
    T017: Serializer for health check responses.
    
    Documents the health check endpoint response format.
    """
    
    status = serializers.ChoiceField(
        choices=[('healthy', 'Healthy'), ('unhealthy', 'Unhealthy'), ('degraded', 'Degraded')],
        help_text="Overall system health status"
    )
    timestamp = serializers.DateTimeField(
        help_text="Timestamp of the health check"
    )
    version = serializers.CharField(
        help_text="Application version"
    )
    checks = serializers.DictField(
        help_text="Detailed health check results for system components"
    )
    
    class Meta:
        ref_name = 'HealthCheckResponse'
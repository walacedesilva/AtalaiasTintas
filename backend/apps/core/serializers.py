"""
Serializers for user management and authentication in the paint store system.
Handles data serialization/deserialization for API endpoints.
"""

from rest_framework import serializers
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from .models import User, UserProfile, UserSession, AuditLog, UserPreferences


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


class LoginSerializer(serializers.Serializer):
    """
    Serializer for user login authentication
    """
    username = serializers.CharField(required=True)
    password = serializers.CharField(required=True, write_only=True)
    
    def validate_username(self, value):
        """Validate username is not empty"""
        if not value.strip():
            raise serializers.ValidationError("Username cannot be empty")
        return value.strip()
    
    def validate_password(self, value):
        """Validate password is not empty"""
        if not value:
            raise serializers.ValidationError("Password cannot be empty")
        return value


class ChangePasswordSerializer(serializers.Serializer):
    """
    Serializer for password change functionality
    """
    old_password = serializers.CharField(required=True, write_only=True)
    new_password = serializers.CharField(required=True, write_only=True)
    confirm_password = serializers.CharField(required=True, write_only=True)
    
    def validate_new_password(self, value):
        """Validate new password using Django's password validators"""
        try:
            validate_password(value)
        except ValidationError as e:
            raise serializers.ValidationError(e.messages)
        return value
    
    def validate(self, attrs):
        """Validate that new passwords match"""
        if attrs['new_password'] != attrs['confirm_password']:
            raise serializers.ValidationError("New passwords do not match")
        return attrs


class UserProfileSerializer(serializers.ModelSerializer):
    """
    Serializer for UserProfile model
    """
    
    class Meta:
        model = UserProfile
        fields = [
            'cargo', 'setor', 'data_admissao', 'meta_vendas_mensal', 
            'comissao_percentual', 'tema_sistema', 'notificacoes_email', 
            'notificacoes_push', 'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']


class UserSessionSerializer(serializers.ModelSerializer):
    """
    Serializer for UserSession model - safe fields for user display
    """
    duration_minutes = serializers.SerializerMethodField()
    device_info = serializers.SerializerMethodField()
    
    class Meta:
        model = UserSession
        fields = [
            'id', 'ip_address', 'login_time', 'last_activity', 
            'logout_time', 'is_active', 'location_city', 
            'location_country', 'duration_minutes', 'device_info'
        ]
        read_only_fields = '__all__'
    
    def get_duration_minutes(self, obj):
        """Return session duration in minutes"""
        duration = obj.duration()
        return int(duration.total_seconds() / 60)
    
    def get_device_info(self, obj):
        """Return simplified device info"""
        user_agent = obj.user_agent or ''
        
        # Simple device detection
        if 'Mobile' in user_agent or 'Android' in user_agent or 'iPhone' in user_agent:
            device_type = 'Mobile'
        elif 'Tablet' in user_agent or 'iPad' in user_agent:
            device_type = 'Tablet'  
        else:
            device_type = 'Desktop'
            
        # Simple browser detection
        browser = 'Unknown'
        if 'Chrome' in user_agent:
            browser = 'Chrome'
        elif 'Firefox' in user_agent:
            browser = 'Firefox'
        elif 'Safari' in user_agent and 'Chrome' not in user_agent:
            browser = 'Safari'
        elif 'Edge' in user_agent:
            browser = 'Edge'
            
        return {
            'type': device_type,
            'browser': browser
        }


class UserPreferencesSerializer(serializers.ModelSerializer):
    """
    Serializer for UserPreferences model.
    
    Feature: 3-modern-web-interface
    Task: T007 - User Preferences API Endpoints
    """
    
    quick_actions_count = serializers.SerializerMethodField()
    
    class Meta:
        model = UserPreferences
        fields = [
            'id', 'user', 'theme', 'density', 'quick_actions',
            'sidebar_collapsed', 'show_breadcrumbs', 'high_contrast',
            'reduce_motion', 'quick_actions_count', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'user', 'created_at', 'updated_at', 'quick_actions_count']
    
    def get_quick_actions_count(self, obj):
        """Return count of configured quick actions"""
        return len(obj.quick_actions) if obj.quick_actions else 0
    
    def validate_quick_actions(self, value):
        """
        Validate quick_actions JSON structure
        """
        if value is None:
            return value
            
        if not isinstance(value, list):
            raise serializers.ValidationError("Quick actions must be a list")
        
        # Validate each quick action item
        for i, action in enumerate(value):
            if not isinstance(action, dict):
                raise serializers.ValidationError(f"Quick action {i} must be an object")
            
            required_fields = ['action', 'label', 'icon']
            for field in required_fields:
                if field not in action:
                    raise serializers.ValidationError(
                        f"Quick action {i} missing required field: {field}"
                    )
                if not isinstance(action[field], str) or not action[field].strip():
                    raise serializers.ValidationError(
                        f"Quick action {i} field '{field}' must be a non-empty string"
                    )
        
        # Limit number of quick actions
        if len(value) > 10:
            raise serializers.ValidationError("Maximum of 10 quick actions allowed")
        
        return value
    
    def validate_theme(self, value):
        """Validate theme choice"""
        valid_themes = [choice[0] for choice in UserPreferences.THEME_CHOICES]
        if value not in valid_themes:
            raise serializers.ValidationError(f"Invalid theme. Choose from: {valid_themes}")
        return value
    
    def validate_density(self, value):
        """Validate density choice"""
        valid_densities = [choice[0] for choice in UserPreferences.DENSITY_CHOICES]
        if value not in valid_densities:
            raise serializers.ValidationError(f"Invalid density. Choose from: {valid_densities}")
        return value
    
    def update(self, instance, validated_data):
        """
        Custom update to handle quick_actions merging logic
        """
        # If quick_actions is being updated and is empty, restore defaults
        if 'quick_actions' in validated_data and not validated_data['quick_actions']:
            validated_data['quick_actions'] = instance.get_default_quick_actions()
        
        return super().update(instance, validated_data)


class UserPreferencesUpdateSerializer(serializers.ModelSerializer):
    """
    Specialized serializer for partial updates to user preferences.
    Allows updating individual preference sections independently.
    """
    
    class Meta:
        model = UserPreferences
        fields = [
            'theme', 'density', 'quick_actions', 'sidebar_collapsed',
            'show_breadcrumbs', 'high_contrast', 'reduce_motion'
        ]
    
    def validate_quick_actions(self, value):
        """Reuse validation from main serializer"""
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
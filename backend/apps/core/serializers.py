"""
Serializers for user management and authentication in the paint store system.
Handles data serialization/deserialization for API endpoints.
"""

from rest_framework import serializers
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from .models import User, UserProfile, UserSession, AuditLog, UserPreferences, BackupRecord, Configuracao
import json


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
        fields = ['bio', 'avatar', 'theme_preference', 'language_preference']


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
            'id', 'user', 'theme', 'language', 'currency', 'timezone', 'date_format', 
            'time_format', 'decimal_places', 'notifications_email', 'notifications_push',
            'notifications_sms', 'dashboard_layout', 'quick_actions', 'default_view',
            'items_per_page', 'auto_logout_time', 'show_tooltips', 'compact_mode',
            'keyboard_shortcuts', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'user', 'created_at', 'updated_at']
    
    def validate_theme(self, value):
        """Validate theme choice"""
        valid_themes = ['light', 'dark', 'auto']
        if value not in valid_themes:
            raise serializers.ValidationError(f"Theme must be one of: {', '.join(valid_themes)}")
        return value
    
    def validate_language(self, value):
        """Validate language choice"""
        valid_languages = ['pt_BR', 'en_US', 'es_ES']
        if value not in valid_languages:
            raise serializers.ValidationError(f"Language must be one of: {', '.join(valid_languages)}")
        return value
    
    def validate_currency(self, value):
        """Validate currency choice"""
        valid_currencies = ['BRL', 'USD', 'EUR']
        if value not in valid_currencies:
            raise serializers.ValidationError(f"Currency must be one of: {', '.join(valid_currencies)}")
        return value
    
    def validate_timezone(self, value):
        """Validate timezone choice"""
        # Basic timezone validation - could be expanded with pytz
        valid_timezones = [
            'America/Sao_Paulo', 'America/New_York', 'Europe/London', 
            'UTC', 'America/Los_Angeles'
        ]
        if value not in valid_timezones:
            raise serializers.ValidationError(f"Timezone must be one of: {', '.join(valid_timezones)}")
        return value
    
    def validate_date_format(self, value):
        """Validate date format choice"""
        valid_formats = ['DD/MM/YYYY', 'MM/DD/YYYY', 'YYYY-MM-DD']
        if value not in valid_formats:
            raise serializers.ValidationError(f"Date format must be one of: {', '.join(valid_formats)}")
        return value
    
    def validate_time_format(self, value):
        """Validate time format choice"""
        valid_formats = ['24h', '12h']
        if value not in valid_formats:
            raise serializers.ValidationError(f"Time format must be one of: {', '.join(valid_formats)}")
        return value
    
    def validate_decimal_places(self, value):
        """Validate decimal places"""
        if value < 0 or value > 6:
            raise serializers.ValidationError("Decimal places must be between 0 and 6")
        return value
    
    def validate_dashboard_layout(self, value):
        """Validate dashboard layout choice"""
        valid_layouts = ['grid', 'list', 'cards', 'minimal']
        if value not in valid_layouts:
            raise serializers.ValidationError(f"Dashboard layout must be one of: {', '.join(valid_layouts)}")
        return value
    
    def validate_quick_actions(self, value):
        """Validate quick actions list"""
        valid_actions = [
            'new_sale', 'check_inventory', 'create_client', 'generate_report',
            'mix_paint', 'process_return', 'view_notifications', 'backup_data'
        ]
        
        if not isinstance(value, list):
            raise serializers.ValidationError("Quick actions must be a list")
        
        for action in value:
            if action not in valid_actions:
                raise serializers.ValidationError(f"Invalid quick action: {action}")
        
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
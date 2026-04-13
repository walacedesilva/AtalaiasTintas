"""
Core application views.
Authentication and user management views for the paint store system.
"""
from rest_framework import status, generics, permissions, viewsets
from rest_framework.decorators import api_view, permission_classes, action
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.authtoken.models import Token
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.db import transaction

from .models import User, UserSession, AuditLog, UserPreferences, Configuracao
from .permissions import IsAuthenticated, BusinessPermissions, BusinessRole
from .serializers import (
    UserSerializer, UserProfileSerializer, LoginSerializer,
    ChangePasswordSerializer, UserSessionSerializer, UserPreferencesSerializer,
    UserPreferencesUpdateSerializer, UserCreateSerializer, UserUpdateSerializer,
    AdminUserUpdateSerializer, ConfiguracaoSerializer, ConfiguracaoUpdateSerializer
)


class LoginView(APIView):
    """
    User login endpoint with session tracking and audit logging
    Task: T026 - Authentication views implementation
    """
    permission_classes = [permissions.AllowAny]
    
    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        if serializer.is_valid():
            username = serializer.validated_data['username']
            password = serializer.validated_data['password']
            
            user = authenticate(request, username=username, password=password)
            
            if user and user.is_active:
                # Create or get auth token
                token, created = Token.objects.get_or_create(user=user)
                
                # Create user session
                session = UserSession.objects.create(
                    user=user,
                    session_key=request.session.session_key or '',
                    ip_address=self.get_client_ip(request),
                    user_agent=request.META.get('HTTP_USER_AGENT', '')[:500],
                    is_active=True
                )
                
                # Log successful login
                AuditLog.log_action(
                    user=user,
                    action=AuditLog.ACTION_LOGIN,
                    resource='auth',
                    description=f'User {username} logged in successfully',
                    risk_level=AuditLog.RISK_LOW,
                    success=True,
                    request=request,
                    session=session
                )
                
                # Update last login
                user.last_login = timezone.now()
                user.save(update_fields=['last_login'])
                
                return Response({
                    'token': token.key,
                    'user': UserSerializer(user).data,
                    'session_id': session.id,
                    'message': 'Login successful'
                }, status=status.HTTP_200_OK)
            else:
                # Log failed login attempt
                AuditLog.log_action(
                    user=None,
                    action=AuditLog.ACTION_LOGIN,
                    resource='auth',
                    description=f'Failed login attempt for username: {username}',
                    risk_level=AuditLog.RISK_MEDIUM,
                    success=False,
                    error_message='Invalid credentials',
                    request=request
                )
                
                return Response(
                    {'error': 'Invalid credentials'}, 
                    status=status.HTTP_401_UNAUTHORIZED
                )
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def get_client_ip(self, request):
        """Extract client IP from request"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip


class LogoutView(APIView):
    """
    User logout endpoint with session cleanup
    Task: T026 - Authentication views implementation
    """
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        try:
            # Deactivate user sessions
            UserSession.objects.filter(user=request.user, is_active=True).update(is_active=False)
            
            # Delete auth token
            if hasattr(request.user, 'auth_token'):
                request.user.auth_token.delete()
            
            # Log successful logout
            AuditLog.log_action(
                user=request.user,
                action=AuditLog.ACTION_LOGOUT,
                resource='auth',
                description=f'User {request.user.username} logged out',
                risk_level=AuditLog.RISK_LOW,
                success=True,
                request=request
            )
            
            logout(request)
            
            return Response(
                {'message': 'Logout successful'}, 
                status=status.HTTP_200_OK
            )
        
        except Exception as e:
            return Response(
                {'error': f'Logout failed: {str(e)}'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class UserProfileView(APIView):
    """
    User profile view and update endpoint (current user info)
    Task: T026 - Authentication views implementation  
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """Get current user profile"""
        serializer = UserSerializer(request.user)
        return Response(serializer.data)
    
    def put(self, request):
        """Update user profile"""
        serializer = UserProfileSerializer(request.user, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            
            # Log profile update
            AuditLog.log_action(
                user=request.user,
                action=AuditLog.ACTION_UPDATE,
                resource='user_profile',
                resource_id=str(request.user.id),
                description='User profile updated',
                risk_level=AuditLog.RISK_LOW,
                success=True,
                request=request
            )
            
            return Response(UserSerializer(request.user).data)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ChangePasswordView(APIView):
    """
    Password change endpoint
    Task: T026 - Authentication views implementation
    """
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        serializer = ChangePasswordSerializer(data=request.data)
        if serializer.is_valid():
            user = request.user
            
            # Verify old password
            if not user.check_password(serializer.validated_data['old_password']):
                return Response(
                    {'old_password': 'Invalid current password'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Set new password
            user.set_password(serializer.validated_data['new_password'])
            user.save()
            
            # Invalidate all sessions except current
            UserSession.objects.filter(user=user).exclude(
                session_key=request.session.session_key
            ).update(is_active=False)
            
            # Log password change
            AuditLog.log_action(
                user=user,
                action=AuditLog.ACTION_UPDATE,
                resource='user_password',
                resource_id=str(user.id),
                description='Password changed successfully',
                risk_level=AuditLog.RISK_MEDIUM,
                success=True,
                request=request
            )
            
            return Response({'message': 'Password changed successfully'})
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class UserSessionViewSet(viewsets.ReadOnlyModelViewSet):
    """
    User session management - read only for security monitoring
    Task: T026 - Authentication views implementation
    """
    serializer_class = UserSessionSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Only return current user's sessions unless user is admin"""
        if BusinessPermissions.can_administer(self.request.user):
            return UserSession.objects.all().order_by('-created_at')
        return UserSession.objects.filter(user=self.request.user).order_by('-created_at')
    
    @action(detail=False, methods=['post'])
    def terminate_sessions(self, request):
        """Terminate all other sessions except current"""
        sessions_terminated = UserSession.objects.filter(
            user=request.user,
            is_active=True
        ).exclude(
            session_key=request.session.session_key
        ).update(is_active=False)
        
        # Log session termination
        AuditLog.log_action(
            user=request.user,
            action=AuditLog.ACTION_LOGOUT,
            resource='user_sessions',
            description=f'Terminated {sessions_terminated} active sessions',
            risk_level=AuditLog.RISK_MEDIUM,
            success=True,
            request=request
        )
        
        return Response({
            'message': f'Terminated {sessions_terminated} sessions',
            'sessions_terminated': sessions_terminated
        })


class UserPreferencesViewSet(viewsets.ModelViewSet):
    """
    User preferences management
    """
    serializer_class = UserPreferencesSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return UserPreferences.objects.filter(user=self.request.user)


class UserManagementViewSet(viewsets.ModelViewSet):
    """
    User management endpoints (admin only) - CRUD operations for users
    Tasks: T032 & T033 - User Creation and Management Views
    """
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Only admins can see all users"""
        if BusinessPermissions.can_administer(self.request.user):
            return User.objects.all().order_by('-date_joined')
        else:
            # Non-admins can only see themselves
            return User.objects.filter(id=self.request.user.id)
    
    def get_serializer_class(self):
        """Use different serializers based on action and permissions"""
        if self.action == 'create':
            return UserCreateSerializer
        elif self.action in ['update', 'partial_update']:
            if BusinessPermissions.can_administer(self.request.user):
                return AdminUserUpdateSerializer
            else:
                return UserUpdateSerializer
        return UserSerializer
    
    def create(self, request, *args, **kwargs):
        """Create new user (admin only)"""
        if not BusinessPermissions.can_administer(request.user):
            return Response(
                {'detail': 'Admin permission required to create users'}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            try:
                with transaction.atomic():
                    user = serializer.save()
                    
                    # Log user creation
                    AuditLog.log_action(
                        user=request.user,
                        action=AuditLog.ACTION_CREATE,
                        resource='user',
                        resource_id=str(user.id),
                        description=f'User {user.username} created by admin',
                        risk_level=AuditLog.RISK_HIGH,
                        success=True,
                        request=request
                    )
                    
                    headers = self.get_success_headers(serializer.data)
                    return Response(
                        UserSerializer(user).data, 
                        status=status.HTTP_201_CREATED, 
                        headers=headers
                    )
            
            except Exception as e:
                # Log creation failure
                AuditLog.log_action(
                    user=request.user,
                    action=AuditLog.ACTION_CREATE,
                    resource='user',
                    description='User creation failed',
                    risk_level=AuditLog.RISK_HIGH,
                    success=False,
                    error_message=str(e),
                    request=request
                )
                return Response(
                    {'detail': f'User creation failed: {str(e)}'}, 
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def update(self, request, *args, **kwargs):
        """Update user (admin or self)"""
        instance = self.get_object()
        
        # Check permissions
        if instance != request.user and not BusinessPermissions.can_administer(request.user):
            return Response(
                {'detail': 'Permission denied'}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        partial = kwargs.pop('partial', False)
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        
        if serializer.is_valid():
            try:
                with transaction.atomic():
                    user = serializer.save()
                    
                    # Log user update
                    AuditLog.log_action(
                        user=request.user,
                        action=AuditLog.ACTION_UPDATE,
                        resource='user',
                        resource_id=str(user.id),
                        description=f'User {user.username} updated',
                        risk_level=AuditLog.RISK_MEDIUM,
                        success=True,
                        request=request
                    )
                    
                    return Response(UserSerializer(user).data)
            
            except Exception as e:
                # Log update failure
                AuditLog.log_action(
                    user=request.user,
                    action=AuditLog.ACTION_UPDATE,
                    resource='user',
                    resource_id=str(instance.id),
                    description='User update failed',
                    risk_level=AuditLog.RISK_MEDIUM,
                    success=False,
                    error_message=str(e),
                    request=request
                )
                return Response(
                    {'detail': f'User update failed: {str(e)}'}, 
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def destroy(self, request, *args, **kwargs):
        """Deactivate user instead of deleting (admin only)"""
        if not BusinessPermissions.can_administer(request.user):
            return Response(
                {'detail': 'Admin permission required to deactivate users'}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        instance = self.get_object()
        
        # Prevent admin from deactivating themselves
        if instance == request.user:
            return Response(
                {'detail': 'Cannot deactivate your own account'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            with transaction.atomic():
                # Deactivate instead of delete
                instance.is_active = False
                instance.ativo = False
                instance.save(update_fields=['is_active', 'ativo'])
                
                # Terminate user sessions
                UserSession.objects.filter(user=instance, is_active=True).update(is_active=False)
                
                # Log user deactivation
                AuditLog.log_action(
                    user=request.user,
                    action=AuditLog.ACTION_DELETE,
                    resource='user',
                    resource_id=str(instance.id),
                    description=f'User {instance.username} deactivated',
                    risk_level=AuditLog.RISK_HIGH,
                    success=True,
                    request=request
                )
                
                return Response(
                    {'message': f'User {instance.username} deactivated successfully'}, 
                    status=status.HTTP_200_OK
                )
        
        except Exception as e:
            # Log deactivation failure
            AuditLog.log_action(
                user=request.user,
                action=AuditLog.ACTION_DELETE,
                resource='user',
                resource_id=str(instance.id),
                description='User deactivation failed',
                risk_level=AuditLog.RISK_HIGH,
                success=False,
                error_message=str(e),
                request=request
            )
            return Response(
                {'detail': f'User deactivation failed: {str(e)}'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=True, methods=['post'])
    def reset_password(self, request, pk=None):
        """Reset user password (admin only)"""
        if not BusinessPermissions.can_administer(request.user):
            return Response(
                {'detail': 'Admin permission required to reset passwords'}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        user = self.get_object()
        new_password = request.data.get('password')
        
        if not new_password:
            return Response(
                {'password': 'New password is required'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            # Validate password
            validate_password(new_password, user)
            
            with transaction.atomic():
                # Set new password
                user.set_password(new_password)
                user.save(update_fields=['password'])
                
                # Terminate all user sessions
                UserSession.objects.filter(user=user, is_active=True).update(is_active=False)
                
                # Log password reset
                AuditLog.log_action(
                    user=request.user,
                    action=AuditLog.ACTION_UPDATE,
                    resource='user_password',
                    resource_id=str(user.id),
                    description=f'Password reset for user {user.username}',
                    risk_level=AuditLog.RISK_HIGH,
                    success=True,
                    request=request
                )
                
                return Response(
                    {'message': f'Password reset successfully for {user.username}'}, 
                    status=status.HTTP_200_OK
                )
        
        except ValidationError as e:
            return Response(
                {'password': list(e.messages)}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            # Log password reset failure
            AuditLog.log_action(
                user=request.user,
                action=AuditLog.ACTION_UPDATE,
                resource='user_password',
                resource_id=str(user.id),
                description='Password reset failed',
                risk_level=AuditLog.RISK_HIGH,
                success=False,
                error_message=str(e),
                request=request
            )
            return Response(
                {'detail': f'Error resetting password: {str(e)}'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class ConfiguracaoViewSet(viewsets.ModelViewSet):
    """
    ViewSet for system configuration management
    Task: T045 - Configuration management views
    
    Provides CRUD operations for system-wide configuration settings.
    Only administrators can modify configurations.
    """
    queryset = Configuracao.objects.all().order_by('categoria', 'chave')
    serializer_class = ConfiguracaoSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Filter configurations based on user permissions"""
        queryset = super().get_queryset()
        
        # Filter by category if requested
        categoria = self.request.query_params.get('categoria')
        if categoria:
            queryset = queryset.filter(categoria=categoria)
        
        # Search by key or description
        search = self.request.query_params.get('search')
        if search:
            queryset = queryset.filter(
                models.Q(chave__icontains=search) |
                models.Q(descricao__icontains=search)
            )
        
        return queryset
    
    def get_serializer_class(self):
        """Use different serializers for different actions"""
        if self.action in ['update', 'partial_update'] and not BusinessPermissions.can_administer(self.request.user):
            # Non-admins can only update values, not structure
            return ConfiguracaoUpdateSerializer
        return ConfiguracaoSerializer
    
    def create(self, request, *args, **kwargs):
        """Create new configuration (admin only)"""
        if not BusinessPermissions.can_administer(request.user):
            return Response(
                {'detail': 'Admin permission required to create configurations'}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            try:
                with transaction.atomic():
                    config = serializer.save()
                    
                    # Log configuration creation
                    AuditLog.log_action(
                        user=request.user,
                        action=AuditLog.ACTION_CREATE,
                        resource='configuration',
                        resource_id=str(config.id),
                        description=f'Configuration created: {config.chave}',
                        risk_level=AuditLog.RISK_MEDIUM,
                        success=True,
                        request=request
                    )
                    
                    return Response(
                        ConfiguracaoSerializer(config).data, 
                        status=status.HTTP_201_CREATED
                    )
            
            except Exception as e:
                AuditLog.log_action(
                    user=request.user,
                    action=AuditLog.ACTION_CREATE,
                    resource='configuration',
                    description='Configuration creation failed',
                    risk_level=AuditLog.RISK_MEDIUM,
                    success=False,
                    error_message=str(e),
                    request=request
                )
                return Response(
                    {'detail': f'Configuration creation failed: {str(e)}'}, 
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def update(self, request, *args, **kwargs):
        """Update configuration"""
        instance = self.get_object()
        partial = kwargs.pop('partial', False)
        
        # Check permissions for full updates
        if not partial and not BusinessPermissions.can_administer(request.user):
            return Response(
                {'detail': 'Admin permission required for full configuration updates'}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        
        if serializer.is_valid():
            try:
                with transaction.atomic():
                    old_value = instance.valor
                    config = serializer.save()
                    
                    # Log configuration update
                    AuditLog.log_action(
                        user=request.user,
                        action=AuditLog.ACTION_UPDATE,
                        resource='configuration',
                        resource_id=str(config.id),
                        description=f'Configuration updated: {config.chave} ({old_value} -> {config.valor})',
                        risk_level=AuditLog.RISK_MEDIUM,
                        success=True,
                        request=request
                    )
                    
                    return Response(ConfiguracaoSerializer(config).data)
            
            except Exception as e:
                AuditLog.log_action(
                    user=request.user,
                    action=AuditLog.ACTION_UPDATE,
                    resource='configuration',
                    resource_id=str(instance.id),
                    description='Configuration update failed',
                    risk_level=AuditLog.RISK_MEDIUM,
                    success=False,
                    error_message=str(e),
                    request=request
                )
                return Response(
                    {'detail': f'Configuration update failed: {str(e)}'}, 
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def destroy(self, request, *args, **kwargs):
        """Delete configuration (admin only)"""
        if not BusinessPermissions.can_administer(request.user):
            return Response(
                {'detail': 'Admin permission required to delete configurations'}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        instance = self.get_object()
        
        try:
            with transaction.atomic():
                config_key = instance.chave
                instance.delete()
                
                # Log configuration deletion
                AuditLog.log_action(
                    user=request.user,
                    action=AuditLog.ACTION_DELETE,
                    resource='configuration',
                    resource_id=str(instance.id),
                    description=f'Configuration deleted: {config_key}',
                    risk_level=AuditLog.RISK_HIGH,
                    success=True,
                    request=request
                )
                
                return Response(
                    {'message': f'Configuration {config_key} deleted successfully'}, 
                    status=status.HTTP_200_OK
                )
        
        except Exception as e:
            AuditLog.log_action(
                user=request.user,
                action=AuditLog.ACTION_DELETE,
                resource='configuration',
                resource_id=str(instance.id),
                description='Configuration deletion failed',
                risk_level=AuditLog.RISK_HIGH,
                success=False,
                error_message=str(e),
                request=request
            )
            return Response(
                {'detail': f'Configuration deletion failed: {str(e)}'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['get'])
    def categories(self, request):
        """Get list of all configuration categories"""
        categories = Configuracao.objects.values_list('categoria', flat=True).distinct()
        categories = [cat for cat in categories if cat]  # Remove None values
        return Response({'categories': sorted(categories)})
    
    @action(detail=False, methods=['get'])
    def by_category(self, request):
        """Get configurations grouped by category"""
        result = {}
        
        # Get all categories
        categories = Configuracao.objects.values_list('categoria', flat=True).distinct()
        
        for categoria in categories:
            if categoria:  # Skip None categories
                configs = Configuracao.objects.filter(categoria=categoria).order_by('chave')
                result[categoria] = ConfiguracaoSerializer(configs, many=True).data
        
        # Add uncategorized configs
        uncategorized = Configuracao.objects.filter(categoria__isnull=True).order_by('chave')
        if uncategorized.exists():
            result['uncategorized'] = ConfiguracaoSerializer(uncategorized, many=True).data
        
        return Response(result)
    
    @action(detail=True, methods=['post'])
    def reset_to_default(self, request, pk=None):
        """Reset configuration to default value (admin only)"""
        if not BusinessPermissions.can_administer(request.user):
            return Response(
                {'detail': 'Admin permission required to reset configurations'}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        config = self.get_object()
        default_value = request.data.get('default_value')
        
        if not default_value:
            return Response(
                {'default_value': 'Default value is required'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            with transaction.atomic():
                old_value = config.valor
                config.valor = default_value
                config.save(update_fields=['valor'])
                
                # Log configuration reset
                AuditLog.log_action(
                    user=request.user,
                    action=AuditLog.ACTION_UPDATE,
                    resource='configuration',
                    resource_id=str(config.id),
                    description=f'Configuration reset: {config.chave} ({old_value} -> {default_value})',
                    risk_level=AuditLog.RISK_MEDIUM,
                    success=True,
                    request=request
                )
                
                return Response(
                    ConfiguracaoSerializer(config).data
                )
        
        except Exception as e:
            AuditLog.log_action(
                user=request.user,
                action=AuditLog.ACTION_UPDATE,
                resource='configuration',
                resource_id=str(config.id),
                description='Configuration reset failed',
                risk_level=AuditLog.RISK_MEDIUM,
                success=False,
                error_message=str(e),
                request=request
            )
            return Response(
                {'detail': f'Configuration reset failed: {str(e)}'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


# Add models import for Q queries
from django.db import models


# ================================
# Blue-Green Deployment API Endpoints
# ================================

class DeploymentStatusView(APIView):
    """
    API endpoints for blue-green deployment coordination
    Task: T060 - Deployment status API endpoints
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """Get current deployment status and environment information"""
        try:
            # Check if user has admin permissions for deployment status
            if not BusinessPermissions.can_administer(request.user):
                return Response(
                    {'detail': 'Admin permission required to view deployment status'}, 
                    status=status.HTTP_403_FORBIDDEN
                )
            
            # Get current environment from configuration or environment variable
            import os
            current_env = os.environ.get('DEPLOYMENT_ENV', 'blue')
            
            # Check service health
            from apps.monitoring.services import SystemHealthService
            health_service = SystemHealthService()
            health_status = health_service.get_overall_health()
            
            # Get deployment marker files
            project_root = os.environ.get('PROJECT_ROOT', '/opt/atalaias_tintas')
            blue_marker = os.path.join(project_root, '.deployment_blue')
            green_marker = os.path.join(project_root, '.deployment_green')
            
            deployment_status = {
                'current_environment': current_env,
                'target_environment': 'green' if current_env == 'blue' else 'blue',
                'timestamp': timezone.now().isoformat(),
                'health_status': health_status,
                'environments': {
                    'blue': {
                        'active': current_env == 'blue',
                        'deployed': os.path.exists(blue_marker),
                        'last_deployment': self._get_marker_timestamp(blue_marker) if os.path.exists(blue_marker) else None,
                        'health_endpoint': 'http://127.0.0.1:8000/health/',
                        'api_endpoint': 'http://127.0.0.1:8000/api/',
                    },
                    'green': {
                        'active': current_env == 'green',
                        'deployed': os.path.exists(green_marker),
                        'last_deployment': self._get_marker_timestamp(green_marker) if os.path.exists(green_marker) else None,
                        'health_endpoint': 'http://127.0.0.1:8002/health/',
                        'api_endpoint': 'http://127.0.0.1:8002/api/',
                    }
                },
                'deployment_history': self._get_deployment_history(),
                'can_deploy': self._can_deploy(),
                'system_info': self._get_system_info()
            }
            
            # Log deployment status check
            AuditLog.log_action(
                user=request.user,
                action=AuditLog.ACTION_VIEW,
                resource='deployment_status',
                description='Deployment status checked',
                risk_level=AuditLog.RISK_LOW,
                success=True,
                request=request
            )
            
            return Response(deployment_status)
            
        except Exception as e:
            AuditLog.log_action(
                user=request.user,
                action=AuditLog.ACTION_VIEW,
                resource='deployment_status',
                description='Deployment status check failed',
                risk_level=AuditLog.RISK_LOW,
                success=False,
                error_message=str(e),
                request=request
            )
            return Response(
                {'detail': f'Failed to get deployment status: {str(e)}'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def post(self, request):
        """Update deployment status (used by deployment scripts)"""
        try:
            # Check admin permissions
            if not BusinessPermissions.can_administer(request.user):
                return Response(
                    {'detail': 'Admin permission required to update deployment status'}, 
                    status=status.HTTP_403_FORBIDDEN
                )
            
            action = request.data.get('action')
            environment = request.data.get('environment')
            
            if not action or not environment:
                return Response(
                    {'error': 'Both action and environment are required'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            if environment not in ['blue', 'green']:
                return Response(
                    {'error': 'Environment must be either blue or green'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            valid_actions = ['start_deployment', 'complete_deployment', 'rollback', 'health_check']
            if action not in valid_actions:
                return Response(
                    {'error': f'Action must be one of: {", ".join(valid_actions)}'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Process the action
            result = self._process_deployment_action(action, environment, request.data)
            
            # Log deployment action
            AuditLog.log_action(
                user=request.user,
                action=AuditLog.ACTION_UPDATE,
                resource='deployment_status',
                description=f'Deployment action: {action} for {environment} environment',
                risk_level=AuditLog.RISK_HIGH,
                success=True,
                request=request,
                ip_address=self._get_client_ip(request)
            )
            
            return Response(result)
            
        except Exception as e:
            AuditLog.log_action(
                user=request.user,
                action=AuditLog.ACTION_UPDATE,
                resource='deployment_status',
                description=f'Deployment action failed: {str(e)}',
                risk_level=AuditLog.RISK_HIGH,
                success=False,
                error_message=str(e),
                request=request
            )
            return Response(
                {'detail': f'Deployment action failed: {str(e)}'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def _get_marker_timestamp(self, marker_path):
        """Get timestamp from deployment marker file"""
        try:
            import os
            stat = os.stat(marker_path)
            return timezone.datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc).isoformat()
        except:
            return None
    
    def _get_deployment_history(self):
        """Get recent deployment history"""
        try:
            history_file = "/var/log/tintas/deployment_history.log"
            if os.path.exists(history_file):
                with open(history_file, 'r') as f:
                    lines = f.readlines()
                    recent_deployments = []
                    for line in lines[-10:]:  # Last 10 deployments
                        parts = line.strip().split('|')
                        if len(parts) >= 4:
                            recent_deployments.append({
                                'timestamp': parts[0],
                                'environment': parts[1],
                                'deployment_id': parts[2],
                                'status': parts[3],
                                'hostname': parts[4] if len(parts) > 4 else 'unknown'
                            })
                    return recent_deployments
        except:
            pass
        return []
    
    def _can_deploy(self):
        """Check if deployment is possible"""
        try:
            # Check if there are any ongoing deployments
            from django.core.cache import cache
            ongoing_deployment = cache.get('deployment_in_progress')
            
            if ongoing_deployment:
                return {
                    'can_deploy': False,
                    'reason': 'Deployment already in progress',
                    'started_by': ongoing_deployment.get('user'),
                    'started_at': ongoing_deployment.get('timestamp')
                }
            
            # Check system health
            from apps.monitoring.services import SystemHealthService
            health_service = SystemHealthService()
            health_status = health_service.get_overall_health()
            
            if health_status.get('status') == 'critical':
                return {
                    'can_deploy': False,
                    'reason': 'System health is critical',
                    'health_issues': health_status.get('issues', [])
                }
            
            return {
                'can_deploy': True,
                'reason': 'System is ready for deployment'
            }
            
        except Exception as e:
            return {
                'can_deploy': False,
                'reason': f'Unable to determine deployment readiness: {str(e)}'
            }
    
    def _get_system_info(self):
        """Get basic system information"""
        try:
            import platform
            import sys
            
            return {
                'hostname': platform.node(),
                'platform': platform.platform(),
                'python_version': sys.version,
                'django_version': '6.0.4',
                'uptime': self._get_uptime(),
                'load_average': self._get_load_average()
            }
        except:
            return {}
    
    def _get_uptime(self):
        """Get system uptime"""
        try:
            with open('/proc/uptime', 'r') as f:
                uptime_seconds = float(f.readline().split()[0])
                return int(uptime_seconds)
        except:
            return None
    
    def _get_load_average(self):
        """Get system load average"""
        try:
            import os
            return list(os.getloadavg())
        except:
            return None
    
    def _process_deployment_action(self, action, environment, data):
        """Process deployment actions"""
        from django.core.cache import cache
        
        if action == 'start_deployment':
            # Set deployment in progress flag
            cache.set('deployment_in_progress', {
                'environment': environment,
                'user': self.request.user.username,
                'timestamp': timezone.now().isoformat()
            }, timeout=3600)  # 1 hour timeout
            
            return {
                'status': 'deployment_started',
                'environment': environment,
                'message': f'Deployment to {environment} environment started'
            }
        
        elif action == 'complete_deployment':
            # Clear deployment in progress flag
            cache.delete('deployment_in_progress')
            
            # Update current environment
            os.environ['DEPLOYMENT_ENV'] = environment
            
            return {
                'status': 'deployment_completed',
                'environment': environment,
                'message': f'Deployment to {environment} environment completed'
            }
        
        elif action == 'rollback':
            # Clear deployment in progress flag
            cache.delete('deployment_in_progress')
            
            # Rollback to previous environment
            previous_env = 'blue' if environment == 'green' else 'green'
            os.environ['DEPLOYMENT_ENV'] = previous_env
            
            return {
                'status': 'rollback_completed',
                'environment': previous_env,
                'message': f'Rollback to {previous_env} environment completed'
            }
        
        elif action == 'health_check':
            # Perform health check on specified environment
            health_url = f'http://127.0.0.1:{"8000" if environment == "blue" else "8002"}/health/'
            
            try:
                import requests
                response = requests.get(health_url, timeout=10)
                
                return {
                    'status': 'health_check_completed',
                    'environment': environment,
                    'healthy': response.status_code == 200,
                    'response_time': response.elapsed.total_seconds() * 1000,
                    'message': f'Health check for {environment} environment completed'
                }
            except requests.exceptions.RequestException as e:
                return {
                    'status': 'health_check_failed',
                    'environment': environment,
                    'healthy': False,
                    'error': str(e),
                    'message': f'Health check for {environment} environment failed'
                }
    
    def _get_client_ip(self, request):
        """Get client IP address"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip


class DeploymentHealthView(APIView):
    """
    Health check endpoint specifically for deployment coordination
    """
    permission_classes = [permissions.AllowAny]  # Allow load balancer health checks
    
    def get(self, request):
        """Perform health check for deployment coordination"""
        try:
            # Quick health check for deployment purposes
            from django.db import connection
            from django.core.cache import cache
            
            # Test database connection
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
                cursor.fetchone()
            
            # Test cache connection
            cache.set('deployment_health_check', 'ok', timeout=60)
            cache_result = cache.get('deployment_health_check')
            
            if cache_result != 'ok':
                raise Exception("Cache test failed")
            
            # Get current environment
            import os
            current_env = os.environ.get('DEPLOYMENT_ENV', 'blue')
            
            return Response({
                'status': 'healthy',
                'environment': current_env,
                'timestamp': timezone.now().isoformat(),
                'checks': {
                    'database': 'ok',
                    'cache': 'ok',
                    'application': 'ok'
                }
            })
            
        except Exception as e:
            return Response({
                'status': 'unhealthy',
                'environment': os.environ.get('DEPLOYMENT_ENV', 'unknown'),
                'timestamp': timezone.now().isoformat(),
                'error': str(e),
                'checks': {
                    'database': 'error' if 'database' in str(e).lower() else 'unknown',
                    'cache': 'error' if 'cache' in str(e).lower() else 'unknown',
                    'application': 'error'
                }
            }, status=status.HTTP_503_SERVICE_UNAVAILABLE)


class DeploymentLockView(APIView):
    """
    Deployment lock management for preventing concurrent deployments
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """Get current deployment lock status"""
        try:
            if not BusinessPermissions.can_administer(request.user):
                return Response(
                    {'detail': 'Admin permission required'}, 
                    status=status.HTTP_403_FORBIDDEN
                )
            
            from django.core.cache import cache
            
            lock_info = cache.get('deployment_lock')
            if lock_info:
                return Response({
                    'locked': True,
                    'lock_info': lock_info,
                    'remaining_ttl': cache.ttl('deployment_lock')
                })
            else:
                return Response({
                    'locked': False,
                    'lock_info': None
                })
                
        except Exception as e:
            return Response(
                {'detail': f'Failed to get lock status: {str(e)}'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def post(self, request):
        """Acquire deployment lock"""
        try:
            if not BusinessPermissions.can_administer(request.user):
                return Response(
                    {'detail': 'Admin permission required'}, 
                    status=status.HTTP_403_FORBIDDEN
                )
            
            from django.core.cache import cache
            
            # Check if lock already exists
            existing_lock = cache.get('deployment_lock')
            if existing_lock:
                return Response({
                    'success': False,
                    'message': 'Deployment lock already acquired',
                    'lock_info': existing_lock
                }, status=status.HTTP_409_CONFLICT)
            
            # Acquire lock
            lock_info = {
                'user': request.user.username,
                'user_id': request.user.id,
                'timestamp': timezone.now().isoformat(),
                'reason': request.data.get('reason', 'Deployment in progress'),
                'environment': request.data.get('environment', 'unknown')
            }
            
            timeout = request.data.get('timeout', 3600)  # Default 1 hour
            cache.set('deployment_lock', lock_info, timeout=timeout)
            
            # Log lock acquisition
            AuditLog.log_action(
                user=request.user,
                action=AuditLog.ACTION_CREATE,
                resource='deployment_lock',
                description=f'Deployment lock acquired for {lock_info["environment"]} environment',
                risk_level=AuditLog.RISK_MEDIUM,
                success=True,
                request=request
            )
            
            return Response({
                'success': True,
                'message': 'Deployment lock acquired',
                'lock_info': lock_info,
                'timeout': timeout
            })
            
        except Exception as e:
            return Response(
                {'detail': f'Failed to acquire lock: {str(e)}'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def delete(self, request):
        """Release deployment lock"""
        try:
            if not BusinessPermissions.can_administer(request.user):
                return Response(
                    {'detail': 'Admin permission required'}, 
                    status=status.HTTP_403_FORBIDDEN
                )
            
            from django.core.cache import cache
            
            lock_info = cache.get('deployment_lock')
            if not lock_info:
                return Response({
                    'success': False,
                    'message': 'No deployment lock found'
                }, status=status.HTTP_404_NOT_FOUND)
            
            # Check if current user can release the lock
            force_release = request.data.get('force', False)
            if lock_info.get('user_id') != request.user.id and not force_release:
                return Response({
                    'success': False,
                    'message': 'Cannot release lock acquired by another user. Use force=true to override.',
                    'lock_info': lock_info
                }, status=status.HTTP_403_FORBIDDEN)
            
            # Release lock
            cache.delete('deployment_lock')
            
            # Log lock release
            AuditLog.log_action(
                user=request.user,
                action=AuditLog.ACTION_DELETE,
                resource='deployment_lock',
                description=f'Deployment lock released (force: {force_release})',
                risk_level=AuditLog.RISK_MEDIUM,
                success=True,
                request=request
            )
            
            return Response({
                'success': True,
                'message': 'Deployment lock released',
                'previous_lock_info': lock_info
            })
            
        except Exception as e:
            return Response(
                {'detail': f'Failed to release lock: {str(e)}'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

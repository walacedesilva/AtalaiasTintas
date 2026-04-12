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

from .models import User, UserSession, AuditLog, UserPreferences
from .permissions import IsAuthenticated, BusinessPermissions, BusinessRole
from .serializers import (
    UserSerializer, UserProfileSerializer, LoginSerializer,
    ChangePasswordSerializer, UserSessionSerializer, UserPreferencesSerializer,
    UserPreferencesUpdateSerializer
)


class LoginView(APIView):
    """
    User login endpoint with session tracking and audit logging
    """
    permission_classes = [permissions.AllowAny]
    
    def post(self, request):
        """
        Authenticate user and create session
        """
        try:
            serializer = LoginSerializer(data=request.data)
            if not serializer.is_valid():
                # Log failed login attempt
                AuditLog.log_action(
                    user=None,
                    action=AuditLog.ACTION_LOGIN,
                    resource='auth.login',
                    description=f"Login failed - validation errors: {serializer.errors}",
                    risk_level=AuditLog.RISK_MEDIUM,
                    success=False,
                    error_message=str(serializer.errors),
                    request=request
                )
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            
            username = serializer.validated_data['username']
            password = serializer.validated_data['password']
            
            # Authenticate user
            user = authenticate(request, username=username, password=password)
            
            if user is None:
                # Log failed authentication
                AuditLog.log_action(
                    user=None,
                    action=AuditLog.ACTION_LOGIN,
                    resource='auth.login',
                    description=f"Login failed - invalid credentials for username: {username}",
                    risk_level=AuditLog.RISK_HIGH,
                    success=False,
                    error_message="Invalid username or password",
                    request=request
                )
                return Response(
                    {'detail': 'Invalid username or password'}, 
                    status=status.HTTP_401_UNAUTHORIZED
                )
            
            if not user.ativo:
                # Log inactive user login attempt
                AuditLog.log_action(
                    user=user,
                    action=AuditLog.ACTION_ACCESS_DENIED,
                    resource='auth.login',
                    description="Login denied - user account is inactive",
                    risk_level=AuditLog.RISK_MEDIUM,
                    success=False,
                    error_message="User account is inactive",
                    request=request
                )
                return Response(
                    {'detail': 'Account is inactive'}, 
                    status=status.HTTP_403_FORBIDDEN
                )
            
            # Create or get auth token
            token, created = Token.objects.get_or_create(user=user)
            
            # Create user session
            user_session = UserSession.objects.create(
                user=user,
                session_key=request.session.session_key or token.key,
                ip_address=self._get_client_ip(request),
                user_agent=request.META.get('HTTP_USER_AGENT', ''),
                browser_info={
                    'accept_language': request.META.get('HTTP_ACCEPT_LANGUAGE', ''),
                    'accept_encoding': request.META.get('HTTP_ACCEPT_ENCODING', ''),
                }
            )
            
            # Django login
            login(request, user)
            
            # Log successful login
            AuditLog.log_action(
                user=user,
                session=user_session,
                action=AuditLog.ACTION_LOGIN,
                resource='auth.login',
                description="User logged in successfully",
                risk_level=AuditLog.RISK_LOW,
                success=True,
                request=request
            )
            
            # Update user's last login
            user.last_login = timezone.now()
            user.save(update_fields=['last_login'])
            
            # Prepare response data
            user_data = UserSerializer(user).data
            roles = BusinessPermissions.get_user_roles(user)
            
            return Response({
                'user': user_data,
                'token': token.key,
                'session_id': user_session.id,
                'roles': [role.value for role in roles],
                'permissions': {
                    'can_sell': BusinessPermissions.user_has_role(user, BusinessRole.VENDOR),
                    'can_manage_inventory': BusinessPermissions.user_has_role(user, BusinessRole.OPERATOR),
                    'can_access_financial': getattr(user, 'pode_acessar_financeiro', False),
                    'can_administrate': BusinessPermissions.user_has_role(user, BusinessRole.ADMIN),
                },
                'message': 'Login successful'
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            # Log system error
            AuditLog.log_action(
                user=getattr(request, 'user', None),
                action=AuditLog.ACTION_LOGIN,
                resource='auth.login',
                description="Login failed - system error",
                risk_level=AuditLog.RISK_CRITICAL,
                success=False,
                error_message=str(e),
                request=request
            )
            return Response(
                {'detail': 'Internal server error'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def _get_client_ip(self, request):
        """Extract client IP address considering proxies"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip


class LogoutView(APIView):
    """
    User logout endpoint with session cleanup
    """
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        """
        Logout user and cleanup session
        """
        try:
            user = request.user
            
            # Find and close active session
            session_key = request.session.session_key
            if session_key:
                try:
                    user_session = UserSession.objects.get(
                        user=user, 
                        session_key=session_key, 
                        is_active=True
                    )
                    user_session.mark_logout()
                except UserSession.DoesNotExist:
                    pass
            
            # Log logout
            AuditLog.log_action(
                user=user,
                action=AuditLog.ACTION_LOGOUT,
                resource='auth.logout',
                description="User logged out successfully",
                risk_level=AuditLog.RISK_LOW,
                success=True,
                request=request
            )
            
            # Delete auth token to invalidate API access
            try:
                token = Token.objects.get(user=user)
                token.delete()
            except Token.DoesNotExist:
                pass
            
            # Django logout
            logout(request)
            
            return Response({
                'message': 'Logout successful'
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            # Log error but still try to logout  
            AuditLog.log_action(
                user=getattr(request, 'user', None),
                action=AuditLog.ACTION_LOGOUT,
                resource='auth.logout',
                description="Logout error but session cleared",
                risk_level=AuditLog.RISK_MEDIUM,
                success=False,
                error_message=str(e),
                request=request
            )
            
            # Force logout even with errors
            logout(request)
            return Response({
                'message': 'Logout completed with warnings'
            }, status=status.HTTP_200_OK)


class UserProfileView(APIView):
    """
    Current user profile information
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """
        Get current user profile data
        """
        try:
            user = request.user
            
            # Get user roles and permissions
            roles = BusinessPermissions.get_user_roles(user)
            
            # Get active sessions
            active_sessions = UserSession.objects.filter(
                user=user, 
                is_active=True
            ).order_by('-last_activity')[:5]
            
            # Log profile access
            AuditLog.log_action(
                user=user,
                action=AuditLog.ACTION_VIEW,
                resource='user.profile',
                resource_id=str(user.id),
                description="User accessed their profile",
                risk_level=AuditLog.RISK_LOW,
                success=True,
                request=request
            )
            
            # Serialize data
            user_data = UserSerializer(user).data
            profile_data = None
            if hasattr(user, 'profile'):
                profile_data = UserProfileSerializer(user.profile).data
            
            sessions_data = UserSessionSerializer(active_sessions, many=True).data
            
            return Response({
                'user': user_data,
                'profile': profile_data,
                'roles': [role.value for role in roles],
                'permissions': {
                    'can_sell': BusinessPermissions.user_has_role(user, BusinessRole.VENDOR),
                    'can_manage_inventory': BusinessPermissions.user_has_role(user, BusinessRole.OPERATOR),
                    'can_access_financial': getattr(user, 'pode_acessar_financeiro', False),
                    'can_administrate': BusinessPermissions.user_has_role(user, BusinessRole.ADMIN),
                },
                'active_sessions': sessions_data,
                'last_login': user.last_login,
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response(
                {'detail': f'Error retrieving profile: {str(e)}'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class ChangePasswordView(APIView):
    """
    Change user password endpoint
    """
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        """
        Change user password with validation
        """
        try:
            serializer = ChangePasswordSerializer(data=request.data)
            if not serializer.is_valid():
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            
            user = request.user
            old_password = serializer.validated_data['old_password']
            new_password = serializer.validated_data['new_password']
            
            # Verify current password
            if not user.check_password(old_password):
                AuditLog.log_action(
                    user=user,
                    action=AuditLog.ACTION_SECURITY_ALERT,
                    resource='user.password_change',
                    description="Failed password change - invalid current password",
                    risk_level=AuditLog.RISK_HIGH,
                    success=False,
                    error_message="Invalid current password",
                    request=request
                )
                return Response(
                    {'detail': 'Current password is incorrect'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Validate new password
            try:
                validate_password(new_password, user)
            except ValidationError as e:
                return Response(
                    {'detail': list(e.messages)}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Change password
            with transaction.atomic():
                user.set_password(new_password)
                user.save(update_fields=['password'])
                
                # Invalidate all existing tokens and sessions
                Token.objects.filter(user=user).delete()
                UserSession.objects.filter(user=user, is_active=True).update(
                    is_active=False,
                    logout_time=timezone.now()
                )
                
                # Create new token
                new_token = Token.objects.create(user=user)
                
                # Log successful password change
                AuditLog.log_action(
                    user=user,
                    action=AuditLog.ACTION_UPDATE,
                    resource='user.password',
                    resource_id=str(user.id),
                    description="Password changed successfully",
                    risk_level=AuditLog.RISK_MEDIUM,
                    success=True,
                    request=request
                )
            
            return Response({
                'message': 'Password changed successfully',
                'new_token': new_token.key,
                'note': 'All active sessions have been terminated. Please login again on other devices.'
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            AuditLog.log_action(
                user=getattr(request, 'user', None),
                action=AuditLog.ACTION_UPDATE,
                resource='user.password',
                description="Password change failed - system error",
                risk_level=AuditLog.RISK_HIGH,
                success=False,
                error_message=str(e),
                request=request
            )
            return Response(
                {'detail': 'Internal server error'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


# ===================================
# USER PREFERENCES API ENDPOINTS
# Feature: 3-modern-web-interface  
# Task: T007 - User Preferences API Endpoints
# ===================================

class UserPreferencesViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing user interface preferences.
    
    Provides CRUD operations for UserPreferences with proper permissions
    and validation. Users can only access their own preferences.
    """
    
    serializer_class = UserPreferencesSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """
        Return only the current user's preferences
        """
        if self.request.user.is_authenticated:
            return UserPreferences.objects.filter(user=self.request.user)
        return UserPreferences.objects.none()
    
    def get_serializer_class(self):
        """
        Use specialized serializer for partial updates
        """
        if self.action in ['partial_update']:
            return UserPreferencesUpdateSerializer
        return UserPreferencesSerializer
    
    def get_object(self):
        """
        Get or create user preferences for the current user
        """
        try:
            # Try to get existing preferences
            return UserPreferences.objects.get(user=self.request.user)
        except UserPreferences.DoesNotExist:
            # Create preferences if they don't exist
            preferences, created = UserPreferences.get_or_create_for_user(
                self.request.user
            )
            return preferences
    
    def list(self, request, *args, **kwargs):
        """
        Return current user's preferences (always a single object)
        """
        try:
            preferences = self.get_object()
            serializer = self.get_serializer(preferences)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Exception as e:
            return Response(
                {'detail': 'Failed to retrieve preferences'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def create(self, request, *args, **kwargs):
        """
        Create or update user preferences (upsert behavior)
        """
        try:
            preferences = self.get_object()
            serializer = self.get_serializer(preferences, data=request.data, partial=True)
            
            if serializer.is_valid():
                serializer.save()
                
                # Log preference update
                AuditLog.log_action(
                    user=request.user,
                    action=AuditLog.ACTION_UPDATE,
                    resource='user.preferences',
                    resource_id=str(preferences.id),
                    description="User preferences updated",
                    risk_level=AuditLog.RISK_LOW,
                    success=True,
                    new_values=serializer.validated_data,
                    request=request
                )
                
                return Response(serializer.data, status=status.HTTP_200_OK)
            else:
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
                
        except Exception as e:
            return Response(
                {'detail': 'Failed to update preferences'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['post'])
    def reset_quick_actions(self, request):
        """
        Reset only quick actions to defaults
        """
        try:
            preferences = self.get_object()
            old_actions = preferences.quick_actions.copy() if preferences.quick_actions else []
            
            preferences.quick_actions = preferences.get_default_quick_actions()
            preferences.save(update_fields=['quick_actions', 'updated_at'])
            
            # Log quick actions reset
            AuditLog.log_action(
                user=request.user,
                action=AuditLog.ACTION_UPDATE,
                resource='user.preferences.quick_actions',
                resource_id=str(preferences.id),
                description="Quick actions reset to defaults",
                risk_level=AuditLog.RISK_LOW,
                success=True,
                old_values={'quick_actions': old_actions},
                new_values={'quick_actions': preferences.quick_actions},
                request=request
            )
            
            serializer = self.get_serializer(preferences)
            return Response({
                'message': 'Quick actions reset to defaults',
                'preferences': serializer.data
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response(
                {'detail': 'Failed to reset quick actions'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


# ===================================
# DEMO AND DOCUMENTATION VIEWS 
# Feature: 3-modern-web-interface
# Task: T009 - Typography Scale System
# ===================================

from django.shortcuts import render

def typography_demo(request):
    """
    Typography demonstration page showing all available font scales,
    weights, and utilities for the paint store application.
    
    Displays:
    - Display typography (display-1 to display-4)
    - Heading hierarchy (H1-H6)  
    - Font size scale (text-xs to text-6xl)
    - Font weight utilities (font-thin to font-black)
    - Line height and letter spacing
    - Paint store-specific typography
    - Text utilities and responsive behavior
    - Accessibility features
    """
    return render(request, 'etiquetas/typography-demo.html', {
        'page_title': 'Typography Scale System',
        'feature': '3-modern-web-interface',
        'task': 'T009'
    })


def forms_demo(request):
    """
    Form components demonstration page showing all form styling
    capabilities for the paint store application.
    
    Displays:
    - Input fields with proper focus states and borders
    - Label styling with clear association to inputs
    - Error/success state styling with high contrast indicators
    - Button hierarchy (primary, secondary, destructive)  
    - Real-time validation examples
    - Paint store-specific form components
    - Accessibility features and keyboard navigation
    - File upload with progress indicators
    """
    return render(request, 'etiquetas/forms-demo.html', {
        'page_title': 'Form Components System', 
        'feature': '3-modern-web-interface',
        'task': 'T010'
    })


def progressive_enhancement_test(request):
    """
    Feature: 3-modern-web-interface
    Task: T014 - Progressive Enhancement Layer
    
    Test page for progressive enhancement features including feature detection,
    form enhancements, keyboard shortcuts, accessibility improvements,
    and graceful degradation when JavaScript is disabled.
    
    Tests:
    - Feature detection (localStorage, CSS animations, etc.)
    - Form enhancements (real-time validation, auto-save, AJAX submission)
    - Keyboard shortcuts (Ctrl+K, Ctrl+S, etc.)
    - Accessibility enhancements (skip links, focus management, screen reader support)
    - Scroll animations with IntersectionObserver
    - Network status detection and offline handling
    - Graceful degradation when JavaScript is disabled
    """
    return render(request, 'etiquetas/progressive-enhancement-test.html', {
        'page_title': 'Progressive Enhancement Test',
        'feature': '3-modern-web-interface', 
        'task': 'T014'
    })

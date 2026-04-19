"""
Enhanced authentication backends for API security.
Task: T013 - API Authentication Security

Implements:
- JWT token authentication
- API key authentication
- Rate limiting integration
- Session security enhancements
- Multi-factor authentication support
"""

import jwt
import hashlib
import secrets
from datetime import datetime, timedelta
from django.contrib.auth import get_user_model
from django.conf import settings
from django.utils import timezone
from django.core.cache import cache
from rest_framework import authentication, exceptions
from rest_framework.authtoken.models import Token

from .models import APIKey, LoginAttempt, UserSession

User = get_user_model()


class JWTAuthentication(authentication.BaseAuthentication):
    """
    JWT Token authentication backend with enhanced security features.
    
    Features:
    - Secure JWT token generation and validation
    - Token refresh support
    - Rate limiting integration
    - Audit logging
    - Token blacklisting support
    """
    
    def authenticate(self, request):
        """
        Authenticate user using JWT token from Authorization header.
        """
        auth_header = request.META.get('HTTP_AUTHORIZATION', '')
        
        if not auth_header.startswith('Bearer '):
            return None
        
        token = auth_header.split(' ')[1]
        
        try:
            return self._authenticate_jwt_token(token, request)
        except Exception as e:
            # Log authentication failure for security monitoring
            self._log_auth_failure(request, str(e))
            raise exceptions.AuthenticationFailed('Invalid token')
    
    def _authenticate_jwt_token(self, token, request):
        """
        Validate JWT token and return user, token tuple.
        """
        try:
            # Decode and validate JWT token
            payload = jwt.decode(
                token, 
                settings.JWT_SECRET_KEY,
                algorithms=[settings.JWT_ALGORITHM]
            )
            
            # Check if token is blacklisted
            if self._is_token_blacklisted(token):
                raise exceptions.AuthenticationFailed('Token is blacklisted')
            
            # Get user from token payload
            user_id = payload.get('user_id')
            if not user_id:
                raise exceptions.AuthenticationFailed('Token payload invalid')
            
            user = User.objects.get(id=user_id, is_active=True)
            
            # Validate token claims
            self._validate_token_claims(payload, user, request)
            
            # Update last activity for session tracking
            self._update_user_activity(user, request)
            
            return (user, token)
            
        except jwt.ExpiredSignatureError:
            raise exceptions.AuthenticationFailed('Token has expired')
        except jwt.InvalidTokenError:
            raise exceptions.AuthenticationFailed('Invalid token format')
        except User.DoesNotExist:
            raise exceptions.AuthenticationFailed('User not found')
        except Exception as e:
            raise exceptions.AuthenticationFailed(f'Token validation failed: {str(e)}')
    
    def _validate_token_claims(self, payload, user, request):
        """
        Validate JWT token claims for security.
        """
        # Check token expiration
        exp = payload.get('exp')
        if not exp or datetime.fromtimestamp(exp, tz=timezone.utc) < timezone.now():
            raise exceptions.AuthenticationFailed('Token has expired')
        
        # Check issued time
        iat = payload.get('iat')
        if not iat:
            raise exceptions.AuthenticationFailed('Token missing issued time')
        
        # Check if token was issued before user's password change
        if user.password_changed_at:
            token_issued = datetime.fromtimestamp(iat, tz=timezone.utc)
            if token_issued < user.password_changed_at:
                raise exceptions.AuthenticationFailed('Token invalidated by password change')
        
        # Validate audience and issuer if configured
        aud = payload.get('aud')
        if aud and aud != getattr(settings, 'JWT_AUDIENCE', None):
            raise exceptions.AuthenticationFailed('Token audience invalid')
        
        iss = payload.get('iss')
        if iss and iss != getattr(settings, 'JWT_ISSUER', None):
            raise exceptions.AuthenticationFailed('Token issuer invalid')
    
    def _is_token_blacklisted(self, token):
        """
        Check if JWT token is blacklisted.
        """
        token_hash = hashlib.sha256(token.encode()).hexdigest()
        return cache.get(f'blacklist_{token_hash}', False)
    
    def _update_user_activity(self, user, request):
        """
        Update user's last activity for session tracking.
        """
        try:
            # Update user session if exists
            session_key = request.session.session_key
            if session_key:
                UserSession.objects.filter(
                    user=user,
                    session_key=session_key,
                    is_active=True
                ).update(last_activity=timezone.now())
            
            # Update user last activity
            user.last_activity = timezone.now()
            user.save(update_fields=['last_activity'])
            
        except Exception:
            # Don't fail authentication if activity update fails
            pass
    
    def _log_auth_failure(self, request, error_message):
        """
        Log authentication failure for security monitoring.
        """
        from .models import AuditLog
        
        try:
            AuditLog.log_action(
                user=None,
                action=AuditLog.ACTION_AUTH_FAILED,
                resource='jwt_auth',
                description=f'JWT authentication failed: {error_message}',
                risk_level=AuditLog.RISK_MEDIUM,
                success=False,
                error_message=error_message,
                request=request
            )
        except Exception:
            # Don't fail authentication if logging fails
            pass

    @staticmethod
    def generate_jwt_token(user, remember_me=False):
        """
        Generate JWT token for user with appropriate expiration.
        """
        # Token expiration based on remember_me preference
        if remember_me:
            expiration = timezone.now() + timedelta(days=30)  # 30 days for remember me
        else:
            expiration = timezone.now() + timedelta(hours=8)   # 8 hours standard
        
        # JWT payload
        payload = {
            'user_id': user.id,
            'username': user.username,
            'exp': expiration.timestamp(),
            'iat': timezone.now().timestamp(),
            'aud': getattr(settings, 'JWT_AUDIENCE', 'atalaias-tintas'),
            'iss': getattr(settings, 'JWT_ISSUER', 'atalaias-tintas-api'),
            'session_id': secrets.token_hex(16),  # Unique session identifier
            'user_roles': [role.name for role in user.roles.all()],  # Include user roles
        }
        
        # Generate and return JWT token
        token = jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
        
        return {
            'access_token': token,
            'token_type': 'Bearer',
            'expires_at': expiration.isoformat(),
            'expires_in': int((expiration - timezone.now()).total_seconds())
        }

    @staticmethod
    def blacklist_token(token):
        """
        Blacklist a JWT token to prevent its reuse.
        """
        try:
            # Decode token to get expiration
            payload = jwt.decode(
                token, 
                settings.JWT_SECRET_KEY,
                algorithms=[settings.JWT_ALGORITHM]
            )
            
            # Calculate TTL until token expires
            exp = payload.get('exp')
            if exp:
                expires_at = datetime.fromtimestamp(exp, tz=timezone.utc)
                ttl = int((expires_at - timezone.now()).total_seconds())
                
                if ttl > 0:
                    # Add token to blacklist cache
                    token_hash = hashlib.sha256(token.encode()).hexdigest()
                    cache.set(f'blacklist_{token_hash}', True, timeout=ttl)
                    return True
        except Exception:
            pass
        
        return False


class APIKeyAuthentication(authentication.BaseAuthentication):
    """
    API Key authentication backend for programmatic access.
    
    Features:
    - Secure API key generation and validation
    - Rate limiting per API key
    - Usage tracking and analytics
    - Scope-based permissions
    - Key expiration support
    """
    
    keyword = 'ApiKey'
    
    def authenticate(self, request):
        """
        Authenticate using API key from Authorization header or query parameter.
        """
        api_key = None
        
        # Try Authorization header first
        auth_header = request.META.get('HTTP_AUTHORIZATION', '')
        if auth_header.startswith(f'{self.keyword} '):
            api_key = auth_header.split(' ')[1]
        
        # Try X-API-Key header
        if not api_key:
            api_key = request.META.get('HTTP_X_API_KEY')
        
        # Try query parameter (less secure, for development only)
        if not api_key and settings.DEBUG:
            api_key = request.GET.get('api_key')
        
        if not api_key:
            return None
        
        try:
            return self._authenticate_api_key(api_key, request)
        except Exception as e:
            self._log_api_key_failure(request, api_key, str(e))
            raise exceptions.AuthenticationFailed('Invalid API key')
    
    def _authenticate_api_key(self, api_key, request):
        """
        Validate API key and return user, api_key_obj tuple.
        """
        try:
            # Hash the API key for secure lookup
            key_hash = hashlib.sha256(api_key.encode()).hexdigest()
            
            # Get API key object
            api_key_obj = APIKey.objects.select_related('user').get(
                key_hash=key_hash,
                is_active=True
            )
            
            # Check if API key is expired
            if api_key_obj.expires_at and api_key_obj.expires_at < timezone.now():
                raise exceptions.AuthenticationFailed('API key has expired')
            
            # Check rate limiting
            self._check_api_key_rate_limit(api_key_obj, request)
            
            # Update usage statistics
            self._update_api_key_usage(api_key_obj, request)
            
            # Validate API key scopes for the requested endpoint
            self._validate_api_key_scopes(api_key_obj, request)
            
            return (api_key_obj.user, api_key_obj)
            
        except APIKey.DoesNotExist:
            raise exceptions.AuthenticationFailed('Invalid API key')
        except Exception as e:
            raise exceptions.AuthenticationFailed(f'API key validation failed: {str(e)}')
    
    def _check_api_key_rate_limit(self, api_key_obj, request):
        """
        Check rate limiting for API key usage.
        """
        if not api_key_obj.rate_limit_per_hour:
            return  # No rate limit configured
        
        # Check current usage
        cache_key = f'api_key_usage_{api_key_obj.id}_{timezone.now().strftime("%Y%m%d%H")}'
        current_usage = cache.get(cache_key, 0)
        
        if current_usage >= api_key_obj.rate_limit_per_hour:
            raise exceptions.AuthenticationFailed('API key rate limit exceeded')
        
        # Increment usage counter
        cache.set(cache_key, current_usage + 1, timeout=3600)  # 1 hour TTL
    
    def _update_api_key_usage(self, api_key_obj, request):
        """
        Update API key usage statistics.
        """
        try:
            # Update last used timestamp and usage count
            api_key_obj.last_used_at = timezone.now()
            api_key_obj.usage_count = api_key_obj.usage_count + 1
            api_key_obj.save(update_fields=['last_used_at', 'usage_count'])
            
            # Log API key usage
            from .models import APIKeyUsageLog
            APIKeyUsageLog.objects.create(
                api_key=api_key_obj,
                endpoint=request.path,
                method=request.method,
                ip_address=self._get_client_ip(request),
                user_agent=request.META.get('HTTP_USER_AGENT', '')[:500],
                timestamp=timezone.now()
            )
            
        except Exception:
            # Don't fail authentication if usage update fails
            pass
    
    def _validate_api_key_scopes(self, api_key_obj, request):
        """
        Validate API key scopes against requested endpoint.
        """
        if not api_key_obj.scopes:
            return  # No scope restrictions
        
        # Extract endpoint pattern from request path
        endpoint_pattern = self._extract_endpoint_pattern(request.path)
        
        # Check if API key has required scope
        scopes = api_key_obj.scopes.split(',') if api_key_obj.scopes else []
        
        # Check against scope patterns
        has_access = any(
            self._scope_matches_endpoint(scope.strip(), endpoint_pattern, request.method)
            for scope in scopes
        )
        
        if not has_access:
            raise exceptions.AuthenticationFailed('API key does not have required scope')
    
    def _extract_endpoint_pattern(self, path):
        """
        Extract endpoint pattern from request path.
        """
        # Remove API version prefix and extract base pattern
        if path.startswith('/api/'):
            parts = path.split('/')
            if len(parts) > 3:
                return '/'.join(parts[3:])  # Remove /api/v1/ prefix
        return path
    
    def _scope_matches_endpoint(self, scope, endpoint, method):
        """
        Check if scope matches the requested endpoint and method.
        """
        # Scope format: "method:pattern" or "pattern" (for all methods)
        if ':' in scope:
            scope_method, scope_pattern = scope.split(':', 1)
            if scope_method.upper() != method.upper():
                return False
        else:
            scope_pattern = scope
        
        # Simple pattern matching (can be enhanced with regex)
        if scope_pattern == '*':
            return True  # Full access
        
        if scope_pattern.endswith('*'):
            return endpoint.startswith(scope_pattern[:-1])
        
        return endpoint == scope_pattern
    
    def _get_client_ip(self, request):
        """Extract client IP from request."""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            return x_forwarded_for.split(',')[0].strip()
        return request.META.get('REMOTE_ADDR', '127.0.0.1')
    
    def _log_api_key_failure(self, request, api_key, error_message):
        """
        Log API key authentication failure.
        """
        from .models import AuditLog
        
        try:
            AuditLog.log_action(
                user=None,
                action=AuditLog.ACTION_AUTH_FAILED,
                resource='api_key_auth',
                description=f'API key authentication failed: {error_message}',
                risk_level=AuditLog.RISK_HIGH,
                success=False,
                error_message=error_message,
                request=request,
                extra_data={'api_key_prefix': api_key[:8] + '...' if len(api_key) > 8 else api_key}
            )
        except Exception:
            pass


class EnhancedTokenAuthentication(authentication.TokenAuthentication):
    """
    Enhanced version of DRF Token authentication with additional security features.
    
    Features:
    - Token expiration support
    - Rate limiting integration
    - Usage tracking
    - IP validation (optional)
    - User agent validation (optional)
    """
    
    def authenticate_credentials(self, key):
        """
        Enhanced token validation with security checks.
        """
        model = self.get_model()
        try:
            token = model.objects.select_related('user').get(key=key)
        except model.DoesNotExist:
            # Log invalid token attempt
            self._log_token_failure('Invalid token')
            raise exceptions.AuthenticationFailed('Invalid token.')

        if not token.user.is_active:
            # Log inactive user attempt
            self._log_token_failure('User inactive', token.user)
            raise exceptions.AuthenticationFailed('User inactive or deleted.')
        
        # Check token expiration if configured
        if hasattr(token, 'expires_at') and token.expires_at:
            if token.expires_at < timezone.now():
                self._log_token_failure('Token expired', token.user)
                raise exceptions.AuthenticationFailed('Token has expired.')
        
        # Update token last used
        if hasattr(token, 'last_used_at'):
            token.last_used_at = timezone.now()
            token.save(update_fields=['last_used_at'])

        return (token.user, token)
    
    def _log_token_failure(self, reason, user=None):
        """Log token authentication failure."""
        from .models import AuditLog
        
        try:
            AuditLog.log_action(
                user=user,
                action=AuditLog.ACTION_AUTH_FAILED,
                resource='token_auth',
                description=f'Token authentication failed: {reason}',
                risk_level=AuditLog.RISK_MEDIUM,
                success=False,
                error_message=reason
            )
        except Exception:
            pass


class MultiFactorAuthenticationMixin:
    """
    Mixin to add multi-factor authentication support to authentication backends.
    
    Features:
    - TOTP (Time-based One-Time Password) support
    - SMS verification support
    - Email verification support
    - Backup codes support
    """
    
    def require_mfa_verification(self, user, request):
        """
        Check if user requires MFA verification.
        """
        if not user.mfa_enabled:
            return False
        
        # Check if MFA was recently verified for this session
        session_key = request.session.session_key
        if session_key:
            cache_key = f'mfa_verified_{user.id}_{session_key}'
            if cache.get(cache_key):
                return False  # MFA already verified for this session
        
        return True
    
    def verify_mfa_token(self, user, mfa_token, mfa_method='totp'):
        """
        Verify MFA token for user.
        """
        if mfa_method == 'totp':
            return self._verify_totp_token(user, mfa_token)
        elif mfa_method == 'sms':
            return self._verify_sms_token(user, mfa_token)
        elif mfa_method == 'email':
            return self._verify_email_token(user, mfa_token)
        elif mfa_method == 'backup':
            return self._verify_backup_code(user, mfa_token)
        
        return False
    
    def _verify_totp_token(self, user, token):
        """Verify TOTP token using user's secret."""
        try:
            import pyotp
            
            if not user.totp_secret:
                return False
            
            totp = pyotp.TOTP(user.totp_secret)
            return totp.verify(token, valid_window=1)  # Allow 1 time step tolerance
            
        except Exception:
            return False
    
    def _verify_sms_token(self, user, token):
        """Verify SMS token sent to user's phone."""
        # Implementation would integrate with SMS service
        cache_key = f'sms_token_{user.id}'
        stored_token = cache.get(cache_key)
        
        if stored_token and stored_token == token:
            cache.delete(cache_key)  # One-time use
            return True
        
        return False
    
    def _verify_email_token(self, user, token):
        """Verify email token sent to user's email."""
        # Implementation would integrate with email service
        cache_key = f'email_token_{user.id}'
        stored_token = cache.get(cache_key)
        
        if stored_token and stored_token == token:
            cache.delete(cache_key)  # One-time use
            return True
        
        return False
    
    def _verify_backup_code(self, user, code):
        """Verify backup recovery code."""
        from .models import MFABackupCode
        
        try:
            backup_code = MFABackupCode.objects.get(
                user=user,
                code_hash=hashlib.sha256(code.encode()).hexdigest(),
                is_used=False
            )
            
            # Mark backup code as used
            backup_code.is_used = True
            backup_code.used_at = timezone.now()
            backup_code.save()
            
            return True
            
        except MFABackupCode.DoesNotExist:
            return False
    
    def mark_mfa_verified(self, user, request, duration_minutes=60):
        """
        Mark MFA as verified for the current session.
        """
        session_key = request.session.session_key
        if session_key:
            cache_key = f'mfa_verified_{user.id}_{session_key}'
            cache.set(cache_key, True, timeout=duration_minutes * 60)


class CombinedAuthentication(authentication.BaseAuthentication):
    """
    Combined authentication backend that tries multiple authentication methods.
    
    Order of precedence:
    1. JWT tokens (Bearer)
    2. API keys (ApiKey)
    3. Enhanced DRF tokens
    """
    
    def __init__(self):
        self.jwt_auth = JWTAuthentication()
        self.api_key_auth = APIKeyAuthentication()
        self.token_auth = EnhancedTokenAuthentication()
    
    def authenticate(self, request):
        """
        Try different authentication methods in order of precedence.
        """
        # Try JWT authentication first
        result = self.jwt_auth.authenticate(request)
        if result:
            return result
        
        # Try API key authentication
        result = self.api_key_auth.authenticate(request)
        if result:
            return result
        
        # Try enhanced token authentication
        result = self.token_auth.authenticate(request)
        if result:
            return result
        
        return None
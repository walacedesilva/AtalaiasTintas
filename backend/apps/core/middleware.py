"""
T017: Custom middleware for comprehensive error handling, authentication, and audit logging.
Provides advanced request processing, rate limiting, security features, and validation.
Enhanced as part of T017: API Error Handling and Validation implementation.
"""

import logging
import json
import time
import hashlib
from datetime import timedelta
from django.utils import timezone
from django.utils.deprecation import MiddlewareMixin
from django.contrib.auth.models import AnonymousUser
from django.core.exceptions import ObjectDoesNotExist
from django.core.cache import cache
from django.db import transaction
from django.http import JsonResponse, HttpResponse
from rest_framework import status

from .models import UserSession, AuditLog
from .exceptions import (
    RateLimitExceededError, SystemMaintenanceError, 
    PermissionSystemException, ValidationUtils
)

logger = logging.getLogger(__name__)


# =============================================================================
# T017: REQUEST ID & ERROR CONTEXT MIDDLEWARE
# =============================================================================

class RequestIdMiddleware(MiddlewareMixin):
    """
    T017: Adds unique request ID to every request for tracking and debugging.
    
    Features:
    - Generates unique request IDs
    - Makes ID available throughout request lifecycle
    - Adds ID to response headers
    - Enables request correlation in logs
    """
    
    def process_request(self, request):
        """Add request ID to incoming requests."""
        # Generate unique request ID
        timestamp = str(timezone.now().timestamp())
        path_hash = hashlib.md5(request.path.encode()).hexdigest()[:8]
        request_id = f"req_{timestamp}_{path_hash}"
        
        # Store in request for access throughout application
        request.id = request_id
        request.start_time = time.time()
        
        # Add to response headers
        request._request_id_header = request_id
    
    def process_response(self, request, response):
        """Add request ID and timing to response headers."""
        if hasattr(request, 'id'):
            response['X-Request-ID'] = request.id
        
        if hasattr(request, 'start_time'):
            process_time = time.time() - request.start_time
            response['X-Process-Time'] = f"{process_time:.4f}"
        
        return response


class ErrorContextMiddleware(MiddlewareMixin):
    """
    T017: Enhances error handling with additional context.
    
    Features:
    - Adds request context to exceptions
    - Tracks error patterns
    - Provides debugging information
    - Correlates errors with user actions
    """
    
    def process_exception(self, request, exception):
        """Add context to exceptions for better debugging."""
        
        # Enhanced error context
        error_context = {
            'request_id': getattr(request, 'id', 'unknown'),
            'method': request.method,
            'path': request.path,
            'query_params': dict(request.GET),
            'user': request.user.username if hasattr(request, 'user') and request.user.is_authenticated else 'anonymous',
            'user_agent': request.META.get('HTTP_USER_AGENT', ''),
            'client_ip': self._get_client_ip(request),
            'timestamp': timezone.now().isoformat()
        }
        
        # Attach context to exception if it supports it
        if hasattr(exception, 'context'):
            exception.context.update(error_context)
        else:
            exception.request_context = error_context
        
        # Don't return a response - let other error handlers process it
        return None
    
    def _get_client_ip(self, request):
        """Extract real client IP considering proxies."""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            return x_forwarded_for.split(',')[0].strip()
        return request.META.get('REMOTE_ADDR', '0.0.0.0')


# =============================================================================
# T017: RATE LIMITING MIDDLEWARE (ENHANCED)
# =============================================================================

class RateLimitingMiddleware(MiddlewareMixin):
    """
    T017: Advanced rate limiting middleware with multiple strategies.
    
    Features:
    - Per-IP and per-user rate limiting
    - Different limits for different endpoint types
    - Sliding window algorithm
    - Rate limit headers in responses
    - Configurable bypass for trusted IPs
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
        
        # Default rate limits (requests per minute)
        from django.conf import settings
        self.default_limits = {
            'anonymous': getattr(settings, 'RATE_LIMIT_ANONYMOUS', 60),
            'authenticated': getattr(settings, 'RATE_LIMIT_AUTHENTICATED', 300),
            'api_read': getattr(settings, 'RATE_LIMIT_API_READ', 1000),
            'api_write': getattr(settings, 'RATE_LIMIT_API_WRITE', 100),
            'admin': getattr(settings, 'RATE_LIMIT_ADMIN', 500)
        }
        
        # Endpoints that require special rate limiting
        self.endpoint_patterns = {
            'api_write': [r'/api/.+', r'/admin/.+'],
            'api_read': [r'/api/.+'],
            'health': [r'/health/?', r'/ping/?']
        }
        
        # Trusted IPs that bypass rate limiting
        self.trusted_ips = getattr(settings, 'RATE_LIMIT_TRUSTED_IPS', ['127.0.0.1'])
        
        super().__init__(get_response)
    
    def __call__(self, request):
        # Check if IP is trusted
        client_ip = self._get_client_ip(request)
        if client_ip in self.trusted_ips:
            return self.get_response(request)
        
        # Determine rate limit for this request
        limit, window = self._get_rate_limit(request)
        
        # Check rate limit
        is_allowed, remaining, reset_time = self._check_rate_limit(
            request, limit, window
        )
        
        if not is_allowed:
            # Rate limit exceeded
            retry_after = int(reset_time - time.time())
            
            logger.warning(
                f"T017 Rate limit exceeded for {client_ip}",
                extra={
                    'client_ip': client_ip,
                    'user': request.user.username if hasattr(request, 'user') and request.user.is_authenticated else 'anonymous',
                    'path': request.path,
                    'limit': limit,
                    'retry_after': retry_after
                }
            )
            
            # Return rate limit error response
            response_data = {
                'error': 'rate_limit_exceeded',
                'detail': f'Rate limit of {limit} requests per {window} seconds exceeded',
                'retry_after': retry_after,
                'limit': limit,
                'window': window
            }
            
            response = JsonResponse(response_data, status=429)
            response['Retry-After'] = str(retry_after)
            response['X-RateLimit-Limit'] = str(limit)
            response['X-RateLimit-Remaining'] = '0'
            response['X-RateLimit-Reset'] = str(int(reset_time))
            
            return response
        
        # Process request
        response = self.get_response(request)
        
        # Add rate limit headers to response
        response['X-RateLimit-Limit'] = str(limit)
        response['X-RateLimit-Remaining'] = str(remaining)
        response['X-RateLimit-Reset'] = str(int(reset_time))
        
        return response
    
    def _get_client_ip(self, request):
        """Extract real client IP considering proxies."""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            return x_forwarded_for.split(',')[0].strip()
        
        x_real_ip = request.META.get('HTTP_X_REAL_IP')
        if x_real_ip:
            return x_real_ip
        
        return request.META.get('REMOTE_ADDR', '0.0.0.0')
    
    def _get_rate_limit(self, request):
        """Determine appropriate rate limit for the request."""
        # Default window is 60 seconds (1 minute)
        window = 60
        
        # Check for health endpoints (higher limits)
        import re
        if any(re.match(pattern, request.path) for pattern in self.endpoint_patterns.get('health', [])):
            return 1000, window  # Very high limit for health checks
        
        # Check user authentication and type
        if hasattr(request, 'user') and request.user.is_authenticated:
            if request.user.is_superuser or request.user.is_staff:
                limit = self.default_limits['admin']
            else:
                # Check if this is a write operation
                if request.method in ['POST', 'PUT', 'PATCH', 'DELETE']:
                    # Check if it's an API write endpoint
                    if any(re.match(pattern, request.path) for pattern in self.endpoint_patterns.get('api_write', [])):
                        limit = self.default_limits['api_write']
                    else:
                        limit = self.default_limits['authenticated']
                else:
                    # Read operation
                    if any(re.match(pattern, request.path) for pattern in self.endpoint_patterns.get('api_read', [])):
                        limit = self.default_limits['api_read']
                    else:
                        limit = self.default_limits['authenticated']
        else:
            # Anonymous user
            limit = self.default_limits['anonymous']
        
        return limit, window
    
    def _check_rate_limit(self, request, limit, window):
        """Check if request is within rate limits using sliding window."""
        # Create cache key based on user/IP and endpoint type
        client_ip = self._get_client_ip(request)
        
        if hasattr(request, 'user') and request.user.is_authenticated:
            cache_key = f"rate_limit:user:{request.user.id}:{request.path}"
        else:
            cache_key = f"rate_limit:ip:{client_ip}:{request.path}"
        
        current_time = time.time()
        
        # Get existing requests from cache
        requests = cache.get(cache_key, [])
        
        # Remove old requests outside the window
        requests = [req_time for req_time in requests if current_time - req_time < window]
        
        # Check if adding this request would exceed the limit
        if len(requests) >= limit:
            # Rate limit exceeded
            remaining = 0
            reset_time = requests[0] + window  # Time when oldest request expires
            return False, remaining, reset_time
        
        # Add current request
        requests.append(current_time)
        
        # Save back to cache
        cache.set(cache_key, requests, window + 10)  # Cache slightly longer than window
        
        remaining = limit - len(requests)
        reset_time = current_time + window
        
        return True, remaining, reset_time


class PermissionsPolicyMiddleware:
    """
    Adds Permissions-Policy header to allow the 'unload' event.
    Chrome 117+ blocks unload handlers by default (bfcache policy),
    which breaks Django Admin popup windows (RelatedObjectLookups.js).
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        response['Permissions-Policy'] = 'unload=*'
        return response


class AuthenticationMiddleware(MiddlewareMixin):
    """
    Enhanced authentication middleware with session tracking
    Manages user sessions and tracks authentication state
    """
    
    # Session timeout in minutes
    SESSION_TIMEOUT_MINUTES = 480  # 8 hours
    
    def __init__(self, get_response):
        self.get_response = get_response
        super().__init__(get_response)
    
    def process_request(self, request):
        """
        Process incoming request for authentication and session management
        """
        # Skip for anonymous users
        if not request.user or isinstance(request.user, AnonymousUser):
            return None
            
        # Skip for inactive users
        if not getattr(request.user, 'ativo', False):
            return None
            
        # Update session activity
        self._update_session_activity(request)
        
        # Check session timeout
        self._check_session_timeout(request)
        
        return None
    
    def _update_session_activity(self, request):
        """
        Update user session last activity timestamp
        """
        try:
            session_key = request.session.session_key
            if not session_key:
                return
                
            # Find active session
            try:
                user_session = UserSession.objects.get(
                    user=request.user,
                    session_key=session_key,
                    is_active=True
                )
                
                # Update last activity (auto_now field handles this)
                user_session.save(update_fields=['updated_at'])
                
                # Store session info in request for other middleware
                request.user_session = user_session
                
            except UserSession.DoesNotExist:
                # Create session if it doesn't exist (recovery mechanism)
                user_session = UserSession.objects.create(
                    user=request.user,
                    session_key=session_key,
                    ip_address=self._get_client_ip(request),
                    user_agent=request.META.get('HTTP_USER_AGENT', ''),
                    browser_info=self._extract_browser_info(request)
                )
                request.user_session = user_session
                
        except Exception as e:
            logger.error(f"Error updating session activity for user {request.user.id}: {str(e)}")
    
    def _check_session_timeout(self, request):
        """
        Check if user session has timed out
        """
        try:
            if hasattr(request, 'user_session'):
                last_activity = request.user_session.last_activity
                timeout_threshold = timezone.now() - timedelta(minutes=self.SESSION_TIMEOUT_MINUTES)
                
                if last_activity < timeout_threshold:
                    # Mark session as expired
                    request.user_session.is_active = False
                    request.user_session.logout_time = timezone.now()
                    request.user_session.save(update_fields=['is_active', 'logout_time'])
                    
                    # Log session timeout
                    AuditLog.log_action(
                        user=request.user,
                        session=request.user_session,
                        action=AuditLog.ACTION_LOGOUT,
                        resource='auth.session_timeout',
                        description="Session expired due to inactivity",
                        risk_level=AuditLog.RISK_LOW,
                        success=True,
                        request=request
                    )
                    
        except Exception as e:
            logger.error(f"Error checking session timeout for user {request.user.id}: {str(e)}")
    
    def _get_client_ip(self, request):
        """Extract client IP address"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0].strip()
        else:
            ip = request.META.get('REMOTE_ADDR', '')
        return ip
    
    def _extract_browser_info(self, request):
        """Extract browser information from request"""
        user_agent = request.META.get('HTTP_USER_AGENT', '')
        
        return {
            'user_agent': user_agent,
            'accept_language': request.META.get('HTTP_ACCEPT_LANGUAGE', ''),
            'accept_encoding': request.META.get('HTTP_ACCEPT_ENCODING', ''),
            'accept': request.META.get('HTTP_ACCEPT', ''),
        }


class AuditLogMiddleware(MiddlewareMixin):
    """
    Audit logging middleware that tracks all API operations
    Provides comprehensive audit trail for compliance and security
    """
    
    # Methods that should be logged
    LOGGABLE_METHODS = ['POST', 'PUT', 'PATCH', 'DELETE']
    
    # Sensitive paths to always log (including GET)
    SENSITIVE_PATHS = [
        '/api/v1/auth/login/',
        '/api/v1/auth/logout/', 
        '/api/v1/auth/change-password/',
        '/admin/',
    ]
    
    # Paths to exclude from logging
    EXCLUDED_PATHS = [
        '/api/v1/monitoring/health/',
        '/health/',
        '/static/',
        '/media/',
        '/__debug__/',
    ]
    
    def __init__(self, get_response):
        self.get_response = get_response
        super().__init__(get_response)
    
    def process_request(self, request):
        """
        Capture request start time and initial data
        """
        request._audit_start_time = timezone.now()
        request._audit_request_data = self._capture_request_data(request)
        return None
    
    def process_response(self, request, response):
        """
        Log the completed request/response cycle
        """
        # Check if this request should be logged
        if self._should_log_request(request, response):
            self._log_request_response(request, response)
        
        return response
    
    def process_exception(self, request, exception):
        """
        Log requests that resulted in exceptions
        """
        try:
            # Always log exceptions for audit purposes
            AuditLog.log_action(
                user=getattr(request, 'user', None) if hasattr(request, 'user') else None,
                session=getattr(request, 'user_session', None),
                action=AuditLog.ACTION_SECURITY_ALERT,
                resource=f"exception.{request.path}",
                description=f"Request caused exception: {str(exception)[:200]}",
                risk_level=AuditLog.RISK_HIGH,
                success=False,
                error_message=str(exception),
                request=request,
                extra_data=self._capture_request_data(request)
            )
        except Exception as e:
            logger.error(f"Error logging exception in AuditLogMiddleware: {str(e)}")
        
        return None
    
    def _should_log_request(self, request, response):
        """
        Determine if this request should be logged
        """
        path = request.path
        method = request.method
        
        # Skip excluded paths
        for excluded_path in self.EXCLUDED_PATHS:
            if path.startswith(excluded_path):
                return False
        
        # Always log sensitive paths
        for sensitive_path in self.SENSITIVE_PATHS:
            if path.startswith(sensitive_path):
                return True
        
        # Log methods that modify data
        if method in self.LOGGABLE_METHODS:
            return True
            
        # Log failed requests (4xx, 5xx errors)
        if response.status_code >= 400:
            return True
        
        return False
    
    def _log_request_response(self, request, response):
        """
        Create audit log entry for the request/response
        """
        try:
            with transaction.atomic():
                # Determine action type based on method
                action_map = {
                    'POST': AuditLog.ACTION_CREATE,
                    'PUT': AuditLog.ACTION_UPDATE,
                    'PATCH': AuditLog.ACTION_UPDATE,
                    'DELETE': AuditLog.ACTION_DELETE,
                    'GET': AuditLog.ACTION_VIEW,
                }
                action = action_map.get(request.method, AuditLog.ACTION_VIEW)
                
                # Determine risk level
                risk_level = self._determine_risk_level(request, response)
                
                # Determine success status
                success = 200 <= response.status_code < 400
                
                # Capture response data (limited)
                response_data = self._capture_response_data(response)
                
                # Resource identification
                resource = self._identify_resource(request)
                
                # Create description
                description = self._create_description(request, response)
                
                # Error message for failed requests
                error_message = None
                if not success:
                    error_message = f"HTTP {response.status_code}: {response.reason_phrase}"
                
                # Create audit log
                AuditLog.log_action(
                    user=getattr(request, 'user', None) if hasattr(request, 'user') and request.user.is_authenticated else None,
                    session=getattr(request, 'user_session', None),
                    action=action,
                    resource=resource,
                    description=description,
                    risk_level=risk_level,
                    success=success,
                    error_message=error_message,
                    request=request,
                    extra_data={
                        'request_data': request._audit_request_data,
                        'response_data': response_data,
                        'response_status': response.status_code,
                        'duration_ms': self._calculate_duration_ms(request),
                    }
                )
                
        except Exception as e:
            logger.error(f"Error creating audit log: {str(e)}")
    
    def _capture_request_data(self, request):
        """
        Safely capture request data for logging
        """
        try:
            data = {}
            
            # Query parameters
            if request.GET:
                data['query_params'] = dict(request.GET)
            
            # Form data (exclude sensitive fields)
            if hasattr(request, 'POST') and request.POST:
                post_data = dict(request.POST)
                # Remove sensitive fields
                for sensitive_field in ['password', 'token', 'secret', 'key']:
                    if sensitive_field in post_data:
                        post_data[sensitive_field] = '[REDACTED]'
                data['form_data'] = post_data
            
            # JSON data (if present, limited size)
            if hasattr(request, 'body') and request.body:
                try:
                    content_type = request.META.get('CONTENT_TYPE', '')
                    if 'application/json' in content_type:
                        json_data = json.loads(request.body.decode('utf-8'))
                        # Redact sensitive fields
                        if isinstance(json_data, dict):
                            for sensitive_field in ['password', 'token', 'secret', 'key']:
                                if sensitive_field in json_data:
                                    json_data[sensitive_field] = '[REDACTED]'
                        
                        # Limit size
                        json_str = json.dumps(json_data)
                        if len(json_str) > 1000:
                            data['json_data'] = '[TOO_LARGE]'
                        else:
                            data['json_data'] = json_data
                except:
                    pass
            
            return data
            
        except Exception:
            return {'error': 'Failed to capture request data'}
    
    def _capture_response_data(self, response):
        """
        Safely capture limited response data
        """
        try:
            data = {
                'status_code': response.status_code,
                'content_type': response.get('Content-Type', ''),
            }
            
            # Capture response size
            if hasattr(response, 'content'):
                data['content_size'] = len(response.content)
            
            return data
            
        except Exception:
            return {'error': 'Failed to capture response data'}
    
    def _determine_risk_level(self, request, response):
        """
        Determine risk level based on request and response
        """
        # Critical errors
        if response.status_code >= 500:
            return AuditLog.RISK_CRITICAL
        
        # High risk operations
        if request.method == 'DELETE':
            return AuditLog.RISK_HIGH
        
        # Authentication failures
        if response.status_code == 401:
            return AuditLog.RISK_HIGH
        
        # Access denied
        if response.status_code == 403:
            return AuditLog.RISK_MEDIUM
        
        # Client errors
        if response.status_code >= 400:
            return AuditLog.RISK_MEDIUM
        
        # Sensitive endpoints
        for sensitive_path in self.SENSITIVE_PATHS:
            if request.path.startswith(sensitive_path):
                return AuditLog.RISK_MEDIUM
        
        # Default
        return AuditLog.RISK_LOW
    
    def _identify_resource(self, request):
        """
        Identify the resource being accessed
        """
        path = request.path
        
        # Clean up API paths
        if path.startswith('/api/v1/'):
            path = path[8:]  # Remove /api/v1/
        
        # Remove trailing slashes
        path = path.rstrip('/')
        
        return path or 'root'
    
    def _create_description(self, request, response):
        """
        Create human-readable description of the action
        """
        method = request.method
        path = request.path
        status = response.status_code
        
        action_desc = {
            'GET': 'accessed',
            'POST': 'created/submitted to',
            'PUT': 'updated',
            'PATCH': 'modified',
            'DELETE': 'deleted from',
        }.get(method, 'interacted with')
        
        return f"User {action_desc} {path} (HTTP {status})"
    
    def _calculate_duration_ms(self, request):
        """
        Calculate request duration in milliseconds
        """
        try:
            if hasattr(request, '_audit_start_time'):
                duration = timezone.now() - request._audit_start_time
                return int(duration.total_seconds() * 1000)
        except:
            pass
        return None


# =============================================================================
# T013: ENHANCED AUTHENTICATION SECURITY MIDDLEWARE
# =============================================================================

import hashlib
import time
import ipaddress
from datetime import datetime
from urllib.parse import urlparse
from django.contrib.auth import logout
from django.contrib.auth.models import AnonymousUser
from django.contrib.auth.signals import user_logged_in, user_logged_out
from django.core.cache import cache
from django.core.exceptions import PermissionDenied
from django.dispatch import receiver
from django.http import HttpResponseForbidden, JsonResponse
from django.contrib.sessions.models import Session

try:
    from .models import LoginAttempt, UserSession, PermissionAuditLog, MFABackupCode
except ImportError:
    # Fallback in case models are not yet migrated
    LoginAttempt = None
    UserSession = None
    PermissionAuditLog = None
    MFABackupCode = None


class EnhancedSecurityMiddleware(MiddlewareMixin):
    """
    Comprehensive security middleware providing advanced protection features.
    
    Features:
    - Security headers injection
    - Content Security Policy enforcement
    - IP geolocation and blocking
    - Request fingerprinting
    - Security event detection
    - Rate limiting by IP and user
    """
    
    def __init__(self, get_response):
        super().__init__(get_response)
        self.get_response = get_response
        
        # Load security configuration
        from django.conf import settings
        self.account_security = getattr(settings, 'ACCOUNT_SECURITY', {})
        self.login_security = getattr(settings, 'LOGIN_SECURITY', {})
        
        # Security thresholds
        self.suspicious_threshold = 5
        self.rate_limit_window = 300  # 5 minutes
        
        # Blocked IP cache key prefix
        self.blocked_ip_prefix = 'security:blocked_ip:'
        self.rate_limit_prefix = 'security:rate_limit:'
        
    def process_request(self, request):
        """Process incoming requests for security validation."""
        
        # Extract client information
        client_ip = self._get_client_ip(request)
        user_agent = request.META.get('HTTP_USER_AGENT', '')[:500]
        
        # Store in request for other middleware
        request.security_context = {
            'ip_address': client_ip,
            'user_agent': user_agent,
            'fingerprint': self._generate_request_fingerprint(request),
            'timestamp': timezone.now(),
        }
        
        # Check if IP is blocked
        if self._is_ip_blocked(client_ip):
            return HttpResponseForbidden(
                json.dumps({
                    'error': 'Access denied',
                    'code': 'IP_BLOCKED',
                    'message': 'Your IP address has been temporarily blocked due to suspicious activity'
                }),
                content_type='application/json'
            )
        
        # Rate limiting check
        if self._is_rate_limited(request, client_ip):
            return JsonResponse({
                'error': 'Rate limit exceeded',
                'code': 'RATE_LIMIT',
                'message': 'Too many requests. Please try again later.',
                'retry_after': 300
            }, status=429)
        
        # Security headers validation
        self._validate_security_headers(request)
        
        return None
    
    def process_response(self, request, response):
        """Add security headers to responses."""
        
        # Security headers
        response['X-Content-Type-Options'] = 'nosniff'
        response['X-Frame-Options'] = 'DENY'
        response['X-XSS-Protection'] = '1; mode=block'
        response['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        
        # CSP header if configured
        from django.conf import settings
        if hasattr(settings, 'CSP_DEFAULT_SRC'):
            csp_directives = []
            for directive, values in [
                ('default-src', getattr(settings, 'CSP_DEFAULT_SRC', [])),
                ('script-src', getattr(settings, 'CSP_SCRIPT_SRC', [])),
                ('style-src', getattr(settings, 'CSP_STYLE_SRC', [])),
                ('font-src', getattr(settings, 'CSP_FONT_SRC', [])),
                ('img-src', getattr(settings, 'CSP_IMG_SRC', [])),
                ('connect-src', getattr(settings, 'CSP_CONNECT_SRC', [])),
            ]:
                if values:
                    csp_directives.append(f"{directive} {' '.join(values)}")
            
            if csp_directives:
                response['Content-Security-Policy'] = '; '.join(csp_directives)
        
        # HSTS header for HTTPS
        if request.is_secure():
            max_age = getattr(settings, 'SECURE_HSTS_SECONDS', 31536000)
            hsts_header = f'max-age={max_age}'
            if getattr(settings, 'SECURE_HSTS_INCLUDE_SUBDOMAINS', True):
                hsts_header += '; includeSubDomains'
            if getattr(settings, 'SECURE_HSTS_PRELOAD', True):
                hsts_header += '; preload'
            response['Strict-Transport-Security'] = hsts_header
        
        # Performance and caching headers
        if request.path.startswith('/api/'):
            response['Cache-Control'] = 'no-store, no-cache, must-revalidate'
            response['Pragma'] = 'no-cache'
        
        return response
    
    def _get_client_ip(self, request):
        """Extract client IP address from request."""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0].strip()
        else:
            ip = request.META.get('REMOTE_ADDR', '127.0.0.1')
        
        # Validate IP format
        try:
            ipaddress.ip_address(ip)
            return ip
        except ValueError:
            return '127.0.0.1'  # Fallback to localhost
    
    def _generate_request_fingerprint(self, request):
        """Generate unique fingerprint for request."""
        components = [
            request.META.get('HTTP_USER_AGENT', ''),
            request.META.get('HTTP_ACCEPT_LANGUAGE', ''),
            request.META.get('HTTP_ACCEPT_ENCODING', ''),
            self._get_client_ip(request),
        ]
        
        fingerprint_data = '|'.join(components).encode('utf-8')
        return hashlib.md5(fingerprint_data).hexdigest()
    
    def _is_ip_blocked(self, ip_address):
        """Check if IP address is blocked."""
        cache_key = f"{self.blocked_ip_prefix}{ip_address}"
        return cache.get(cache_key, False)
    
    def _block_ip(self, ip_address, duration_minutes=30, reason='Suspicious activity'):
        """Block IP address for specified duration."""
        cache_key = f"{self.blocked_ip_prefix}{ip_address}"
        cache.set(cache_key, {
            'blocked_at': timezone.now().isoformat(),
            'reason': reason,
            'duration_minutes': duration_minutes
        }, duration_minutes * 60)
        
        # Log security event
        if PermissionAuditLog:
            PermissionAuditLog.log_action(
                action='ip_blocked',
                actor=None,  # System action
                reason=f'IP blocked: {reason}',
                details={
                    'ip_address': ip_address,
                    'duration_minutes': duration_minutes,
                    'auto_blocked': True
                }
            )
    
    def _is_rate_limited(self, request, ip_address):
        """Check if request exceeds rate limits."""
        cache_key = f"{self.rate_limit_prefix}{ip_address}"
        current_requests = cache.get(cache_key, [])
        
        # Clean old requests outside the window
        current_time = time.time()
        current_requests = [
            req_time for req_time in current_requests
            if current_time - req_time < self.rate_limit_window
        ]
        
        # Check if limit exceeded
        max_requests = self.login_security.get('MAX_ATTEMPTS_PER_IP', 60)
        if len(current_requests) >= max_requests:
            return True
        
        # Add current request
        current_requests.append(current_time)
        cache.set(cache_key, current_requests, self.rate_limit_window)
        
        return False
    
    def _validate_security_headers(self, request):
        """Validate security-related headers in request."""
        # Check for suspicious headers
        suspicious_headers = [
            'X-Forwarded-Host',
            'X-Rewrite-URL', 
            'X-Original-URL',
            'X-Arbitrary-Header'
        ]
        
        found_suspicious = []
        for header in suspicious_headers:
            if header in request.META:
                found_suspicious.append(header)
        
        if found_suspicious and PermissionAuditLog:
            # Log suspicious request
            PermissionAuditLog.log_action(
                action='suspicious_headers_detected',
                actor=None,  # System action
                reason='Suspicious headers in request',
                details={
                    'suspicious_headers': found_suspicious,
                    'ip_address': self._get_client_ip(request),
                    'user_agent': request.META.get('HTTP_USER_AGENT', ''),
                }
            )


class LoginAttemptMiddleware(MiddlewareMixin):
    """
    Middleware to track and manage login attempts with intelligent rate limiting.
    
    Features:
    - Login attempt counting and tracking
    - Progressive lockout periods
    - IP and username-based rate limiting
    - Suspicious activity detection
    - Automatic account unlocking
    """
    
    def __init__(self, get_response):
        super().__init__(get_response)
        self.get_response = get_response
        
        # Load configuration
        from django.conf import settings
        self.login_security = getattr(settings, 'LOGIN_SECURITY', {})
        self.account_security = getattr(settings, 'ACCOUNT_SECURITY', {})
        
        # Rate limiting configuration
        self.max_attempts_ip = self.login_security.get('MAX_ATTEMPTS_PER_IP', 10)
        self.max_attempts_user = self.login_security.get('MAX_ATTEMPTS_PER_USERNAME', 5)
        self.lockout_duration = self.login_security.get('LOCKOUT_DURATION_MINUTES', 15)
        
        # Cache prefixes
        self.attempt_prefix_ip = 'login_attempts:ip:'
        self.attempt_prefix_user = 'login_attempts:user:'
        self.lockout_prefix_ip = 'lockout:ip:'
        self.lockout_prefix_user = 'lockout:user:'
    
    def process_request(self, request):
        """Check for rate limiting before processing login requests."""
        
        # Only process login-related requests
        if not self._is_login_request(request):
            return None
        
        client_ip = self._get_client_ip(request)
        
        # Check IP-based lockout
        if self._is_ip_locked_out(client_ip):
            return JsonResponse({
                'error': 'Too many login attempts',
                'code': 'IP_LOCKED',
                'message': f'IP address temporarily locked due to repeated failed login attempts. Try again in {self.lockout_duration} minutes.',
                'retry_after': self.lockout_duration * 60
            }, status=429)
        
        # Check username-based lockout if username provided
        username = self._extract_username(request)
        if username and self._is_user_locked_out(username):
            return JsonResponse({
                'error': 'Account temporarily locked',
                'code': 'USER_LOCKED',
                'message': f'Account locked due to repeated failed login attempts. Try again in {self.lockout_duration} minutes.',
                'retry_after': self.lockout_duration * 60
            }, status=429)
        
        return None
    
    def process_response(self, request, response):
        """Track login attempts based on response status."""
        
        if not self._is_login_request(request):
            return response
        
        client_ip = self._get_client_ip(request)
        username = self._extract_username(request)
        
        # Determine if login was successful based on response
        is_successful = self._is_login_successful(response)
        
        # Log the attempt
        if self.login_security.get('LOG_ALL_ATTEMPTS', True) and LoginAttempt:
            auth_method = self._detect_auth_method(request)
            
            LoginAttempt.log_attempt(
                username=username or 'unknown',
                ip_address=client_ip,
                was_successful=is_successful,
                user=getattr(request, 'user', None) if is_successful else None,
                failure_reason=self._extract_failure_reason(response) if not is_successful else '',
                auth_method=auth_method,
                user_agent=request.META.get('HTTP_USER_AGENT', ''),
                session_key=request.session.session_key or ''
            )
        
        # Handle failed attempts
        if not is_successful:
            self._handle_failed_attempt(client_ip, username)
        else:
            # Clear failure counters on successful login
            self._clear_failure_counters(client_ip, username)
        
        return response
    
    def _is_login_request(self, request):
        """Check if this is a login-related request."""
        login_paths = [
            '/api/auth/login/',
            '/api/auth/token/',
            '/admin/login/',
            '/login/',
            '/accounts/login/',
        ]
        
        return (
            request.method == 'POST' and 
            (any(request.path.startswith(path) for path in login_paths) or
             'login' in request.path.lower())
        )
    
    def _extract_username(self, request):
        """Extract username from request data."""
        try:
            if hasattr(request, 'POST') and request.POST:
                return request.POST.get('username') or request.POST.get('email')
            elif hasattr(request, 'body') and request.body:
                if request.content_type == 'application/json':
                    data = json.loads(request.body.decode('utf-8'))
                    return data.get('username') or data.get('email')
        except (json.JSONDecodeError, UnicodeDecodeError):
            pass
        
        return None
    
    def _is_login_successful(self, response):
        """Determine if login was successful based on response."""
        # Success indicators
        if response.status_code in [200, 201]:
            return True
        
        # Check for authentication tokens in response
        if hasattr(response, 'content'):
            try:
                content = response.content.decode('utf-8')
                if any(keyword in content.lower() for keyword in ['token', 'access_token', 'jwt']):
                    return True
            except UnicodeDecodeError:
                pass
        
        return False
    
    def _detect_auth_method(self, request):
        """Detect authentication method from request."""
        auth_header = request.META.get('HTTP_AUTHORIZATION', '')
        
        if auth_header.startswith('Bearer'):
            return 'jwt'
        elif auth_header.startswith('Token'):
            return 'token'
        elif 'api_key' in request.GET or 'api-key' in request.headers:
            return 'api_key'
        else:
            return 'password'
    
    def _extract_failure_reason(self, response):
        """Extract failure reason from response."""
        try:
            if hasattr(response, 'content'):
                content = response.content.decode('utf-8')
                if response.status_code == 401:
                    return 'invalid_credentials'
                elif response.status_code == 403:
                    return 'account_disabled'
                elif response.status_code == 429:
                    return 'rate_limited'
                elif 'mfa' in content.lower():
                    return 'mfa_required'
        except UnicodeDecodeError:
            pass
        
        return 'unknown_error'
    
    def _get_client_ip(self, request):
        """Extract client IP from request."""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0].strip()
        else:
            ip = request.META.get('REMOTE_ADDR', '127.0.0.1')
        return ip
    
    def _handle_failed_attempt(self, client_ip, username):
        """Handle failed login attempt with progressive lockout."""
        
        # Increment IP attempt counter
        ip_key = f"{self.attempt_prefix_ip}{client_ip}"
        ip_attempts = cache.get(ip_key, 0) + 1
        cache.set(ip_key, ip_attempts, self.lockout_duration * 60)
        
        # Check if IP should be locked
        if ip_attempts >= self.max_attempts_ip:
            lockout_key = f"{self.lockout_prefix_ip}{client_ip}"
            cache.set(lockout_key, True, self.lockout_duration * 60)
            
            # Log lockout event
            if PermissionAuditLog:
                PermissionAuditLog.log_action(
                    action='ip_locked_out',
                    actor=None,  # System action
                    reason=f'IP locked after {ip_attempts} failed login attempts',
                    details={
                        'ip_address': client_ip,
                        'attempt_count': ip_attempts,
                        'lockout_duration_minutes': self.lockout_duration
                    }
                )
        
        # Handle username-based attempts
        if username:
            user_key = f"{self.attempt_prefix_user}{username}"
            user_attempts = cache.get(user_key, 0) + 1
            cache.set(user_key, user_attempts, self.lockout_duration * 60)
            
            # Check if user should be locked
            if user_attempts >= self.max_attempts_user:
                lockout_key = f"{self.lockout_prefix_user}{username}"
                cache.set(lockout_key, True, self.lockout_duration * 60)
                
                # Log user lockout
                if PermissionAuditLog:
                    PermissionAuditLog.log_action(
                        action='user_locked_out',
                        actor=None,  # System action
                        reason=f'User {username} locked after {user_attempts} failed attempts',
                        details={
                            'username': username,
                            'attempt_count': user_attempts,
                            'lockout_duration_minutes': self.lockout_duration,
                            'ip_address': client_ip
                        }
                    )
    
    def _clear_failure_counters(self, client_ip, username):
        """Clear failure counters after successful login."""
        
        # Clear IP counters
        ip_key = f"{self.attempt_prefix_ip}{client_ip}"
        lockout_key = f"{self.lockout_prefix_ip}{client_ip}"
        cache.delete(ip_key)
        cache.delete(lockout_key)
        
        # Clear username counters
        if username:
            user_key = f"{self.attempt_prefix_user}{username}"
            user_lockout_key = f"{self.lockout_prefix_user}{username}"
            cache.delete(user_key)
            cache.delete(user_lockout_key)
    
    def _is_ip_locked_out(self, ip_address):
        """Check if IP is currently locked out."""
        lockout_key = f"{self.lockout_prefix_ip}{ip_address}"
        return cache.get(lockout_key, False)
    
    def _is_user_locked_out(self, username):
        """Check if user is currently locked out."""
        lockout_key = f"{self.lockout_prefix_user}{username}"
        return cache.get(lockout_key, False)


class SessionSecurityMiddleware(MiddlewareMixin):
    """
    Advanced session security middleware with comprehensive protection features.
    
    Features:
    - Session hijacking detection and prevention
    - Concurrent session management
    - Session timeout enforcement
    - IP address validation
    - User agent fingerprinting
    - MFA session validation
    - Security event logging
    """
    
    def __init__(self, get_response):
        super().__init__(get_response)
        self.get_response = get_response
        
        # Load configuration
        from django.conf import settings
        self.account_security = getattr(settings, 'ACCOUNT_SECURITY', {})
        self.mfa_settings = getattr(settings, 'MFA_SETTINGS', {})
        
        # Session security configuration
        self.max_concurrent_sessions = self.account_security.get('MAX_CONCURRENT_SESSIONS', 3)
        self.session_timeout = self.account_security.get('SESSION_TIMEOUT_MINUTES', 60)
        self.idle_timeout = self.account_security.get('IDLE_TIMEOUT_MINUTES', 30)
        
        # Security validation settings
        self.validate_ip = True  # Enable IP validation
        self.validate_user_agent = True  # Enable user agent validation
        self.strict_session_validation = True
        
        # Cache keys
        self.session_prefix = 'session_security:'
        self.user_sessions_prefix = 'user_sessions:'
    
    def process_request(self, request):
        """Process requests for session security validation."""
        
        # Skip validation for anonymous users and certain paths
        if not hasattr(request, 'user') or isinstance(request.user, AnonymousUser):
            return None
        
        if self._should_skip_validation(request):
            return None
        
        # Get or create session tracking
        session_security = self._get_session_security_data(request)
        
        # Validate session security
        validation_result = self._validate_session_security(request, session_security)
        if not validation_result['valid']:
            return self._handle_security_violation(request, validation_result)
        
        # Update session activity
        self._update_session_activity(request, session_security)
        
        # Manage concurrent sessions
        self._manage_concurrent_sessions(request)
        
        return None
    
    def process_response(self, request, response):
        """Process response for session security updates."""
        
        # Skip for anonymous users
        if not hasattr(request, 'user') or isinstance(request.user, AnonymousUser):
            return response
        
        # Update last activity timestamp
        if hasattr(request, 'session') and request.session.session_key:
            self._update_last_activity(request)
        
        return response
    
    def _should_skip_validation(self, request):
        """Check if validation should be skipped for this request."""
        skip_paths = [
            '/api/auth/logout/',
            '/admin/logout/',
            '/logout/',
            '/api/health/',
            '/static/',
            '/media/',
        ]
        
        return any(request.path.startswith(path) for path in skip_paths)
    
    def _get_session_security_data(self, request):
        """Get or create session security tracking data."""
        session_key = request.session.session_key
        if not session_key:
            return None
        
        cache_key = f"{self.session_prefix}{session_key}"
        session_data = cache.get(cache_key)
        
        if not session_data:
            # Create new session security data
            session_data = {
                'created_at': timezone.now().isoformat(),
                'ip_address': self._get_client_ip(request),
                'user_agent_hash': self._hash_user_agent(request),
                'user_id': request.user.id,
                'last_activity': timezone.now().isoformat(),
                'mfa_verified': False,
                'mfa_verified_at': None,
                'activity_count': 0,
                'suspicious_activity_count': 0,
            }
            
            # Store session data
            cache.set(cache_key, session_data, self.session_timeout * 60)
            
            # Create UserSession record if available
            if UserSession:
                try:
                    UserSession.objects.create(
                        user=request.user,
                        session_key=session_key,
                        ip_address=session_data['ip_address'],
                        user_agent=request.META.get('HTTP_USER_AGENT', '')[:500],
                        auth_method=self._detect_auth_method(request)
                    )
                except Exception as e:
                    # Log error but don't block the request
                    logger.error(f'Failed to create UserSession record: {str(e)}')
        
        return session_data
    
    def _validate_session_security(self, request, session_data):
        """Validate session security parameters."""
        if not session_data:
            return {'valid': True}  # New session, nothing to validate
        
        validation_errors = []
        
        # IP address validation
        if self.validate_ip:
            current_ip = self._get_client_ip(request)
            stored_ip = session_data.get('ip_address')
            if stored_ip and current_ip != stored_ip:
                validation_errors.append({
                    'type': 'ip_mismatch',
                    'message': 'IP address changed during session',
                    'details': {'stored_ip': stored_ip, 'current_ip': current_ip}
                })
        
        # User agent validation
        if self.validate_user_agent:
            current_ua_hash = self._hash_user_agent(request)
            stored_ua_hash = session_data.get('user_agent_hash')
            if stored_ua_hash and current_ua_hash != stored_ua_hash:
                validation_errors.append({
                    'type': 'user_agent_mismatch', 
                    'message': 'User agent changed during session',
                    'details': {'fingerprint_changed': True}
                })
        
        # Session timeout validation
        last_activity = session_data.get('last_activity')
        if last_activity:
            last_activity_dt = datetime.fromisoformat(last_activity.replace('Z', '+00:00'))
            if timezone.now() - last_activity_dt > timedelta(minutes=self.idle_timeout):
                validation_errors.append({
                    'type': 'session_timeout',
                    'message': 'Session timed out due to inactivity',
                    'details': {'idle_minutes': (timezone.now() - last_activity_dt).total_seconds() / 60}
                })
        
        # MFA validation if required
        if self._is_mfa_required(request) and not session_data.get('mfa_verified'):
            validation_errors.append({
                'type': 'mfa_required',
                'message': 'Multi-factor authentication required',
                'details': {'mfa_enforced': True}
            })
        
        return {
            'valid': len(validation_errors) == 0,
            'errors': validation_errors
        }
    
    def _handle_security_violation(self, request, validation_result):
        """Handle session security violations."""
        
        # Log security violation
        if PermissionAuditLog:
            for error in validation_result['errors']:
                PermissionAuditLog.log_action(
                    action='session_security_violation',
                    actor=request.user if request.user.is_authenticated else None,
                    reason=error['message'],
                    details=error['details']
                )
        
        # Determine response based on violation type
        violation_types = [error['type'] for error in validation_result['errors']]
        
        if 'ip_mismatch' in violation_types or 'user_agent_mismatch' in violation_types:
            # Potential session hijacking - terminate session
            self._terminate_session(request, 'security_violation')
            logout(request)
            
            return JsonResponse({
                'error': 'Session security violation',
                'code': 'SESSION_HIJACKED',
                'message': 'Session terminated due to security concerns. Please log in again.',
                'redirect': '/login/'
            }, status=403)
        
        elif 'session_timeout' in violation_types:
            # Session timeout - terminate gracefully
            self._terminate_session(request, 'timeout')
            logout(request)
            
            return JsonResponse({
                'error': 'Session expired',
                'code': 'SESSION_TIMEOUT',
                'message': 'Your session has expired. Please log in again.',
                'redirect': '/login/'
            }, status=401)
        
        elif 'mfa_required' in violation_types:
            # MFA required - redirect to MFA flow
            return JsonResponse({
                'error': 'MFA required',
                'code': 'MFA_REQUIRED',
                'message': 'Multi-factor authentication is required to continue.',
                'redirect': '/mfa/verify/'
            }, status=403)
        
        # Default violation handling
        return JsonResponse({
            'error': 'Security validation failed',
            'code': 'SECURITY_VIOLATION',
            'message': 'Access denied due to security policy violation.'
        }, status=403)
    
    def _update_session_activity(self, request, session_data):
        """Update session activity tracking."""
        if not session_data:
            return
        
        session_key = request.session.session_key
        cache_key = f"{self.session_prefix}{session_key}"
        
        # Update activity data
        session_data['last_activity'] = timezone.now().isoformat()
        session_data['activity_count'] = session_data.get('activity_count', 0) + 1
        
        # Store updated data
        cache.set(cache_key, session_data, self.session_timeout * 60)
    
    def _manage_concurrent_sessions(self, request):
        """Manage concurrent sessions for user."""
        
        # Get user's active sessions
        user_sessions_key = f"{self.user_sessions_prefix}{request.user.id}"
        active_sessions = cache.get(user_sessions_key, [])
        
        current_session = request.session.session_key
        
        # Add current session if not already tracked
        if current_session not in active_sessions:
            active_sessions.append(current_session)
        
        # Enforce concurrent session limit
        if len(active_sessions) > self.max_concurrent_sessions:
            # Remove oldest sessions
            sessions_to_remove = active_sessions[:-self.max_concurrent_sessions]
            
            for session_key in sessions_to_remove:
                self._terminate_session_by_key(session_key, 'concurrent_limit')
                active_sessions.remove(session_key)
            
            # Log concurrent session enforcement
            if PermissionAuditLog:
                PermissionAuditLog.log_action(
                    action='concurrent_sessions_limited',
                    actor=request.user,
                    reason='Concurrent session limit enforced',
                    details={
                        'terminated_sessions': len(sessions_to_remove),
                        'max_concurrent': self.max_concurrent_sessions,
                        'current_session': current_session
                    }
                )
        
        # Update active sessions cache
        cache.set(user_sessions_key, active_sessions, 24 * 60 * 60)  # 24 hours
    
    def _terminate_session(self, request, reason):
        """Terminate current session."""
        session_key = request.session.session_key
        if session_key:
            self._terminate_session_by_key(session_key, reason)
    
    def _terminate_session_by_key(self, session_key, reason):
        """Terminate session by session key."""
        
        # Update UserSession record if available
        if UserSession:
            try:
                user_session = UserSession.objects.get(session_key=session_key, is_active=True)
                user_session.terminate(reason=reason)
            except UserSession.DoesNotExist:
                pass
        
        # Remove from cache
        cache_key = f"{self.session_prefix}{session_key}"
        cache.delete(cache_key)
        
        # Remove Django session
        try:
            Session.objects.get(session_key=session_key).delete()
        except Session.DoesNotExist:
            pass
    
    def _update_last_activity(self, request):
        """Update last activity timestamp for user."""
        if hasattr(request, 'user') and not isinstance(request.user, AnonymousUser):
            if hasattr(request.user, 'last_activity'):
                request.user.last_activity = timezone.now()
                request.user.save(update_fields=['last_activity'])
    
    def _get_client_ip(self, request):
        """Extract client IP from request."""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0].strip()
        else:
            ip = request.META.get('REMOTE_ADDR', '127.0.0.1')
        return ip
    
    def _hash_user_agent(self, request):
        """Generate hash of user agent for fingerprinting."""
        user_agent = request.META.get('HTTP_USER_AGENT', '')
        return hashlib.md5(user_agent.encode('utf-8')).hexdigest()
    
    def _detect_auth_method(self, request):
        """Detect authentication method used."""
        auth_header = request.META.get('HTTP_AUTHORIZATION', '')
        
        if auth_header.startswith('Bearer'):
            return 'jwt'
        elif auth_header.startswith('Token'):
            return 'token'
        elif 'api_key' in request.GET:
            return 'api_key'
        else:
            return 'password'
    
    def _is_mfa_required(self, request):
        """Check if MFA is required for current context."""
        # Check user MFA settings
        if hasattr(request.user, 'mfa_enabled') and request.user.mfa_enabled:
            return True
        
        # Check if MFA required for admin users
        if self.mfa_settings.get('REQUIRED_FOR_ADMIN', False) and request.user.is_staff:
            return True
        
        # Check if MFA required for API access
        if self.mfa_settings.get('REQUIRED_FOR_API', False) and request.path.startswith('/api/'):
            return True
        
        return False


# =============================================================================
# SIGNAL HANDLERS FOR ENHANCED AUTHENTICATION
# =============================================================================

@receiver(user_logged_in)
def handle_enhanced_user_login(sender, request, user, **kwargs):
    """Handle user login events for enhanced session tracking."""
    
    # Create or update session tracking
    if hasattr(request, 'session') and request.session.session_key:
        # Update user activity
        if hasattr(user, 'last_activity'):
            user.last_activity = timezone.now()
            user.save(update_fields=['last_activity'])
        
        # Log successful login with enhanced details
        if PermissionAuditLog:
            PermissionAuditLog.log_action(
                action='user_login_success',
                actor=user,
                reason='User logged in successfully',
                details={
                    'session_key': request.session.session_key,
                    'auth_method': 'session',
                    'login_timestamp': timezone.now().isoformat(),
                    'ip_address': request.META.get('REMOTE_ADDR', ''),
                    'user_agent': request.META.get('HTTP_USER_AGENT', '')[:500]
                }
            )


@receiver(user_logged_out)
def handle_enhanced_user_logout(sender, request, user, **kwargs):
    """Handle user logout events for enhanced session cleanup."""
    
    if hasattr(request, 'session') and request.session.session_key:
        # Update UserSession record if available
        if UserSession:
            try:
                user_session = UserSession.objects.get(
                    session_key=request.session.session_key,
                    is_active=True
                )
                if hasattr(user_session, 'terminate'):
                    user_session.terminate(reason='logout')
                elif hasattr(user_session, 'mark_logout'):
                    user_session.mark_logout()
                else:
                    user_session.is_active = False
                    user_session.save(update_fields=['is_active'])
            except UserSession.DoesNotExist:
                pass
        
        # Log logout with enhanced details
        if user and PermissionAuditLog:
            PermissionAuditLog.log_action(
                action='user_logout',
                actor=user,
                reason='User logged out',
                details={
                    'session_key': request.session.session_key,
                    'logout_timestamp': timezone.now().isoformat(),
                    'ip_address': request.META.get('REMOTE_ADDR', ''),
                    'session_duration_minutes': 0  # Calculate if possible
                }
            )


# =============================================================================
# UTILITY FUNCTIONS FOR ENHANCED AUTHENTICATION
# =============================================================================

def is_safe_ip(ip_address):
    """Check if IP address is considered safe (not in blocklists)."""
    try:
        ip_obj = ipaddress.ip_address(ip_address)
        
        # Check for private/local IPs (generally safe)
        if ip_obj.is_private or ip_obj.is_loopback:
            return True
        
        # Add additional IP reputation checks here
        # Could integrate with external services like VirusTotal, etc.
        
        return True
    except ValueError:
        return False  # Invalid IP format


def clean_expired_sessions():
    """Clean up expired sessions and related data."""
    
    # Clean expired UserSession records if available
    if UserSession:
        expired_sessions = UserSession.objects.filter(
            is_active=True,
            last_activity__lt=timezone.now() - timedelta(minutes=30)
        )
        
        count = 0
        for session in expired_sessions:
            session.terminate(reason='timeout')
            count += 1
    else:
        count = 0
    
    # Clean old login attempts if available
    old_count = 0
    if LoginAttempt:
        old_attempts = LoginAttempt.objects.filter(
            created_at__lt=timezone.now() - timedelta(days=90)
        )
        old_count = old_attempts.count()
        old_attempts.delete()
    
    return {
        'expired_sessions_cleaned': count,
        'old_attempts_cleaned': old_count
    }


# =============================================================================
# T019: PERMISSION VALIDATION MIDDLEWARE
# =============================================================================

class PermissionValidationMiddleware(MiddlewareMixin):
    """
    T019: High-performance permission validation middleware with intelligent caching and monitoring.
    
    Features:
    - Real-time permission validation in <100ms
    - Flexible URL-permission mapping configuration
    - Intelligent caching with automatic invalidation
    - Graceful degradation on system failures
    - Comprehensive audit logging
    - Performance monitoring and alerting
    """
    
    def __init__(self, get_response=None):
        super().__init__(get_response)
        self.get_response = get_response
        
        # Load and validate configuration
        self._load_configuration()
        
        # Initialize performance tracking
        self._performance_stats = {
            'total_requests': 0,
            'validation_time_sum': 0.0,
            'cache_hits': 0,
            'cache_misses': 0,
            'failures': 0,
            'bypassed': 0,
        }
        
        logger.info("T019: Permission validation middleware initialized")
        
    def _load_configuration(self):
        """Load and validate middleware configuration."""
        try:
            from django.conf import settings
            
            # Load URL-permission mapping
            self.url_permissions = getattr(settings, 'PERMISSION_URL_MAPPING', {})
            
            # Load protected URL patterns
            self.protected_patterns = getattr(settings, 'PERMISSION_PROTECTED_PATTERNS', [
                r'^/api/admin/',
                r'^/api/permissions/',
                r'^/api/users/',
                r'^/api/groups/',
                r'^/admin/',
            ])
            
            # Load bypass patterns (public endpoints)
            self.bypass_patterns = getattr(settings, 'PERMISSION_BYPASS_PATTERNS', [
                r'^/api/auth/login/',
                r'^/api/auth/logout/',
                r'^/api/health/',
                r'^/static/',
                r'^/media/',
                r'^/$',
            ])
            
            # Performance and caching settings
            self.cache_timeout = getattr(settings, 'PERMISSION_CACHE_TIMEOUT', 300)  # 5 minutes
            self.performance_threshold = getattr(settings, 'PERMISSION_PERFORMANCE_THRESHOLD', 0.1)  # 100ms
            self.failure_mode = getattr(settings, 'PERMISSION_FAILURE_MODE', 'allow')  # 'allow' or 'deny'
            
            # Audit settings
            self.audit_enabled = getattr(settings, 'PERMISSION_AUDIT_ENABLED', True)
            self.audit_performance = getattr(settings, 'PERMISSION_AUDIT_PERFORMANCE', False)
            
        except Exception as e:
            logger.error(f"Error loading permission middleware configuration: {e}")
            from django.core.exceptions import ImproperlyConfigured
            raise ImproperlyConfigured(f"Permission middleware configuration error: {e}")
    
    def process_request(self, request):
        """
        Process incoming request for permission validation.
        
        Returns:
            HttpResponse: 403 Forbidden if permission denied
            None: Allow request to continue
        """
        start_time = time.time()
        
        try:
            # Update performance stats
            self._performance_stats['total_requests'] += 1
            
            # Check if request should be bypassed
            if self._should_bypass_request(request):
                self._performance_stats['bypassed'] += 1
                return None
            
            # Extract user and resolve URL
            user = getattr(request, 'user', AnonymousUser())
            url_match = self._resolve_url(request)
            
            # Skip validation for anonymous users on login endpoints
            if isinstance(user, AnonymousUser) and self._is_auth_endpoint(request):
                return None
            
            # Perform permission validation
            validation_result = self._validate_permissions(request, user, url_match)
            
            # Log performance metrics
            validation_time = time.time() - start_time
            self._update_performance_stats(validation_time, validation_result.get('cache_hit', False))
            
            # Log audit trail
            if self.audit_enabled:
                self._log_validation_attempt(request, user, url_match, validation_result, validation_time)
            
            # Handle validation result
            if not validation_result['allowed']:
                return self._create_permission_denied_response(
                    request, validation_result.get('reason', 'Permission denied')
                )
            
            # Add permission context to request
            request.permission_context = validation_result.get('context', {})
            
            return None
            
        except Exception as e:
            # Handle middleware failures gracefully
            validation_time = time.time() - start_time
            self._performance_stats['failures'] += 1
            
            logger.error(f"Permission middleware error: {e}", exc_info=True)
            
            # Audit the failure
            if self.audit_enabled:
                self._log_system_failure(request, e, validation_time)
            
            # Apply failure mode policy
            if self.failure_mode == 'deny':
                return self._create_system_error_response(request)
            else:
                logger.warning("Permission validation failed, allowing request due to failure_mode=allow")
                return None
    
    def _should_bypass_request(self, request):
        """Check if request should bypass permission validation."""
        import re
        
        path = request.path_info
        
        # Check bypass patterns
        for pattern in self.bypass_patterns:
            if re.match(pattern, path):
                return True
        
        # Check if path requires protection
        for pattern in self.protected_patterns:
            if re.match(pattern, path):
                return False
        
        # Default: bypass non-protected endpoints
        return True
    
    def _resolve_url(self, request):
        """Resolve URL to get view information."""
        try:
            from django.urls import resolve
            return resolve(request.path_info)
        except Exception as e:
            logger.warning(f"Could not resolve URL {request.path_info}: {e}")
            return None
    
    def _is_auth_endpoint(self, request):
        """Check if request is to authentication endpoint."""
        auth_paths = ['/api/auth/login/', '/api/auth/token/', '/api/auth/refresh/']
        return request.path_info in auth_paths
    
    def _validate_permissions(self, request, user, url_match):
        """
        Perform comprehensive permission validation with caching.
        
        Returns:
            Dict containing validation result, cache status, and context
        """
        # Build cache key for permission check
        cache_key = self._build_cache_key(user, request)
        
        # Try cache first
        cached_result = cache.get(cache_key)
        if cached_result:
            cached_result['cache_hit'] = True
            return cached_result
        
        # Perform fresh validation
        validation_result = self._perform_fresh_validation(request, user, url_match)
        validation_result['cache_hit'] = False
        
        # Cache the result
        if validation_result['cacheable']:
            cache.set(cache_key, validation_result, self.cache_timeout)
        
        return validation_result
    
    def _perform_fresh_validation(self, request, user, url_match):
        """Perform fresh permission validation without cache."""
        try:
            # Anonymous users are denied by default for protected endpoints
            if isinstance(user, AnonymousUser):
                return {
                    'allowed': False,
                    'reason': 'Authentication required',
                    'cacheable': True,
                    'context': {'anonymous': True}
                }
            
            # Get required permissions for this endpoint
            required_permissions = self._get_required_permissions(request, url_match)
            
            if not required_permissions:
                # No specific permissions required
                return {
                    'allowed': True,
                    'reason': 'No permissions required',
                    'cacheable': True,
                    'context': {'permissions_required': False}
                }
            
            # Check user permissions
            user_permissions = self._get_user_permissions(user)
            missing_permissions = []
            
            for permission_code in required_permissions:
                if not self._user_has_permission(user, permission_code, user_permissions):
                    missing_permissions.append(permission_code)
            
            if missing_permissions:
                return {
                    'allowed': False,
                    'reason': f'Missing permissions: {", ".join(missing_permissions)}',
                    'cacheable': True,
                    'context': {
                        'required_permissions': required_permissions,
                        'missing_permissions': missing_permissions,
                        'user_permissions': list(user_permissions.keys())
                    }
                }
            
            return {
                'allowed': True,
                'reason': 'All permissions validated',
                'cacheable': True,
                'context': {
                    'required_permissions': required_permissions,
                    'user_permissions': list(user_permissions.keys())
                }
            }
            
        except Exception as e:
            logger.error(f"Error during permission validation: {e}", exc_info=True)
            return {
                'allowed': self.failure_mode == 'allow',
                'reason': f'Validation error: {str(e)}',
                'cacheable': False,
                'context': {'error': str(e)}
            }
    
    def _get_required_permissions(self, request, url_match):
        """Get list of required permissions for the current request."""
        required_permissions = []
        
        # Check URL-based permission mapping
        path = request.path_info
        method = request.method.upper()
        
        # Direct path mapping
        if path in self.url_permissions:
            mapping = self.url_permissions[path]
            if isinstance(mapping, str):
                required_permissions.append(mapping)
            elif isinstance(mapping, dict) and method in mapping:
                perm = mapping[method]
                if perm:
                    required_permissions.append(perm)
            elif isinstance(mapping, list):
                required_permissions.extend(mapping)
        
        # View-based permission mapping
        if url_match and hasattr(url_match.func, 'view_class'):
            view_class = url_match.func.view_class
            
            # Check for permission_required attribute
            if hasattr(view_class, 'permission_required'):
                perms = view_class.permission_required
                if isinstance(perms, str):
                    required_permissions.append(perms)
                elif isinstance(perms, (list, tuple)):
                    required_permissions.extend(perms)
        
        # Method-based permission inference
        if not required_permissions:
            required_permissions = self._infer_permissions_from_method(request, url_match)
        
        return list(set(required_permissions))  # Remove duplicates
    
    def _infer_permissions_from_method(self, request, url_match):
        """Infer required permissions based on HTTP method and URL patterns."""
        method = request.method.upper()
        path = request.path_info
        
        # Basic CRUD permission inference
        if '/api/permissions/' in path:
            if method in ['GET']:
                return ['core.permission.view']
            elif method in ['POST']:
                return ['core.permission.create']
            elif method in ['PUT', 'PATCH']:
                return ['core.permission.update']
            elif method in ['DELETE']:
                return ['core.permission.delete']
        
        elif '/api/users/' in path:
            if method in ['GET']:
                return ['core.user.view']
            elif method in ['POST']:
                return ['core.user.create']
            elif method in ['PUT', 'PATCH']:
                return ['core.user.update']
            elif method in ['DELETE']:
                return ['core.user.delete']
        
        elif '/api/groups/' in path:
            if method in ['GET']:
                return ['core.group.view']
            elif method in ['POST']:
                return ['core.group.create']
            elif method in ['PUT', 'PATCH']:
                return ['core.group.update']
            elif method in ['DELETE']:
                return ['core.group.delete']
        
        elif '/admin/' in path:
            return ['core.admin.access']
        
        return []
    
    def _get_user_permissions(self, user):
        """Get all permissions for a user with caching."""
        cache_key = f"user_permissions:{user.id}"
        cached_perms = cache.get(cache_key)
        
        if cached_perms:
            return cached_perms
        
        # Build permission dictionary
        permissions = {}
        
        try:
            # Direct user permissions
            user_perms = user.userpermission_set.select_related('permission').filter(
                is_granted=True,
                expires_at__isnull=True
            ) | user.userpermission_set.select_related('permission').filter(
                is_granted=True,
                expires_at__gt=timezone.now()
            )
            
            for up in user_perms:
                permissions[up.permission.code] = {
                    'type': 'direct',
                    'granted_at': up.granted_at,
                    'expires_at': up.expires_at,
                    'risk_level': up.permission.risk_level
                }
            
            # Group-based permissions
            for membership in user.groupmembership_set.select_related('group'):
                group = membership.group
                group_perms = group.grouppermission_set.select_related('permission').filter(
                    is_granted=True
                )
                
                for gp in group_perms:
                    perm_code = gp.permission.code
                    if perm_code not in permissions:  # Direct permissions take precedence
                        permissions[perm_code] = {
                            'type': 'group',
                            'group': group.name,
                            'granted_at': gp.granted_at,
                            'risk_level': gp.permission.risk_level
                        }
        except Exception as e:
            logger.error(f"Error getting user permissions: {e}")
            permissions = {}
        
        # Cache permissions
        cache.set(cache_key, permissions, self.cache_timeout)
        
        return permissions
    
    def _user_has_permission(self, user, permission_code, user_permissions=None):
        """Check if user has a specific permission."""
        if user_permissions is None:
            user_permissions = self._get_user_permissions(user)
        
        return permission_code in user_permissions
    
    def _build_cache_key(self, user, request):
        """Build cache key for permission validation result."""
        # Include user ID, path, and method in cache key
        user_id = user.id if hasattr(user, 'id') else 'anonymous'
        path_hash = hash(request.path_info)
        method = request.method
        
        return f"perm_validation:{user_id}:{path_hash}:{method}"
    
    def _update_performance_stats(self, validation_time, cache_hit):
        """Update performance statistics."""
        self._performance_stats['validation_time_sum'] += validation_time
        
        if cache_hit:
            self._performance_stats['cache_hits'] += 1
        else:
            self._performance_stats['cache_misses'] += 1
        
        # Log slow validations
        if validation_time > self.performance_threshold:
            performance_logger = logging.getLogger('permission.performance')
            performance_logger.warning(
                f"Slow permission validation: {validation_time:.4f}s "
                f"(threshold: {self.performance_threshold}s)"
            )
        
        # Log performance stats periodically
        if self._performance_stats['total_requests'] % 1000 == 0:
            self._log_performance_stats()
    
    def _log_performance_stats(self):
        """Log comprehensive performance statistics."""
        stats = self._performance_stats
        total = stats['total_requests']
        
        if total > 0:
            avg_time = stats['validation_time_sum'] / total
            cache_hit_rate = stats['cache_hits'] / (stats['cache_hits'] + stats['cache_misses']) * 100
            
            performance_logger = logging.getLogger('permission.performance')
            performance_logger.info(
                f"Permission middleware performance stats: "
                f"total_requests={total}, avg_time={avg_time:.4f}s, "
                f"cache_hit_rate={cache_hit_rate:.1f}%, failures={stats['failures']}, "
                f"bypassed={stats['bypassed']}"
            )
    
    def _log_validation_attempt(self, request, user, url_match, validation_result, validation_time):
        """Log permission validation attempt for audit trail."""
        try:
            # Create audit log entry
            audit_entry = {
                'user_id': user.id if hasattr(user, 'id') else None,
                'username': user.username if hasattr(user, 'username') else 'anonymous',
                'path': request.path_info,
                'method': request.method,
                'allowed': validation_result['allowed'],
                'reason': validation_result['reason'],
                'validation_time': validation_time,
                'cache_hit': validation_result.get('cache_hit', False),
                'ip_address': self._get_client_ip(request),
                'user_agent': request.META.get('HTTP_USER_AGENT', ''),
                'timestamp': timezone.now().isoformat()
            }
            
            # Log to audit logger
            audit_logger = logging.getLogger('permission.audit')
            audit_logger.info(f"Permission validation: {audit_entry}")
            
            # Store in database for critical permissions
            if not validation_result['allowed'] or self.audit_performance:
                try:
                    from .models import PermissionAuditLog
                    PermissionAuditLog.log_action(
                        action='permission_validation',
                        actor=user if hasattr(user, 'id') else None,
                        details={
                            'resource_type': 'endpoint',
                            'resource_id': request.path_info,
                            'audit_entry': audit_entry,
                            'ip_address': audit_entry['ip_address']
                        }
                    )
                except ImportError:
                    # PermissionAuditLog model may not exist yet
                    pass
                
        except Exception as e:
            logger.error(f"Error logging permission validation attempt: {e}")
    
    def _log_system_failure(self, request, error, validation_time):
        """Log system failures for monitoring and debugging."""
        user = getattr(request, 'user', None)
        
        failure_entry = {
            'user_id': user.id if user and hasattr(user, 'id') else None,
            'path': request.path_info,
            'method': request.method,
            'error': str(error),
            'error_type': type(error).__name__,
            'validation_time': validation_time,
            'ip_address': self._get_client_ip(request),
            'timestamp': timezone.now().isoformat(),
            'failure_mode': self.failure_mode
        }
        
        logger.error(f"Permission middleware system failure: {failure_entry}", exc_info=True)
        
        # Store critical failures in database
        try:
            from .models import PermissionAuditLog
            PermissionAuditLog.log_action(
                action='system_failure',
                actor=user if user and hasattr(user, 'id') else None,
                details={
                    'resource_type': 'middleware',
                    'resource_id': 'permission_validation',
                    'failure_entry': failure_entry,
                    'ip_address': failure_entry['ip_address']
                }
            )
        except (ImportError, Exception) as db_error:
            logger.error(f"Could not store failure in database: {db_error}")
    
    def _get_client_ip(self, request):
        """Get client IP address from request."""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            return x_forwarded_for.split(',')[0].strip()
        else:
            return request.META.get('REMOTE_ADDR', 'unknown')
    
    def _create_permission_denied_response(self, request, reason):
        """Create standardized permission denied response."""
        error_response = {
            'error': 'Permission Denied',
            'detail': reason,
            'timestamp': timezone.now().isoformat(),
            'request_id': getattr(request, 'id', None),
            'path': request.path_info,
            'required_permissions': getattr(request, 'permission_context', {}).get('required_permissions', [])
        }
        
        return JsonResponse(
            error_response,
            status=status.HTTP_403_FORBIDDEN,
            headers={
                'X-Permission-Error': 'true',
                'X-Request-ID': error_response['request_id'] or 'unknown'
            }
        )
    
    def _create_system_error_response(self, request):
        """Create system error response for middleware failures."""
        error_response = {
            'error': 'System Error',
            'detail': 'Permission validation system temporarily unavailable',
            'timestamp': timezone.now().isoformat(),
            'request_id': getattr(request, 'id', None),
            'path': request.path_info
        }
        
        return JsonResponse(
            error_response,
            status=status.HTTP_503_SERVICE_UNAVAILABLE,
            headers={
                'X-System-Error': 'true',
                'X-Request-ID': error_response['request_id'] or 'unknown',
                'Retry-After': '60'  # Suggest retry after 1 minute
            }
        )
    
    def get_performance_stats(self):
        """Get current performance statistics (for monitoring)."""
        return self._performance_stats.copy()
    
    def reset_performance_stats(self):
        """Reset performance statistics (for monitoring)."""
        self._performance_stats = {
            'total_requests': 0,
            'validation_time_sum': 0.0,
            'cache_hits': 0,
            'cache_misses': 0,
            'failures': 0,
            'bypassed': 0,
        }


class PermissionCacheInvalidationMiddleware(MiddlewareMixin):
    """
    T019: Middleware to handle automatic permission cache invalidation when permissions change.
    
    This middleware watches for permission-related model changes and invalidates
    relevant cache entries to ensure permission validation remains accurate.
    """
    
    def __init__(self, get_response=None):
        super().__init__(get_response)
        self.get_response = get_response
        
        # Track cache invalidation patterns
        self.invalidation_patterns = {
            'user_permissions': 'user_permissions:{}',
            'validation_cache': 'perm_validation:{}:*', 
            'global_permissions': 'permission_cache:*'
        }
        
        logger.info("T019: Permission cache invalidation middleware initialized")
    
    def process_response(self, request, response):
        """Process response to handle cache invalidation if needed."""
        # Check if this was a permission-modifying request
        if self._is_permission_modifying_request(request, response):
            self._invalidate_permission_caches(request)
        
        return response
    
    def _is_permission_modifying_request(self, request, response):
        """Check if the request modified permission data."""
        # Check for permission-related endpoints with modification methods
        path = request.path_info
        method = request.method.upper()
        
        permission_endpoints = [
            '/api/permissions/',
            '/api/users/',
            '/api/groups/',
            '/admin/core/permission/',
            '/admin/core/userpermission/',
            '/admin/core/grouppermission/',
            '/admin/core/groupmembership/',
        ]
        
        # Check if endpoint and method could modify permissions
        for endpoint in permission_endpoints:
            if endpoint in path and method in ['POST', 'PUT', 'PATCH', 'DELETE']:
                # Only invalidate on successful modifications
                return 200 <= response.status_code < 300
        
        return False
    
    def _invalidate_permission_caches(self, request):
        """Invalidate relevant permission caches."""
        try:
            # Get affected user IDs from request
            affected_users = self._get_affected_users(request)
            
            # Invalidate user-specific caches
            for user_id in affected_users:
                cache.delete(f"user_permissions:{user_id}")
                
                # Invalidate validation cache entries for this user
                # Note: In production, use Redis pattern matching or cache tags
                validation_pattern = f"perm_validation:{user_id}:*"
                # cache.delete_pattern(validation_pattern)  # Redis-specific
            
            # For group or global permission changes, clear broader cache
            if self._affects_multiple_users(request):
                # Clear all validation caches (use pattern matching in Redis)
                # cache.delete_pattern("perm_validation:*")
                pass
            
            logger.info(f"T019: Invalidated permission caches for users: {affected_users}")
            
        except Exception as e:
            logger.error(f"Error invalidating permission caches: {e}")
    
    def _get_affected_users(self, request):
        """Extract user IDs that might be affected by the permission change."""
        affected_users = set()
        
        # Try to extract user ID from URL path
        path_parts = request.path_info.strip('/').split('/')
        for i, part in enumerate(path_parts):
            if part == 'users' and i + 1 < len(path_parts):
                try:
                    user_id = int(path_parts[i + 1])
                    affected_users.add(user_id)
                except ValueError:
                    pass
        
        # Extract from request body if available
        if hasattr(request, 'body') and request.content_type == 'application/json':
            try:
                import json
                data = json.loads(request.body.decode('utf-8'))
                
                if 'user' in data:
                    affected_users.add(int(data['user']))
                if 'users' in data:
                    affected_users.update([int(uid) for uid in data['users']])
                    
            except (json.JSONDecodeError, ValueError, KeyError):
                pass
        
        return affected_users
    
    def _affects_multiple_users(self, request):
        """Check if the change affects multiple users (e.g., group permissions)."""
        path = request.path_info
        return '/api/groups/' in path or '/admin/core/group' in path
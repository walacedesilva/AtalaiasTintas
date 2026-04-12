"""
Custom middleware for authentication, session management and audit logging.
Provides comprehensive tracking and security features for the paint store system.
"""

import logging
import json
from datetime import timedelta
from django.utils import timezone
from django.utils.deprecation import MiddlewareMixin
from django.contrib.auth.models import AnonymousUser
from django.core.exceptions import ObjectDoesNotExist
from django.db import transaction

from .models import UserSession, AuditLog

logger = logging.getLogger(__name__)


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
"""
T017: Custom Exception Handling and Validation System.

Provides comprehensive error handling for the User Permissions System with
consistent error responses, proper logging, and security-conscious error messages.
"""

from django.core.exceptions import ValidationError as DjangoValidationError
from django.http import Http404
from rest_framework import status
from rest_framework.views import exception_handler
from rest_framework.response import Response
from rest_framework.exceptions import (
    APIException, ValidationError, PermissionDenied, 
    NotAuthenticated, NotFound, Throttled
)
import logging
import traceback
from django.utils import timezone
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

# =============================================================================
# T017: CUSTOM EXCEPTION CLASSES
# =============================================================================

class PermissionSystemException(APIException):
    """
    Base exception class for all permission system related errors.
    
    Provides consistent error structure and logging across the system.
    """
    status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
    default_detail = 'A permission system error occurred.'
    default_code = 'permission_system_error'
    
    def __init__(self, detail=None, code=None, user_id=None, context=None):
        super().__init__(detail, code)
        self.user_id = user_id
        self.context = context or {}
        self.timestamp = timezone.now()


class PermissionValidationError(PermissionSystemException):
    """
    Raised when permission validation fails.
    
    Used for business rule violations and invalid permission assignments.
    """
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = 'Permission validation failed.'
    default_code = 'permission_validation_error'


class InsufficientPermissionsError(PermissionSystemException):
    """
    Raised when user lacks required permissions for an operation.
    
    More specific than DRF's PermissionDenied for permission system operations.
    """
    status_code = status.HTTP_403_FORBIDDEN
    default_detail = 'Insufficient permissions for this operation.'
    default_code = 'insufficient_permissions'


class PermissionNotFoundError(PermissionSystemException):
    """
    Raised when a requested permission or related object is not found.
    """
    status_code = status.HTTP_404_NOT_FOUND
    default_detail = 'The requested permission was not found.'
    default_code = 'permission_not_found'


class PermissionConflictError(PermissionSystemException):
    """
    Raised when permission assignment creates a conflict.
    
    Examples: Duplicate assignments, conflicting permissions, etc.
    """
    status_code = status.HTTP_409_CONFLICT
    default_detail = 'Permission assignment conflict detected.'
    default_code = 'permission_conflict'


class PermissionExpiredError(PermissionSystemException):
    """
    Raised when attempting to use an expired permission.
    """
    status_code = status.HTTP_410_GONE
    default_detail = 'The permission has expired.'
    default_code = 'permission_expired'


class RateLimitExceededError(PermissionSystemException):
    """
    Raised when API rate limits are exceeded.
    """
    status_code = status.HTTP_429_TOO_MANY_REQUESTS
    default_detail = 'Rate limit exceeded. Please try again later.'
    default_code = 'rate_limit_exceeded'
    
    def __init__(self, detail=None, retry_after=None, **kwargs):
        super().__init__(detail=detail, **kwargs)
        self.retry_after = retry_after


class SystemMaintenanceError(PermissionSystemException):
    """
    Raised when the system is under maintenance.
    """
    status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    default_detail = 'System is temporarily unavailable for maintenance.'
    default_code = 'system_maintenance'


class DataIntegrityError(PermissionSystemException):
    """
    Raised when data integrity violations are detected.
    """
    status_code = status.HTTP_422_UNPROCESSABLE_ENTITY
    default_detail = 'Data integrity violation detected.'
    default_code = 'data_integrity_error'


# =============================================================================
# T017: CUSTOM EXCEPTION HANDLER
# =============================================================================

def custom_exception_handler(exc, context):
    """
    Custom exception handler that provides consistent error responses.
    
    Features:
    - Consistent error response format
    - Proper logging with context
    - Security-conscious error messages
    - Request ID tracking for debugging
    - Field-specific validation errors
    """
    
    # Get the standard DRF exception response
    response = exception_handler(exc, context)
    
    # Extract request context
    request = context.get('request')
    view = context.get('view')
    
    # Generate request ID for tracking
    request_id = getattr(request, 'id', None) if request else None
    if not request_id and request:
        request_id = f"{timezone.now().timestamp():.6f}"
        request.id = request_id
    
    # Initialize error response structure
    error_data = {
        'error': 'Unknown error',
        'detail': 'An unexpected error occurred',
        'timestamp': timezone.now().isoformat(),
        'request_id': request_id
    }
    
    # Handle custom permission system exceptions
    if isinstance(exc, PermissionSystemException):
        error_data.update({
            'error': exc.default_code,
            'detail': str(exc.detail),
            'code': exc.get_codes() if hasattr(exc, 'get_codes') else exc.default_code
        })
        
        # Log custom exception with context
        logger.warning(
            f"Permission system exception: {exc.default_code}",
            extra={
                'exception_type': exc.__class__.__name__,
                'user_id': getattr(exc, 'user_id', None),
                'request_id': request_id,
                'context': getattr(exc, 'context', {}),
                'view': view.__class__.__name__ if view else None
            }
        )
        
        # Add retry-after header for rate limiting
        if isinstance(exc, RateLimitExceededError) and hasattr(exc, 'retry_after'):
            if not response:
                response = Response()
            response['Retry-After'] = str(exc.retry_after)
    
    # Handle DRF built-in exceptions
    elif response is not None:
        status_code = response.status_code
        
        if isinstance(exc, ValidationError):
            error_data.update({
                'error': 'validation_error',
                'detail': 'Invalid input data provided',
                'field_errors': _format_validation_errors(exc.detail)
            })
        
        elif isinstance(exc, PermissionDenied):
            error_data.update({
                'error': 'permission_denied',
                'detail': 'You do not have permission to perform this action'
            })
        
        elif isinstance(exc, NotAuthenticated):
            error_data.update({
                'error': 'authentication_required',
                'detail': 'Authentication credentials were not provided or are invalid'
            })
        
        elif isinstance(exc, NotFound) or isinstance(exc, Http404):
            error_data.update({
                'error': 'resource_not_found',
                'detail': 'The requested resource was not found'
            })
        
        elif isinstance(exc, Throttled):
            error_data.update({
                'error': 'rate_limit_exceeded',
                'detail': f'Rate limit exceeded. Try again in {exc.wait} seconds',
                'retry_after': exc.wait
            })
            
            # Add retry-after header
            response['Retry-After'] = str(exc.wait)
        
        else:
            # Generic DRF exception
            error_data.update({
                'error': 'api_error',
                'detail': str(exc.detail) if hasattr(exc, 'detail') else 'An API error occurred'
            })
        
        # Log DRF exception
        logger.warning(
            f"API exception: {exc.__class__.__name__}",
            extra={
                'status_code': status_code,
                'exception_detail': str(exc.detail) if hasattr(exc, 'detail') else str(exc),
                'request_id': request_id,
                'view': view.__class__.__name__ if view else None,
                'user': request.user.username if request and hasattr(request, 'user') and request.user.is_authenticated else 'anonymous'
            }
        )
    
    # Handle unexpected exceptions (500 errors)
    else:
        status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        
        # Log full exception for debugging (but don't expose to client)
        logger.error(
            f"Unhandled exception: {exc.__class__.__name__}",
            extra={
                'exception_detail': str(exc),
                'traceback': traceback.format_exc(),
                'request_id': request_id,
                'view': view.__class__.__name__ if view else None,
                'user': request.user.username if request and hasattr(request, 'user') and request.user.is_authenticated else 'anonymous'
            }
        )
        
        # Return generic error message (security)
        error_data.update({
            'error': 'internal_server_error',
            'detail': 'An internal server error occurred. Please contact support if the problem persists.'
        })
        
        response = Response(error_data, status=status_code)
    
    # Update response with consistent error format
    if response is not None:
        response.data = error_data
        
        # Add security headers
        response['X-Request-ID'] = request_id
        response['X-Content-Type-Options'] = 'nosniff'
        
        # Add CORS headers if needed
        if request and hasattr(request, 'META'):
            origin = request.META.get('HTTP_ORIGIN')
            if origin:
                response['Access-Control-Allow-Origin'] = origin
    
    return response


def _format_validation_errors(detail):
    """
    Format DRF validation errors into a consistent field-based structure.
    
    Handles both field-level and non-field errors properly.
    """
    if isinstance(detail, dict):
        formatted_errors = {}
        for field, errors in detail.items():
            if isinstance(errors, list):
                formatted_errors[field] = [str(error) for error in errors]
            else:
                formatted_errors[field] = [str(errors)]
        return formatted_errors
    
    elif isinstance(detail, list):
        return {'non_field_errors': [str(error) for error in detail]}
    
    else:
        return {'non_field_errors': [str(detail)]}


# =============================================================================
# T017: INPUT VALIDATION UTILITIES
# =============================================================================

class ValidationUtils:
    """
    Utility class for common validation operations.
    
    Provides reusable validation methods with consistent error handling.
    """
    
    @staticmethod
    def validate_permission_code(code: str) -> str:
        """
        Validate permission code format and security.
        
        Rules:
        - Must follow module.resource.action pattern
        - No special characters except dots and underscores
        - Maximum length of 100 characters
        - No SQL injection patterns
        """
        if not code:
            raise PermissionValidationError('Permission code is required')
        
        if len(code) > 100:
            raise PermissionValidationError('Permission code must be 100 characters or less')
        
        # Check format (module.resource.action)
        parts = code.split('.')
        if len(parts) < 2:
            raise PermissionValidationError(
                'Permission code must follow format: module.resource.action'
            )
        
        # Check for valid characters
        import re
        if not re.match(r'^[a-zA-Z0-9_.]+$', code):
            raise PermissionValidationError(
                'Permission code can only contain letters, numbers, dots, and underscores'
            )
        
        # Security check - basic SQL injection patterns
        sql_patterns = ['DROP', 'DELETE', 'UPDATE', 'INSERT', 'SELECT', '--', '/*', '*/', ';']
        code_upper = code.upper()
        for pattern in sql_patterns:
            if pattern in code_upper:
                raise PermissionValidationError('Permission code contains invalid characters')
        
        return code.lower()  # Normalize to lowercase
    
    @staticmethod
    def validate_risk_level(risk_level: str) -> str:
        """
        Validate permission risk level.
        """
        valid_levels = ['low', 'medium', 'high', 'critical']
        
        if not risk_level:
            raise PermissionValidationError('Risk level is required')
        
        risk_level = risk_level.lower()
        if risk_level not in valid_levels:
            raise PermissionValidationError(
                f'Risk level must be one of: {", ".join(valid_levels)}'
            )
        
        return risk_level
    
    @staticmethod
    def validate_user_permission_assignment(user, permission, expires_at=None):
        """
        Validate user permission assignment business rules.
        """
        from .models import UserPermission
        
        # Check if user exists and is active
        if not user.is_active:
            raise PermissionValidationError('Cannot assign permissions to inactive users')
        
        # Check if permission is active
        if not permission.is_active:
            raise PermissionValidationError('Cannot assign inactive permissions')
        
        # Check for existing active assignment
        existing = UserPermission.objects.filter(
            user=user,
            permission=permission,
            is_granted=True
        ).exists()
        
        if existing:
            raise PermissionConflictError(
                f'User already has permission: {permission.code}'
            )
        
        # Validate expiration date
        if expires_at:
            if expires_at <= timezone.now():
                raise PermissionValidationError('Expiration date must be in the future')
            
            # Don't allow excessively long permissions for high-risk permissions
            if permission.risk_level in ['high', 'critical']:
                max_days = 90 if permission.risk_level == 'high' else 30
                max_expiry = timezone.now() + timezone.timedelta(days=max_days)
                
                if expires_at > max_expiry:
                    raise PermissionValidationError(
                        f'{permission.risk_level.title()} risk permissions cannot be assigned for more than {max_days} days'
                    )
    
    @staticmethod
    def sanitize_error_message(message: str, context: Optional[Dict[str, Any]] = None) -> str:
        """
        Sanitize error messages to prevent information disclosure.
        
        Removes sensitive information while maintaining usefulness for debugging.
        """
        # Remove file paths
        import re
        message = re.sub(r'[/\\\\][\\w/\\\\.-]+\\.(py|html|js)', '[FILE_PATH]', message)
        
        # Remove SQL query details
        message = re.sub(r'SELECT.*FROM.*WHERE', '[SQL_QUERY]', message, flags=re.IGNORECASE | re.DOTALL)
        
        # Remove internal IDs (but keep user-facing IDs)
        if context and context.get('hide_internal_ids', True):
            message = re.sub(r'id=[0-9]+', 'id=[ID]', message)
        
        # Truncate very long messages
        if len(message) > 500:
            message = message[:497] + '...'
        
        return message


# =============================================================================
# T017: BUSINESS RULE VALIDATORS
# =============================================================================

class BusinessRuleValidator:
    """
    Validators for specific business rules in the permission system.
    """
    
    @staticmethod
    def validate_group_membership(user, group):
        """
        Validate group membership business rules.
        """
        from .models import GroupMembership
        
        # Check if user is active
        if not user.is_active:
            raise PermissionValidationError('Cannot add inactive users to groups')
        
        # Check if group is active
        if not group.is_active:
            raise PermissionValidationError('Cannot add users to inactive groups')
        
        # Check for existing membership
        existing = GroupMembership.objects.filter(user=user, group=group).exists()
        if existing:
            raise PermissionConflictError(f'User is already a member of group: {group.name}')
        
        # Check group capacity (if defined)
        if hasattr(group, 'max_members') and group.max_members:
            current_members = GroupMembership.objects.filter(group=group).count()
            if current_members >= group.max_members:
                raise PermissionValidationError(f'Group has reached maximum capacity of {group.max_members} members')
    
    @staticmethod
    def validate_permission_deletion(permission):
        """
        Validate permission deletion business rules.
        """
        from .models import UserPermission, GroupPermission
        
        # Check if permission has active assignments
        active_user_assignments = UserPermission.objects.filter(
            permission=permission,
            is_granted=True
        ).count()
        
        active_group_assignments = GroupPermission.objects.filter(
            permission=permission,
            is_granted=True
        ).count()
        
        total_assignments = active_user_assignments + active_group_assignments
        
        if total_assignments > 0:
            raise PermissionValidationError(
                f'Cannot delete permission with {total_assignments} active assignments. '
                f'Revoke all assignments before deletion.'
            )
        
        # Extra validation for system-critical permissions
        if hasattr(permission, 'is_system_permission') and permission.is_system_permission:
            raise PermissionValidationError('Cannot delete system-critical permissions')
    
    @staticmethod
    def validate_risk_level_change(permission, new_risk_level, current_user):
        """
        Validate risk level changes with proper authorization.
        """
        old_risk_level = permission.risk_level
        
        # Risk level escalation requires higher privileges
        risk_levels = {'low': 1, 'medium': 2, 'high': 3, 'critical': 4}
        
        old_level = risk_levels.get(old_risk_level, 0)
        new_level = risk_levels.get(new_risk_level, 0)
        
        if new_level > old_level:
            # Escalating risk level
            if not current_user.is_superuser:
                if new_level >= 3 and not current_user.has_perm('core.manage_high_risk_permissions'):
                    raise InsufficientPermissionsError(
                        'High-risk permission management requires special authorization'
                    )
        
        # Log risk level changes
        logger.info(
            f"Permission risk level change: {permission.code} from {old_risk_level} to {new_risk_level}",
            extra={
                'permission_id': permission.id,
                'user_id': current_user.id,
                'old_risk_level': old_risk_level,
                'new_risk_level': new_risk_level
            }
        )
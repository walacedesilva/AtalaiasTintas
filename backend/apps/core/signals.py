"""
Signal handlers for the core app.

Features:
- 3-modern-web-interface / 4-inventory-fiscal-integration 
- 8-user-permissions-system

Tasks:
- T006 - User Preferences Model, T014 - Inventory/Fiscal Event Signals
- T007 - Audit Logging Infrastructure (Permission System)
"""

import logging
import threading
from typing import Any, Dict, Optional

from django.db.models.signals import post_save, post_delete, pre_save
from django.contrib.auth.signals import user_login_failed, user_logged_in, user_logged_out
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from django.utils import timezone

from .models import (
    UserPreferences, Permission, UserGroup, UserPermission, 
    GroupPermission, GroupMembership, PermissionAuditLog
)

logger = logging.getLogger(__name__)
User = get_user_model()

# Import audit logger (will be available after T007 implementation)
try:
    from .audit import audit_logger, log_security_violation
    AUDIT_AVAILABLE = True
except ImportError:
    AUDIT_AVAILABLE = False
    logger.warning("Audit system not available - signals will log to standard logger")

# Thread-local storage to prevent recursive signal calls and store request context
_audit_context = threading.local()


@receiver(post_save, sender=User)
def create_user_preferences(sender, instance, created, **kwargs):
    """
    Automatically create UserPreferences when a new User is created.
    
    This ensures every user has associated interface preferences with
    sensible defaults from the moment their account is created.
    
    Args:
        sender: The User model class
        instance: The specific User instance that was saved
        created: Boolean indicating if this is a new user
        **kwargs: Additional signal arguments
    """
    if created:
        UserPreferences.objects.create(
            user=instance,
            theme='light',
            density='comfortable',
            sidebar_collapsed=False,
            show_breadcrumbs=True,
            high_contrast=False,
            reduce_motion=False,
            quick_actions=[
                {'action': 'create_label', 'label': 'Nova Etiqueta', 'icon': 'bi-tag'},
                {'action': 'inventory_count', 'label': 'Contagem', 'icon': 'bi-clipboard-check'},
                {'action': 'sales_report', 'label': 'Vendas', 'icon': 'bi-graph-up'},
                {'action': 'tint_mix', 'label': 'Misturar Tinta', 'icon': 'bi-palette'},
            ]
        )


# ===============================================================================
# Audit Logging Utility Functions - T007
# ===============================================================================

def is_audit_enabled() -> bool:
    """Check if audit logging is currently enabled for this thread."""
    return getattr(_audit_context, 'enabled', True)


def disable_audit():
    """Temporarily disable audit logging for this thread."""
    _audit_context.enabled = False


def enable_audit():
    """Re-enable audit logging for this thread."""
    _audit_context.enabled = True


def get_current_request():
    """Get current HTTP request from thread-local storage if available."""
    return getattr(_audit_context, 'current_request', None)


def set_current_request(request):
    """Set current HTTP request in thread-local storage for audit context."""
    _audit_context.current_request = request


def extract_request_info(request) -> Optional[Dict[str, str]]:
    """Extract relevant information from HTTP request for audit logging."""
    if not request:
        return None
        
    return {
        'ip_address': request.META.get('REMOTE_ADDR', 'unknown'),
        'user_agent': request.META.get('HTTP_USER_AGENT', 'unknown')[:500],
        'method': request.method,
        'path': request.path,
        'referrer': request.META.get('HTTP_REFERER', 'unknown')[:200]
    }


# ===============================================================================
# User Permission Audit Signals - T007
# ===============================================================================

@receiver(post_save, sender=UserPermission)
def log_user_permission_change(sender, instance, created, **kwargs):
    """Log user permission grants and modifications."""
    if not is_audit_enabled() or not AUDIT_AVAILABLE:
        return
    
    try:
        action = 'GRANT' if created else 'MODIFY'
        request = get_current_request()
        
        # Determine the user who made the change (from request if available)
        acting_user = getattr(request, 'user', None) if request else None
        
        details = {
            'user_id': instance.user.id,
            'user_username': instance.user.username,
            'permission_code': instance.permission.code,
            'grant_type': instance.grant_type,
            'is_active': instance.is_active,
            'requires_approval': instance.requires_approval,
            'approved_by': instance.approved_by.username if instance.approved_by else None,
            'valid_from': instance.valid_from.isoformat() if instance.valid_from else None,
            'valid_until': instance.valid_until.isoformat() if instance.valid_until else None,
        }
        
        # Add modification context for updates
        if not created:
            # Get original values if this is an update
            original = UserPermission.objects.filter(id=instance.id).first()
            if original:
                details['changes'] = {
                    'grant_type_changed': original.grant_type != instance.grant_type,
                    'active_changed': original.is_active != instance.is_active,
                    'approval_changed': original.requires_approval != instance.requires_approval
                }
        
        # Log the audit entry
        audit_logger.log_permission_change(
            action=action,
            entity_type='user_permission',
            entity_id=str(instance.id),
            user=acting_user,
            permission=instance.permission,
            details=details,
            request_info=extract_request_info(request)
        )
        
    except Exception as e:
        logger.error(f"Failed to log user permission change: {str(e)}")


@receiver(post_delete, sender=UserPermission)
def log_user_permission_deletion(sender, instance, **kwargs):
    """Log user permission revocations.""" 
    if not is_audit_enabled() or not AUDIT_AVAILABLE:
        return
        
    try:
        request = get_current_request()
        acting_user = getattr(request, 'user', None) if request else None
        
        details = {
            'user_id': instance.user.id,
            'user_username': instance.user.username,
            'permission_code': instance.permission.code,
            'grant_type': instance.grant_type,
            'was_active': instance.is_active,
            'deletion_reason': 'explicit_revocation'
        }
        
        audit_logger.log_permission_change(
            action='REVOKE',
            entity_type='user_permission',
            entity_id=str(instance.id),
            user=acting_user,
            permission=instance.permission,
            details=details,
            request_info=extract_request_info(request)
        )
        
    except Exception as e:
        logger.error(f"Failed to log user permission deletion: {str(e)}")


# =============================================================================== 
# Group Membership Audit Signals - T007
# ===============================================================================

@receiver(post_save, sender=GroupMembership)
def log_group_membership_change(sender, instance, created, **kwargs):
    """Log group membership assignments and modifications."""
    if not is_audit_enabled() or not AUDIT_AVAILABLE:
        return
        
    try:
        action = 'GRANT' if created else 'MODIFY'
        request = get_current_request()
        acting_user = getattr(request, 'user', None) if request else None
        
        details = {
            'user_id': instance.user.id,
            'user_username': instance.user.username,
            'group_id': instance.group.id,
            'group_name': instance.group.name,
            'is_primary': instance.is_primary,
            'is_active': instance.is_active,
            'role': instance.role,
            'valid_from': instance.valid_from.isoformat() if instance.valid_from else None,
            'valid_until': instance.valid_until.isoformat() if instance.valid_until else None,
        }
        
        # Track primary membership changes specially
        if instance.is_primary and not created:
            details['primary_membership_changed'] = True
            
        audit_logger.log_permission_change(
            action=action,
            entity_type='group_membership',
            entity_id=f"{instance.user.id}:{instance.group.id}",
            user=acting_user,
            details=details,
            request_info=extract_request_info(request)
        )
        
    except Exception as e:
        logger.error(f"Failed to log group membership change: {str(e)}")


@receiver(post_delete, sender=GroupMembership) 
def log_group_membership_deletion(sender, instance, **kwargs):
    """Log group membership removals."""
    if not is_audit_enabled() or not AUDIT_AVAILABLE:
        return
        
    try:
        request = get_current_request()
        acting_user = getattr(request, 'user', None) if request else None
        
        details = {
            'user_id': instance.user.id,
            'user_username': instance.user.username,
            'group_id': instance.group.id,
            'group_name': instance.group.name,
            'was_primary': instance.is_primary,
            'was_active': instance.is_active,
            'role': instance.role,
            'removal_reason': 'explicit_removal'
        }
        
        audit_logger.log_permission_change(
            action='REVOKE',
            entity_type='group_membership',
            entity_id=f"{instance.user.id}:{instance.group.id}",
            user=acting_user,
            details=details,
            request_info=extract_request_info(request)
        )
        
    except Exception as e:
        logger.error(f"Failed to log group membership deletion: {str(e)}")


# ===============================================================================
# Group Permission Audit Signals - T007
# ===============================================================================

@receiver(post_save, sender=GroupPermission)
def log_group_permission_change(sender, instance, created, **kwargs):
    """Log group permission assignments and modifications."""
    if not is_audit_enabled() or not AUDIT_AVAILABLE:
        return
        
    try:
        action = 'GRANT' if created else 'MODIFY'
        request = get_current_request()
        acting_user = getattr(request, 'user', None) if request else None
        
        details = {
            'group_id': instance.group.id,
            'group_name': instance.group.name,
            'permission_code': instance.permission.code,
            'grant_type': instance.grant_type,
            'inherited': instance.inherited,
            'is_active': instance.is_active,
            'valid_from': instance.valid_from.isoformat() if instance.valid_from else None,
            'valid_until': instance.valid_until.isoformat() if instance.valid_until else None,
        }
        
        # Calculate potential impact
        affected_users = instance.group.get_all_users().count()
        details['potentially_affected_users'] = affected_users
        
        audit_logger.log_permission_change(
            action=action,
            entity_type='group_permission',
            entity_id=str(instance.id),
            user=acting_user,
            permission=instance.permission,
            details=details,
            request_info=extract_request_info(request)
        )
        
    except Exception as e:
        logger.error(f"Failed to log group permission change: {str(e)}")


@receiver(post_delete, sender=GroupPermission)
def log_group_permission_deletion(sender, instance, **kwargs):
    """Log group permission revocations."""
    if not is_audit_enabled() or not AUDIT_AVAILABLE:
        return
        
    try:
        request = get_current_request()
        acting_user = getattr(request, 'user', None) if request else None
        
        details = {
            'group_id': instance.group.id,
            'group_name': instance.group.name, 
            'permission_code': instance.permission.code,
            'grant_type': instance.grant_type,
            'was_inherited': instance.inherited,
            'was_active': instance.is_active,
            'revocation_reason': 'explicit_revocation'
        }
        
        audit_logger.log_permission_change(
            action='REVOKE',
            entity_type='group_permission',
            entity_id=str(instance.id),
            user=acting_user,
            permission=instance.permission,
            details=details,
            request_info=extract_request_info(request)
        )
        
    except Exception as e:
        logger.error(f"Failed to log group permission deletion: {str(e)}")


# ===============================================================================
# Authentication and Security Audit Signals - T007
# ===============================================================================

@receiver(user_logged_in)
def log_user_login(sender, request, user, **kwargs):
    """Log successful user authentication."""
    if not is_audit_enabled() or not AUDIT_AVAILABLE:
        return
        
    try:
        details = {
            'username': user.username,
            'login_method': 'standard',
            'session_key': request.session.session_key[:10] if request.session.session_key else None,
        }
        
        audit_logger.log_permission_change(
            action='LOGIN',
            entity_type='authentication',
            entity_id=str(user.id),
            user=user,
            details=details,
            request_info=extract_request_info(request)
        )
        
    except Exception as e:
        logger.error(f"Failed to log user login: {str(e)}")


@receiver(user_login_failed)
def log_login_failure(sender, credentials, request, **kwargs):
    """Log failed authentication attempts."""
    if not is_audit_enabled() or not AUDIT_AVAILABLE:
        return
        
    try:
        details = {
            'attempted_username': credentials.get('username', 'unknown')[:100],
            'failure_reason': 'invalid_credentials',
            'attempt_count': getattr(request.session, 'failed_login_count', 1),
        }
        
        # Check for potential brute force
        if details['attempt_count'] > 5:
            details['potential_brute_force'] = True
            log_security_violation(
                user=None,
                violation_type='repeated_login_failures',
                details={
                    'username': details['attempted_username'],
                    'attempt_count': details['attempt_count'],
                    'ip_address': extract_request_info(request).get('ip_address') if request else 'unknown'
                },
                request_info=extract_request_info(request)
            )
        
        audit_logger.log_permission_change(
            action='SECURITY_VIOLATION',
            entity_type='authentication',
            entity_id=details['attempted_username'],
            user=None,
            details=details,
            request_info=extract_request_info(request)
        )
        
    except Exception as e:
        logger.error(f"Failed to log login failure: {str(e)}")


@receiver(user_logged_out)
def log_user_logout(sender, request, user, **kwargs):
    """Log user logout events."""  
    if not is_audit_enabled() or not AUDIT_AVAILABLE:
        return
        
    try:
        details = {
            'username': user.username if user else 'anonymous',
            'logout_method': 'explicit',
            'session_duration': 'unknown',  # Could calculate if session start time is tracked
        }
        
        audit_logger.log_permission_change(
            action='LOGOUT',
            entity_type='authentication', 
            entity_id=str(user.id) if user else 'anonymous',
            user=user,
            details=details,
            request_info=extract_request_info(request)
        )
        
    except Exception as e:
        logger.error(f"Failed to log user logout: {str(e)}")


# ===============================================================================
# Security Monitoring Signals - T007
# ===============================================================================

@receiver(pre_save, sender=User)
def monitor_user_security_changes(sender, instance, **kwargs):
    """Monitor security-relevant changes to user accounts."""
    if not is_audit_enabled() or not AUDIT_AVAILABLE:
        return
        
    try:
        # Only log for existing users (updates)
        if instance.pk:
            try:
                original = User.objects.get(pk=instance.pk)
                request = get_current_request()
                acting_user = getattr(request, 'user', None) if request else None
                
                security_changes = {}
                
                # Monitor critical field changes
                if original.is_active != instance.is_active:
                    security_changes['active_status_changed'] = {
                        'from': original.is_active,
                        'to': instance.is_active
                    }
                    
                if original.is_staff != instance.is_staff:
                    security_changes['staff_status_changed'] = {
                        'from': original.is_staff,
                        'to': instance.is_staff
                    }
                    
                if original.is_superuser != instance.is_superuser:
                    security_changes['superuser_status_changed'] = {
                        'from': original.is_superuser,
                        'to': instance.is_superuser
                    }
                    
                # Password change detection (hash comparison)
                if original.password != instance.password:
                    security_changes['password_changed'] = True
                    
                # Email change detection
                if original.email != instance.email:
                    security_changes['email_changed'] = {
                        'from': original.email,
                        'to': instance.email
                    }
                
                # Log only if there are security-relevant changes
                if security_changes:
                    details = {
                        'target_user': instance.username,
                        'changes': security_changes,
                        'modified_by': acting_user.username if acting_user else 'system',
                    }
                    
                    # Determine if this is a high-risk change
                    high_risk_changes = ['superuser_status_changed', 'staff_status_changed']
                    is_high_risk = any(change in security_changes for change in high_risk_changes)
                    
                    action = 'SECURITY_VIOLATION' if is_high_risk else 'MODIFY'
                    
                    audit_logger.log_permission_change(
                        action=action,
                        entity_type='user_security',
                        entity_id=str(instance.id),
                        user=acting_user,
                        details=details,
                        request_info=extract_request_info(request)
                    )
                    
            except User.DoesNotExist:
                # This is a new user, skip security monitoring
                pass
                
    except Exception as e:
        logger.error(f"Failed to monitor user security changes: {str(e)}")


# ===============================================================================
# Middleware for Request Context - T007 
# ===============================================================================

class AuditRequestMiddleware:
    """
    Middleware to provide request context for audit logging.
    
    Stores the current request in thread-local storage so that signal handlers
    can access request information like user, IP address, etc.
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        # Store request in thread-local storage for audit signals
        set_current_request(request)
        
        try:
            response = self.get_response(request)
            return response
        finally:
            # Clean up thread-local storage
            set_current_request(None)


# ===============================================================================
# Management Functions - T007
# ===============================================================================

def disable_audit_for_migration():
    """
    Context manager to disable audit logging during migrations.
    
    Usage:
        with disable_audit_for_migration():
            # Run migration code
            pass
    """
    class DisableAudit:
        def __enter__(self):
            disable_audit()
        
        def __exit__(self, exc_type, exc_val, exc_tb):
            enable_audit()
    
    return DisableAudit()


def bulk_audit_disable():
    """Disable audit logging for bulk operations."""
    disable_audit()


def bulk_audit_enable():
    """Re-enable audit logging after bulk operations."""
    enable_audit()


# Initialize logging
logger.info("Core app signals initialized successfully - including audit logging for T007")


# ---------------------------------------------------------------------------
# Inventory / Fiscal integration signals — T014
# ---------------------------------------------------------------------------

def connect_inventory_signals():
    """Register inventory & fiscal event handlers.

    Called from InventoryConfig.ready() to avoid import-time circular imports.
    """
    try:
        from apps.sales.models import Venda as _Venda  # noqa: F401
        post_save.connect(_on_venda_finalizada, sender=_Venda, dispatch_uid='inventory_venda_finalizada')
        logger.debug("Inventory signal handlers connected.")
    except ImportError:
        logger.warning("Sales app not available — inventory signals not connected.")


def _on_venda_finalizada(sender, instance, created, **kwargs):
    """Trigger NFe automation check when a sale is saved with status FINALIZADA.

    - Confirms stock reservations for the checkout session.
    - Triggers NFe emission if applicable (B2B customer).

    Full NFe transmission logic lives in Phase 3 (T041-T055).
    """
    status = getattr(instance, 'status', None)
    if status != 'FINALIZADA':
        return

    sessao = getattr(instance, 'sessao_checkout', None) or str(instance.pk)

    # 1. Confirm stock reservations
    try:
        from apps.inventory.services import EstoqueService
        EstoqueService.confirmar_reservas(sessao_checkout=sessao, venda_id=instance.pk)
    except Exception as exc:
        logger.error("Erro ao confirmar reservas para venda %s: %s", instance.pk, exc)

    # 2. Trigger NFe processing (async, Phase 3 stub)
    try:
        from apps.fiscal.services import NFEService
        if NFEService.deve_emitir_nfe_automatica(instance):
            NFEService.processar_nfe_venda(str(instance.pk), usuario=None)
    except Exception as exc:
        logger.error("Erro ao processar NFe para venda %s: %s", instance.pk, exc)
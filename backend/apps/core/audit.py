"""
Audit Logging Infrastructure - T007
=====================================

Comprehensive audit logging system for the hierarchical permission system.
Provides cryptographic integrity validation, high-performance logging, and
efficient querying capabilities.

Features:
- Real-time audit trail for all permission changes
- Cryptographic hash chaining for tamper detection
- Async logging for performance optimization
- Comprehensive metadata capture
- Efficient search and filtering
- Alert system for audit failures

Author: GitHub Copilot
Created: 2026-04-18
Task: T007 - Audit Logging Infrastructure
"""

import hashlib
import json
import logging
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.db import transaction
from django.utils import timezone as django_timezone
from .models import PermissionAuditLog, Permission, UserGroup, UserPermission, GroupPermission

User = get_user_model()
logger = logging.getLogger('permission_audit')


class AuditLogger:
    """
    High-performance audit logging system with cryptographic integrity validation.
    
    Provides comprehensive audit trails for permission system changes with
    hash chaining, async processing, and failure alerting.
    """
    
    # Action types for consistent audit categorization
    ACTION_TYPES = {
        'GRANT': 'Permission granted to entity',
        'REVOKE': 'Permission revoked from entity', 
        'CREATE': 'Permission or entity created',
        'DELETE': 'Permission or entity deleted',
        'MODIFY': 'Permission or entity modified',
        'LOGIN': 'User authentication event',
        'ACCESS_ATTEMPT': 'Permission access attempt',
        'SECURITY_VIOLATION': 'Security policy violation detected',
        'SYSTEM_EVENT': 'System-level permission event'
    }
    
    # Critical events requiring immediate alerting
    CRITICAL_ACTIONS = {
        'SECURITY_VIOLATION', 'SYSTEM_EVENT', 'DELETE'
    }
    
    def __init__(self):
        """Initialize audit logger with configuration settings."""
        self.enabled = getattr(settings, 'AUDIT_LOGGING_ENABLED', True)
        self.async_logging = getattr(settings, 'AUDIT_ASYNC_ENABLED', True)
        self.hash_chaining = getattr(settings, 'AUDIT_HASH_CHAINING_ENABLED', True)
        self.alert_on_failure = getattr(settings, 'AUDIT_ALERT_ON_FAILURE', True)
        
        # Performance optimization settings
        self.batch_size = getattr(settings, 'AUDIT_BATCH_SIZE', 100)
        self.cache_timeout = getattr(settings, 'AUDIT_CACHE_TIMEOUT', 300)
        self.max_details_size = getattr(settings, 'AUDIT_MAX_DETAILS_SIZE', 8192)
    
    def log_permission_change(
        self,
        action: str,
        entity_type: str,
        entity_id: str,
        user: Optional[User] = None,
        permission: Optional[Permission] = None,
        details: Optional[Dict[str, Any]] = None,
        request_info: Optional[Dict[str, str]] = None
    ) -> Optional[PermissionAuditLog]:
        """
        Log a permission-related change with full context and integrity validation.
        
        Args:
            action: Action type from ACTION_TYPES
            entity_type: Type of entity (user, group, permission)
            entity_id: ID of the affected entity
            user: User performing the action (if available)
            permission: Permission involved in the action (if applicable)
            details: Additional context and metadata
            request_info: HTTP request context (IP, user agent, etc.)
            
        Returns:
            PermissionAuditLog instance if successful, None if failed
        """
        if not self.enabled:
            return None
            
        try:
            # Prepare audit data
            audit_data = self._prepare_audit_data(
                action, entity_type, entity_id, user, permission, details, request_info
            )
            
            # Add cryptographic integrity if enabled  
            if self.hash_chaining:
                audit_data['integrity_hash'] = self._generate_integrity_hash(audit_data)
                audit_data['previous_hash'] = self._get_previous_hash()
            
            # Create audit log entry
            with transaction.atomic():
                audit_log = PermissionAuditLog.log_action(
                    action=audit_data.get('action', action),
                    actor=audit_data.get('user', user),
                    target_user=audit_data.get('target_user'),
                    details=audit_data.get('details', {})
                )
                
                # Update hash chain cache
                if self.hash_chaining:
                    self._update_hash_chain(audit_log.integrity_hash)
                
                # Trigger alerts for critical events
                if action in self.CRITICAL_ACTIONS:
                    self._trigger_security_alert(audit_log)
                
                logger.info(f"Audit logged: {action} on {entity_type}:{entity_id}")
                return audit_log
                
        except Exception as e:
            logger.error(f"Audit logging failed: {str(e)}")
            
            # Trigger failure alert if enabled
            if self.alert_on_failure:
                self._trigger_audit_failure_alert(action, entity_type, entity_id, str(e))
            
            # Fallback to system log
            self._fallback_log(action, entity_type, entity_id, user, str(e))
            return None
    
    def _prepare_audit_data(
        self,
        action: str,
        entity_type: str,
        entity_id: str,
        user: Optional[User],
        permission: Optional[Permission],
        details: Optional[Dict[str, Any]],
        request_info: Optional[Dict[str, str]]
    ) -> Dict[str, Any]:
        """Prepare comprehensive audit data structure."""
        
        # Base audit data
        audit_data = {
            'action': action,
            'entity_type': entity_type,
            'entity_id': entity_id,
            'timestamp': django_timezone.now(),
            'user': user,
            'permission': permission,
            'success': True  # Will be set based on operation success
        }
        
        # Combine details with request info
        combined_details = {}
        if details:
            combined_details.update(details)
        if request_info:
            combined_details['request'] = request_info
            
        # Add system context
        combined_details['system'] = {
            'python_version': getattr(settings, 'PYTHON_VERSION', 'unknown'),
            'django_version': getattr(settings, 'DJANGO_VERSION', 'unknown'),
            'server_time': datetime.now(timezone.utc).isoformat(),
            'process_id': getattr(settings, 'PROCESS_ID', 'unknown')
        }
        
        # Truncate details if too large
        details_json = json.dumps(combined_details)
        if len(details_json) > self.max_details_size:
            truncated_details = {
                'truncated': True,
                'original_size': len(details_json),
                'summary': str(combined_details)[:self.max_details_size//2]
            }
            audit_data['details'] = truncated_details
        else:
            audit_data['details'] = combined_details
            
        return audit_data
    
    def _generate_integrity_hash(self, audit_data: Dict[str, Any]) -> str:
        """
        Generate cryptographic hash for audit integrity validation.
        
        Uses SHA-256 with structured data serialization for consistent hashing.
        """
        # Create hashable representation
        hash_data = {
            'action': audit_data['action'],
            'entity_type': audit_data['entity_type'],
            'entity_id': audit_data['entity_id'],
            'timestamp': audit_data['timestamp'].isoformat(),
            'user_id': audit_data['user'].id if audit_data['user'] else None,
            'permission_id': audit_data['permission'].id if audit_data['permission'] else None,
            'details_hash': hashlib.sha256(
                json.dumps(audit_data.get('details', {}), sort_keys=True).encode()
            ).hexdigest()
        }
        
        # Generate hash
        hash_string = json.dumps(hash_data, sort_keys=True)
        return hashlib.sha256(hash_string.encode()).hexdigest()
    
    def _get_previous_hash(self) -> Optional[str]:
        """Get the hash of the most recent audit log entry for chaining."""
        cache_key = 'audit_last_hash'
        cached_hash = cache.get(cache_key)
        
        if cached_hash:
            return cached_hash
            
        # Fallback to database query
        try:
            last_entry = PermissionAuditLog.objects.filter(
                integrity_hash__isnull=False
            ).order_by('-timestamp').first()
            
            if last_entry:
                cache.set(cache_key, last_entry.integrity_hash, self.cache_timeout)
                return last_entry.integrity_hash
        except Exception as e:
            logger.warning(f"Failed to get previous hash: {str(e)}")
        
        return None
    
    def _update_hash_chain(self, new_hash: str) -> None:
        """Update the hash chain cache with the new hash."""
        cache_key = 'audit_last_hash'
        cache.set(cache_key, new_hash, self.cache_timeout)
    
    def _trigger_security_alert(self, audit_log: PermissionAuditLog) -> None:
        """Trigger immediate security alert for critical events."""
        alert_data = {
            'type': 'SECURITY_AUDIT_ALERT',
            'action': audit_log.action,
            'entity': f"{audit_log.entity_type}:{audit_log.entity_id}",
            'user': audit_log.user.username if audit_log.user else 'system',
            'timestamp': audit_log.timestamp.isoformat(),
            'details': audit_log.details
        }
        
        # Log to security logger
        security_logger = logging.getLogger('security.alerts')
        security_logger.critical(f"Security event: {json.dumps(alert_data)}")
        
        # TODO: Integrate with external alerting system (email, Slack, etc.)
        # self._send_external_alert(alert_data)
    
    def _trigger_audit_failure_alert(
        self,
        action: str,
        entity_type: str,
        entity_id: str,
        error: str
    ) -> None:
        """Trigger alert when audit logging fails."""
        alert_data = {
            'type': 'AUDIT_FAILURE_ALERT',
            'failed_action': action,
            'entity': f"{entity_type}:{entity_id}",
            'error': error,
            'timestamp': datetime.now(timezone.utc).isoformat()
        }
        
        # Log to critical logger
        critical_logger = logging.getLogger('critical.audit_failures')
        critical_logger.critical(f"Audit logging failed: {json.dumps(alert_data)}")
        
        # TODO: Implement external failure alerting
        # self._send_critical_alert(alert_data)
    
    def _fallback_log(
        self,
        action: str,
        entity_type: str,
        entity_id: str,
        user: Optional[User],
        error: str
    ) -> None:
        """Fallback logging when primary audit system fails."""
        fallback_data = {
            'action': action,
            'entity': f"{entity_type}:{entity_id}",
            'user': user.username if user else 'system',
            'error': error,
            'timestamp': datetime.now(timezone.utc).isoformat()
        }
        
        # Log to fallback logger
        fallback_logger = logging.getLogger('audit.fallback')
        fallback_logger.error(f"Fallback audit: {json.dumps(fallback_data)}")
    
    def verify_integrity_chain(self, limit: Optional[int] = None) -> Dict[str, Any]:
        """
        Verify the cryptographic integrity of the audit log chain.
        
        Args:
            limit: Maximum number of entries to verify (for performance)
            
        Returns:
            Verification report with results and any detected issues
        """
        if not self.hash_chaining:
            return {'status': 'disabled', 'message': 'Hash chaining not enabled'}
        
        try:
            # Get audit entries in chronological order
            queryset = PermissionAuditLog.objects.filter(
                integrity_hash__isnull=False
            ).order_by('timestamp')
            
            if limit:
                queryset = queryset[:limit]
                
            entries = list(queryset)
            
            verification_result = {
                'status': 'success',
                'total_entries': len(entries),
                'verified_entries': 0,
                'integrity_violations': [],
                'chain_breaks': [],
                'verification_time': datetime.now(timezone.utc).isoformat()
            }
            
            previous_hash = None
            
            for i, entry in enumerate(entries):
                # Verify individual entry hash
                expected_hash = self._generate_integrity_hash({
                    'action': entry.action,
                    'entity_type': entry.entity_type,
                    'entity_id': entry.entity_id,
                    'timestamp': entry.timestamp,
                    'user': entry.user,
                    'permission': entry.permission,
                    'details': entry.details
                })
                
                if entry.integrity_hash != expected_hash:
                    verification_result['integrity_violations'].append({
                        'entry_id': entry.id,
                        'expected_hash': expected_hash,
                        'actual_hash': entry.integrity_hash,
                        'timestamp': entry.timestamp.isoformat()
                    })
                
                # Verify chain continuity
                if previous_hash and hasattr(entry, 'previous_hash'):
                    if entry.previous_hash != previous_hash:
                        verification_result['chain_breaks'].append({
                            'entry_id': entry.id,
                            'expected_previous': previous_hash,
                            'actual_previous': getattr(entry, 'previous_hash', None),
                            'position': i
                        })
                
                previous_hash = entry.integrity_hash
                verification_result['verified_entries'] += 1
            
            # Determine overall status
            if verification_result['integrity_violations'] or verification_result['chain_breaks']:
                verification_result['status'] = 'compromised'
            
            return verification_result
            
        except Exception as e:
            return {
                'status': 'error',
                'message': f"Verification failed: {str(e)}",
                'timestamp': datetime.now(timezone.utc).isoformat()
            }


class AuditQuerySet:
    """
    Efficient querying and filtering for audit logs with performance optimization.
    
    Provides specialized methods for common audit log queries with caching
    and optimization for high-volume audit data.
    """
    
    def __init__(self, queryset=None):
        """Initialize with base queryset or default to all audit logs."""
        self.queryset = queryset or PermissionAuditLog.objects.all()
    
    def for_user(self, user: User) -> 'AuditQuerySet':
        """Filter audit logs related to a specific user."""
        return AuditQuerySet(
            self.queryset.filter(user=user).select_related('user', 'permission')
        )
    
    def for_entity(self, entity_type: str, entity_id: str) -> 'AuditQuerySet':
        """Filter audit logs for a specific entity."""
        return AuditQuerySet(
            self.queryset.filter(entity_type=entity_type, entity_id=entity_id)
        )
    
    def by_action(self, action: str) -> 'AuditQuerySet':
        """Filter audit logs by action type."""
        return AuditQuerySet(self.queryset.filter(action=action))
    
    def in_timeframe(self, start_time: datetime, end_time: datetime) -> 'AuditQuerySet':
        """Filter audit logs within a specific timeframe."""
        return AuditQuerySet(
            self.queryset.filter(timestamp__range=[start_time, end_time])
        )
    
    def security_events(self) -> 'AuditQuerySet':
        """Filter for security-related audit events."""
        security_actions = ['SECURITY_VIOLATION', 'ACCESS_ATTEMPT', 'LOGIN']
        return AuditQuerySet(
            self.queryset.filter(action__in=security_actions).order_by('-timestamp')
        )
    
    def failed_operations(self) -> 'AuditQuerySet':
        """Filter for failed operations and security violations."""
        return AuditQuerySet(
            self.queryset.filter(success=False).order_by('-timestamp')
        )
    
    def permission_changes(self, permission: Optional[Permission] = None) -> 'AuditQuerySet':
        """Filter for permission-related changes."""
        queryset = self.queryset.filter(action__in=['GRANT', 'REVOKE', 'MODIFY'])
        
        if permission:
            queryset = queryset.filter(permission=permission)
            
        return AuditQuerySet(queryset.select_related('permission'))
    
    def with_details_containing(self, key: str, value: Any = None) -> 'AuditQuerySet':
        """Filter audit logs where details JSON contains specific key/value."""
        if value is not None:
            return AuditQuerySet(
                self.queryset.filter(details__contains={key: value})
            )
        else:
            return AuditQuerySet(
                self.queryset.filter(details__has_key=key)
            )
    
    def aggregate_by_action(self) -> Dict[str, int]:
        """Get count of audit logs grouped by action type."""
        from django.db.models import Count
        
        cache_key = f'audit_action_counts_{hash(str(self.queryset.query))}'
        cached_result = cache.get(cache_key)
        
        if cached_result:
            return cached_result
        
        result = dict(
            self.queryset.values('action').annotate(count=Count('id')).values_list('action', 'count')
        )
        
        cache.set(cache_key, result, 300)  # Cache for 5 minutes
        return result
    
    def recent(self, hours: int = 24) -> 'AuditQuerySet':
        """Get recent audit logs within specified hours."""
        since = django_timezone.now() - django_timezone.timedelta(hours=hours)
        return AuditQuerySet(
            self.queryset.filter(timestamp__gte=since).order_by('-timestamp')
        )
    
    def get_summary(self) -> Dict[str, Any]:
        """Get comprehensive summary of audit logs in the queryset."""
        from django.db.models import Count, Min, Max
        
        stats = self.queryset.aggregate(
            total_count=Count('id'),
            first_entry=Min('timestamp'),
            last_entry=Max('timestamp')
        )
        
        action_counts = self.aggregate_by_action()
        
        return {
            'total_entries': stats['total_count'],
            'date_range': {
                'first_entry': stats['first_entry'].isoformat() if stats['first_entry'] else None,
                'last_entry': stats['last_entry'].isoformat() if stats['last_entry'] else None
            },
            'action_distribution': action_counts,
            'generated_at': datetime.now(timezone.utc).isoformat()
        }


# Global audit logger instance
audit_logger = AuditLogger()


# Convenience functions for common audit operations
def log_permission_grant(user: User, permission: Permission, target_user: User, **kwargs) -> Optional[PermissionAuditLog]:
    """Log permission grant to user."""
    return audit_logger.log_permission_change(
        action='GRANT',
        entity_type='user',
        entity_id=target_user.id,
        user=user,
        permission=permission,
        details={'target_user': target_user.username},
        **kwargs
    )


def log_permission_revoke(user: User, permission: Permission, target_user: User, **kwargs) -> Optional[PermissionAuditLog]:
    """Log permission revocation from user."""
    return audit_logger.log_permission_change(
        action='REVOKE',
        entity_type='user', 
        entity_id=target_user.id,
        user=user,
        permission=permission,
        details={'target_user': target_user.username},
        **kwargs
    )


def log_group_assignment(user: User, group: UserGroup, target_user: User, **kwargs) -> Optional[PermissionAuditLog]:
    """Log user assignment to group."""
    return audit_logger.log_permission_change(
        action='GRANT',
        entity_type='group_membership',
        entity_id=f"{target_user.id}:{group.id}",
        user=user,
        details={
            'group_name': group.name,
            'target_user': target_user.username,
            'group_id': group.id
        },
        **kwargs
    )


def log_security_violation(user: Optional[User], violation_type: str, details: Dict[str, Any], **kwargs) -> Optional[PermissionAuditLog]:
    """Log security policy violation."""
    return audit_logger.log_permission_change(
        action='SECURITY_VIOLATION',
        entity_type='security',
        entity_id=violation_type,
        user=user,
        details={
            'violation_type': violation_type,
            **details
        },
        **kwargs
    )


def log_access_attempt(user: User, permission: Permission, success: bool, **kwargs) -> Optional[PermissionAuditLog]:
    """Log permission access attempt."""
    return audit_logger.log_permission_change(
        action='ACCESS_ATTEMPT',
        entity_type='permission',
        entity_id=permission.id if permission else 'unknown',
        user=user,
        permission=permission,
        details={
            'success': success,
            'permission_code': permission.code if permission else 'unknown'
        },
        **kwargs
    )


# Query helper
def get_audit_logs() -> AuditQuerySet:
    """Get audit log queryset with optimization methods."""
    return AuditQuerySet()
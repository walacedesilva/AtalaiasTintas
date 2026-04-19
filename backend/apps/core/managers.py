"""
Model Managers for User Permission System
Provides optimized database queries, caching, and business logic for permission resolution.

Created: 2026-04-18
Author: Sistema de Tintas - Spec Kit Implementation T003
"""

from django.contrib.auth.models import BaseUserManager
from django.db import models, transaction
from django.core.cache import cache
from django.db.models import Q, Prefetch, Exists, OuterRef
from django.utils import timezone
from django.conf import settings
from typing import List, Dict, Set, Optional, Union, Any
import hashlib
import json
import logging

logger = logging.getLogger(__name__)


class CustomUserManager(BaseUserManager):
    """
    Custom User Manager with permission system integration.
    Provides efficient permission checking and user management methods.
    """
    
    def create_user(self, username: str, email: str = None, password: str = None, **extra_fields):
        """Create and save a regular user with the given username and password."""
        if not username:
            raise ValueError('Username is required')
        
        email = self.normalize_email(email)
        user = self.model(username=username, email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user
    
    def create_superuser(self, username: str, email: str = None, password: str = None, **extra_fields):
        """Create and save a superuser with the given username and password."""
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('pode_administrar', True)
        
        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')
        
        return self.create_user(username, email, password, **extra_fields)
    
    def with_permission(self, permission_code: str) -> models.QuerySet:
        """
        Return users who have the specified permission (directly or through groups).
        Uses optimized query with proper JOINs and caching.
        """
        return self.filter(
            Q(user_permissions_new__permission__module=permission_code.split('.')[0],
              user_permissions_new__permission__resource=permission_code.split('.')[1],
              user_permissions_new__permission__action=permission_code.split('.')[2],
              user_permissions_new__is_active=True,
              user_permissions_new__grant_type='allow') |
            Q(group_memberships__group__group_permissions__permission__module=permission_code.split('.')[0],
              group_memberships__group__group_permissions__permission__resource=permission_code.split('.')[1],
              group_memberships__group__group_permissions__permission__action=permission_code.split('.')[2],
              group_memberships__is_active=True,
              group_memberships__group__group_permissions__is_active=True,
              group_memberships__group__group_permissions__grant_type='allow')
        ).distinct()
    
    def with_module_access(self, module: str) -> models.QuerySet:
        """Return users who have any permission in the specified module."""
        return self.filter(
            Q(user_permissions_new__permission__module=module,
              user_permissions_new__is_active=True,
              user_permissions_new__grant_type='allow') |
            Q(group_memberships__group__group_permissions__permission__module=module,
              group_memberships__is_active=True,
              group_memberships__group__group_permissions__is_active=True,
              group_memberships__group__group_permissions__grant_type='allow')
        ).distinct()
    
    def active_users(self) -> models.QuerySet:
        """Return only active users with optimized permission prefetching."""
        return self.filter(is_active=True).select_related().prefetch_related(
            'user_permissions_new__permission',
            'group_memberships__group__group_permissions__permission',
            'group_memberships__group__parent'
        )


class PermissionManager(models.Manager):
    """
    Permission Manager with efficient resolution and caching support.
    Handles permission queries, validation, and cache management.
    """
    
    CACHE_TIMEOUT = getattr(settings, 'PERMISSION_CACHE_TIMEOUT', 300)  # 5 minutes default
    CACHE_PREFIX = 'perm'
    
    def get_by_code(self, code: str) -> Optional['Permission']:
        """
        Get permission by full code (module.resource.action).
        Uses caching for performance optimization.
        """
        cache_key = f"{self.CACHE_PREFIX}:code:{code}"
        permission = cache.get(cache_key)
        
        if permission is None:
            parts = code.split('.')
            if len(parts) != 3:
                raise ValueError(f"Invalid permission code format: {code}")
            
            try:
                permission = self.get(
                    module=parts[0],
                    resource=parts[1], 
                    action=parts[2],
                    is_active=True
                )
                cache.set(cache_key, permission, self.CACHE_TIMEOUT)
            except self.model.DoesNotExist:
                logger.warning(f"Permission not found: {code}")
                return None
                
        return permission
    
    def by_module(self, module: str) -> models.QuerySet:
        """Get all permissions for a specific module."""
        return self.filter(module=module, is_active=True).order_by('resource', 'action')
    
    def system_permissions(self) -> models.QuerySet:
        """Get all system-defined permissions."""
        return self.filter(is_system=True, is_active=True)
    
    def user_creatable_permissions(self) -> models.QuerySet:
        """Get permissions that can be assigned by users (non-system)."""
        return self.filter(is_system=False, is_active=True)
    
    def resolve_user_permissions(self, user, with_inheritance: bool = True) -> Set[str]:
        """
        Resolve all effective permissions for a user with caching.
        
        Args:
            user: User instance
            with_inheritance: Include permissions from parent groups
            
        Returns:
            Set of permission codes the user has access to
        """
        cache_key = f"{self.CACHE_PREFIX}:user:{user.id}:{with_inheritance}"
        permissions = cache.get(cache_key)
        
        if permissions is None:
            permissions = set()
            
            # Direct user permissions
            direct_perms = self.filter(
                user_permissions__user=user,
                user_permissions__is_active=True,
                user_permissions__grant_type='allow',
                is_active=True
            ).values_list('module', 'resource', 'action')
            
            for module, resource, action in direct_perms:
                permissions.add(f"{module}.{resource}.{action}")
            
            # Group permissions (with inheritance if enabled)
            if with_inheritance:
                group_perms = self._resolve_group_permissions(user)
                permissions.update(group_perms)
            
            # Apply denials (they override allows)
            permissions = self._apply_permission_denials(user, permissions)
            
            cache.set(cache_key, permissions, self.CACHE_TIMEOUT)
            
        return permissions
    
    def _resolve_group_permissions(self, user) -> Set[str]:
        """Resolve permissions from user's groups with hierarchical inheritance."""
        permissions = set()
        
        # Get user's active groups with parent relationships
        from .models import GroupMembership
        memberships = GroupMembership.objects.filter(
            user=user,
            is_active=True
        ).select_related('group').prefetch_related(
            'group__group_permissions__permission',
            'group__parent'
        )
        
        for membership in memberships:
            group = membership.group
            
            # Direct group permissions
            group_perms = self.filter(
                group_permissions__group=group,
                group_permissions__is_active=True,
                group_permissions__grant_type='allow',
                is_active=True
            ).values_list('module', 'resource', 'action')
            
            for module, resource, action in group_perms:
                permissions.add(f"{module}.{resource}.{action}")
            
            # Inherited permissions from parent groups
            permissions.update(self._resolve_inherited_permissions(group))
                
        return permissions
    
    def _resolve_inherited_permissions(self, group) -> Set[str]:
        """Recursively resolve permissions inherited from parent groups."""
        permissions = set()
        current_group = group.parent
        
        while current_group:
            inherited_perms = self.filter(
                group_permissions__group=current_group,
                group_permissions__is_active=True,
                group_permissions__grant_type='allow',
                group_permissions__inherit_to_children=True,
                is_active=True
            ).values_list('module', 'resource', 'action')
            
            for module, resource, action in inherited_perms:
                permissions.add(f"{module}.{resource}.{action}")
                
            current_group = current_group.parent
            
        return permissions
    
    def _apply_permission_denials(self, user, allowed_permissions: Set[str]) -> Set[str]:
        """Apply permission denials to override allows."""
        # Direct user denials
        user_denials = self.filter(
            user_permissions__user=user,
            user_permissions__is_active=True,
            user_permissions__grant_type='deny',
            is_active=True
        ).values_list('module', 'resource', 'action')
        
        # Group denials
        group_denials = self.filter(
            group_permissions__group__group_memberships__user=user,
            group_permissions__group__group_memberships__is_active=True,
            group_permissions__is_active=True,
            group_permissions__grant_type='deny',
            is_active=True
        ).values_list('module', 'resource', 'action')
        
        # Build denial set
        denial_codes = set()
        for module, resource, action in list(user_denials) + list(group_denials):
            denial_codes.add(f"{module}.{resource}.{action}")
        
        # Remove denied permissions from allowed set
        return allowed_permissions - denial_codes
    
    def invalidate_user_cache(self, user):
        """Invalidate permission cache for a specific user."""
        for with_inheritance in [True, False]:
            cache_key = f"{self.CACHE_PREFIX}:user:{user.id}:{with_inheritance}"
            cache.delete(cache_key)
        
        logger.info(f"Permission cache invalidated for user {user.username}")


class UserGroupManager(models.Manager):
    """
    UserGroup Manager with hierarchical operations and inheritance calculation.
    Handles group hierarchy, membership management, and permission inheritance.
    """
    
    def active_groups(self) -> models.QuerySet:
        """Get all active groups with optimized hierarchy prefetching."""
        return self.filter(is_active=True).select_related('parent', 'created_by').prefetch_related(
            'group_permissions__permission',
            'group_memberships__user'
        )
    
    def root_groups(self) -> models.QuerySet:
        """Get top-level groups (no parent)."""
        return self.filter(parent__isnull=True, is_active=True)
    
    def system_groups(self) -> models.QuerySet:
        """Get system-defined groups that cannot be deleted."""
        return self.filter(is_system=True, is_active=True)
    
    def user_creatable_groups(self) -> models.QuerySet:
        """Get groups that can be managed by users (non-system)."""
        return self.filter(is_system=False, is_active=True)
    
    def get_children(self, group) -> models.QuerySet:
        """Get direct children of a group."""
        return self.filter(parent=group, is_active=True)
    
    def get_descendants(self, group) -> List['UserGroup']:
        """
        Get all descendants of a group (recursive).
        Returns flattened list of all child groups at any level.
        """
        descendants = []
        children = list(self.get_children(group))
        
        for child in children:
            descendants.append(child)
            descendants.extend(self.get_descendants(child))
            
        return descendants
    
    def get_ancestors(self, group) -> List['UserGroup']:
        """
        Get all ancestors of a group (up to root).
        Returns list from immediate parent to root.
        """
        ancestors = []
        current = group.parent
        
        while current:
            ancestors.append(current)
            current = current.parent
            
        return ancestors
    
    def get_user_groups(self, user, include_inherited: bool = False) -> models.QuerySet:
        """
        Get groups user belongs to.
        
        Args:
            user: User instance
            include_inherited: Include parent groups in hierarchy
        """
        direct_groups = self.filter(
            group_memberships__user=user,
            group_memberships__is_active=True,
            is_active=True
        )
        
        if not include_inherited:
            return direct_groups
        
        # Include parent groups for inherited permissions
        all_groups = set(direct_groups)
        for group in direct_groups:
            all_groups.update(self.get_ancestors(group))
            
        return self.filter(id__in=[g.id for g in all_groups])
    
    def can_inherit_permissions(self, parent_group, child_group) -> bool:
        """
        Check if child_group can inherit permissions from parent_group.
        Validates hierarchy relationship and inheritance rules.
        """
        if not parent_group or not child_group:
            return False
            
        # Check if parent_group is actually an ancestor of child_group
        ancestors = self.get_ancestors(child_group)
        return parent_group in ancestors
    
    def validate_hierarchy(self, group, new_parent) -> bool:
        """
        Validate that setting new_parent wouldn't create circular reference.
        
        Args:
            group: Group to set parent for
            new_parent: Proposed parent group
            
        Returns:
            True if hierarchy is valid, False if circular reference detected
        """
        if not new_parent:
            return True
            
        # Check if new_parent is a descendant of group
        descendants = self.get_descendants(group)
        return new_parent not in descendants
    
    def get_effective_permissions(self, group) -> Set[str]:
        """
        Get all effective permissions for a group including inherited ones.
        Uses caching for performance optimization.
        """
        cache_key = f"group:permissions:{group.id}"
        permissions = cache.get(cache_key)
        
        if permissions is None:
            permissions = set()
            
            # Direct group permissions
            from .models import Permission
            direct_perms = Permission.objects.filter(
                group_permissions__group=group,
                group_permissions__is_active=True,
                group_permissions__grant_type='allow',
                is_active=True
            ).values_list('module', 'resource', 'action')
            
            for module, resource, action in direct_perms:
                permissions.add(f"{module}.{resource}.{action}")
            
            # Inherited permissions from ancestors
            ancestors = self.get_ancestors(group)
            for ancestor in ancestors:
                inherited_perms = Permission.objects.filter(
                    group_permissions__group=ancestor,
                    group_permissions__is_active=True,
                    group_permissions__grant_type='allow',
                    group_permissions__inherit_to_children=True,
                    is_active=True
                ).values_list('module', 'resource', 'action')
                
                for module, resource, action in inherited_perms:
                    permissions.add(f"{module}.{resource}.{action}")
            
            cache.set(cache_key, permissions, 300)  # 5 minute cache
            
        return permissions
    
    def invalidate_group_cache(self, group):
        """Invalidate permission cache for group and all descendants."""
        cache.delete(f"group:permissions:{group.id}")
        
        # Also invalidate descendant caches since they inherit permissions
        for child in self.get_descendants(group):
            cache.delete(f"group:permissions:{child.id}")


class PermissionAuditLogManager(models.Manager):
    """
    Audit Manager with secure logging and integrity validation.
    Provides immutable audit trail for all permission-related operations.
    """
    
    def log_permission_change(self, action: str, actor, details: Dict[str, Any], 
                            target_user=None, target_group=None, permission=None,
                            reason: str = '', ip_address: str = '', 
                            user_agent: str = '', session_key: str = '') -> 'PermissionAuditLog':
        """
        Create audit log entry for permission change.
        
        Args:
            action: Type of action performed
            actor: User who performed the action
            details: Dictionary with action details
            target_user: User affected by action (optional)
            target_group: Group affected by action (optional) 
            permission: Permission affected by action (optional)
            reason: Reason for the action
            ip_address: IP address of the actor
            user_agent: User agent string
            session_key: Session identifier
            
        Returns:
            Created audit log entry
        """
        # Validate action type
        valid_actions = [
            'user_created', 'user_updated', 'user_deleted',
            'group_created', 'group_updated', 'group_deleted',
            'permission_created', 'permission_updated', 'permission_deleted',
            'user_permission_granted', 'user_permission_revoked',
            'group_permission_granted', 'group_permission_revoked',
            'user_added_to_group', 'user_removed_from_group',
            'permission_checked', 'access_granted', 'access_denied',
            'login_attempt', 'logout', 'session_expired',
            'bulk_permission_update', 'system_maintenance'
        ]
        
        if action not in valid_actions:
            raise ValueError(f"Invalid action type: {action}")
        
        # Ensure details is JSON serializable
        try:
            json.dumps(details)
        except (TypeError, ValueError) as e:
            raise ValueError(f"Details must be JSON serializable: {e}")
        
        # Create audit entry with integrity hash
        audit_entry = self.create(
            action=action,
            actor=actor,
            target_user=target_user,
            target_group=target_group,
            permission=permission,
            details=details,
            reason=reason[:500],  # Truncate reason to prevent abuse
            ip_address=ip_address[:45],  # IPv6 max length
            user_agent=user_agent[:500],  # Reasonable user agent limit
            session_key=session_key[:40],  # Django session key length
            result='success'  # Default to success, caller can update if needed
        )
        
        logger.info(f"Audit log created: {action} by {actor.username} for {target_user or target_group}")
        return audit_entry
    
    def log_permission_check(self, user, permission_code: str, granted: bool, 
                           ip_address: str = '', user_agent: str = '', 
                           session_key: str = '') -> 'PermissionAuditLog':
        """Log permission check for compliance and debugging."""
        return self.log_permission_change(
            action='permission_checked',
            actor=user,
            target_user=user,
            details={
                'permission_code': permission_code,
                'granted': granted,
                'check_timestamp': timezone.now().isoformat()
            },
            reason=f"Permission check: {permission_code}",
            ip_address=ip_address,
            user_agent=user_agent,
            session_key=session_key
        )
    
    def log_access_attempt(self, user, resource: str, granted: bool, 
                         reason: str = '', ip_address: str = '', 
                         user_agent: str = '', session_key: str = '') -> 'PermissionAuditLog':
        """Log access attempts for security monitoring."""
        action = 'access_granted' if granted else 'access_denied'
        
        return self.log_permission_change(
            action=action,
            actor=user,
            target_user=user,
            details={
                'resource': resource,
                'granted': granted,
                'access_timestamp': timezone.now().isoformat()
            },
            reason=reason or f"Access attempt to {resource}",
            ip_address=ip_address,
            user_agent=user_agent,
            session_key=session_key
        )
    
    def get_user_activity(self, user, days: int = 30) -> models.QuerySet:
        """Get audit trail for user activity in the last N days."""
        cutoff_date = timezone.now() - timezone.timedelta(days=days)
        
        return self.filter(
            Q(actor=user) | Q(target_user=user),
            created_at__gte=cutoff_date
        ).order_by('-created_at')
    
    def get_permission_history(self, permission, days: int = 90) -> models.QuerySet:
        """Get audit trail for a specific permission in the last N days."""
        cutoff_date = timezone.now() - timezone.timedelta(days=days)
        
        return self.filter(
            permission=permission,
            created_at__gte=cutoff_date
        ).order_by('-created_at')
    
    def get_security_events(self, days: int = 7) -> models.QuerySet:
        """Get security-relevant events for monitoring."""
        cutoff_date = timezone.now() - timezone.timedelta(days=days)
        
        security_actions = [
            'access_denied', 'user_permission_granted', 'user_permission_revoked',
            'group_permission_granted', 'group_permission_revoked', 
            'user_added_to_group', 'user_removed_from_group'
        ]
        
        return self.filter(
            action__in=security_actions,
            created_at__gte=cutoff_date
        ).order_by('-created_at')
    
    def validate_audit_integrity(self) -> Dict[str, Any]:
        """
        Validate audit log integrity for compliance.
        
        Returns:
            Dictionary with integrity validation results
        """
        total_entries = self.count()
        
        # Check for gaps in creation timestamps (potential tampering)
        entries_last_24h = self.filter(
            created_at__gte=timezone.now() - timezone.timedelta(hours=24)
        ).count()
        
        # Check for suspicious patterns
        failed_access_attempts = self.filter(
            action='access_denied',
            created_at__gte=timezone.now() - timezone.timedelta(hours=24)
        ).count()
        
        # Validate JSON integrity in details field
        invalid_json_count = 0
        for entry in self.filter(created_at__gte=timezone.now() - timezone.timedelta(days=1)):
            try:
                json.loads(json.dumps(entry.details))
            except (TypeError, ValueError):
                invalid_json_count += 1
        
        return {
            'total_entries': total_entries,
            'entries_last_24h': entries_last_24h,
            'failed_access_attempts': failed_access_attempts,
            'invalid_json_entries': invalid_json_count,
            'integrity_score': max(0, 100 - (invalid_json_count * 10)),
            'last_validated': timezone.now().isoformat()
        }


class GroupMembershipManager(models.Manager):
    """
    Group Membership Manager for user-group relationship management.
    Handles membership validation, temporal permissions, and bulk operations.
    """
    
    def active_memberships(self) -> models.QuerySet:
        """Get all active group memberships."""
        return self.filter(is_active=True)
    
    def get_user_memberships(self, user) -> models.QuerySet:
        """Get all active memberships for a user."""
        return self.filter(user=user, is_active=True).select_related('group')
    
    def get_group_members(self, group) -> models.QuerySet:
        """Get all active members of a group."""
        return self.filter(group=group, is_active=True).select_related('user')
    
    def add_user_to_group(self, user, group, added_by, is_primary: bool = False, 
                         valid_from: Optional[timezone.datetime] = None,
                         valid_until: Optional[timezone.datetime] = None,
                         notes: str = '') -> 'GroupMembership':
        """
        Add user to group with validation and audit logging.
        
        Args:
            user: User to add to group
            group: Target group
            added_by: User performing the action
            is_primary: Whether this is the user's primary group
            valid_from: Optional start date for membership
            valid_until: Optional end date for membership
            notes: Optional notes about the membership
            
        Returns:
            Created GroupMembership instance
        """
        # Validate primary group uniqueness
        if is_primary:
            existing_primary = self.filter(user=user, is_primary=True, is_active=True)
            if existing_primary.exists():
                raise ValueError(f"User {user.username} already has a primary group")
        
        # Validate group capacity if set 
        if group.max_users:
            current_members = self.filter(group=group, is_active=True).count()
            if current_members >= group.max_users:
                raise ValueError(f"Group {group.name} is at maximum capacity ({group.max_users})")
        
        # Validate temporal constraints
        if valid_from and valid_until and valid_from >= valid_until:
            raise ValueError("valid_from must be before valid_until")
        
        # Create membership
        with transaction.atomic():
            membership = self.create(
                user=user,
                group=group,
                is_active=True,
                is_primary=is_primary,
                valid_from=valid_from or timezone.now(),
                valid_until=valid_until,
                added_by=added_by,
                notes=notes[:500]  # Truncate notes
            )
            
            # Invalidate permission caches
            from .managers import PermissionManager
            PermissionManager().invalidate_user_cache(user)
            
            logger.info(f"User {user.username} added to group {group.name} by {added_by.username}")
            
        return membership
    
    def remove_user_from_group(self, user, group, removed_by, reason: str = '') -> bool:
        """
        Remove user from group (soft delete) with audit logging.
        
        Args:
            user: User to remove from group
            group: Target group  
            removed_by: User performing the action
            reason: Reason for removal
            
        Returns:
            True if membership was found and deactivated, False otherwise
        """
        try:
            with transaction.atomic():
                membership = self.get(user=user, group=group, is_active=True)
                membership.is_active = False
                membership.notes = f"Removed by {removed_by.username}: {reason}"[:500]
                membership.save()
                
                # Invalidate permission caches
                from .managers import PermissionManager
                PermissionManager().invalidate_user_cache(user)
                
                logger.info(f"User {user.username} removed from group {group.name} by {removed_by.username}")
                return True
                
        except self.model.DoesNotExist:
            logger.warning(f"Attempted to remove {user.username} from {group.name}, but membership not found")
            return False
    
    def get_temporal_memberships(self) -> models.QuerySet:
        """Get memberships with temporal validity constraints."""
        return self.filter(
            Q(valid_from__isnull=False) | Q(valid_until__isnull=False),
            is_active=True
        )
    
    def cleanup_expired_memberships(self) -> int:
        """
        Deactivate expired memberships based on valid_until dates.
        
        Returns:
            Number of memberships that were deactivated
        """
        now = timezone.now()
        expired_memberships = self.filter(
            valid_until__lt=now,
            is_active=True
        )
        
        count = expired_memberships.count()
        
        if count > 0:
            expired_memberships.update(
                is_active=False,
                notes=models.F('notes') + f" | Auto-expired on {now.isoformat()}"
            )
            
            # Invalidate caches for affected users
            from .managers import PermissionManager
            perm_manager = PermissionManager()
            for membership in expired_memberships:
                perm_manager.invalidate_user_cache(membership.user)
            
            logger.info(f"Deactivated {count} expired group memberships")
        
        return count
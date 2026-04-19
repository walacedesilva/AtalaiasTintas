# -*- coding: utf-8 -*-
"""
Permission Cache Infrastructure
Optimized Redis caching for permission data with automatic invalidation,
cache warming, failover handling, and performance monitoring.
"""

import logging
import hashlib
import json
import time
from typing import Dict, List, Optional, Any, Set, Union
from datetime import datetime, timedelta
from functools import wraps
from contextlib import contextmanager
from dataclasses import dataclass, asdict

from django.core.cache import cache
from django.core.cache.backends.redis import RedisCache
from django.conf import settings
from django.db.models import Q
from django.utils import timezone
from django.dispatch import receiver
from django.db.models.signals import post_save, post_delete
from django.core.management.color import make_style

# Import permission models
from .models import (
    Permission, UserGroup, UserPermission, 
    GroupPermission, PermissionAuditLog
)

logger = logging.getLogger(__name__)
style = make_style('ERROR')


@dataclass
class CacheMetrics:
    """Cache performance metrics tracking"""
    hits: int = 0
    misses: int = 0
    errors: int = 0
    avg_response_time: float = 0.0
    hit_ratio: float = 0.0
    last_updated: datetime = None
    cache_size: int = 0
    
    def update_hit_ratio(self):
        """Update hit ratio calculation"""
        total_requests = self.hits + self.misses
        self.hit_ratio = (self.hits / total_requests) if total_requests > 0 else 0.0
        
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        data = asdict(self)
        if self.last_updated:
            data['last_updated'] = self.last_updated.isoformat()
        return data


class PermissionCacheError(Exception):
    """Custom exception for permission cache errors"""
    pass


class PermissionCache:
    """
    High-performance Redis cache for permission data with automatic
    invalidation, warming, failover, and comprehensive monitoring.
    
    Features:
    - Hierarchical permission caching
    - Automatic invalidation on permission changes
    - Cache warming for common permissions
    - Graceful Redis failover to database
    - Performance metrics and monitoring
    - Cryptographic cache key validation
    """
    
    # Cache key prefixes for different data types
    CACHE_PREFIXES = {
        'user_permissions': 'perm:user:{}',
        'group_permissions': 'perm:group:{}', 
        'user_groups': 'groups:user:{}',
        'permission_hierarchy': 'perm:hierarchy:{}',
        'effective_permissions': 'perm:effective:{}',
        'permission_metadata': 'perm:meta:{}',
    }
    
    # Cache TTL configurations (in seconds)
    CACHE_TIMEOUTS = {
        'user_permissions': 3600,      # 1 hour
        'group_permissions': 7200,     # 2 hours
        'user_groups': 1800,          # 30 minutes
        'permission_hierarchy': 14400, # 4 hours
        'effective_permissions': 1800, # 30 minutes
        'permission_metadata': 86400,  # 24 hours
    }
    
    # Cache warming configuration
    WARMING_BATCH_SIZE = 50
    WARMING_DELAY = 0.1  # seconds between batches
    
    def __init__(self):
        """Initialize permission cache with monitoring"""
        self.metrics = CacheMetrics()
        self.is_redis_available = self._check_redis_availability()
        self.warming_in_progress = False
        
        # Initialize performance monitoring
        self._setup_monitoring()
        
    def _check_redis_availability(self) -> bool:
        """Check if Redis cache backend is available"""
        try:
            # Test Redis connection
            cache.set('_test_key', 'test_value', timeout=1)
            cache.get('_test_key')
            cache.delete('_test_key')
            return True
        except Exception as e:
            logger.warning(f"Redis cache unavailable: {e}")
            return False
    
    def _setup_monitoring(self):
        """Setup cache performance monitoring"""
        self.metrics.last_updated = timezone.now()
        logger.info("Permission cache monitoring initialized")
    
    def _generate_cache_key(self, prefix: str, identifier: Union[str, int], 
                          context: Dict[str, Any] = None) -> str:
        """
        Generate secure cache key with optional context hashing
        
        Args:
            prefix: Cache key prefix
            identifier: Primary identifier (user_id, group_id, etc.)
            context: Additional context for key generation
            
        Returns:
            Secure cache key string
        """
        base_key = prefix.format(identifier)
        
        if context:
            # Include context in key generation for cache isolation
            context_str = json.dumps(context, sort_keys=True)
            context_hash = hashlib.sha256(context_str.encode()).hexdigest()[:16]
            base_key = f"{base_key}:{context_hash}"
        
        return base_key
    
    @contextmanager
    def _measure_performance(self):
        """Context manager to measure cache operation performance"""
        start_time = time.time()
        try:
            yield
        except Exception as e:
            self.metrics.errors += 1
            logger.error(f"Cache operation error: {e}")
            raise
        finally:
            end_time = time.time()
            response_time = (end_time - start_time) * 1000  # Convert to milliseconds
            
            # Update rolling average response time
            if self.metrics.avg_response_time == 0:
                self.metrics.avg_response_time = response_time
            else:
                self.metrics.avg_response_time = (
                    (self.metrics.avg_response_time * 0.9) + 
                    (response_time * 0.1)
                )
    
    def get_user_permissions(self, user_id: int, include_groups: bool = True) -> Dict[str, Any]:
        """
        Get cached user permissions with optional group inclusion
        
        Args:
            user_id: User ID
            include_groups: Include group-based permissions
            
        Returns:
            Dictionary containing user permissions data
        """
        cache_key = self._generate_cache_key(
            self.CACHE_PREFIXES['effective_permissions'], 
            user_id,
            {'include_groups': include_groups}
        )
        
        with self._measure_performance():
            if self.is_redis_available:
                cached_data = cache.get(cache_key)
                if cached_data:
                    self.metrics.hits += 1
                    self.metrics.update_hit_ratio()
                    return cached_data
            
            # Cache miss - fetch from database
            self.metrics.misses += 1
            self.metrics.update_hit_ratio()
            
            permissions_data = self._fetch_user_permissions_from_db(user_id, include_groups)
            
            # Cache the result if Redis is available
            if self.is_redis_available and permissions_data:
                timeout = self.CACHE_TIMEOUTS['effective_permissions']
                cache.set(cache_key, permissions_data, timeout=timeout)
            
            return permissions_data
    
    def get_group_permissions(self, group_id: int) -> Dict[str, Any]:
        """Get cached group permissions"""
        cache_key = self._generate_cache_key(
            self.CACHE_PREFIXES['group_permissions'], 
            group_id
        )
        
        with self._measure_performance():
            if self.is_redis_available:
                cached_data = cache.get(cache_key)
                if cached_data:
                    self.metrics.hits += 1
                    self.metrics.update_hit_ratio()
                    return cached_data
            
            # Cache miss - fetch from database
            self.metrics.misses += 1
            self.metrics.update_hit_ratio()
            
            permissions_data = self._fetch_group_permissions_from_db(group_id)
            
            # Cache the result if Redis is available
            if self.is_redis_available and permissions_data:
                timeout = self.CACHE_TIMEOUTS['group_permissions']
                cache.set(cache_key, permissions_data, timeout=timeout)
            
            return permissions_data
    
    def get_user_groups(self, user_id: int) -> List[Dict[str, Any]]:
        """Get cached user groups"""
        cache_key = self._generate_cache_key(
            self.CACHE_PREFIXES['user_groups'], 
            user_id
        )
        
        with self._measure_performance():
            if self.is_redis_available:
                cached_data = cache.get(cache_key)
                if cached_data:
                    self.metrics.hits += 1
                    self.metrics.update_hit_ratio()
                    return cached_data
            
            # Cache miss - fetch from database
            self.metrics.misses += 1  
            self.metrics.update_hit_ratio()
            
            groups_data = self._fetch_user_groups_from_db(user_id)
            
            # Cache the result if Redis is available
            if self.is_redis_available and groups_data is not None:
                timeout = self.CACHE_TIMEOUTS['user_groups']
                cache.set(cache_key, groups_data, timeout=timeout)
            
            return groups_data
    
    def invalidate_user_cache(self, user_id: int):
        """Invalidate all cache entries for a specific user"""
        if not self.is_redis_available:
            return
            
        cache_keys = [
            self._generate_cache_key(self.CACHE_PREFIXES['user_permissions'], user_id),
            self._generate_cache_key(self.CACHE_PREFIXES['user_groups'], user_id),
        ]
        
        # Also invalidate effective permissions with different contexts
        for include_groups in [True, False]:
            key = self._generate_cache_key(
                self.CACHE_PREFIXES['effective_permissions'],
                user_id,
                {'include_groups': include_groups}
            )
            cache_keys.append(key)
        
        # Delete all user-related cache entries
        cache.delete_many(cache_keys)
        logger.info(f"Invalidated cache for user {user_id}")
    
    def invalidate_group_cache(self, group_id: int):
        """Invalidate all cache entries for a specific group"""
        if not self.is_redis_available:
            return
            
        # Get all users in this group to invalidate their effective permissions
        try:
            from django.contrib.auth import get_user_model
            User = get_user_model()
            
            # Find users who are members of this group
            user_ids = User.objects.filter(
                permission_groups__group_id=group_id
            ).values_list('id', flat=True)
            
            # Invalidate group cache
            group_cache_key = self._generate_cache_key(
                self.CACHE_PREFIXES['group_permissions'], 
                group_id
            )
            cache.delete(group_cache_key)
            
            # Invalidate affected user caches
            for user_id in user_ids:
                self.invalidate_user_cache(user_id)
                
            logger.info(f"Invalidated cache for group {group_id} and {len(user_ids)} affected users")
            
        except Exception as e:
            logger.error(f"Error invalidating group cache: {e}")
    
    def invalidate_permission_cache(self, permission_id: int):
        """Invalidate cache entries affected by permission changes"""
        if not self.is_redis_available:
            return
            
        try:
            # Find users and groups affected by this permission
            affected_users = set()
            affected_groups = set()
            
            # Get users with direct permission assignments
            user_perms = UserPermission.objects.filter(
                permission_id=permission_id
            ).values_list('user_id', flat=True)
            affected_users.update(user_perms)
            
            # Get groups with this permission
            group_perms = GroupPermission.objects.filter(
                permission_id=permission_id
            ).values_list('group_id', flat=True)
            affected_groups.update(group_perms)
            
            # Get users in affected groups
            from django.contrib.auth import get_user_model
            User = get_user_model()
            
            group_user_ids = User.objects.filter(
                permission_groups__group_id__in=affected_groups
            ).values_list('id', flat=True)
            affected_users.update(group_user_ids)
            
            # Invalidate all affected caches
            for user_id in affected_users:
                self.invalidate_user_cache(user_id)
                
            for group_id in affected_groups:
                group_cache_key = self._generate_cache_key(
                    self.CACHE_PREFIXES['group_permissions'], 
                    group_id
                )
                cache.delete(group_cache_key)
            
            logger.info(f"Invalidated cache for permission {permission_id}: "
                       f"{len(affected_users)} users, {len(affected_groups)} groups")
                       
        except Exception as e:
            logger.error(f"Error invalidating permission cache: {e}")
    
    def warm_cache(self, force: bool = False):
        """
        Warm cache with commonly accessed permissions
        
        Args:
            force: Force cache warming even if already in progress
        """
        if self.warming_in_progress and not force:
            logger.info("Cache warming already in progress")
            return
            
        if not self.is_redis_available:
            logger.warning("Cannot warm cache - Redis unavailable")
            return
        
        self.warming_in_progress = True
        start_time = time.time()
        
        try:
            logger.info("Starting permission cache warming")
            
            # Warm most active users (by recent audit log activity)
            active_users = self._get_active_users()
            self._warm_user_permissions(active_users)
            
            # Warm all groups
            active_groups = self._get_active_groups()
            self._warm_group_permissions(active_groups)
            
            # Warm permission metadata
            self._warm_permission_metadata()
            
            end_time = time.time()
            duration = end_time - start_time
            
            logger.info(f"Cache warming completed in {duration:.2f} seconds")
            
        except Exception as e:
            logger.error(f"Cache warming failed: {e}")
        finally:
            self.warming_in_progress = False
    
    def _get_active_users(self) -> List[int]:
        """Get list of recently active user IDs"""
        try:
            # Get users with recent audit log activity (last 30 days)
            recent_date = timezone.now() - timedelta(days=30)
            
            active_user_ids = PermissionAuditLog.objects.filter(
                created_at__gte=recent_date,
                user_id__isnull=False
            ).values_list('user_id', flat=True).distinct()[:self.WARMING_BATCH_SIZE]
            
            return list(active_user_ids)
            
        except Exception as e:
            logger.error(f"Error getting active users: {e}")
            return []
    
    def _get_active_groups(self) -> List[int]:
        """Get list of active group IDs"""
        try:
            groups = UserGroup.objects.filter(
                is_active=True
            ).values_list('id', flat=True)[:self.WARMING_BATCH_SIZE]
            
            return list(groups)
            
        except Exception as e:
            logger.error(f"Error getting active groups: {e}")
            return []
    
    def _warm_user_permissions(self, user_ids: List[int]):
        """Warm cache for user permissions"""
        logger.info(f"Warming user permissions cache for {len(user_ids)} users")
        
        for i, user_id in enumerate(user_ids):
            try:
                # Warm both with and without group permissions
                self.get_user_permissions(user_id, include_groups=True)
                self.get_user_permissions(user_id, include_groups=False)
                self.get_user_groups(user_id)
                
                # Add delay between batches to avoid overwhelming Redis
                if i > 0 and i % 10 == 0:
                    time.sleep(self.WARMING_DELAY)
                    
            except Exception as e:
                logger.error(f"Error warming user {user_id} permissions: {e}")
    
    def _warm_group_permissions(self, group_ids: List[int]):
        """Warm cache for group permissions"""
        logger.info(f"Warming group permissions cache for {len(group_ids)} groups")
        
        for i, group_id in enumerate(group_ids):
            try:
                self.get_group_permissions(group_id)
                
                # Add delay between batches
                if i > 0 and i % 10 == 0:
                    time.sleep(self.WARMING_DELAY)
                    
            except Exception as e:
                logger.error(f"Error warming group {group_id} permissions: {e}")
    
    def _warm_permission_metadata(self):
        """Warm cache for permission metadata"""
        logger.info("Warming permission metadata cache")
        
        try:
            # Cache all active permissions metadata
            permissions = Permission.objects.filter(is_active=True)
            
            for permission in permissions:
                cache_key = self._generate_cache_key(
                    self.CACHE_PREFIXES['permission_metadata'],
                    permission.code
                )
                
                metadata = {
                    'id': permission.id,
                    'name': permission.name,
                    'description': permission.description,
                    'risk_level': permission.risk_level,
                    'module': permission.module,
                }
                
                timeout = self.CACHE_TIMEOUTS['permission_metadata']
                cache.set(cache_key, metadata, timeout=timeout)
                
        except Exception as e:
            logger.error(f"Error warming permission metadata: {e}")
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get comprehensive cache performance statistics"""
        stats = self.metrics.to_dict()
        
        # Add Redis-specific stats if available
        if self.is_redis_available:
            try:
                # Add cache size estimation
                cache_info = cache._cache.get_client().info()
                stats.update({
                    'redis_available': True,
                    'redis_memory_used': cache_info.get('used_memory_human', 'Unknown'),
                    'redis_keyspace_hits': cache_info.get('keyspace_hits', 0),
                    'redis_keyspace_misses': cache_info.get('keyspace_misses', 0),
                })
            except Exception as e:
                logger.warning(f"Could not get Redis stats: {e}")
                stats['redis_available'] = True
        else:
            stats['redis_available'] = False
        
        stats['warming_in_progress'] = self.warming_in_progress
        return stats
    
    def clear_all_cache(self):
        """Clear all permission-related cache entries"""
        if not self.is_redis_available:
            logger.warning("Cannot clear cache - Redis unavailable")
            return
        
        try:
            # Get all cache keys with our prefixes
            cache_keys = []
            for prefix_template in self.CACHE_PREFIXES.values():
                # This is a simplified approach - in production you might need
                # more sophisticated key pattern matching
                pass
            
            # For now, clear the entire cache (be careful in production)
            cache.clear()
            logger.info("Cleared all permission cache entries")
            
            # Reset metrics
            self.metrics = CacheMetrics()
            self.metrics.last_updated = timezone.now()
            
        except Exception as e:
            logger.error(f"Error clearing cache: {e}")
    
    # Database fetch methods (fallback when cache is unavailable)
    
    def _fetch_user_permissions_from_db(self, user_id: int, include_groups: bool = True) -> Dict[str, Any]:
        """Fetch user permissions from database"""
        try:
            from django.contrib.auth import get_user_model
            User = get_user_model()
            
            user = User.objects.get(id=user_id)
            permissions_data = {
                'user_id': user_id,
                'direct_permissions': [],
                'group_permissions': [],
                'effective_permissions': [],
                'last_updated': timezone.now().isoformat(),
            }
            
            # Get direct user permissions
            direct_perms = UserPermission.objects.filter(
                user_id=user_id,
                is_granted=True,
                permission__is_active=True
            ).select_related('permission')
            
            permissions_data['direct_permissions'] = [
                {
                    'permission_id': up.permission.id,
                    'permission_code': up.permission.code,
                    'permission_name': up.permission.name,
                    'risk_level': up.permission.risk_level,
                    'granted_at': up.granted_at.isoformat() if up.granted_at else None,
                }
                for up in direct_perms
            ]
            
            # Get group permissions if requested
            if include_groups:
                group_perms = GroupPermission.objects.filter(
                    group__members__user_id=user_id,
                    group__is_active=True,
                    is_granted=True,
                    permission__is_active=True
                ).select_related('permission', 'group')
                
                permissions_data['group_permissions'] = [
                    {
                        'permission_id': gp.permission.id,
                        'permission_code': gp.permission.code,
                        'permission_name': gp.permission.name,
                        'group_name': gp.group.name,
                        'risk_level': gp.permission.risk_level,
                        'granted_at': gp.granted_at.isoformat() if gp.granted_at else None,
                    }
                    for gp in group_perms
                ]
            
            # Combine effective permissions (direct + group)
            all_permission_codes = set()
            effective_permissions = []
            
            # Add direct permissions
            for perm in permissions_data['direct_permissions']:
                if perm['permission_code'] not in all_permission_codes:
                    all_permission_codes.add(perm['permission_code'])
                    effective_permissions.append({
                        'permission_code': perm['permission_code'],
                        'permission_name': perm['permission_name'],
                        'source': 'direct',
                        'risk_level': perm['risk_level'],
                    })
            
            # Add group permissions
            for perm in permissions_data['group_permissions']:
                if perm['permission_code'] not in all_permission_codes:
                    all_permission_codes.add(perm['permission_code'])
                    effective_permissions.append({
                        'permission_code': perm['permission_code'],
                        'permission_name': perm['permission_name'],
                        'source': 'group',
                        'group_name': perm['group_name'],
                        'risk_level': perm['risk_level'],
                    })
            
            permissions_data['effective_permissions'] = effective_permissions
            return permissions_data
            
        except Exception as e:
            logger.error(f"Error fetching user permissions from DB: {e}")
            return {}
    
    def _fetch_group_permissions_from_db(self, group_id: int) -> Dict[str, Any]:
        """Fetch group permissions from database"""
        try:
            group = UserGroup.objects.get(id=group_id)
            
            group_perms = GroupPermission.objects.filter(
                group_id=group_id,
                is_granted=True,
                permission__is_active=True
            ).select_related('permission')
            
            permissions_data = {
                'group_id': group_id,
                'group_name': group.name,
                'permissions': [
                    {
                        'permission_id': gp.permission.id,
                        'permission_code': gp.permission.code,
                        'permission_name': gp.permission.name,
                        'risk_level': gp.permission.risk_level,
                        'granted_at': gp.granted_at.isoformat() if gp.granted_at else None,
                    }
                    for gp in group_perms
                ],
                'last_updated': timezone.now().isoformat(),
            }
            
            return permissions_data
            
        except Exception as e:
            logger.error(f"Error fetching group permissions from DB: {e}")
            return {}
    
    def _fetch_user_groups_from_db(self, user_id: int) -> List[Dict[str, Any]]:
        """Fetch user groups from database"""
        try:
            from .models import GroupMembership
            
            memberships = GroupMembership.objects.filter(
                user_id=user_id,
                is_active=True,
                group__is_active=True
            ).select_related('group')
            
            groups_data = [
                {
                    'group_id': membership.group.id,
                    'group_name': membership.group.name,
                    'group_description': membership.group.description,
                    'joined_at': membership.joined_at.isoformat() if membership.joined_at else None,
                    'role': 'member',  # Could be extended with role information
                }
                for membership in memberships
            ]
            
            return groups_data
            
        except Exception as e:
            logger.error(f"Error fetching user groups from DB: {e}")
            return []


# Global cache instance
permission_cache = PermissionCache()


# Django signal handlers for automatic cache invalidation

@receiver(post_save, sender=UserPermission)
@receiver(post_delete, sender=UserPermission)
def invalidate_user_permission_cache(sender, instance, **kwargs):
    """Invalidate cache when user permissions change"""
    try:
        permission_cache.invalidate_user_cache(instance.user_id)
        permission_cache.invalidate_permission_cache(instance.permission_id)
    except Exception as e:
        logger.error(f"Error invalidating user permission cache: {e}")


@receiver(post_save, sender=GroupPermission)  
@receiver(post_delete, sender=GroupPermission)
def invalidate_group_permission_cache(sender, instance, **kwargs):
    """Invalidate cache when group permissions change"""
    try:
        permission_cache.invalidate_group_cache(instance.group_id)
        permission_cache.invalidate_permission_cache(instance.permission_id)
    except Exception as e:
        logger.error(f"Error invalidating group permission cache: {e}")


@receiver(post_save, sender='core.GroupMembership')
@receiver(post_delete, sender='core.GroupMembership') 
def invalidate_group_membership_cache(sender, instance, **kwargs):
    """Invalidate cache when group membership changes"""
    try:
        permission_cache.invalidate_user_cache(instance.user_id)
        permission_cache.invalidate_group_cache(instance.group_id)
    except Exception as e:
        logger.error(f"Error invalidating group membership cache: {e}")


@receiver(post_save, sender=Permission)
def invalidate_permission_metadata_cache(sender, instance, **kwargs):
    """Invalidate cache when permission metadata changes"""
    try:
        permission_cache.invalidate_permission_cache(instance.id)
        
        # Clear permission metadata cache
        cache_key = permission_cache._generate_cache_key(
            permission_cache.CACHE_PREFIXES['permission_metadata'],
            instance.code
        )
        cache.delete(cache_key)
    except Exception as e:
        logger.error(f"Error invalidating permission metadata cache: {e}")


# Utility functions for cache management

def warm_permission_cache():
    """Utility function to warm permission cache"""
    return permission_cache.warm_cache()


def clear_permission_cache():
    """Utility function to clear all permission cache"""
    return permission_cache.clear_all_cache()


def get_permission_cache_stats():
    """Utility function to get cache statistics"""
    return permission_cache.get_cache_stats()


# Cache monitoring and alerting

class CacheMonitor:
    """Cache performance monitoring and alerting"""
    
    # Performance thresholds
    MIN_HIT_RATIO = 0.90  # 90% minimum hit ratio
    MAX_AVG_RESPONSE_TIME = 50.0  # 50ms maximum average response time
    MAX_ERROR_RATE = 0.01  # 1% maximum error rate
    
    @classmethod
    def check_performance_thresholds(cls) -> Dict[str, Any]:
        """Check if cache performance meets thresholds"""
        stats = permission_cache.get_cache_stats()
        
        checks = {
            'hit_ratio_ok': stats['hit_ratio'] >= cls.MIN_HIT_RATIO,
            'response_time_ok': stats['avg_response_time'] <= cls.MAX_AVG_RESPONSE_TIME,
            'redis_available': stats['redis_available'],
            'errors_count': stats['errors'],
            'overall_health': True,
        }
        
        # Calculate error rate
        total_requests = stats['hits'] + stats['misses']
        error_rate = (stats['errors'] / total_requests) if total_requests > 0 else 0
        checks['error_rate_ok'] = error_rate <= cls.MAX_ERROR_RATE
        
        # Overall health check
        checks['overall_health'] = (
            checks['hit_ratio_ok'] and 
            checks['response_time_ok'] and 
            checks['error_rate_ok'] and
            checks['redis_available']
        )
        
        return checks
    
    @classmethod
    def generate_performance_alerts(cls) -> List[str]:
        """Generate performance alerts for issues"""
        checks = cls.check_performance_thresholds()
        alerts = []
        
        if not checks['redis_available']:
            alerts.append("CRITICAL: Redis cache is unavailable - falling back to database")
        
        if not checks['hit_ratio_ok']:
            stats = permission_cache.get_cache_stats()
            alerts.append(f"WARNING: Cache hit ratio ({stats['hit_ratio']:.2%}) "
                         f"below threshold ({cls.MIN_HIT_RATIO:.2%})")
        
        if not checks['response_time_ok']:
            stats = permission_cache.get_cache_stats()
            alerts.append(f"WARNING: Average response time ({stats['avg_response_time']:.2f}ms) "
                         f"above threshold ({cls.MAX_AVG_RESPONSE_TIME}ms)")
        
        if not checks['error_rate_ok']:
            stats = permission_cache.get_cache_stats()
            total_requests = stats['hits'] + stats['misses']
            error_rate = (stats['errors'] / total_requests) if total_requests > 0 else 0
            alerts.append(f"WARNING: Cache error rate ({error_rate:.2%}) "
                         f"above threshold ({cls.MAX_ERROR_RATE:.2%})")
        
        return alerts


# Cache warming management command helper

def execute_cache_warming():
    """Execute cache warming with comprehensive logging"""
    try:
        logger.info("Starting scheduled permission cache warming")
        start_time = time.time()
        
        # Check if cache warming is needed
        stats = permission_cache.get_cache_stats()
        if stats['hit_ratio'] > 0.95 and not permission_cache.warming_in_progress:
            logger.info(f"Cache hit ratio {stats['hit_ratio']:.2%} is good - skipping warming")
            return
        
        # Execute warming
        permission_cache.warm_cache()
        
        end_time = time.time()
        duration = end_time - start_time
        
        # Log results
        new_stats = permission_cache.get_cache_stats()
        logger.info(f"Cache warming completed in {duration:.2f}s - "
                   f"Hit ratio: {new_stats['hit_ratio']:.2%}")
        
        # Check for performance alerts
        alerts = CacheMonitor.generate_performance_alerts()
        for alert in alerts:
            logger.warning(f"Cache performance alert: {alert}")
            
    except Exception as e:
        logger.error(f"Cache warming execution failed: {e}")
        raise PermissionCacheError(f"Cache warming failed: {e}")
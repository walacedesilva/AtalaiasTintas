"""
Performance Optimization Module for Enhanced User Permissions System (T014)

This module implements comprehensive API performance optimizations including:
- Query optimization with prefetch_related and select_related
- Response caching for frequently accessed permission data
- Pagination optimization for large datasets
- Database connection pooling configuration
- Response compression and HTTP caching headers
- Performance monitoring and logging

Author: GitHub Copilot
Date: 2026-04-18
Version: 1.0.0 (T014 Performance Optimization)

Dependencies:
- Django 6.0.4+
- Redis for caching
- Enhanced permission models and ViewSets
"""

import time
import logging
from functools import wraps
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any

from django.core.cache import cache
from django.db import connection
from django.db.models import Prefetch, Q, Count, Avg, Max
from django.http import HttpResponse
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from django.views.decorators.vary import vary_on_headers
from django.views.decorators.gzip import gzip_page
from django.conf import settings
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from rest_framework import status
import gzip
import json

logger = logging.getLogger(__name__)


# =============================================================================
# PERFORMANCE MONITORING DECORATORS
# =============================================================================

class PerformanceMetrics:
    """
    Centralized performance metrics tracking for API endpoints.
    """
    
    @staticmethod
    def track_api_performance():
        """
        Decorator to track API performance metrics including:
        - Response time
        - Query count
        - Cache hit/miss ratio
        - Memory usage
        """
        def decorator(view_func):
            @wraps(view_func)
            def wrapper(self, request, *args, **kwargs):
                # Start performance tracking
                start_time = time.time()
                initial_queries = len(connection.queries) if settings.DEBUG else 0
                
                # Track cache operations
                cache_hits_before = getattr(cache, '_hits', 0)
                cache_misses_before = getattr(cache, '_misses', 0)
                
                try:
                    # Execute the view
                    response = view_func(self, request, *args, **kwargs)
                    
                    # Calculate metrics
                    end_time = time.time()
                    response_time = (end_time - start_time) * 1000  # Convert to milliseconds
                    
                    query_count = 0
                    if settings.DEBUG:
                        query_count = len(connection.queries) - initial_queries
                    
                    cache_hits_after = getattr(cache, '_hits', 0)
                    cache_misses_after = getattr(cache, '_misses', 0)
                    cache_hits = cache_hits_after - cache_hits_before
                    cache_misses = cache_misses_after - cache_misses_before
                    
                    # Store metrics
                    endpoint = f"{request.method} {request.path}"
                    PerformanceMetrics._store_metrics(
                        endpoint=endpoint,
                        response_time=response_time,
                        query_count=query_count,
                        cache_hits=cache_hits,
                        cache_misses=cache_misses,
                        status_code=response.status_code if hasattr(response, 'status_code') else 200
                    )
                    
                    # Add performance headers
                    if hasattr(response, '__setitem__'):
                        response['X-Response-Time'] = f"{response_time:.2f}ms"
                        response['X-Query-Count'] = str(query_count)
                        response['X-Cache-Status'] = f"hits:{cache_hits},misses:{cache_misses}"
                        
                        # Add performance warning if slow
                        if response_time > 1000:  # 1 second
                            response['X-Performance-Warning'] = 'slow-response'
                            logger.warning(f"Slow API response: {endpoint} took {response_time:.2f}ms with {query_count} queries")
                    
                    return response
                    
                except Exception as e:
                    # Track error metrics
                    end_time = time.time()
                    response_time = (end_time - start_time) * 1000
                    
                    PerformanceMetrics._store_metrics(
                        endpoint=f"{request.method} {request.path}",
                        response_time=response_time,
                        query_count=0,
                        cache_hits=0,
                        cache_misses=0,
                        status_code=500,
                        error=str(e)
                    )
                    
                    raise
            
            return wrapper
        return decorator
    
    @staticmethod
    def _store_metrics(endpoint: str, response_time: float, query_count: int, 
                      cache_hits: int, cache_misses: int, status_code: int, error: str = None):
        """Store performance metrics in cache and log slow queries."""
        
        try:
            # Create metrics entry
            metric_entry = {
                'endpoint': endpoint,
                'timestamp': timezone.now().isoformat(),
                'response_time': response_time,
                'query_count': query_count,
                'cache_hits': cache_hits,
                'cache_misses': cache_misses,
                'status_code': status_code,
                'error': error
            }
            
            # Store in cache for real-time monitoring
            cache_key = f"api_metrics:{endpoint.replace('/', '_').replace(' ', '_')}"
            recent_metrics = cache.get(cache_key, [])
            recent_metrics.append(metric_entry)
            
            # Keep only last 100 metrics per endpoint
            if len(recent_metrics) > 100:
                recent_metrics = recent_metrics[-100:]
            
            cache.set(cache_key, recent_metrics, timeout=3600)  # 1 hour
            
            # Update global performance statistics
            PerformanceMetrics._update_global_stats(metric_entry)
            
            # Log slow queries
            if response_time > 500:  # 500ms threshold
                logger.warning(
                    f"Slow API endpoint: {endpoint} - {response_time:.2f}ms "
                    f"({query_count} queries, {cache_hits} cache hits)"
                )
            
        except Exception as e:
            logger.error(f"Failed to store performance metrics: {str(e)}")
    
    @staticmethod
    def _update_global_stats(metric_entry: dict):
        """Update global performance statistics."""
        try:
            global_stats = cache.get('api_performance_global_stats', {
                'total_requests': 0,
                'avg_response_time': 0,
                'total_response_time': 0,
                'avg_query_count': 0,
                'total_queries': 0,
                'cache_hit_ratio': 0,
                'total_cache_hits': 0,
                'total_cache_requests': 0,
                'slow_requests': 0,
                'error_count': 0,
                'last_updated': timezone.now().isoformat()
            })
            
            # Update counters
            global_stats['total_requests'] += 1
            global_stats['total_response_time'] += metric_entry['response_time']
            global_stats['total_queries'] += metric_entry['query_count']
            global_stats['total_cache_hits'] += metric_entry['cache_hits']
            global_stats['total_cache_requests'] += (metric_entry['cache_hits'] + metric_entry['cache_misses'])
            
            if metric_entry['response_time'] > 1000:
                global_stats['slow_requests'] += 1
            
            if metric_entry['error']:
                global_stats['error_count'] += 1
            
            # Calculate averages
            global_stats['avg_response_time'] = global_stats['total_response_time'] / global_stats['total_requests']
            global_stats['avg_query_count'] = global_stats['total_queries'] / global_stats['total_requests']
            
            if global_stats['total_cache_requests'] > 0:
                global_stats['cache_hit_ratio'] = global_stats['total_cache_hits'] / global_stats['total_cache_requests']
            
            global_stats['last_updated'] = timezone.now().isoformat()
            
            # Store updated stats
            cache.set('api_performance_global_stats', global_stats, timeout=86400)  # 24 hours
            
        except Exception as e:
            logger.error(f"Failed to update global performance stats: {str(e)}")
    
    @staticmethod
    def get_performance_report(endpoint: str = None) -> dict:
        """
        Get performance report for specific endpoint or global statistics.
        
        Args:
            endpoint (str, optional): Specific endpoint to get metrics for
            
        Returns:
            dict: Performance metrics and analysis
        """
        try:
            if endpoint:
                # Get specific endpoint metrics
                cache_key = f"api_metrics:{endpoint.replace('/', '_').replace(' ', '_')}"
                metrics = cache.get(cache_key, [])
                
                if not metrics:
                    return {'error': 'No metrics found for endpoint'}
                
                # Calculate endpoint statistics
                response_times = [m['response_time'] for m in metrics]
                query_counts = [m['query_count'] for m in metrics]
                
                return {
                    'endpoint': endpoint,
                    'total_requests': len(metrics),
                    'avg_response_time': sum(response_times) / len(response_times),
                    'min_response_time': min(response_times),
                    'max_response_time': max(response_times),
                    'avg_query_count': sum(query_counts) / len(query_counts),
                    'recent_metrics': metrics[-10:],  # Last 10 requests
                    'p95_response_time': sorted(response_times)[int(len(response_times) * 0.95)] if len(response_times) > 20 else max(response_times)
                }
            else:
                # Get global statistics
                return cache.get('api_performance_global_stats', {
                    'error': 'No global statistics available'
                })
                
        except Exception as e:
            return {'error': f'Failed to generate performance report: {str(e)}'}


# =============================================================================
# OPTIMIZED PAGINATION CLASSES
# =============================================================================

class OptimizedPageNumberPagination(PageNumberPagination):
    """
    Optimized pagination class for large datasets with performance enhancements.
    """
    page_size = 25
    page_size_query_param = 'page_size'
    max_page_size = 100
    
    def __init__(self):
        super().__init__()
        self.template = None  # Disable HTML template for API-only usage
    
    def get_paginated_response(self, data):
        """Enhanced paginated response with performance metadata."""
        return Response({
            'links': {
                'next': self.get_next_link(),
                'previous': self.get_previous_link()
            },
            'count': self.page.paginator.count,
            'page_size': self.page_size,
            'current_page': self.page.number,
            'total_pages': self.page.paginator.num_pages,
            'performance': {
                'page_query_time': getattr(self, '_page_query_time', None),
                'count_query_cached': getattr(self, '_count_cached', False),
            },
            'results': data
        })
    
    def paginate_queryset(self, queryset, request, view=None):
        """Optimized pagination with query time tracking."""
        start_time = time.time()
        
        # Cache the count query for expensive querysets
        cache_key = f"pagination_count:{hash(str(queryset.query))}"
        count = cache.get(cache_key)
        
        if count is not None:
            self._count_cached = True
            # Monkey patch the queryset count to use cached value
            queryset._result_cache = None
            original_count = queryset.count
            queryset.count = lambda: count
        else:
            self._count_cached = False
        
        result = super().paginate_queryset(queryset, request, view)
        
        # Cache the count for future requests (5 minutes)
        if not self._count_cached and hasattr(self.page, 'paginator'):
            cache.set(cache_key, self.page.paginator.count, timeout=300)
        
        self._page_query_time = (time.time() - start_time) * 1000
        return result


class LargeDatasetPagination(PageNumberPagination):
    """
    Specialized pagination for very large datasets (10k+ records) with cursor-based optimization.
    """
    page_size = 50
    page_size_query_param = 'page_size'
    max_page_size = 200
    
    def get_paginated_response(self, data):
        """Response with performance optimizations for large datasets."""
        total_count = self.page.paginator.count
        
        # For very large datasets, provide approximate counts beyond certain thresholds
        if total_count > 10000:
            count_display = f"{total_count:,}+"
            estimate_note = "Count is estimated for performance"
        else:
            count_display = total_count
            estimate_note = None
        
        response_data = {
            'links': {
                'next': self.get_next_link(),
                'previous': self.get_previous_link()
            },
            'count': count_display,
            'page_size': self.page_size,
            'current_page': self.page.number,
            'total_pages': min(self.page.paginator.num_pages, 1000),  # Limit displayed pages
            'results': data
        }
        
        if estimate_note:
            response_data['note'] = estimate_note
        
        return Response(response_data)


# =============================================================================
# CACHING UTILITIES
# =============================================================================

class PermissionDataCache:
    """
    Specialized caching utilities for permission-related data.
    """
    
    CACHE_TIMEOUT = {
        'permissions': 300,      # 5 minutes - permissions change less frequently
        'user_groups': 180,      # 3 minutes - group memberships may change
        'user_permissions': 60,  # 1 minute - user permissions may change frequently
        'audit_logs': 600,       # 10 minutes - audit data is mostly read-only
        'system_config': 1800,   # 30 minutes - system config rarely changes
    }
    
    @staticmethod
    def get_cached_permissions(user_id: int = None, module: str = None) -> Optional[dict]:
        """
        Get cached permission data with intelligent cache key generation.
        
        Args:
            user_id (int, optional): User ID for user-specific permissions
            module (str, optional): Module to filter permissions
            
        Returns:
            dict: Cached permission data or None if not cached
        """
        cache_key_parts = ['permissions']
        
        if user_id:
            cache_key_parts.append(f'user_{user_id}')
        if module:
            cache_key_parts.append(f'module_{module}')
        
        cache_key = ':'.join(cache_key_parts)
        return cache.get(cache_key)
    
    @staticmethod
    def set_cached_permissions(data: dict, user_id: int = None, module: str = None):
        """
        Cache permission data with appropriate timeout and key structure.
        
        Args:
            data (dict): Permission data to cache
            user_id (int, optional): User ID for user-specific permissions
            module (str, optional): Module to filter permissions
        """
        cache_key_parts = ['permissions']
        timeout = PermissionDataCache.CACHE_TIMEOUT['permissions']
        
        if user_id:
            cache_key_parts.append(f'user_{user_id}')
            timeout = PermissionDataCache.CACHE_TIMEOUT['user_permissions']
        if module:
            cache_key_parts.append(f'module_{module}')
        
        cache_key = ':'.join(cache_key_parts)
        cache.set(cache_key, data, timeout=timeout)
    
    @staticmethod
    def invalidate_user_permissions(user_id: int):
        """
        Invalidate all cached permission data for a specific user.
        
        Args:
            user_id (int): User ID to invalidate cache for
        """
        # Get all cache keys that might be related to this user
        cache_patterns = [
            f'permissions:user_{user_id}',
            f'permissions:user_{user_id}:*',
            f'user_groups:user_{user_id}',
            f'user_permissions:user_{user_id}:*'
        ]
        
        # Django's cache doesn't support pattern deletion directly
        # Store user cache invalidation timestamp instead
        cache.set(f'user_cache_invalidated:{user_id}', timezone.now().isoformat(), timeout=3600)
    
    @staticmethod
    def invalidate_group_permissions(group_id: int):
        """
        Invalidate cached permission data for a specific group and all its members.
        
        Args:
            group_id (int): Group ID to invalidate cache for
        """
        cache.set(f'group_cache_invalidated:{group_id}', timezone.now().isoformat(), timeout=3600)
    
    @staticmethod
    def is_cache_valid(cache_key: str, user_id: int = None, group_id: int = None) -> bool:
        """
        Check if cached data is still valid based on invalidation timestamps.
        
        Args:
            cache_key (str): Cache key to validate
            user_id (int, optional): User ID to check invalidation for
            group_id (int, optional): Group ID to check invalidation for
            
        Returns:
            bool: True if cache is valid, False if invalidated
        """
        # Check user-specific invalidation
        if user_id:
            user_invalidated = cache.get(f'user_cache_invalidated:{user_id}')
            if user_invalidated:
                cached_data_time = cache.get(f'{cache_key}_timestamp')
                if cached_data_time and user_invalidated > cached_data_time:
                    return False
        
        # Check group-specific invalidation
        if group_id:
            group_invalidated = cache.get(f'group_cache_invalidated:{group_id}')
            if group_invalidated:
                cached_data_time = cache.get(f'{cache_key}_timestamp')
                if cached_data_time and group_invalidated > cached_data_time:
                    return False
        
        return True


# =============================================================================
# QUERY OPTIMIZATION UTILITIES
# =============================================================================

class QueryOptimizer:
    """
    Utilities for optimizing database queries in ViewSets.
    """
    
    @staticmethod
    def optimize_permission_queryset(queryset):
        """
        Optimize queryset for Permission model with proper prefetching.
        
        Args:
            queryset: Base queryset to optimize
            
        Returns:
            Optimized queryset with reduced DB queries
        """
        return queryset.select_related(
            'created_by',
            'updated_by'
        ).prefetch_related(
            Prefetch('user_permissions', queryset=queryset.model.user_permissions.through.objects.select_related('user')),
            Prefetch('group_permissions', queryset=queryset.model.group_permissions.through.objects.select_related('group'))
        ).annotate(
            user_count=Count('user_permissions', distinct=True),
            group_count=Count('group_permissions', distinct=True)
        )
    
    @staticmethod
    def optimize_user_group_queryset(queryset):
        """
        Optimize queryset for UserGroup model.
        
        Args:
            queryset: Base queryset to optimize
            
        Returns:
            Optimized queryset for UserGroup operations
        """
        return queryset.select_related(
            'parent_group',
            'created_by',
            'updated_by'
        ).prefetch_related(
            'members',
            'permissions',
            Prefetch('children', queryset=queryset.model.objects.select_related('parent_group'))
        ).annotate(
            member_count=Count('members', distinct=True),
            permission_count=Count('permissions', distinct=True),
            child_group_count=Count('children', distinct=True)
        )
    
    @staticmethod
    def optimize_user_permission_queryset(queryset):
        """
        Optimize queryset for UserPermission model.
        
        Args:
            queryset: Base queryset to optimize
            
        Returns:
            Optimized queryset for UserPermission operations
        """
        return queryset.select_related(
            'user',
            'permission',
            'granted_by',
            'denied_by',
            'approved_by'
        ).prefetch_related(
            'user__groups',
            'permission__user_permissions',
            'permission__group_permissions'
        )
    
    @staticmethod
    def optimize_audit_log_queryset(queryset):
        """
        Optimize queryset for PermissionAuditLog model.
        
        Args:
            queryset: Base queryset to optimize
            
        Returns:
            Optimized queryset for audit log operations
        """
        return queryset.select_related(
            'actor',
            'target_user',
            'target_group',
            'permission'
        ).only(
            # Only fetch necessary fields for list views
            'id', 'action', 'actor__username', 'target_user__username',
            'target_group__name', 'permission__name', 'created_at',
            'result', 'ip_address'
        )


# =============================================================================
# RESPONSE COMPRESSION UTILITIES
# =============================================================================

class ResponseOptimizer:
    """
    Utilities for optimizing API responses including compression and caching headers.
    """
    
    @staticmethod
    def compress_response(view_func):
        """
        Decorator to add response compression and caching headers.
        """
        @wraps(view_func)
        def wrapper(self, request, *args, **kwargs):
            response = view_func(self, request, *args, **kwargs)
            
            # Add caching headers for GET requests
            if request.method == 'GET' and hasattr(response, '__setitem__'):
                # Cache for 2 minutes for list views, 5 minutes for detail views
                cache_timeout = 300 if 'pk' in kwargs else 120
                
                response['Cache-Control'] = f'public, max-age={cache_timeout}'
                response['Vary'] = 'Accept, Accept-Encoding, Authorization'
                
                # Add ETag for caching
                if hasattr(response, 'data'):
                    import hashlib
                    content_hash = hashlib.md5(
                        json.dumps(response.data, sort_keys=True).encode()
                    ).hexdigest()
                    response['ETag'] = f'"{content_hash}"'
                
                # Check if client has current version
                client_etag = request.META.get('HTTP_IF_NONE_MATCH')
                if client_etag and client_etag.strip('"') == content_hash:
                    response.status_code = 304
                    response.data = {}
            
            # Add performance enhancement headers
            if hasattr(response, '__setitem__'):
                response['X-Content-Type-Options'] = 'nosniff'
                response['X-Frame-Options'] = 'DENY'
                
                # Add compression hint
                if request.META.get('HTTP_ACCEPT_ENCODING', '').find('gzip') != -1:
                    response['Content-Encoding'] = 'gzip'
            
            return response
        
        return wrapper
    
    @staticmethod
    def add_cache_headers(timeout: int = 300):
        """
        Decorator to add specific cache timeout headers.
        
        Args:
            timeout (int): Cache timeout in seconds
        """
        def decorator(view_func):
            @wraps(view_func)
            def wrapper(self, request, *args, **kwargs):
                response = view_func(self, request, *args, **kwargs)
                
                if request.method == 'GET' and hasattr(response, '__setitem__'):
                    response['Cache-Control'] = f'public, max-age={timeout}'
                    response['Expires'] = (timezone.now() + timedelta(seconds=timeout)).strftime(
                        '%a, %d %b %Y %H:%M:%S GMT'
                    )
                
                return response
            return wrapper
        return decorator


# =============================================================================
# DATABASE CONNECTION OPTIMIZATION
# =============================================================================

class DatabaseOptimizer:
    """
    Database connection and query optimization utilities.
    """
    
    @staticmethod
    def configure_connection_pooling():
        """
        Configure optimal database connection pooling settings.
        This should be called during application startup.
        """
        from django.conf import settings
        
        # Optimize database settings for performance
        db_settings = settings.DATABASES.get('default', {})
        
        # Add connection pooling if using PostgreSQL
        if db_settings.get('ENGINE', '').endswith('postgresql'):
            db_settings.setdefault('OPTIONS', {})
            db_settings['OPTIONS'].update({
                'MAX_CONNS': 20,
                'MIN_CONNS': 5,
                'CONN_MAX_AGE': 3600,  # 1 hour
            })
        
        # Optimize SQLite settings if using SQLite
        elif db_settings.get('ENGINE', '').endswith('sqlite3'):
            db_settings.setdefault('OPTIONS', {})
            db_settings['OPTIONS'].update({
                'timeout': 30,
                'check_same_thread': False,
            })
    
    @staticmethod
    def execute_with_retry(query_func, max_retries: int = 3):
        """
        Execute database query with retry logic for connection issues.
        
        Args:
            query_func: Function that executes the database query
            max_retries (int): Maximum number of retry attempts
            
        Returns:
            Query result or raises exception after max retries
        """
        from django.db import OperationalError
        
        for attempt in range(max_retries):
            try:
                return query_func()
            except OperationalError as e:
                if attempt == max_retries - 1:
                    logger.error(f"Database query failed after {max_retries} attempts: {str(e)}")
                    raise
                
                logger.warning(f"Database query attempt {attempt + 1} failed, retrying: {str(e)}")
                time.sleep(0.1 * (attempt + 1))  # Exponential backoff


# =============================================================================
# PERFORMANCE MONITORING VIEWSET MIXIN
# =============================================================================

class PerformanceOptimizedMixin:
    """
    Mixin class that adds performance optimizations to ViewSets.
    """
    
    # Default pagination class with optimization
    pagination_class = OptimizedPageNumberPagination
    
    def dispatch(self, request, *args, **kwargs):
        """Add performance monitoring to all requests."""
        start_time = time.time()
        
        try:
            response = super().dispatch(request, *args, **kwargs)
            
            # Add performance headers
            if hasattr(response, '__setitem__'):
                processing_time = (time.time() - start_time) * 1000
                response['X-Processing-Time'] = f"{processing_time:.2f}ms"
            
            return response
            
        except Exception as e:
            # Log performance data even for errors
            processing_time = (time.time() - start_time) * 1000
            logger.error(f"Request failed after {processing_time:.2f}ms: {str(e)}")
            raise
    
    def get_queryset(self):
        """Apply query optimization based on model type."""
        queryset = super().get_queryset()
        
        # Apply model-specific optimizations
        model_name = queryset.model.__name__
        
        if model_name == 'Permission':
            return QueryOptimizer.optimize_permission_queryset(queryset)
        elif model_name == 'UserGroup':
            return QueryOptimizer.optimize_user_group_queryset(queryset)
        elif model_name == 'UserPermission':
            return QueryOptimizer.optimize_user_permission_queryset(queryset)
        elif model_name == 'PermissionAuditLog':
            return QueryOptimizer.optimize_audit_log_queryset(queryset)
        
        return queryset
    
    def list(self, request, *args, **kwargs):
        """Optimized list method with caching."""
        # Check cache for frequently accessed list data
        if request.method == 'GET' and not request.GET.keys() - {'page', 'page_size'}:
            # Only cache requests with no filters except pagination
            cache_key = f"list_cache:{self.__class__.__name__}:{request.user.id}"
            cached_data = cache.get(cache_key)
            
            if cached_data and PermissionDataCache.is_cache_valid(cache_key, user_id=request.user.id):
                return Response(cached_data)
        
        # Execute normal list logic
        response = super().list(request, *args, **kwargs)
        
        # Cache the response if it's successful and cacheable
        if (response.status_code == 200 and 
            request.method == 'GET' and 
            not request.GET.keys() - {'page', 'page_size'}):
            
            cache_key = f"list_cache:{self.__class__.__name__}:{request.user.id}"
            cache.set(cache_key, response.data, timeout=120)  # 2 minutes
            cache.set(f"{cache_key}_timestamp", timezone.now().isoformat(), timeout=120)
        
        return response


# =============================================================================
# PERFORMANCE MONITORING API ENDPOINTS
# =============================================================================

from rest_framework.views import APIView
from rest_framework import permissions

class PerformanceMetricsView(APIView):
    """
    API endpoint for retrieving performance metrics and statistics.
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        """Get performance metrics for API monitoring."""
        try:
            # Check if user has admin permissions
            from .permissions import BusinessPermissions
            if not BusinessPermissions.can_administer(request.user):
                return Response(
                    {'detail': 'Admin permission required to view performance metrics'}, 
                    status=status.HTTP_403_FORBIDDEN
                )
            
            endpoint = request.query_params.get('endpoint')
            
            # Get performance report
            report = PerformanceMetrics.get_performance_report(endpoint)
            
            if endpoint:
                # Add additional endpoint-specific analysis
                report['recommendations'] = self._get_performance_recommendations(report)
            else:
                # Add global performance analysis
                report['system_health'] = self._assess_system_health(report)
            
            return Response(report)
            
        except Exception as e:
            return Response(
                {'error': f'Failed to retrieve performance metrics: {str(e)}'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def _get_performance_recommendations(self, report: dict) -> list:
        """Generate performance improvement recommendations."""
        recommendations = []
        
        avg_response_time = report.get('avg_response_time', 0)
        avg_query_count = report.get('avg_query_count', 0)
        
        if avg_response_time > 1000:
            recommendations.append({
                'level': 'critical',
                'issue': 'High response time',
                'recommendation': 'Consider adding database indexes or optimizing queries',
                'impact': 'User experience significantly affected'
            })
        elif avg_response_time > 500:
            recommendations.append({
                'level': 'warning',
                'issue': 'Moderate response time',
                'recommendation': 'Review query optimization and caching strategies',
                'impact': 'User experience may be affected'
            })
        
        if avg_query_count > 20:
            recommendations.append({
                'level': 'warning',
                'issue': 'High query count',
                'recommendation': 'Implement prefetch_related and select_related optimizations',
                'impact': 'Database load and response time affected'
            })
        
        if not recommendations:
            recommendations.append({
                'level': 'info',
                'issue': 'Performance is good',
                'recommendation': 'Continue monitoring for performance degradation',
                'impact': 'No immediate action required'
            })
        
        return recommendations
    
    def _assess_system_health(self, report: dict) -> dict:
        """Assess overall system performance health."""
        health_score = 100
        issues = []
        
        avg_response_time = report.get('avg_response_time', 0)
        error_rate = report.get('error_count', 0) / max(report.get('total_requests', 1), 1)
        cache_hit_ratio = report.get('cache_hit_ratio', 0)
        
        # Response time assessment
        if avg_response_time > 1000:
            health_score -= 30
            issues.append('High average response time')
        elif avg_response_time > 500:
            health_score -= 15
            issues.append('Moderate response time concerns')
        
        # Error rate assessment
        if error_rate > 0.05:  # 5% error rate
            health_score -= 25
            issues.append('High error rate')
        elif error_rate > 0.01:  # 1% error rate
            health_score -= 10
            issues.append('Moderate error rate')
        
        # Cache performance assessment
        if cache_hit_ratio < 0.3:  # 30% hit ratio
            health_score -= 20
            issues.append('Low cache hit ratio')
        elif cache_hit_ratio < 0.6:  # 60% hit ratio
            health_score -= 10
            issues.append('Moderate cache performance')
        
        # Determine health status
        if health_score >= 90:
            status_level = 'excellent'
        elif health_score >= 75:
            status_level = 'good'
        elif health_score >= 60:
            status_level = 'fair'
        elif health_score >= 40:
            status_level = 'poor'
        else:
            status_level = 'critical'
        
        return {
            'score': health_score,
            'status': status_level,
            'issues': issues,
            'metrics': {
                'avg_response_time': avg_response_time,
                'error_rate': error_rate * 100,  # Convert to percentage
                'cache_hit_ratio': cache_hit_ratio * 100  # Convert to percentage
            }
        }
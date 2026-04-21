"""
T016: Health Check Views for Permission System Monitoring.

Provides comprehensive health check endpoints for the User Permissions System
including system status, cache health, database connectivity, and performance metrics.
"""

from django.http import JsonResponse
from django.db import connection
from django.core.cache import cache
from django.utils import timezone
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.views.decorators.cache import never_cache
from django.db import models
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated, AllowAny
import time
import psutil
import logging

from .models import Permission, UserGroup, UserPermission, PermissionAuditLog
from .performance import PerformanceMetrics
from .cache import permission_cache

logger = logging.getLogger(__name__)

# =============================================================================
# T016: PERMISSION SYSTEM HEALTH CHECK VIEWS
# =============================================================================

@method_decorator([csrf_exempt, never_cache], name='dispatch')
class PermissionSystemHealthView(APIView):
    """
    Comprehensive health check for the User Permissions System.
    
    Checks:
    - Database connectivity and permission model health
    - Cache system status and performance
    - Permission system integrity
    - Recent audit log activity
    
    Returns detailed health status with performance metrics.
    """
    
    permission_classes = [AllowAny]  # Open for load balancer health checks
    
    def get(self, request):
        """Perform comprehensive health check."""
        health_data = {
            'service': 'permission-system',
            'status': 'healthy',
            'timestamp': timezone.now().isoformat(),
            'version': '1.0.0',
            'checks': {}
        }
        
        overall_healthy = True
        
        # Check 1: Database Health
        db_health = self._check_database_health()
        health_data['checks']['database'] = db_health
        if not db_health['healthy']:
            overall_healthy = False
        
        # Check 2: Cache Health
        cache_health = self._check_cache_health()
        health_data['checks']['cache'] = cache_health
        if not cache_health['healthy']:
            overall_healthy = False
        
        # Check 3: Permission System Integrity
        permission_health = self._check_permission_integrity()
        health_data['checks']['permissions'] = permission_health
        if not permission_health['healthy']:
            overall_healthy = False
        
        # Check 4: Performance Metrics
        performance_health = self._check_performance_health()
        health_data['checks']['performance'] = performance_health
        if not performance_health['healthy']:
            overall_healthy = False
        
        # Set overall status
        if not overall_healthy:
            health_data['status'] = 'unhealthy'
            return Response(health_data, status=status.HTTP_503_SERVICE_UNAVAILABLE)
        
        return Response(health_data, status=status.HTTP_200_OK)
    
    def _check_database_health(self):
        """Check database connectivity and permission model health."""
        try:
            start_time = time.time()
            
            # Test database connection
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
                cursor.fetchone()
            
            # Test permission model queries
            permission_count = Permission.objects.count()
            group_count = UserGroup.objects.count()
            user_permission_count = UserPermission.objects.count()
            
            # Test audit log (last 24 hours)
            recent_logs = PermissionAuditLog.objects.filter(
                timestamp__gte=timezone.now() - timezone.timedelta(days=1)
            ).count()
            
            query_time = (time.time() - start_time) * 1000  # Convert to ms
            
            return {
                'healthy': True,
                'response_time_ms': round(query_time, 2),
                'metrics': {
                    'permissions_count': permission_count,
                    'groups_count': group_count,
                    'user_permissions_count': user_permission_count,
                    'recent_audit_logs': recent_logs
                }
            }
            
        except Exception as e:
            logger.error(f"Database health check failed: {str(e)}")
            return {
                'healthy': False,
                'error': 'Database connectivity failure',
                'details': str(e)
            }
    
    def _check_cache_health(self):
        """Check cache system health and performance."""
        try:
            start_time = time.time()
            
            # Test cache write/read
            test_key = 'health_check_test'
            test_value = f'test_{int(time.time())}'
            
            cache.set(test_key, test_value, timeout=30)
            retrieved_value = cache.get(test_key)
            
            if retrieved_value != test_value:
                raise Exception("Cache read/write test failed")
            
            # Clean up test key
            cache.delete(test_key)
            
            # Check permission cache stats if available
            cache_stats = {}
            try:
                cache_stats = permission_cache.get_stats()
            except Exception:
                cache_stats = {'error': 'Cache stats not available'}
            
            cache_time = (time.time() - start_time) * 1000  # Convert to ms
            
            return {
                'healthy': True,
                'response_time_ms': round(cache_time, 2),
                'stats': cache_stats
            }
            
        except Exception as e:
            logger.error(f"Cache health check failed: {str(e)}")
            return {
                'healthy': False,
                'error': 'Cache system failure',
                'details': str(e)
            }
    
    def _check_permission_integrity(self):
        """Check permission system data integrity."""
        try:
            issues = []
            
            # Check for permissions without modules
            permissions_without_modules = Permission.objects.filter(module__isnull=True).count()
            if permissions_without_modules > 0:
                issues.append(f'{permissions_without_modules} permissions without modules')
            
            # Check for inactive permissions with active assignments
            inactive_permissions_assigned = UserPermission.objects.filter(
                permission__is_active=False,
                is_granted=True
            ).count()
            if inactive_permissions_assigned > 0:
                issues.append(f'{inactive_permissions_assigned} assignments to inactive permissions')
            
            # Check for expired permissions still marked as granted
            expired_permissions = UserPermission.objects.filter(
                expires_at__lt=timezone.now(),
                is_granted=True
            ).count()
            if expired_permissions > 0:
                issues.append(f'{expired_permissions} expired permissions still active')
            
            # Check for orphaned audit logs (permissions that no longer exist)
            try:
                orphaned_logs = PermissionAuditLog.objects.exclude(
                    permission_id__in=Permission.objects.values_list('id', flat=True)
                ).count()
                if orphaned_logs > 0:
                    issues.append(f'{orphaned_logs} audit logs for deleted permissions')
            except Exception:
                pass  # This check is optional
            
            return {
                'healthy': len(issues) == 0,
                'issues_found': len(issues),
                'issues': issues if issues else None
            }
            
        except Exception as e:
            logger.error(f"Permission integrity check failed: {str(e)}")
            return {
                'healthy': False,
                'error': 'Permission integrity check failure',
                'details': str(e)
            }
    
    def _check_performance_health(self):
        """Check system performance metrics."""
        try:
            # Get current performance metrics
            metrics = {}
            
            # Memory usage
            try:
                process = psutil.Process()
                memory_info = process.memory_info()
                metrics['memory_usage_mb'] = round(memory_info.rss / 1024 / 1024, 2)
            except Exception:
                metrics['memory_usage_mb'] = 'unavailable'
            
            # Recent API performance (if available)
            try:
                recent_metrics = PerformanceMetrics.get_recent_stats(hours=1)
                metrics.update(recent_metrics)
            except Exception:
                metrics['api_performance'] = 'unavailable'
            
            # Simple performance threshold check
            memory_threshold_mb = 500  # 500MB threshold
            healthy = True
            
            if isinstance(metrics.get('memory_usage_mb'), (int, float)):
                if metrics['memory_usage_mb'] > memory_threshold_mb:
                    healthy = False
            
            return {
                'healthy': healthy,
                'metrics': metrics,
                'thresholds': {
                    'memory_threshold_mb': memory_threshold_mb
                }
            }
            
        except Exception as e:
            logger.error(f"Performance health check failed: {str(e)}")
            return {
                'healthy': False,
                'error': 'Performance check failure',
                'details': str(e)
            }


@method_decorator([csrf_exempt, never_cache], name='dispatch')
class CacheHealthView(APIView):
    """
    Dedicated cache system health check.
    
    Tests cache connectivity, performance, and provides statistics.
    """
    
    permission_classes = [AllowAny]
    
    def get(self, request):
        """Check cache system health."""
        try:
            start_time = time.time()
            
            # Test basic cache operations
            test_operations = []
            
            # Test 1: Basic set/get
            cache.set('health_test_basic', 'test_value', timeout=30)
            retrieved = cache.get('health_test_basic')
            test_operations.append({
                'operation': 'set_get',
                'success': retrieved == 'test_value'
            })
            
            # Test 2: Delete operation
            cache.delete('health_test_basic')
            deleted_check = cache.get('health_test_basic')
            test_operations.append({
                'operation': 'delete',
                'success': deleted_check is None
            })
            
            # Test 3: Multiple key handling
            cache.set_many({'test_key1': 'value1', 'test_key2': 'value2'}, timeout=30)
            multi_values = cache.get_many(['test_key1', 'test_key2'])
            test_operations.append({
                'operation': 'multi_operations',
                'success': len(multi_values) == 2
            })
            
            # Cleanup
            cache.delete_many(['test_key1', 'test_key2'])
            
            response_time = (time.time() - start_time) * 1000
            
            all_success = all(op['success'] for op in test_operations)
            
            return Response({
                'status': 'healthy' if all_success else 'unhealthy',
                'response_time_ms': round(response_time, 2),
                'operations': test_operations,
                'timestamp': timezone.now().isoformat()
            }, status=status.HTTP_200_OK if all_success else status.HTTP_503_SERVICE_UNAVAILABLE)
            
        except Exception as e:
            logger.error(f"Cache health check failed: {str(e)}")
            return Response({
                'status': 'unhealthy',
                'error': str(e),
                'timestamp': timezone.now().isoformat()
            }, status=status.HTTP_503_SERVICE_UNAVAILABLE)


@method_decorator([csrf_exempt, never_cache], name='dispatch')
class DatabaseHealthView(APIView):
    """
    Dedicated database health check.
    
    Tests database connectivity, query performance, and data integrity.
    """
    
    permission_classes = [AllowAny]
    
    def get(self, request):
        """Check database health."""
        try:
            start_time = time.time()
            
            # Test database connection
            with connection.cursor() as cursor:
                cursor.execute("SELECT version()")
                db_version = cursor.fetchone()[0] if cursor.rowcount > 0 else 'unknown'
                
                # Test table accessibility
                cursor.execute("SELECT COUNT(*) FROM core_permission")
                permission_count = cursor.fetchone()[0]
                
                # Test recent activity
                cursor.execute("""
                    SELECT COUNT(*) FROM core_permissionauditlog 
                    WHERE timestamp >= %s
                """, [timezone.now() - timezone.timedelta(hours=24)])
                recent_activity = cursor.fetchone()[0]
            
            response_time = (time.time() - start_time) * 1000
            
            return Response({
                'status': 'healthy',
                'response_time_ms': round(response_time, 2),
                'database_version': db_version,
                'metrics': {
                    'total_permissions': permission_count,
                    'recent_activity_24h': recent_activity
                },
                'timestamp': timezone.now().isoformat()
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Database health check failed: {str(e)}")
            return Response({
                'status': 'unhealthy',
                'error': str(e),
                'timestamp': timezone.now().isoformat()
            }, status=status.HTTP_503_SERVICE_UNAVAILABLE)


@method_decorator([csrf_exempt, never_cache], name='dispatch')
class PerformanceHealthView(APIView):
    """
    Performance metrics health check.
    
    Provides current performance statistics and system resource usage.
    """
    
    permission_classes = [AllowAny]
    
    def get(self, request):
        """Check performance health."""
        try:
            metrics = {}
            
            # System resource usage
            try:
                process = psutil.Process()
                metrics['cpu_percent'] = process.cpu_percent()
                memory_info = process.memory_info()
                metrics['memory_usage_mb'] = round(memory_info.rss / 1024 / 1024, 2)
                metrics['memory_percent'] = round(process.memory_percent(), 2)
            except Exception as e:
                metrics['system_metrics_error'] = str(e)
            
            # Database performance
            try:
                start_time = time.time()
                Permission.objects.count()
                metrics['db_query_time_ms'] = round((time.time() - start_time) * 1000, 2)
            except Exception as e:
                metrics['db_performance_error'] = str(e)
            
            # Cache performance
            try:
                start_time = time.time()
                cache.set('perf_test', 'value', timeout=30)
                cache.get('perf_test')
                cache.delete('perf_test')
                metrics['cache_operation_time_ms'] = round((time.time() - start_time) * 1000, 2)
            except Exception as e:
                metrics['cache_performance_error'] = str(e)
            
            # Performance thresholds
            thresholds = {
                'memory_warning_mb': 400,
                'memory_critical_mb': 800,
                'db_query_warning_ms': 100,
                'db_query_critical_ms': 1000
            }
            
            # Health assessment
            warnings = []
            if metrics.get('memory_usage_mb', 0) > thresholds['memory_warning_mb']:
                warnings.append('High memory usage')
            if metrics.get('db_query_time_ms', 0) > thresholds['db_query_warning_ms']:
                warnings.append('Slow database queries')
            
            status_code = status.HTTP_200_OK
            health_status = 'healthy'
            
            if warnings:
                health_status = 'warning'
            
            # Critical thresholds
            if (metrics.get('memory_usage_mb', 0) > thresholds['memory_critical_mb'] or
                metrics.get('db_query_time_ms', 0) > thresholds['db_query_critical_ms']):
                health_status = 'critical'
                status_code = status.HTTP_503_SERVICE_UNAVAILABLE
            
            return Response({
                'status': health_status,
                'metrics': metrics,
                'thresholds': thresholds,
                'warnings': warnings,
                'timestamp': timezone.now().isoformat()
            }, status=status_code)
            
        except Exception as e:
            logger.error(f"Performance health check failed: {str(e)}")
            return Response({
                'status': 'unhealthy',
                'error': str(e),
                'timestamp': timezone.now().isoformat()
            }, status=status.HTTP_503_SERVICE_UNAVAILABLE)


# =============================================================================
# T016: PERMISSION SYSTEM STATUS VIEWS
# =============================================================================

class PermissionsSummaryView(APIView):
    """
    Provides summary statistics for the permissions system.
    """
    
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """Get permissions system summary."""
        try:
            summary = {
                'permissions': {
                    'total': Permission.objects.count(),
                    'active': Permission.objects.filter(is_active=True).count(),
                    'by_risk_level': dict(Permission.objects.values_list('risk_level').annotate(count=models.Count('id')))
                },
                'groups': {
                    'total': UserGroup.objects.count(),
                    'active': UserGroup.objects.filter(is_active=True).count()
                },
                'assignments': {
                    'user_permissions': UserPermission.objects.filter(is_granted=True).count(),
                    'expired_permissions': UserPermission.objects.filter(
                        expires_at__lt=timezone.now(),
                        is_granted=True
                    ).count()
                },
                'audit': {
                    'total_logs': PermissionAuditLog.objects.count(),
                    'recent_24h': PermissionAuditLog.objects.filter(
                        timestamp__gte=timezone.now() - timezone.timedelta(days=1)
                    ).count()
                }
            }
            
            return Response(summary, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Permissions summary failed: {str(e)}")
            return Response({
                'error': 'Failed to generate permissions summary',
                'details': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class PermissionsIntegrityView(APIView):
    """
    Checks and reports on permissions system data integrity.
    """
    
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """Check permissions system integrity."""
        try:
            integrity_report = {
                'checks_performed': [],
                'issues_found': [],
                'warnings': [],
                'summary': {
                    'total_checks': 0,
                    'issues_count': 0,
                    'warnings_count': 0,
                    'overall_status': 'healthy'
                }
            }
            
            # Check 1: Orphaned permissions
            orphaned_user_perms = UserPermission.objects.exclude(
                permission_id__in=Permission.objects.values_list('id', flat=True)
            ).count()
            
            integrity_report['checks_performed'].append('Orphaned user permissions')
            if orphaned_user_perms > 0:
                integrity_report['issues_found'].append(
                    f'{orphaned_user_perms} user permissions reference deleted permission records'
                )
            
            # Check 2: Expired permissions
            expired_active_perms = UserPermission.objects.filter(
                expires_at__lt=timezone.now(),
                is_granted=True
            ).count()
            
            integrity_report['checks_performed'].append('Expired active permissions')
            if expired_active_perms > 0:
                integrity_report['warnings'].append(
                    f'{expired_active_perms} expired permissions are still marked as active'
                )
            
            # Check 3: Inactive permissions with assignments
            inactive_assigned_perms = UserPermission.objects.filter(
                permission__is_active=False,
                is_granted=True
            ).count()
            
            integrity_report['checks_performed'].append('Inactive permissions with assignments')
            if inactive_assigned_perms > 0:
                integrity_report['warnings'].append(
                    f'{inactive_assigned_perms} assignments to inactive permissions'
                )
            
            # Update summary
            integrity_report['summary']['total_checks'] = len(integrity_report['checks_performed'])
            integrity_report['summary']['issues_count'] = len(integrity_report['issues_found'])
            integrity_report['summary']['warnings_count'] = len(integrity_report['warnings'])
            
            if integrity_report['summary']['issues_count'] > 0:
                integrity_report['summary']['overall_status'] = 'issues_found'
            elif integrity_report['summary']['warnings_count'] > 0:
                integrity_report['summary']['overall_status'] = 'warnings'
            
            return Response(integrity_report, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Permissions integrity check failed: {str(e)}")
            return Response({
                'error': 'Failed to perform integrity check',
                'details': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class CacheStatsView(APIView):
    """
    Provides cache statistics and performance metrics.
    """
    
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """Get cache statistics."""
        try:
            stats = {
                'cache_backend': str(cache.__class__.__name__),
                'timestamp': timezone.now().isoformat()
            }
            
            # Test cache operations and measure performance
            start_time = time.time()
            
            # Basic performance test
            cache.set('stats_test', 'test_value', timeout=30)
            retrieved = cache.get('stats_test')
            cache.delete('stats_test')
            
            stats['basic_operation_time_ms'] = round((time.time() - start_time) * 1000, 2)
            stats['basic_operation_success'] = retrieved == 'test_value'
            
            # Try to get cache-specific stats if available
            try:
                if hasattr(cache, '_cache') and hasattr(cache._cache, 'stats'):
                    # Redis or Memcached stats
                    cache_stats = cache._cache.stats()
                    stats['backend_stats'] = cache_stats
                else:
                    stats['backend_stats'] = 'Not available for this cache backend'
            except Exception:
                stats['backend_stats'] = 'Stats collection failed'
            
            # Permission cache specific stats (if available)
            try:
                permission_cache_stats = permission_cache.get_stats()
                stats['permission_cache_stats'] = permission_cache_stats
            except Exception:
                stats['permission_cache_stats'] = 'Permission cache stats not available'
            
            return Response(stats, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Cache stats collection failed: {str(e)}")
            return Response({
                'error': 'Failed to collect cache statistics',
                'details': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
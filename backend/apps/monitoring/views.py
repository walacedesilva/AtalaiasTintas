"""
Monitoring application views for system health and alerting
User Story 2: Data Integrity and Backup
Task: T042 - Create health check API endpoints
"""

import logging
from datetime import timedelta
from rest_framework.views import APIView
from rest_framework.viewsets import ReadOnlyModelViewSet
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework import status, permissions
from rest_framework.pagination import PageNumberPagination
from django.utils import timezone
from django.db.models import Count, Avg, Q
from django.conf import settings

from .models import SystemHealth, AlertNotification
from .services import HealthCheckService, AlertService, BackupService
from .serializers import (
    SystemHealthSerializer, AlertNotificationSerializer,
    HealthSummarySerializer, ComponentHealthSerializer
)
from .tasks import check_single_component, create_scheduled_backup
from apps.core.models import BackupRecord
from apps.core.serializers import BackupRecordSerializer

logger = logging.getLogger(__name__)


class StandardResultsSetPagination(PageNumberPagination):
    """Standard pagination for monitoring endpoints"""
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100


class SystemHealthViewSet(ReadOnlyModelViewSet):
    """
    ViewSet for system health monitoring data
    Provides read-only access to health check results
    """
    queryset = SystemHealth.objects.all().order_by('-check_timestamp')
    serializer_class = SystemHealthSerializer
    pagination_class = StandardResultsSetPagination
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Filter by component if requested
        component = self.request.query_params.get('component')
        if component:
            queryset = queryset.filter(component=component)
        
        # Filter by status if requested
        status_filter = self.request.query_params.get('status')
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        # Filter by time range
        hours = self.request.query_params.get('hours', '24')
        try:
            hours = int(hours)
            cutoff_time = timezone.now() - timedelta(hours=hours)
            queryset = queryset.filter(check_timestamp__gte=cutoff_time)
        except (ValueError, TypeError):
            pass
        
        return queryset
    
    @action(detail=False, methods=['get'])
    def summary(self, request):
        """Get health summary for all components"""
        hours = int(request.query_params.get('hours', '24'))
        cutoff_time = timezone.now() - timedelta(hours=hours)
        
        # Get latest status for each component
        components = [
            SystemHealth.COMPONENT_DATABASE,
            SystemHealth.COMPONENT_REDIS,
            SystemHealth.COMPONENT_API,
            SystemHealth.COMPONENT_CELERY,
            SystemHealth.COMPONENT_DISK,
            SystemHealth.COMPONENT_MEMORY,
            SystemHealth.COMPONENT_CPU,
        ]
        
        summary_data = []
        
        for component in components:
            # Get latest record for this component
            latest_record = SystemHealth.objects.filter(
                component=component
            ).order_by('-check_timestamp').first()
            
            # Get statistics for the time period
            records = SystemHealth.objects.filter(
                component=component,
                check_timestamp__gte=cutoff_time
            )
            
            total_checks = records.count()
            
            if latest_record:
                uptime_percentage = 0
                avg_response_time = None
                
                if total_checks > 0:
                    healthy_checks = records.exclude(status=SystemHealth.STATUS_DOWN).count()
                    uptime_percentage = (healthy_checks / total_checks) * 100
                    
                    avg_response_time = records.exclude(
                        response_time__isnull=True
                    ).aggregate(avg=Avg('response_time'))['avg']
                
                component_data = {
                    'component': component,
                    'current_status': latest_record.status,
                    'last_check': latest_record.check_timestamp,
                    'uptime_percentage': round(uptime_percentage, 2),
                    'total_checks': total_checks,
                    'avg_response_time': round(avg_response_time, 2) if avg_response_time else None,
                    'current_metrics': {
                        'response_time': latest_record.response_time,
                        'cpu_usage': latest_record.cpu_usage,
                        'memory_usage': latest_record.memory_usage,
                        'disk_usage': latest_record.disk_usage,
                        'active_connections': latest_record.active_connections,
                        'queue_size': latest_record.queue_size,
                        'error_count': latest_record.error_count
                    }
                }
            else:
                component_data = {
                    'component': component,
                    'current_status': 'unknown',
                    'last_check': None,
                    'uptime_percentage': 0,
                    'total_checks': 0,
                    'avg_response_time': None,
                    'current_metrics': {}
                }
            
            summary_data.append(component_data)
        
        # Calculate overall system health
        active_components = [c for c in summary_data if c['current_status'] != 'unknown']
        
        if not active_components:
            overall_status = 'unknown'
        else:
            statuses = [c['current_status'] for c in active_components]
            if SystemHealth.STATUS_DOWN in statuses:
                overall_status = 'down'
            elif SystemHealth.STATUS_CRITICAL in statuses:
                overall_status = 'critical'
            elif SystemHealth.STATUS_WARNING in statuses:
                overall_status = 'warning'
            else:
                overall_status = 'healthy'
        
        return Response({
            'overall_status': overall_status,
            'components': summary_data,
            'period_hours': hours,
            'generated_at': timezone.now()
        })
    
    @action(detail=False, methods=['post'])
    def check_component(self, request):
        """Trigger health check for specific component"""
        component = request.data.get('component')
        
        if not component:
            return Response(
                {'error': 'Component name is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        valid_components = [
            SystemHealth.COMPONENT_DATABASE,
            SystemHealth.COMPONENT_REDIS,
            SystemHealth.COMPONENT_API,
            SystemHealth.COMPONENT_CELERY,
            SystemHealth.COMPONENT_DISK,
            SystemHealth.COMPONENT_MEMORY,
            SystemHealth.COMPONENT_CPU,
        ]
        
        if component not in valid_components:
            return Response(
                {'error': f'Invalid component. Valid options: {valid_components}'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            # Trigger async health check
            task = check_single_component.delay(component)
            
            return Response({
                'message': f'Health check initiated for {component}',
                'task_id': task.id,
                'component': component
            })
            
        except Exception as e:
            logger.error(f"Failed to initiate health check for {component}: {str(e)}")
            return Response(
                {'error': 'Failed to initiate health check'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class AlertNotificationViewSet(ReadOnlyModelViewSet):
    """
    ViewSet for alert notifications
    Provides read-only access to system alerts
    """
    queryset = AlertNotification.objects.all().order_by('-created_at')
    serializer_class = AlertNotificationSerializer
    pagination_class = StandardResultsSetPagination
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Filter by status if requested
        status_filter = self.request.query_params.get('status')
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        # Filter by severity if requested
        severity = self.request.query_params.get('severity')
        if severity:
            queryset = queryset.filter(severity=severity)
        
        # Filter by alert type if requested
        alert_type = self.request.query_params.get('type')
        if alert_type:
            queryset = queryset.filter(alert_type=alert_type)
        
        # Filter by time range
        hours = self.request.query_params.get('hours')
        if hours:
            try:
                hours = int(hours)
                cutoff_time = timezone.now() - timedelta(hours=hours)
                queryset = queryset.filter(created_at__gte=cutoff_time)
            except (ValueError, TypeError):
                pass
        
        return queryset
    
    @action(detail=False, methods=['get'])
    def statistics(self, request):
        """Get alert statistics for dashboard"""
        hours = int(request.query_params.get('hours', '24'))
        cutoff_time = timezone.now() - timedelta(hours=hours)
        
        # Get alert counts by severity
        alerts = AlertNotification.objects.filter(created_at__gte=cutoff_time)
        
        stats = alerts.aggregate(
            total_alerts=Count('id'),
            active_alerts=Count('id', filter=Q(status=AlertNotification.STATUS_ACTIVE)),
            resolved_alerts=Count('id', filter=Q(status=AlertNotification.STATUS_RESOLVED)),
            critical_alerts=Count('id', filter=Q(severity=AlertNotification.SEVERITY_CRITICAL)),
            error_alerts=Count('id', filter=Q(severity=AlertNotification.SEVERITY_ERROR)),
            warning_alerts=Count('id', filter=Q(severity=AlertNotification.SEVERITY_WARNING)),
            info_alerts=Count('id', filter=Q(severity=AlertNotification.SEVERITY_INFO))
        )
        
        # Get alerts by component
        component_alerts = alerts.values('source_component').annotate(
            count=Count('id')
        ).order_by('-count')
        
        return Response({
            'period_hours': hours,
            'statistics': stats,
            'alerts_by_component': list(component_alerts),
            'generated_at': timezone.now()
        })
    
    @action(detail=True, methods=['post'])
    def resolve(self, request, pk=None):
        """Mark an alert as resolved"""
        alert = self.get_object()
        
        if alert.status == AlertNotification.STATUS_RESOLVED:
            return Response(
                {'message': 'Alert is already resolved'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        alert.resolve_alert(resolved_by=request.user)
        
        return Response({
            'message': 'Alert marked as resolved',
            'alert_id': alert.id,
            'resolved_at': alert.resolved_at,
            'resolved_by': alert.resolved_by.username if alert.resolved_by else None
        })


class HealthDashboardView(APIView):
    """
    Comprehensive health dashboard endpoint
    Provides all data needed for monitoring dashboard
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        """Get complete dashboard data"""
        try:
            hours = int(request.query_params.get('hours', '24'))
            
            # Get system health summary
            health_service = HealthCheckService()
            
            # Get current health for all components
            components = [
                SystemHealth.COMPONENT_DATABASE,
                SystemHealth.COMPONENT_REDIS,
                SystemHealth.COMPONENT_API,
                SystemHealth.COMPONENT_CELERY,
                SystemHealth.COMPONENT_DISK,
                SystemHealth.COMPONENT_MEMORY,
                SystemHealth.COMPONENT_CPU,
            ]
            
            current_health = {}
            for component in components:
                latest = SystemHealth.objects.filter(
                    component=component
                ).order_by('-check_timestamp').first()
                
                if latest:
                    current_health[component] = {
                        'status': latest.status,
                        'last_check': latest.check_timestamp,
                        'metrics': {
                            'response_time': latest.response_time,
                            'cpu_usage': latest.cpu_usage,
                            'memory_usage': latest.memory_usage,
                            'disk_usage': latest.disk_usage,
                            'active_connections': latest.active_connections,
                            'queue_size': latest.queue_size,
                            'error_count': latest.error_count
                        }
                    }
                else:
                    current_health[component] = {
                        'status': 'unknown',
                        'last_check': None,
                        'metrics': {}
                    }
            
            # Get active alerts
            active_alerts = AlertNotification.objects.filter(
                status=AlertNotification.STATUS_ACTIVE
            ).order_by('-created_at')[:10]
            
            # Get recent backups
            recent_backups = BackupRecord.objects.filter(
                status__in=[BackupRecord.STATUS_COMPLETED, BackupRecord.STATUS_FAILED]
            ).order_by('-created_at')[:5]
            
            # Calculate overall system status
            statuses = [health['status'] for health in current_health.values() if health['status'] != 'unknown']
            
            if SystemHealth.STATUS_DOWN in statuses:
                overall_status = 'down'
            elif SystemHealth.STATUS_CRITICAL in statuses:
                overall_status = 'critical'
            elif SystemHealth.STATUS_WARNING in statuses:
                overall_status = 'warning'
            elif statuses:
                overall_status = 'healthy'
            else:
                overall_status = 'unknown'
            
            return Response({
                'overall_status': overall_status,
                'last_updated': timezone.now(),
                'components': current_health,
                'active_alerts': AlertNotificationSerializer(active_alerts, many=True).data,
                'recent_backups': BackupRecordSerializer(recent_backups, many=True).data,
                'alert_counts': {
                    'total_active': active_alerts.count(),
                    'critical': active_alerts.filter(severity=AlertNotification.SEVERITY_CRITICAL).count(),
                    'error': active_alerts.filter(severity=AlertNotification.SEVERITY_ERROR).count(),
                    'warning': active_alerts.filter(severity=AlertNotification.SEVERITY_WARNING).count(),
                }
            })
            
        except Exception as e:
            logger.error(f"Dashboard data request failed: {str(e)}")
            return Response(
                {'error': 'Failed to load dashboard data'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class BackupManagementView(APIView):
    """
    API endpoint for backup management
    Task: T043 - Backup management endpoints
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        """Create a new backup"""
        backup_type = request.data.get('backup_type', 'full')
        
        if backup_type not in ['full', 'incremental', 'manual']:
            return Response(
                {'error': 'Invalid backup type. Valid options: full, incremental, manual'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            # Trigger async backup creation
            task = create_scheduled_backup.delay(backup_type)
            
            return Response({
                'message': f'{backup_type.title()} backup initiated',
                'task_id': task.id,
                'backup_type': backup_type,
                'initiated_by': request.user.username,
                'initiated_at': timezone.now()
            })
            
        except Exception as e:
            logger.error(f"Failed to initiate backup: {str(e)}")
            return Response(
                {'error': 'Failed to initiate backup'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def get(self, request):
        """Get backup history and status"""
        hours = int(request.query_params.get('hours', '168'))  # Default 7 days
        cutoff_time = timezone.now() - timedelta(hours=hours)
        
        backups = BackupRecord.objects.filter(
            created_at__gte=cutoff_time
        ).order_by('-created_at')
        
        # Get backup statistics
        stats = backups.aggregate(
            total_backups=Count('id'),
            successful_backups=Count('id', filter=Q(status=BackupRecord.STATUS_COMPLETED)),
            failed_backups=Count('id', filter=Q(status=BackupRecord.STATUS_FAILED)),
            in_progress_backups=Count('id', filter=Q(status=BackupRecord.STATUS_IN_PROGRESS))
        )
        
        return Response({
            'statistics': stats,
            'backups': BackupRecordSerializer(backups[:20], many=True).data,  # Limit to 20 most recent
            'period_hours': hours
        })


class MetricsView(APIView):
    """
    System metrics endpoint for external monitoring tools
    Provides metrics in a format suitable for Prometheus/Grafana
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        """Get current system metrics"""
        try:
            # Get latest metrics for each component
            metrics = {}
            
            components = [
                SystemHealth.COMPONENT_DATABASE,
                SystemHealth.COMPONENT_REDIS,
                SystemHealth.COMPONENT_API,
                SystemHealth.COMPONENT_CELERY,
                SystemHealth.COMPONENT_DISK,
                SystemHealth.COMPONENT_MEMORY,
                SystemHealth.COMPONENT_CPU,
            ]
            
            for component in components:
                latest = SystemHealth.objects.filter(
                    component=component
                ).order_by('-check_timestamp').first()
                
                if latest:
                    # Map status to numeric values for monitoring
                    status_map = {
                        SystemHealth.STATUS_HEALTHY: 1,
                        SystemHealth.STATUS_WARNING: 0.75,
                        SystemHealth.STATUS_CRITICAL: 0.25,
                        SystemHealth.STATUS_DOWN: 0
                    }
                    
                    metrics[f'{component}_status'] = status_map.get(latest.status, 0)
                    
                    if latest.response_time:
                        metrics[f'{component}_response_time_ms'] = latest.response_time
                    if latest.cpu_usage:
                        metrics[f'{component}_cpu_usage_percent'] = latest.cpu_usage
                    if latest.memory_usage:
                        metrics[f'{component}_memory_usage_percent'] = latest.memory_usage
                    if latest.disk_usage:
                        metrics[f'{component}_disk_usage_percent'] = latest.disk_usage
                    if latest.active_connections:
                        metrics[f'{component}_connections'] = latest.active_connections
                    if latest.queue_size:
                        metrics[f'{component}_queue_size'] = latest.queue_size
                    if latest.error_count:
                        metrics[f'{component}_error_count'] = latest.error_count
            
            # Add alert metrics
            active_alerts = AlertNotification.objects.filter(
                status=AlertNotification.STATUS_ACTIVE
            ).aggregate(
                total=Count('id'),
                critical=Count('id', filter=Q(severity=AlertNotification.SEVERITY_CRITICAL)),
                error=Count('id', filter=Q(severity=AlertNotification.SEVERITY_ERROR)),
                warning=Count('id', filter=Q(severity=AlertNotification.SEVERITY_WARNING))
            )
            
            metrics.update({
                'active_alerts_total': active_alerts['total'],
                'active_alerts_critical': active_alerts['critical'],
                'active_alerts_error': active_alerts['error'],
                'active_alerts_warning': active_alerts['warning']
            })
            
            return Response({
                'metrics': metrics,
                'timestamp': timezone.now().isoformat()
            })
            
        except Exception as e:
            logger.error(f"Metrics request failed: {str(e)}")
            return Response(
                {'error': 'Failed to retrieve metrics'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
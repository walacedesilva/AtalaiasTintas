"""
Celery tasks for system monitoring
User Story 2: Data Integrity and Backup
Task: T040 - Implement Celery tasks for monitoring
"""

import logging
from celery import shared_task
from django.conf import settings
from django.utils import timezone
from django.db import models
from datetime import timedelta

from .services import HealthCheckService, AlertService, BackupService
from .models import SystemHealth, AlertNotification
from apps.core.models import BackupRecord

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=2)
def run_health_checks(self):
    """
    Periodic task to run all system health checks
    Runs every 5 minutes via Celery Beat
    """
    try:
        health_service = HealthCheckService()
        results = health_service.run_all_checks()
        
        logger.info(f"Health checks completed: {len(results)} components checked")
        
        # Return summary for monitoring
        summary = {
            'total_checks': len(results),
            'healthy': sum(1 for r in results.values() if r['status'] == SystemHealth.STATUS_HEALTHY),
            'warnings': sum(1 for r in results.values() if r['status'] == SystemHealth.STATUS_WARNING),
            'critical': sum(1 for r in results.values() if r['status'] == SystemHealth.STATUS_CRITICAL),
            'down': sum(1 for r in results.values() if r['status'] == SystemHealth.STATUS_DOWN),
            'timestamp': timezone.now().isoformat()
        }
        
        return summary
        
    except Exception as exc:
        logger.error(f"Health check task failed: {str(exc)}")
        # Retry the task
        raise self.retry(exc=exc, countdown=60)


@shared_task(bind=True, max_retries=3)
def process_alert_notifications(self):
    """
    Task to process and send pending alert notifications
    Runs every 2 minutes via Celery Beat
    """
    try:
        alert_service = AlertService()
        results = alert_service.process_pending_alerts()
        
        logger.info(
            f"Alert processing completed: {results['processed']} processed, "
            f"{results['successful']} successful, {results['failed']} failed"
        )
        
        return results
        
    except Exception as exc:
        logger.error(f"Alert processing task failed: {str(exc)}")
        # Retry with exponential backoff
        raise self.retry(exc=exc, countdown=60 * (2 ** self.request.retries))


@shared_task(bind=True, max_retries=2)
def check_single_component(self, component_name):
    """
    Task to check health of a specific component
    Can be triggered on-demand via API or management command
    
    Args:
        component_name: Name of component to check
    """
    try:
        health_service = HealthCheckService()
        result = health_service.check_component(component_name)
        
        logger.info(f"Component {component_name} check completed: {result['status']}")
        return result
        
    except Exception as exc:
        logger.error(f"Component check task failed for {component_name}: {str(exc)}")
        raise self.retry(exc=exc, countdown=30)


@shared_task(bind=True, max_retries=1)
def create_scheduled_backup(self, backup_type='full'):
    """
    Task to create scheduled database backups
    Runs daily for full backups, hourly for incremental backups
    
    Args:
        backup_type: Type of backup ('full' or 'incremental')
    """
    try:
        backup_service = BackupService()
        
        # Map backup type string to model constant
        backup_type_map = {
            'full': BackupRecord.TYPE_FULL,
            'incremental': BackupRecord.TYPE_INCREMENTAL,
            'manual': BackupRecord.TYPE_MANUAL
        }
        
        backup_type_const = backup_type_map.get(backup_type, BackupRecord.TYPE_FULL)
        
        backup_record = backup_service.create_backup(
            backup_type=backup_type_const,
            initiated_by=None  # Automated backup
        )
        
        result = {
            'backup_id': backup_record.backup_id,
            'filename': backup_record.filename,
            'status': backup_record.status,
            'file_size': backup_record.file_size,
            'created_at': backup_record.created_at.isoformat()
        }
        
        logger.info(f"Backup created: {backup_record.filename}")
        return result
        
    except Exception as exc:
        logger.error(f"Scheduled backup task failed: {str(exc)}")
        
        # Create failed backup record for audit trail
        try:
            BackupRecord.objects.create(
                backup_type=backup_type_const,
                filename=f"failed_backup_{timezone.now().strftime('%Y%m%d_%H%M%S')}.sql",
                status=BackupRecord.STATUS_FAILED,
                error_message=str(exc),
                error_details={'task_exception': type(exc).__name__},
                is_automated=True
            )
        except Exception:
            pass
        
        # Don't retry backup tasks to avoid storage issues
        raise exc


@shared_task(bind=True, max_retries=1)
def cleanup_old_backups(self):
    """
    Task to clean up expired backup files
    Runs daily to maintain disk space
    """
    try:
        backup_service = BackupService()
        cleaned_count = backup_service.cleanup_expired_backups()
        
        logger.info(f"Backup cleanup completed: {cleaned_count} files cleaned")
        
        return {
            'cleaned_count': cleaned_count,
            'timestamp': timezone.now().isoformat()
        }
        
    except Exception as exc:
        logger.error(f"Backup cleanup task failed: {str(exc)}")
        raise exc


@shared_task(bind=True, max_retries=2)
def cleanup_old_monitoring_data(self):
    """
    Task to clean up old monitoring data to prevent database bloat
    Runs weekly to maintain performance
    """
    try:
        # Define retention periods
        health_retention_days = getattr(settings, 'MONITORING_HEALTH_RETENTION_DAYS', 30)
        alert_retention_days = getattr(settings, 'MONITORING_ALERT_RETENTION_DAYS', 90)
        
        cutoff_date_health = timezone.now() - timedelta(days=health_retention_days)
        cutoff_date_alerts = timezone.now() - timedelta(days=alert_retention_days)
        
        # Clean up old health records
        deleted_health = SystemHealth.objects.filter(
            check_timestamp__lt=cutoff_date_health
        ).delete()
        
        # Clean up old resolved alerts
        deleted_alerts = AlertNotification.objects.filter(
            created_at__lt=cutoff_date_alerts,
            status=AlertNotification.STATUS_RESOLVED
        ).delete()
        
        result = {
            'health_records_deleted': deleted_health[0] if deleted_health else 0,
            'alerts_deleted': deleted_alerts[0] if deleted_alerts else 0,
            'timestamp': timezone.now().isoformat()
        }
        
        logger.info(
            f"Monitoring data cleanup completed: "
            f"{result['health_records_deleted']} health records, "
            f"{result['alerts_deleted']} alerts deleted"
        )
        
        return result
        
    except Exception as exc:
        logger.error(f"Monitoring data cleanup task failed: {str(exc)}")
        raise self.retry(exc=exc, countdown=300)


@shared_task(bind=True, max_retries=1)
def generate_health_summary_report(self, hours=24):
    """
    Task to generate system health summary report
    Can be scheduled daily or triggered on-demand
    
    Args:
        hours: Number of hours to include in the report
    """
    try:
        cutoff_time = timezone.now() - timedelta(hours=hours)
        
        # Get health statistics for the period
        health_stats = {}
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
            records = SystemHealth.objects.filter(
                component=component,
                check_timestamp__gte=cutoff_time
            )
            
            total_checks = records.count()
            if total_checks == 0:
                continue
            
            health_stats[component] = {
                'total_checks': total_checks,
                'healthy_count': records.filter(status=SystemHealth.STATUS_HEALTHY).count(),
                'warning_count': records.filter(status=SystemHealth.STATUS_WARNING).count(),
                'critical_count': records.filter(status=SystemHealth.STATUS_CRITICAL).count(),
                'down_count': records.filter(status=SystemHealth.STATUS_DOWN).count(),
                'avg_response_time': records.exclude(response_time__isnull=True).aggregate(
                    avg=models.Avg('response_time')
                )['avg'],
                'uptime_percentage': (
                    records.exclude(status=SystemHealth.STATUS_DOWN).count() / total_checks
                ) * 100
            }
        
        # Get alert statistics
        alert_stats = AlertNotification.objects.filter(
            created_at__gte=cutoff_time
        ).aggregate(
            total_alerts=models.Count('id'),
            critical_alerts=models.Count('id', filter=models.Q(severity=AlertNotification.SEVERITY_CRITICAL)),
            error_alerts=models.Count('id', filter=models.Q(severity=AlertNotification.SEVERITY_ERROR)),
            warning_alerts=models.Count('id', filter=models.Q(severity=AlertNotification.SEVERITY_WARNING)),
            resolved_alerts=models.Count('id', filter=models.Q(status=AlertNotification.STATUS_RESOLVED))
        )
        
        report = {
            'period_hours': hours,
            'generated_at': timezone.now().isoformat(),
            'health_stats': health_stats,
            'alert_stats': alert_stats,
            'overall_status': 'healthy'  # This would be calculated based on current state
        }
        
        # Determine overall status
        current_issues = AlertNotification.objects.filter(
            status=AlertNotification.STATUS_ACTIVE,
            severity__in=[AlertNotification.SEVERITY_CRITICAL, AlertNotification.SEVERITY_ERROR]
        ).count()
        
        if current_issues > 0:
            report['overall_status'] = 'degraded'
        
        logger.info(f"Health summary report generated for last {hours} hours")
        return report
        
    except Exception as exc:
        logger.error(f"Health report generation task failed: {str(exc)}")
        raise exc
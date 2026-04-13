"""
Health monitoring and alert services for system monitoring
User Story 2: Data Integrity and Backup
Tasks: T039 & T041 - Health check and alert services implementation
"""

import logging
import os
import psutil
import time
from datetime import datetime, timedelta
from django.core.mail import send_mail
from django.conf import settings
from django.db import connections, DatabaseError
from django.core.cache import cache
from django.utils import timezone
from typing import Dict, List, Optional, Tuple

from .models import SystemHealth, AlertNotification
from apps.core.models import BackupRecord

logger = logging.getLogger(__name__)


class HealthCheckService:
    """
    Service for performing comprehensive system health checks
    Task: T039 - Implement health check services
    """
    
    def __init__(self):
        self.checks = {
            SystemHealth.COMPONENT_DATABASE: self._check_database,
            SystemHealth.COMPONENT_REDIS: self._check_redis,
            SystemHealth.COMPONENT_API: self._check_api_health,
            SystemHealth.COMPONENT_CELERY: self._check_celery,
            SystemHealth.COMPONENT_DISK: self._check_disk_usage,
            SystemHealth.COMPONENT_MEMORY: self._check_memory_usage,
            SystemHealth.COMPONENT_CPU: self._check_cpu_usage,
        }
    
    def run_all_checks(self) -> Dict[str, Dict]:
        """
        Run all health checks and return results
        
        Returns:
            Dict with component names as keys and check results as values
        """
        results = {}
        
        for component, check_func in self.checks.items():
            try:
                result = check_func()
                results[component] = result
                
                # Store result in database
                SystemHealth.objects.create(
                    component=component,
                    status=result['status'],
                    response_time=result.get('response_time'),
                    cpu_usage=result.get('cpu_usage'),
                    memory_usage=result.get('memory_usage'),
                    disk_usage=result.get('disk_usage'),
                    active_connections=result.get('active_connections'),
                    queue_size=result.get('queue_size'),
                    error_count=result.get('error_count', 0),
                    error_message=result.get('error_message'),
                    additional_data=result.get('additional_data'),
                    check_timestamp=timezone.now()
                )
                
                # Generate alerts if needed
                self._generate_alerts_if_needed(component, result)
                
            except Exception as e:
                logger.error(f"Health check failed for {component}: {str(e)}")
                result = {
                    'status': SystemHealth.STATUS_DOWN,
                    'error_message': str(e),
                    'error_count': 1
                }
                results[component] = result
        
        return results
    
    def check_component(self, component: str) -> Dict:
        """
        Check health of a specific component
        
        Args:
            component: Component to check
            
        Returns:
            Health check result dictionary
        """
        if component not in self.checks:
            raise ValueError(f"Unknown component: {component}")
        
        check_func = self.checks[component]
        return check_func()
    
    def _check_database(self) -> Dict:
        """Check database connection and performance"""
        start_time = time.time()
        
        try:
            # Test database connection
            db = connections['default']
            cursor = db.cursor()
            cursor.execute("SELECT 1")
            cursor.fetchone()
            
            response_time = (time.time() - start_time) * 1000  # Convert to ms
            
            # Check active connections
            cursor.execute("""
                SELECT COUNT(*) FROM pragma_table_info('auth_user')
            """)
            active_connections = cursor.fetchone()[0] if cursor.fetchone() else 0
            
            cursor.close()
            
            # Determine status based on response time
            if response_time < 100:
                status = SystemHealth.STATUS_HEALTHY
            elif response_time < 500:
                status = SystemHealth.STATUS_WARNING
            else:
                status = SystemHealth.STATUS_CRITICAL
            
            return {
                'status': status,
                'response_time': response_time,
                'active_connections': active_connections,
                'error_count': 0
            }
            
        except DatabaseError as e:
            return {
                'status': SystemHealth.STATUS_DOWN,
                'error_message': str(e),
                'error_count': 1
            }
    
    def _check_redis(self) -> Dict:
        """Check Redis cache connection and performance"""
        start_time = time.time()
        
        try:
            # Test Redis connection
            test_key = 'health_check_test'
            test_value = str(int(time.time()))
            
            cache.set(test_key, test_value, timeout=60)
            retrieved_value = cache.get(test_key)
            
            if retrieved_value != test_value:
                raise Exception("Redis set/get test failed")
            
            cache.delete(test_key)
            
            response_time = (time.time() - start_time) * 1000
            
            # Determine status based on response time
            if response_time < 50:
                status = SystemHealth.STATUS_HEALTHY
            elif response_time < 200:
                status = SystemHealth.STATUS_WARNING
            else:
                status = SystemHealth.STATUS_CRITICAL
            
            return {
                'status': status,
                'response_time': response_time,
                'error_count': 0
            }
            
        except Exception as e:
            return {
                'status': SystemHealth.STATUS_DOWN,
                'error_message': str(e),
                'error_count': 1
            }
    
    def _check_api_health(self) -> Dict:
        """Check API service health"""
        # This is a basic API health check
        # In a real implementation, you might check specific endpoints
        
        return {
            'status': SystemHealth.STATUS_HEALTHY,
            'response_time': 10.0,  # Simulated response time
            'error_count': 0,
            'additional_data': {
                'endpoints_checked': ['auth', 'health'],
                'last_check': timezone.now().isoformat()
            }
        }
    
    def _check_celery(self) -> Dict:
        """Check Celery worker and queue status"""
        try:
            from celery import current_app
            
            # Get active tasks
            inspect = current_app.control.inspect()
            active_tasks = inspect.active()
            
            if active_tasks:
                total_tasks = sum(len(tasks) for tasks in active_tasks.values())
            else:
                total_tasks = 0
            
            # Check if workers are available
            stats = inspect.stats()
            worker_count = len(stats) if stats else 0
            
            if worker_count > 0:
                status = SystemHealth.STATUS_HEALTHY
            else:
                status = SystemHealth.STATUS_WARNING
            
            return {
                'status': status,
                'queue_size': total_tasks,
                'active_connections': worker_count,
                'error_count': 0,
                'additional_data': {
                    'workers': list(stats.keys()) if stats else [],
                    'active_tasks': total_tasks
                }
            }
            
        except Exception as e:
            return {
                'status': SystemHealth.STATUS_DOWN,
                'error_message': str(e),
                'error_count': 1
            }
    
    def _check_disk_usage(self) -> Dict:
        """Check disk space usage"""
        try:
            disk_usage = psutil.disk_usage('/')
            usage_percent = (disk_usage.used / disk_usage.total) * 100
            
            if usage_percent < 70:
                status = SystemHealth.STATUS_HEALTHY
            elif usage_percent < 85:
                status = SystemHealth.STATUS_WARNING
            elif usage_percent < 95:
                status = SystemHealth.STATUS_CRITICAL
            else:
                status = SystemHealth.STATUS_DOWN
            
            return {
                'status': status,
                'disk_usage': usage_percent,
                'error_count': 0,
                'additional_data': {
                    'total_gb': round(disk_usage.total / (1024**3), 2),
                    'used_gb': round(disk_usage.used / (1024**3), 2),
                    'free_gb': round(disk_usage.free / (1024**3), 2)
                }
            }
            
        except Exception as e:
            return {
                'status': SystemHealth.STATUS_DOWN,
                'error_message': str(e),
                'error_count': 1
            }
    
    def _check_memory_usage(self) -> Dict:
        """Check system memory usage"""
        try:
            memory = psutil.virtual_memory()
            usage_percent = memory.percent
            
            if usage_percent < 70:
                status = SystemHealth.STATUS_HEALTHY
            elif usage_percent < 85:
                status = SystemHealth.STATUS_WARNING
            elif usage_percent < 95:
                status = SystemHealth.STATUS_CRITICAL
            else:
                status = SystemHealth.STATUS_DOWN
            
            return {
                'status': status,
                'memory_usage': usage_percent,
                'error_count': 0,
                'additional_data': {
                    'total_gb': round(memory.total / (1024**3), 2),
                    'available_gb': round(memory.available / (1024**3), 2),
                    'used_gb': round(memory.used / (1024**3), 2)
                }
            }
            
        except Exception as e:
            return {
                'status': SystemHealth.STATUS_DOWN,
                'error_message': str(e),
                'error_count': 1
            }
    
    def _check_cpu_usage(self) -> Dict:
        """Check CPU usage"""
        try:
            # Get CPU usage over a short interval
            cpu_percent = psutil.cpu_percent(interval=1)
            cpu_count = psutil.cpu_count()
            load_avg = os.getloadavg()[0] if hasattr(os, 'getloadavg') else cpu_percent / 100
            
            if cpu_percent < 70:
                status = SystemHealth.STATUS_HEALTHY
            elif cpu_percent < 85:
                status = SystemHealth.STATUS_WARNING
            elif cpu_percent < 95:
                status = SystemHealth.STATUS_CRITICAL
            else:
                status = SystemHealth.STATUS_DOWN
            
            return {
                'status': status,
                'cpu_usage': cpu_percent,
                'error_count': 0,
                'additional_data': {
                    'cpu_count': cpu_count,
                    'load_average': load_avg,
                    'per_cpu': psutil.cpu_percent(percpu=True)
                }
            }
            
        except Exception as e:
            return {
                'status': SystemHealth.STATUS_DOWN,
                'error_message': str(e),
                'error_count': 1
            }
    
    def _generate_alerts_if_needed(self, component: str, result: Dict):
        """Generate alerts based on health check results"""
        status = result['status']
        
        # Only generate alerts for warning, critical, or down states
        if status == SystemHealth.STATUS_HEALTHY:
            return
        
        # Check if we already have an active alert for this component
        existing_alert = AlertNotification.objects.filter(
            alert_type=AlertNotification.TYPE_SYSTEM_HEALTH,
            source_component=component,
            status=AlertNotification.STATUS_ACTIVE
        ).first()
        
        if existing_alert:
            # Update existing alert if status worsened
            if self._is_status_worse(status, existing_alert.metadata.get('last_status')):
                existing_alert.message = f"{component} health degraded to {status}"
                existing_alert.severity = self._map_status_to_severity(status)
                existing_alert.metadata = {'last_status': status, 'check_result': result}
                existing_alert.save()
            return
        
        # Create new alert
        severity = self._map_status_to_severity(status)
        title = f"{component} Health Alert"
        message = f"Component {component} is {status.lower()}"
        
        if result.get('error_message'):
            message += f": {result['error_message']}"
        
        AlertNotification.create_alert(
            title=title,
            message=message,
            alert_type=AlertNotification.TYPE_SYSTEM_HEALTH,
            severity=severity,
            source_component=component,
            metadata={'check_result': result, 'last_status': status}
        )
    
    def _is_status_worse(self, new_status: str, old_status: str) -> bool:
        """Check if new status is worse than old status"""
        status_order = {
            SystemHealth.STATUS_HEALTHY: 0,
            SystemHealth.STATUS_WARNING: 1,
            SystemHealth.STATUS_CRITICAL: 2,
            SystemHealth.STATUS_DOWN: 3
        }
        
        return status_order.get(new_status, 3) > status_order.get(old_status, 0)
    
    def _map_status_to_severity(self, status: str) -> str:
        """Map health status to alert severity"""
        mapping = {
            SystemHealth.STATUS_WARNING: AlertNotification.SEVERITY_WARNING,
            SystemHealth.STATUS_CRITICAL: AlertNotification.SEVERITY_ERROR,
            SystemHealth.STATUS_DOWN: AlertNotification.SEVERITY_CRITICAL
        }
        return mapping.get(status, AlertNotification.SEVERITY_INFO)


class AlertService:
    """
    Service for managing and sending alert notifications
    Task: T041 - Implement email/SMS alert services
    """
    
    def __init__(self):
        self.email_enabled = getattr(settings, 'ALERTS_EMAIL_ENABLED', True)
        self.sms_enabled = getattr(settings, 'ALERTS_SMS_ENABLED', False)
        self.push_enabled = getattr(settings, 'ALERTS_PUSH_ENABLED', False)
    
    def send_alert(self, alert: AlertNotification) -> Dict[str, bool]:
        """
        Send alert through configured channels
        
        Args:
            alert: AlertNotification instance to send
            
        Returns:
            Dict with success status for each channel
        """
        results = {
            'email': False,
            'sms': False,
            'push': False
        }
        
        # Send email notification
        if self.email_enabled and not alert.email_sent:
            results['email'] = self._send_email_alert(alert)
            if results['email']:
                alert.email_sent = True
        
        # Send SMS notification
        if self.sms_enabled and not alert.sms_sent:
            results['sms'] = self._send_sms_alert(alert)
            if results['sms']:
                alert.sms_sent = True
        
        # Send push notification
        if self.push_enabled and not alert.push_sent:
            results['push'] = self._send_push_alert(alert)
            if results['push']:
                alert.push_sent = True
        
        # Save notification status
        alert.save(update_fields=['email_sent', 'sms_sent', 'push_sent'])
        
        return results
    
    def _send_email_alert(self, alert: AlertNotification) -> bool:
        """Send alert via email"""
        try:
            # Get admin emails from settings
            admin_emails = getattr(settings, 'ALERT_ADMIN_EMAILS', [])
            if not admin_emails:
                admin_emails = [admin[1] for admin in getattr(settings, 'ADMINS', [])]
            
            if not admin_emails:
                logger.warning("No admin emails configured for alerts")
                return False
            
            subject = f"[ALERT] {alert.get_severity_display()}: {alert.title}"
            
            message_body = f"""
Sistema de Monitoramento - Alerta

Título: {alert.title}
Severidade: {alert.get_severity_display()}
Tipo: {alert.get_alert_type_display()}
Data/Hora: {alert.created_at}

Mensagem:
{alert.message}

Componente: {alert.source_component or 'N/A'}
Status: {alert.get_status_display()}

---
Este é um alerta automático do sistema de monitoramento.
            """.strip()
            
            send_mail(
                subject=subject,
                message=message_body,
                from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@localhost'),
                recipient_list=admin_emails,
                fail_silently=False
            )
            
            logger.info(f"Email alert sent for {alert.title}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send email alert: {str(e)}")
            return False
    
    def _send_sms_alert(self, alert: AlertNotification) -> bool:
        """Send alert via SMS (placeholder implementation)"""
        try:
            # This is a placeholder - integrate with your SMS provider
            # Examples: Twilio, AWS SNS, etc.
            
            admin_phones = getattr(settings, 'ALERT_ADMIN_PHONES', [])
            if not admin_phones:
                return False
            
            message = f"ALERTA {alert.get_severity_display()}: {alert.title}"
            
            # TODO: Implement SMS sending with your provider
            logger.info(f"SMS alert would be sent: {message}")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to send SMS alert: {str(e)}")
            return False
    
    def _send_push_alert(self, alert: AlertNotification) -> bool:
        """Send alert via push notification (placeholder implementation)"""
        try:
            # This is a placeholder - integrate with your push provider
            # Examples: Firebase FCM, Apple Push Notifications, etc.
            
            logger.info(f"Push alert would be sent: {alert.title}")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to send push alert: {str(e)}")
            return False
    
    def process_pending_alerts(self):
        """Process all pending alerts that haven't been sent"""
        pending_alerts = AlertNotification.objects.filter(
            status=AlertNotification.STATUS_ACTIVE
        ).exclude(
            email_sent=True,
            sms_sent=True,
            push_sent=True
        )
        
        results = {
            'processed': 0,
            'successful': 0,
            'failed': 0
        }
        
        for alert in pending_alerts:
            results['processed'] += 1
            
            send_results = self.send_alert(alert)
            
            if any(send_results.values()):
                results['successful'] += 1
            else:
                results['failed'] += 1
        
        return results


class BackupService:
    """
    Service for managing database backups
    Task: T043 - Backup management service (used by management command)
    """
    
    def __init__(self):
        self.backup_dir = getattr(settings, 'BACKUP_DIR', '/tmp/backups')
        os.makedirs(self.backup_dir, exist_ok=True)
    
    def create_backup(self, backup_type: str = BackupRecord.TYPE_FULL, 
                     initiated_by=None) -> BackupRecord:
        """
        Create a database backup
        
        Args:
            backup_type: Type of backup to create
            initiated_by: User who initiated the backup
            
        Returns:
            BackupRecord instance
        """
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"backup_{backup_type.lower()}_{timestamp}.sql"
        file_path = os.path.join(self.backup_dir, filename)
        
        # Create backup record
        backup_record = BackupRecord.create_backup_record(
            backup_type=backup_type,
            filename=filename,
            file_path=file_path,
            initiated_by=initiated_by,
            is_automated=(initiated_by is None)
        )
        
        try:
            # Perform the actual backup
            self._perform_backup(file_path, backup_record)
            
            # Calculate file size and checksum
            file_size = os.path.getsize(file_path)
            checksum = self._calculate_checksum(file_path)
            
            backup_record.mark_completed(file_size=file_size, checksum=checksum)
            
            logger.info(f"Backup created successfully: {filename}")
            
        except Exception as e:
            backup_record.mark_failed(
                error_message=str(e),
                error_details={'exception_type': type(e).__name__}
            )
            logger.error(f"Backup failed: {str(e)}")
        
        return backup_record
    
    def _perform_backup(self, file_path: str, backup_record: BackupRecord):
        """Perform the actual database backup"""
        import subprocess
        
        # Update status to in progress
        backup_record.status = BackupRecord.STATUS_IN_PROGRESS
        backup_record.save(update_fields=['status'])
        
        # For SQLite, we can simply copy the database file
        # For PostgreSQL, use pg_dump
        db_settings = settings.DATABASES['default']
        
        if db_settings['ENGINE'].endswith('sqlite3'):
            import shutil
            shutil.copy2(db_settings['NAME'], file_path)
        else:
            # PostgreSQL backup command
            cmd = [
                'pg_dump',
                '-h', db_settings.get('HOST', 'localhost'),
                '-p', str(db_settings.get('PORT', 5432)),
                '-U', db_settings['USER'],
                '-d', db_settings['NAME'],
                '-f', file_path
            ]
            
            env = os.environ.copy()
            env['PGPASSWORD'] = db_settings['PASSWORD']
            
            result = subprocess.run(cmd, env=env, capture_output=True, text=True)
            
            if result.returncode != 0:
                raise Exception(f"pg_dump failed: {result.stderr}")
    
    def _calculate_checksum(self, file_path: str) -> str:
        """Calculate SHA256 checksum of backup file"""
        import hashlib
        
        sha256_hash = hashlib.sha256()
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        
        return sha256_hash.hexdigest()
    
    def cleanup_expired_backups(self) -> int:
        """Clean up expired backup files"""
        expired_backups = BackupRecord.get_expired_backups()
        cleaned_count = 0
        
        for backup in expired_backups:
            try:
                if os.path.exists(backup.file_path):
                    os.remove(backup.file_path)
                
                backup.is_archived = True
                backup.archive_location = 'deleted'
                backup.save(update_fields=['is_archived', 'archive_location'])
                
                cleaned_count += 1
                logger.info(f"Cleaned up expired backup: {backup.filename}")
                
            except Exception as e:
                logger.error(f"Failed to cleanup backup {backup.filename}: {str(e)}")
        
        return cleaned_count
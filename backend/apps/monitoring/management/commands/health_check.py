"""
Django management command for running health checks
User Story 2: Data Integrity and Backup
Task: T044 - Create health check management command
"""

from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone
from datetime import timedelta

from apps.monitoring.services import HealthCheckService, AlertService
from apps.monitoring.models import SystemHealth, AlertNotification


class Command(BaseCommand):
    """
    Management command to run system health checks
    
    Usage:
        python manage.py health_check
        python manage.py health_check --component database
        python manage.py health_check --all
        python manage.py health_check --summary
        python manage.py health_check --alerts
    """
    
    help = 'Run system health checks and display results'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--component',
            type=str,
            choices=[
                'database', 'redis', 'api', 'celery', 
                'disk', 'memory', 'cpu'
            ],
            help='Check specific component only'
        )
        
        parser.add_argument(
            '--all',
            action='store_true',
            help='Run all health checks'
        )
        
        parser.add_argument(
            '--summary',
            action='store_true',
            help='Show health summary for last 24 hours'
        )
        
        parser.add_argument(
            '--alerts',
            action='store_true',
            help='Show active alerts'
        )
        
        parser.add_argument(
            '--send-alerts',
            action='store_true',
            help='Process and send pending alerts'
        )
        
        parser.add_argument(
            '--hours',
            type=int,
            default=24,
            help='Hours for summary reports (default: 24)'
        )
    
    def handle(self, *args, **options):
        if options['summary']:
            self._show_summary(options['hours'])
            return
        
        if options['alerts']:
            self._show_alerts()
            return
        
        if options['send_alerts']:
            self._send_pending_alerts()
            return
        
        # Run health checks
        if options['component']:
            self._check_component(options['component'])
        else:
            self._check_all_components()
    
    def _check_component(self, component_name):
        """Check health of a specific component"""
        # Map component name to model constant
        component_map = {
            'database': SystemHealth.COMPONENT_DATABASE,
            'redis': SystemHealth.COMPONENT_REDIS,
            'api': SystemHealth.COMPONENT_API,
            'celery': SystemHealth.COMPONENT_CELERY,
            'disk': SystemHealth.COMPONENT_DISK,
            'memory': SystemHealth.COMPONENT_MEMORY,
            'cpu': SystemHealth.COMPONENT_CPU,
        }
        
        component = component_map.get(component_name)
        if not component:
            raise CommandError(f"Invalid component: {component_name}")
        
        self.stdout.write(f"Checking {component_name} health...")
        
        try:
            health_service = HealthCheckService()
            result = health_service.check_component(component)
            
            self._display_component_result(component_name, result)
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f"✗ Health check failed for {component_name}: {str(e)}")
            )
            raise CommandError("Health check failed")
    
    def _check_all_components(self):
        """Run health checks for all components"""
        self.stdout.write("Running comprehensive health checks...")
        self.stdout.write("=" * 60)
        
        try:
            health_service = HealthCheckService()
            results = health_service.run_all_checks()
            
            # Display results
            for component, result in results.items():
                self._display_component_result(component, result)
                self.stdout.write("-" * 40)
            
            # Overall summary
            healthy_count = sum(1 for r in results.values() if r['status'] == SystemHealth.STATUS_HEALTHY)
            total_count = len(results)
            
            if healthy_count == total_count:
                self.stdout.write(
                    self.style.SUCCESS(
                        f"✓ All {total_count} components are healthy!"
                    )
                )
            else:
                issues = total_count - healthy_count
                self.stdout.write(
                    self.style.WARNING(
                        f"⚠ {healthy_count}/{total_count} components healthy, {issues} issues found"
                    )
                )
        
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f"✗ Health checks failed: {str(e)}")
            )
            raise CommandError("Health checks failed")
    
    def _display_component_result(self, component_name, result):
        """Display health check result for a component"""
        status = result['status']
        
        # Choose color based on status
        if status == SystemHealth.STATUS_HEALTHY:
            status_color = self.style.SUCCESS
            icon = "✓"
        elif status == SystemHealth.STATUS_WARNING:
            status_color = self.style.WARNING
            icon = "⚠"
        elif status == SystemHealth.STATUS_CRITICAL:
            status_color = self.style.ERROR
            icon = "⚠"
        else:  # DOWN
            status_color = self.style.ERROR
            icon = "✗"
        
        self.stdout.write(
            f"{icon} {component_name.upper()}: {status_color(status.upper())}"
        )
        
        # Display metrics if available
        metrics = []
        if result.get('response_time'):
            metrics.append(f"Response: {result['response_time']:.1f}ms")
        if result.get('cpu_usage'):
            metrics.append(f"CPU: {result['cpu_usage']:.1f}%")
        if result.get('memory_usage'):
            metrics.append(f"Memory: {result['memory_usage']:.1f}%")
        if result.get('disk_usage'):
            metrics.append(f"Disk: {result['disk_usage']:.1f}%")
        if result.get('active_connections'):
            metrics.append(f"Connections: {result['active_connections']}")
        if result.get('queue_size'):
            metrics.append(f"Queue: {result['queue_size']}")
        if result.get('error_count', 0) > 0:
            metrics.append(f"Errors: {result['error_count']}")
        
        if metrics:
            self.stdout.write(f"  {' | '.join(metrics)}")
        
        # Display error message if present
        if result.get('error_message'):
            self.stdout.write(
                self.style.ERROR(f"  Error: {result['error_message']}")
            )
        
        # Display additional data if present
        additional_data = result.get('additional_data')
        if additional_data and isinstance(additional_data, dict):
            for key, value in additional_data.items():
                if key not in ['endpoints_checked', 'workers', 'per_cpu']:
                    self.stdout.write(f"  {key}: {value}")
    
    def _show_summary(self, hours):
        """Show health summary for the specified time period"""
        cutoff_time = timezone.now() - timedelta(hours=hours)
        
        self.stdout.write(f"Health Summary - Last {hours} hours")
        self.stdout.write("=" * 50)
        
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
            
            # Get latest status
            latest = records.order_by('-check_timestamp').first()
            
            # Calculate uptime
            healthy_checks = records.exclude(status=SystemHealth.STATUS_DOWN).count()
            uptime_percentage = (healthy_checks / total_checks) * 100
            
            # Get average response time
            avg_response_time = records.exclude(
                response_time__isnull=True
            ).aggregate(avg=models.Avg('response_time'))['avg']
            
            # Status counts
            status_counts = {
                'healthy': records.filter(status=SystemHealth.STATUS_HEALTHY).count(),
                'warning': records.filter(status=SystemHealth.STATUS_WARNING).count(),
                'critical': records.filter(status=SystemHealth.STATUS_CRITICAL).count(),
                'down': records.filter(status=SystemHealth.STATUS_DOWN).count(),
            }
            
            # Choose color based on current status
            if latest.status == SystemHealth.STATUS_HEALTHY:
                status_color = self.style.SUCCESS
            elif latest.status == SystemHealth.STATUS_WARNING:
                status_color = self.style.WARNING
            else:
                status_color = self.style.ERROR
            
            self.stdout.write(
                f"{component.upper()}: {status_color(latest.status.upper())} "
                f"(Uptime: {uptime_percentage:.1f}%)"
            )
            self.stdout.write(
                f"  Checks: {total_checks} total, "
                f"{status_counts['healthy']} healthy, "
                f"{status_counts['warning']} warning, "
                f"{status_counts['critical']} critical, "
                f"{status_counts['down']} down"
            )
            
            if avg_response_time:
                self.stdout.write(f"  Avg response time: {avg_response_time:.1f}ms")
            
            self.stdout.write("")  # Empty line
    
    def _show_alerts(self):
        """Show active alerts"""
        active_alerts = AlertNotification.objects.filter(
            status=AlertNotification.STATUS_ACTIVE
        ).order_by('-created_at')
        
        self.stdout.write("Active Alerts")
        self.stdout.write("=" * 30)
        
        if not active_alerts:
            self.stdout.write(self.style.SUCCESS("✓ No active alerts"))
            return
        
        for alert in active_alerts:
            # Choose color based on severity
            if alert.severity == AlertNotification.SEVERITY_CRITICAL:
                severity_color = self.style.ERROR
                icon = "🔴"
            elif alert.severity == AlertNotification.SEVERITY_ERROR:
                severity_color = self.style.ERROR
                icon = "🟠"
            elif alert.severity == AlertNotification.SEVERITY_WARNING:
                severity_color = self.style.WARNING
                icon = "🟡"
            else:
                severity_color = self.style.HTTP_INFO
                icon = "🔵"
            
            self.stdout.write(
                f"{icon} {severity_color(alert.get_severity_display().upper())}: {alert.title}"
            )
            self.stdout.write(f"  {alert.message}")
            self.stdout.write(f"  Component: {alert.source_component or 'N/A'}")
            self.stdout.write(f"  Created: {alert.created_at}")
            self.stdout.write("")  # Empty line
    
    def _send_pending_alerts(self):
        """Process and send pending alerts"""
        self.stdout.write("Processing pending alerts...")
        
        try:
            alert_service = AlertService()
            results = alert_service.process_pending_alerts()
            
            self.stdout.write(
                self.style.SUCCESS(
                    f"✓ Alert processing completed:\n"
                    f"  Processed: {results['processed']}\n"
                    f"  Successful: {results['successful']}\n"
                    f"  Failed: {results['failed']}"
                )
            )
        
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f"✗ Alert processing failed: {str(e)}")
            )
            raise CommandError("Alert processing failed")


# Import for aggregate functions
from django.db import models
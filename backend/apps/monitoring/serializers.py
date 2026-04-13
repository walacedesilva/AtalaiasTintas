"""
Serializers for monitoring application
User Story 2: Data Integrity and Backup
Task: T042 - API serializers for monitoring endpoints
"""

from rest_framework import serializers
from django.contrib.auth import get_user_model

from .models import SystemHealth, AlertNotification

User = get_user_model()


class SystemHealthSerializer(serializers.ModelSerializer):
    """Serializer for SystemHealth model"""
    
    component_display = serializers.CharField(source='get_component_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    
    class Meta:
        model = SystemHealth
        fields = [
            'id', 'component', 'component_display', 'status', 'status_display',
            'response_time', 'cpu_usage', 'memory_usage', 'disk_usage',
            'active_connections', 'queue_size', 'error_count', 'error_message',
            'additional_data', 'check_timestamp', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']


class AlertNotificationSerializer(serializers.ModelSerializer):
    """Serializer for AlertNotification model"""
    
    severity_display = serializers.CharField(source='get_severity_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    alert_type_display = serializers.CharField(source='get_alert_type_display', read_only=True)
    resolved_by_username = serializers.CharField(source='resolved_by.username', read_only=True)
    
    class Meta:
        model = AlertNotification
        fields = [
            'id', 'title', 'message', 'alert_type', 'alert_type_display',
            'severity', 'severity_display', 'status', 'status_display',
            'source_component', 'metadata', 'email_sent', 'sms_sent', 'push_sent',
            'resolved_at', 'resolved_by', 'resolved_by_username', 'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'email_sent', 'sms_sent', 'push_sent', 'resolved_at', 
            'resolved_by', 'created_at', 'updated_at'
        ]


class ComponentHealthSerializer(serializers.Serializer):
    """Serializer for component health summary"""
    
    component = serializers.CharField()
    current_status = serializers.CharField()
    last_check = serializers.DateTimeField()
    uptime_percentage = serializers.FloatField()
    total_checks = serializers.IntegerField()
    avg_response_time = serializers.FloatField(allow_null=True)
    current_metrics = serializers.DictField()


class HealthSummarySerializer(serializers.Serializer):
    """Serializer for system health summary"""
    
    overall_status = serializers.CharField()
    components = ComponentHealthSerializer(many=True)
    period_hours = serializers.IntegerField()
    generated_at = serializers.DateTimeField()


class AlertStatisticsSerializer(serializers.Serializer):
    """Serializer for alert statistics"""
    
    total_alerts = serializers.IntegerField()
    active_alerts = serializers.IntegerField()
    resolved_alerts = serializers.IntegerField()
    critical_alerts = serializers.IntegerField()
    error_alerts = serializers.IntegerField()
    warning_alerts = serializers.IntegerField()
    info_alerts = serializers.IntegerField()


class ComponentAlertSerializer(serializers.Serializer):
    """Serializer for component alert counts"""
    
    source_component = serializers.CharField()
    count = serializers.IntegerField()


class DashboardDataSerializer(serializers.Serializer):
    """Serializer for dashboard data"""
    
    overall_status = serializers.CharField()
    last_updated = serializers.DateTimeField()
    components = serializers.DictField()
    active_alerts = AlertNotificationSerializer(many=True)
    alert_counts = serializers.DictField()


class MetricsSerializer(serializers.Serializer):
    """Serializer for system metrics"""
    
    metrics = serializers.DictField()
    timestamp = serializers.DateTimeField()


class HealthCheckRequestSerializer(serializers.Serializer):
    """Serializer for health check requests"""
    
    component = serializers.ChoiceField(choices=[
        SystemHealth.COMPONENT_DATABASE,
        SystemHealth.COMPONENT_REDIS,
        SystemHealth.COMPONENT_API,
        SystemHealth.COMPONENT_CELERY,
        SystemHealth.COMPONENT_DISK,
        SystemHealth.COMPONENT_MEMORY,
        SystemHealth.COMPONENT_CPU,
    ])


class BackupRequestSerializer(serializers.Serializer):
    """Serializer for backup creation requests"""
    
    backup_type = serializers.ChoiceField(
        choices=['full', 'incremental', 'manual'],
        default='full'
    )
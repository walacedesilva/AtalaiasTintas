"""
Monitoring models for system health tracking and alerting
User Story 2: Data Integrity and Backup
Tasks: T034-T037 - Monitoring models implementation
"""

from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.core.validators import MinValueValidator, MaxValueValidator
import json

User = get_user_model()


class TimeStampedModel(models.Model):
    """Base model with automatic timestamps"""
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        abstract = True


class SystemHealth(TimeStampedModel):
    """
    Model to track system health metrics and performance indicators
    Task: T034 - SystemHealth model for health metrics
    """
    
    # Health status levels
    STATUS_HEALTHY = 'HEALTHY'
    STATUS_WARNING = 'WARNING'
    STATUS_CRITICAL = 'CRITICAL'
    STATUS_DOWN = 'DOWN'
    
    STATUS_CHOICES = [
        (STATUS_HEALTHY, 'Healthy'),
        (STATUS_WARNING, 'Warning'),
        (STATUS_CRITICAL, 'Critical'),
        (STATUS_DOWN, 'Down'),
    ]
    
    # System component types
    COMPONENT_DATABASE = 'DATABASE'
    COMPONENT_REDIS = 'REDIS'
    COMPONENT_API = 'API'
    COMPONENT_CELERY = 'CELERY'
    COMPONENT_DISK = 'DISK'
    COMPONENT_MEMORY = 'MEMORY'
    COMPONENT_CPU = 'CPU'
    COMPONENT_EXTERNAL_API = 'EXTERNAL_API'
    
    COMPONENT_CHOICES = [
        (COMPONENT_DATABASE, 'Database'),
        (COMPONENT_REDIS, 'Redis Cache'),
        (COMPONENT_API, 'API Services'),
        (COMPONENT_CELERY, 'Background Tasks'),
        (COMPONENT_DISK, 'Disk Storage'),
        (COMPONENT_MEMORY, 'Memory Usage'),
        (COMPONENT_CPU, 'CPU Usage'),
        (COMPONENT_EXTERNAL_API, 'External APIs'),
    ]
    
    # Core fields
    component = models.CharField(
        max_length=50,
        choices=COMPONENT_CHOICES,
        help_text="System component being monitored"
    )
    
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        help_text="Current health status"
    )
    
    # Performance metrics
    response_time = models.FloatField(
        null=True, blank=True,
        validators=[MinValueValidator(0.0)],
        help_text="Response time in milliseconds"
    )
    
    cpu_usage = models.FloatField(
        null=True, blank=True,
        validators=[MinValueValidator(0.0), MaxValueValidator(100.0)],
        help_text="CPU usage percentage"
    )
    
    memory_usage = models.FloatField(
        null=True, blank=True,
        validators=[MinValueValidator(0.0), MaxValueValidator(100.0)],
        help_text="Memory usage percentage"
    )
    
    disk_usage = models.FloatField(
        null=True, blank=True,
        validators=[MinValueValidator(0.0), MaxValueValidator(100.0)],
        help_text="Disk usage percentage"
    )
    
    # Connection metrics
    active_connections = models.IntegerField(
        null=True, blank=True,
        validators=[MinValueValidator(0)],
        help_text="Number of active connections"
    )
    
    queue_size = models.IntegerField(
        null=True, blank=True,
        validators=[MinValueValidator(0)],
        help_text="Queue size for background tasks"
    )
    
    # Error tracking
    error_count = models.IntegerField(
        default=0,
        validators=[MinValueValidator(0)],
        help_text="Number of errors in this check interval"
    )
    
    error_message = models.TextField(
        null=True, blank=True,
        help_text="Last error message if any"
    )
    
    # Additional metadata
    check_timestamp = models.DateTimeField(
        default=timezone.now,
        help_text="When this health check was performed"
    )
    
    additional_data = models.JSONField(
        null=True, blank=True,
        help_text="Additional metrics and metadata"
    )
    
    class Meta:
        ordering = ['-check_timestamp']
        indexes = [
            models.Index(fields=['component', 'check_timestamp']),
            models.Index(fields=['status', 'check_timestamp']),
            models.Index(fields=['check_timestamp']),
        ]
        verbose_name = 'Health Check'
        verbose_name_plural = 'Health Checks'
    
    def __str__(self):
        return f"{self.get_component_display()} - {self.get_status_display()} ({self.check_timestamp})"
    
    @property
    def is_healthy(self):
        """Check if component is healthy"""
        return self.status == self.STATUS_HEALTHY
    
    @property
    def needs_attention(self):
        """Check if component needs attention"""
        return self.status in [self.STATUS_WARNING, self.STATUS_CRITICAL]
    
    @classmethod
    def get_current_status(cls, component):
        """Get the latest health status for a component"""
        return cls.objects.filter(component=component).first()
    
    @classmethod
    def get_system_overview(cls):
        """Get overview of all system components"""
        components = {}
        for component_code, component_name in cls.COMPONENT_CHOICES:
            latest_check = cls.get_current_status(component_code)
            components[component_code] = {
                'name': component_name,
                'status': latest_check.status if latest_check else 'UNKNOWN',
                'last_check': latest_check.check_timestamp if latest_check else None
            }
        return components


class AlertNotification(TimeStampedModel):
    """
    Model to track system alerts and notifications
    Task: T035 - AlertNotification model for alert tracking
    """
    
    # Alert severity levels
    SEVERITY_INFO = 'INFO'
    SEVERITY_WARNING = 'WARNING'
    SEVERITY_ERROR = 'ERROR'
    SEVERITY_CRITICAL = 'CRITICAL'
    
    SEVERITY_CHOICES = [
        (SEVERITY_INFO, 'Information'),
        (SEVERITY_WARNING, 'Warning'),
        (SEVERITY_ERROR, 'Error'),
        (SEVERITY_CRITICAL, 'Critical'),
    ]
    
    # Alert types
    TYPE_SYSTEM_HEALTH = 'SYSTEM_HEALTH'
    TYPE_BACKUP_FAILURE = 'BACKUP_FAILURE'
    TYPE_SECURITY_ALERT = 'SECURITY_ALERT'
    TYPE_PERFORMANCE = 'PERFORMANCE'
    TYPE_DISK_SPACE = 'DISK_SPACE'
    TYPE_DATABASE_ERROR = 'DATABASE_ERROR'
    TYPE_API_ERROR = 'API_ERROR'
    
    TYPE_CHOICES = [
        (TYPE_SYSTEM_HEALTH, 'System Health'),
        (TYPE_BACKUP_FAILURE, 'Backup Failure'),
        (TYPE_SECURITY_ALERT, 'Security Alert'),
        (TYPE_PERFORMANCE, 'Performance Issue'),
        (TYPE_DISK_SPACE, 'Disk Space'),
        (TYPE_DATABASE_ERROR, 'Database Error'),
        (TYPE_API_ERROR, 'API Error'),
    ]
    
    # Alert status
    STATUS_ACTIVE = 'ACTIVE'
    STATUS_ACKNOWLEDGED = 'ACKNOWLEDGED'
    STATUS_RESOLVED = 'RESOLVED'
    STATUS_SUPPRESSED = 'SUPPRESSED'
    
    STATUS_CHOICES = [
        (STATUS_ACTIVE, 'Active'), 
        (STATUS_ACKNOWLEDGED, 'Acknowledged'),
        (STATUS_RESOLVED, 'Resolved'),
        (STATUS_SUPPRESSED, 'Suppressed'),
    ]
    
    # Core fields
    title = models.CharField(
        max_length=200,
        help_text="Brief alert title"
    )
    
    message = models.TextField(
        help_text="Detailed alert message"
    )
    
    alert_type = models.CharField(
        max_length=50,
        choices=TYPE_CHOICES,
        help_text="Type of alert"
    )
    
    severity = models.CharField(
        max_length=20,
        choices=SEVERITY_CHOICES,
        help_text="Alert severity level"
    )
    
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default=STATUS_ACTIVE,
        help_text="Current alert status"
    )
    
    # Related objects
    health_check = models.ForeignKey(
        SystemHealth,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='alerts',
        help_text="Related health check if applicable"
    )
    
    affected_user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='alerts_received',
        help_text="User affected by this alert"
    )
    
    # Alert management
    acknowledged_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='alerts_acknowledged',
        help_text="User who acknowledged the alert"
    )
    
    acknowledged_at = models.DateTimeField(
        null=True, blank=True,
        help_text="When the alert was acknowledged"
    )
    
    resolved_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='alerts_resolved',
        help_text="User who resolved the alert"
    )
    
    resolved_at = models.DateTimeField(
        null=True, blank=True,
        help_text="When the alert was resolved"
    )
    
    resolution_notes = models.TextField(
        null=True, blank=True,
        help_text="Notes about how the alert was resolved"
    )
    
    # Metadata
    source_component = models.CharField(
        max_length=100,
        null=True, blank=True,
        help_text="System component that generated this alert"
    )
    
    metadata = models.JSONField(
        null=True, blank=True,
        help_text="Additional alert metadata"
    )
    
    # Notification flags
    email_sent = models.BooleanField(
        default=False,
        help_text="Whether email notification was sent"
    )
    
    sms_sent = models.BooleanField(
        default=False,
        help_text="Whether SMS notification was sent"
    )
    
    push_sent = models.BooleanField(
        default=False,
        help_text="Whether push notification was sent"
    )
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['alert_type', 'created_at']),
            models.Index(fields=['severity', 'status']),
            models.Index(fields=['status', 'created_at']),
            models.Index(fields=['affected_user', 'status']),
        ]
        verbose_name = 'Alert Notification'
        verbose_name_plural = 'Alert Notifications'
    
    def __str__(self):
        return f"{self.get_severity_display()}: {self.title}"
    
    def acknowledge(self, user, notes=None):
        """Acknowledge this alert"""
        self.status = self.STATUS_ACKNOWLEDGED
        self.acknowledged_by = user
        self.acknowledged_at = timezone.now()
        if notes:
            self.resolution_notes = notes
        self.save(update_fields=[
            'status', 'acknowledged_by', 'acknowledged_at', 'resolution_notes'
        ])
    
    def resolve(self, user, notes=None):
        """Resolve this alert"""
        self.status = self.STATUS_RESOLVED
        self.resolved_by = user
        self.resolved_at = timezone.now()
        if notes:
            self.resolution_notes = notes
        self.save(update_fields=[
            'status', 'resolved_by', 'resolved_at', 'resolution_notes'
        ])
    
    @property
    def is_active(self):
        """Check if alert is still active"""
        return self.status == self.STATUS_ACTIVE
    
    @property
    def age(self):
        """Get alert age as timedelta"""
        return timezone.now() - self.created_at
    
    @classmethod
    def create_alert(cls, title, message, alert_type, severity, **kwargs):
        """Helper method to create new alerts"""
        return cls.objects.create(
            title=title,
            message=message,
            alert_type=alert_type,
            severity=severity,
            **kwargs
        )
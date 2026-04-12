# Data Model: Sistema Core de Infraestrutura

**Date**: 2026-04-11
**Phase**: 1 - Data Architecture
**Feature**: 2-core-infrastructure

## Entity Relationship Overview

```
User ──┐
       │
       ├── UserProfile (1:1)
       │
       ├── UserSession (1:M) 
       │
       └── AuditLog (1:M)

SystemHealth ──┐
               │
               └── AlertNotification (1:M)

Configuration (Global System Settings)
BackupRecord (Audit Trail)
```

## Core Entities

### User
**Purpose**: Central authentication and authorization entity
**Business Rules**: 
- Username must be unique across system
- Password must meet complexity requirements (8+ chars, mixed case, numbers)
- Inactive users cannot authenticate but data is preserved for audit

```python
class User(AbstractUser):
    """Custom user model extending Django's AbstractUser"""
    
    # Standard AbstractUser fields: username, email, first_name, last_name, 
    # is_active, is_staff, is_superuser, date_joined, last_login
    
    # Additional fields for business requirements
    employee_id = models.CharField(max_length=20, unique=True, null=True, blank=True)
    phone_number = models.CharField(max_length=15, blank=True)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)
    last_password_change = models.DateTimeField(auto_now_add=True)
    failed_login_attempts = models.PositiveIntegerField(default=0)
    account_locked_until = models.DateTimeField(null=True, blank=True)
    created_by = models.ForeignKey('self', null=True, blank=True, on_delete=models.SET_NULL)
    
    # Audit fields
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

# Role Constants
ROLE_CHOICES = [
    ('ADMIN', 'Administrador'),      # config + reports
    ('VENDOR', 'Vendedor'),          # sales + customers  
    ('OPERATOR', 'Operador'),        # inventory + products
]
```

**Relationships**:
- One-to-one with UserProfile (extended information)
- One-to-many with UserSession (active sessions)
- One-to-many with AuditLog (user actions)

**State Transitions**:
- `Active` → `Inactive` (admin disable)
- `Unlocked` → `Locked` (failed login attempts)
- `Locked` → `Unlocked` (time-based or admin unlock)

### UserProfile  
**Purpose**: Extended user information and preferences
**Business Rules**:
- Profile is created automatically when user is created
- Timezone affects timestamp display throughout application

```python
class UserProfile(models.Model):
    """Extended user information and preferences"""
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    
    # Contact information
    alternate_email = models.EmailField(blank=True)
    emergency_contact_name = models.CharField(max_length=100, blank=True)
    emergency_contact_phone = models.CharField(max_length=15, blank=True)
    
    # System preferences  
    timezone = models.CharField(max_length=50, default='America/Sao_Paulo')
    language = models.CharField(max_length=5, default='pt-BR')
    email_notifications = models.BooleanField(default=True)
    sms_notifications = models.BooleanField(default=False)
    
    # Session preferences
    session_timeout_minutes = models.PositiveIntegerField(default=480)  # 8 hours
    
    # Audit fields
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
```

### UserSession
**Purpose**: Active user sessions for security and monitoring
**Business Rules**:
- Sessions expire after configured timeout (default 8 hours)
- Multiple sessions per user allowed but tracked for security
- Session data includes IP and user agent for fraud detection

```python
class UserSession(models.Model):
    """Active user sessions for security tracking"""
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sessions')
    session_key = models.CharField(max_length=40, unique=True)
    
    # Security tracking
    ip_address = models.GenericIPAddressField()
    user_agent = models.TextField()
    
    # Session lifecycle
    created_at = models.DateTimeField(auto_now_add=True)
    last_activity = models.DateTimeField(auto_now=True)
    expires_at = models.DateTimeField()
    is_active = models.BooleanField(default=True)
    
    # Logout tracking
    logged_out_at = models.DateTimeField(null=True, blank=True)
    logout_reason = models.CharField(max_length=50, choices=[
        ('USER', 'User Logout'),
        ('TIMEOUT', 'Session Timeout'),
        ('ADMIN', 'Admin Termination'),
        ('SECURITY', 'Security Policy')
    ], null=True, blank=True)
```

### AuditLog
**Purpose**: Immutable record of all user actions for compliance and troubleshooting
**Business Rules**:
- Records are never deleted, only marked as archived
- All sensitive operations must generate audit entries
- Includes before/after state for data modifications

```python
class AuditLog(models.Model):
    """Immutable audit trail of user actions"""
    
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='audit_logs')
    session = models.ForeignKey(UserSession, on_delete=models.SET_NULL, null=True)
    
    # Action details
    action = models.CharField(max_length=50)  # CREATE, UPDATE, DELETE, LOGIN, etc.
    resource_type = models.CharField(max_length=50)  # User, Product, Sale, etc.
    resource_id = models.CharField(max_length=50, null=True)
    description = models.TextField()
    
    # Change tracking (JSON fields for flexibility)
    before_state = models.JSONField(null=True, blank=True)
    after_state = models.JSONField(null=True, blank=True)
    
    # Request context
    ip_address = models.GenericIPAddressField()
    user_agent = models.TextField(blank=True)
    request_path = models.CharField(max_length=255, blank=True)
    
    # Timestamp (immutable)
    timestamp = models.DateTimeField(auto_now_add=True)
    
    # Success/failure tracking
    success = models.BooleanField(default=True)
    error_message = models.TextField(blank=True)
```

### SystemHealth
**Purpose**: Current system health metrics and status
**Business Rules**:
- Health checks run every 60 seconds via Celery task
- Metrics older than 24 hours are archived
- System is considered unhealthy if any critical metric exceeds threshold

```python
class SystemHealth(models.Model):
    """Current system health metrics"""
    
    # System identification
    hostname = models.CharField(max_length=255)
    component = models.CharField(max_length=50, choices=[
        ('WEB', 'Web Application'),
        ('DATABASE', 'Database'),
        ('CACHE', 'Redis Cache'),  
        ('STORAGE', 'File System'),
        ('NETWORK', 'Network Connectivity')
    ])
    
    # Health metrics
    status = models.CharField(max_length=20, choices=[
        ('HEALTHY', 'Healthy'),
        ('WARNING', 'Warning'),
        ('CRITICAL', 'Critical'),
        ('UNKNOWN', 'Unknown')
    ], default='UNKNOWN')
    
    # Detailed metrics (JSON for flexibility)
    metrics = models.JSONField(default=dict)  # {cpu: 45.2, memory: 67.8, response_time: 150}
    
    # Health check metadata
    checked_at = models.DateTimeField(auto_now_add=True)
    response_time_ms = models.PositiveIntegerField(null=True)  # Health check duration
    error_message = models.TextField(blank=True)
    
    class Meta:
        indexes = [
            models.Index(fields=['hostname', 'component', '-checked_at']),
            models.Index(fields=['status', '-checked_at']),
        ]
```

### AlertNotification
**Purpose**: Record of sent alerts and notification delivery status
**Business Rules**:
- Alerts are rate-limited to prevent spam (max 1 per metric per 15 minutes)
- Failed alerts are retried up to 3 times with exponential backoff
- Critical alerts are sent via multiple channels (email + SMS)

```python
class AlertNotification(models.Model):
    """Alert notifications sent to administrators"""
    
    health_check = models.ForeignKey(SystemHealth, on_delete=models.CASCADE, related_name='alerts')
    
    # Alert details
    alert_type = models.CharField(max_length=20, choices=[
        ('EMAIL', 'Email'),
        ('SMS', 'SMS'),
        ('WEBHOOK', 'Webhook')
    ])
    recipient = models.CharField(max_length=255)  # email or phone number
    subject = models.CharField(max_length=255)
    message = models.TextField()
    
    # Delivery tracking
    sent_at = models.DateTimeField(auto_now_add=True)
    delivered = models.BooleanField(default=False)
    delivery_attempts = models.PositiveIntegerField(default=0)
    last_attempt_at = models.DateTimeField(null=True, blank=True)
    error_message = models.TextField(blank=True)
```

### Configuration
**Purpose**: System-wide configuration parameters
**Business Rules**:
- Configuration changes require admin role
- All changes are logged in audit trail
- Changes take effect immediately (no restart required)

```python
class Configuration(models.Model):
    """System-wide configuration parameters"""
    
    key = models.CharField(max_length=100, unique=True)
    value = models.TextField()
    data_type = models.CharField(max_length=20, choices=[
        ('STRING', 'String'),
        ('INTEGER', 'Integer'), 
        ('FLOAT', 'Float'),
        ('BOOLEAN', 'Boolean'),
        ('JSON', 'JSON Object')
    ], default='STRING')
    
    description = models.TextField()
    category = models.CharField(max_length=50)  # SECURITY, MONITORING, BACKUP, etc.
    
    # Change tracking
    modified_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    modified_at = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)
```

### BackupRecord
**Purpose**: Audit trail of backup operations
**Business Rules**:
- Records are created for both successful and failed backups
- Backup files are verified with checksums
- Retention policy automatically deletes records older than 90 days

```python
class BackupRecord(models.Model):
    """Audit trail of backup operations"""
    
    # Backup identification
    backup_type = models.CharField(max_length=20, choices=[
        ('FULL', 'Full Database Backup'),
        ('INCREMENTAL', 'Incremental Backup'),
        ('WAL', 'WAL Archive')
    ])
    file_path = models.TextField()
    file_size_bytes = models.BigIntegerField(null=True)
    checksum_md5 = models.CharField(max_length=32, blank=True)
    
    # Backup execution
    started_at = models.DateTimeField()
    completed_at = models.DateTimeField(null=True, blank=True)
    success = models.BooleanField(default=False)
    error_message = models.TextField(blank=True)
    
    # Retention management
    expires_at = models.DateTimeField()  # Auto-calculated: started_at + 90 days
    deleted_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        indexes = [
            models.Index(fields=['-started_at']),
            models.Index(fields=['expires_at']),
            models.Index(fields=['success', '-started_at']),
        ]
```

## Database Constraints & Indexes

### Performance Indexes
- `User.username` - Unique index (authentication queries)
- `User.employee_id` - Unique index where not null
- `UserSession.session_key` - Unique index (session lookup)
- `UserSession.user_id, is_active` - Composite index (active sessions per user)
- `AuditLog.user_id, timestamp` - Composite index (user activity history)
- `SystemHealth.hostname, component, checked_at` - Composite index (latest health per component)

### Data Integrity Constraints
- User passwords must be hashed (enforced in model save method)
- Session expires_at must be > created_at
- AuditLog timestamp is immutable (database-level constraint)
- BackupRecord expires_at auto-calculated via trigger

### Validation Rules
- User.phone_number: Regex validation for Brazilian format
- UserProfile.timezone: Must be valid timezone from pytz
- SystemHealth.metrics: JSON schema validation for required fields
- Configuration.value: Type validation based on data_type field
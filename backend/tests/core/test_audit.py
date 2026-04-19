"""
Test suite for T007 Audit Logging Infrastructure

Validates audit logging system functionality including:
- Audit log creation for permission changes
- Django signals integration
- Cryptographic integrity validation
- Performance requirements
- Request context preservation

Author: GitHub Copilot
Created: 2026-04-18
Task: T007 - Audit Logging Infrastructure
"""

from django.test import TestCase, RequestFactory
from django.contrib.auth import get_user_model
from django.utils import timezone
from unittest.mock import patch, Mock
import json

from apps.core.models import (
    Permission, UserGroup, UserPermission, GroupPermission, 
    GroupMembership, PermissionAuditLog
)
from apps.core.audit import (
    AuditLogger, AuditQuerySet, audit_logger, 
    log_permission_grant, log_permission_revoke, log_group_assignment,
    log_security_violation, log_access_attempt, get_audit_logs
)
from apps.core.signals import (
    set_current_request, get_current_request, extract_request_info,
    disable_audit, enable_audit, is_audit_enabled
)

User = get_user_model()


class AuditLoggerTest(TestCase):
    """Test core audit logging functionality."""
    
    def setUp(self):
        """Set up test data for audit logging tests."""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        self.admin_user = User.objects.create_superuser(
            username='admin',
            email='admin@example.com',
            password='adminpass123'
        )
        
        self.permission = Permission.objects.create(
            module='test',
            resource='sample',
            action='view',
            name='Test Permission',
            description='Permission for testing'
        )
        
        self.group = UserGroup.objects.create(
            name='Test Group',
            description='Group for testing'
        )
        
        self.factory = RequestFactory()
        
        # Ensure audit is enabled for tests
        enable_audit()
    
    def test_audit_logger_initialization(self):
        """Test audit logger initializes with correct settings."""
        logger = AuditLogger()
        
        self.assertTrue(logger.enabled)
        self.assertEqual(logger.batch_size, 100)
        self.assertEqual(logger.cache_timeout, 300)
        
    def test_log_permission_change_basic(self):
        """Test basic audit log creation."""
        # Create a test request
        request = self.factory.get('/test/')
        request.user = self.admin_user
        set_current_request(request)
        
        # Log a permission change
        audit_log = audit_logger.log_permission_change(
            action='GRANT',
            entity_type='user',
            entity_id=str(self.user.id),
            user=self.admin_user,
            permission=self.permission,
            details={'test_detail': 'test_value'}
        )
        
        # Verify audit log was created
        self.assertIsNotNone(audit_log)
        self.assertEqual(audit_log.action, 'GRANT')
        self.assertEqual(audit_log.entity_type, 'user')
        self.assertEqual(audit_log.entity_id, str(self.user.id))
        self.assertEqual(audit_log.user, self.admin_user)
        self.assertEqual(audit_log.permission, self.permission)
        self.assertIn('test_detail', audit_log.details)
        
        # Clean up
        set_current_request(None)
    
    def test_audit_logger_with_request_context(self):
        """Test audit logging captures request context correctly."""
        # Create a test request with context
        request = self.factory.post('/api/permissions/', 
                                   HTTP_USER_AGENT='Test Agent',
                                   REMOTE_ADDR='192.168.1.1')
        request.user = self.admin_user
        set_current_request(request)
        
        # Log with request context
        audit_log = audit_logger.log_permission_change(
            action='GRANT',
            entity_type='user',
            entity_id=str(self.user.id),
            user=self.admin_user,
            request_info=extract_request_info(request)
        )
        
        # Verify request context was captured
        self.assertIsNotNone(audit_log)
        self.assertIn('request', audit_log.details)
        self.assertEqual(audit_log.details['request']['ip_address'], '192.168.1.1')
        self.assertEqual(audit_log.details['request']['user_agent'], 'Test Agent')
        self.assertEqual(audit_log.details['request']['method'], 'POST')
        self.assertEqual(audit_log.details['request']['path'], '/api/permissions/')
        
        # Clean up
        set_current_request(None)
    
    def test_audit_logger_integrity_hashing(self):
        """Test cryptographic integrity validation."""
        # Create audit log with integrity checking
        audit_log = audit_logger.log_permission_change(
            action='GRANT',
            entity_type='user',
            entity_id=str(self.user.id),
            user=self.admin_user,
            permission=self.permission
        )
        
        # Verify integrity hash was generated
        self.assertIsNotNone(audit_log)
        self.assertIsNotNone(audit_log.integrity_hash)
        self.assertEqual(len(audit_log.integrity_hash), 64)  # SHA-256 hex length
        
        # Test hash verification
        verification_report = audit_logger.verify_integrity_chain(limit=10)
        self.assertEqual(verification_report['status'], 'success')
        self.assertEqual(verification_report['verified_entries'], 1)
        self.assertEqual(len(verification_report['integrity_violations']), 0)
    
    def test_audit_logger_performance_requirements(self):
        """Test audit logging meets performance requirements."""
        import time
        
        # Test single log performance (should be < 100ms per requirement)
        start_time = time.time()
        
        audit_log = audit_logger.log_permission_change(
            action='ACCESS_ATTEMPT',
            entity_type='permission',
            entity_id=str(self.permission.id),
            user=self.user,
            permission=self.permission
        )
        
        end_time = time.time()
        duration = (end_time - start_time) * 1000  # Convert to milliseconds
        
        # Verify performance requirement
        self.assertLess(duration, 100)  # Must be under 100ms
        self.assertIsNotNone(audit_log)
    
    def test_audit_logger_failure_handling(self):
        """Test audit logger handles failures gracefully."""
        # Mock raised exception during audit creation
        with patch('apps.core.audit.PermissionAuditLog.objects.create') as mock_create:
            mock_create.side_effect = Exception("Database error")
            
            # Should not raise exception, but return None
            result = audit_logger.log_permission_change(
                action='GRANT',
                entity_type='user',
                entity_id=str(self.user.id),
                user=self.admin_user
            )
            
            self.assertIsNone(result)


class AuditSignalsTest(TestCase):
    """Test Django signals for automatic audit logging."""
    
    def setUp(self):
        """Set up test data for signal tests."""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        self.admin_user = User.objects.create_superuser(
            username='admin',
            email='admin@example.com',
            password='adminpass123'
        )
        
        self.permission = Permission.objects.create(
            module='test',
            resource='sample',
            action='view',
            name='Test Permission'
        )
        
        self.group = UserGroup.objects.create(
            name='Test Group'
        )
        
        # Set up request context
        factory = RequestFactory()
        request = factory.get('/test/')
        request.user = self.admin_user
        set_current_request(request)
        
        # Ensure audit is enabled
        enable_audit()
    
    def tearDown(self):
        """Clean up after signal tests."""
        set_current_request(None)
    
    def test_user_permission_creation_signal(self):
        """Test that creating UserPermission triggers audit log."""
        initial_count = PermissionAuditLog.objects.count()
        
        # Create user permission (should trigger signal)
        user_permission = UserPermission.objects.create(
            user=self.user,
            permission=self.permission,
            grant_type='ALLOW',
            approved_by=self.admin_user
        )
        
        # Verify audit log was created
        final_count = PermissionAuditLog.objects.count()
        self.assertEqual(final_count, initial_count + 1)
        
        # Check audit log details
        audit_log = PermissionAuditLog.objects.latest('timestamp')
        self.assertEqual(audit_log.action, 'GRANT')
        self.assertEqual(audit_log.entity_type, 'user_permission')
        self.assertEqual(audit_log.entity_id, str(user_permission.id))
        self.assertEqual(audit_log.user, self.admin_user)
        self.assertEqual(audit_log.permission, self.permission)
    
    def test_group_membership_creation_signal(self):
        """Test that creating GroupMembership triggers audit log."""
        initial_count = PermissionAuditLog.objects.count()
        
        # Create group membership (should trigger signal)
        membership = GroupMembership.objects.create(
            user=self.user,
            group=self.group,
            role='member',
            is_primary=True
        )
        
        # Verify audit log was created
        final_count = PermissionAuditLog.objects.count()
        self.assertEqual(final_count, initial_count + 1)
        
        # Check audit log details
        audit_log = PermissionAuditLog.objects.latest('timestamp')
        self.assertEqual(audit_log.action, 'GRANT')
        self.assertEqual(audit_log.entity_type, 'group_membership')
        self.assertEqual(audit_log.entity_id, f"{self.user.id}:{self.group.id}")
    
    def test_audit_disable_functionality(self):
        """Test that audit can be disabled temporarily."""
        # Disable audit
        disable_audit()
        self.assertFalse(is_audit_enabled())
        
        initial_count = PermissionAuditLog.objects.count()
        
        # Create user permission (should NOT trigger audit)
        UserPermission.objects.create(
            user=self.user,
            permission=self.permission,
            grant_type='ALLOW'
        )
        
        # Verify no audit log was created
        final_count = PermissionAuditLog.objects.count()
        self.assertEqual(final_count, initial_count)
        
        # Re-enable audit
        enable_audit()
        self.assertTrue(is_audit_enabled())


class AuditQuerySetTest(TestCase):
    """Test audit log querying and filtering functionality."""
    
    def setUp(self):
        """Set up test audit logs for querying tests."""
        self.user1 = User.objects.create_user(username='user1', password='pass123')
        self.user2 = User.objects.create_user(username='user2', password='pass123')
        self.admin = User.objects.create_superuser(username='admin', password='admin123')
        
        self.permission = Permission.objects.create(
            module='test',
            resource='sample', 
            action='view',
            name='Test Permission'
        )
        
        # Create test audit logs
        self.audit_log1 = PermissionAuditLog.objects.create(
            action='GRANT',
            entity_type='user',
            entity_id=str(self.user1.id),
            user=self.admin,
            permission=self.permission,
            details={'test': 'data1'}
        )
        
        self.audit_log2 = PermissionAuditLog.objects.create(
            action='REVOKE',
            entity_type='user',
            entity_id=str(self.user2.id),
            user=self.admin,
            permission=self.permission,
            details={'test': 'data2'}
        )
        
        self.audit_log3 = PermissionAuditLog.objects.create(
            action='SECURITY_VIOLATION',
            entity_type='authentication',
            entity_id='failed_login',
            user=None,
            details={'violation': 'brute_force'}
        )
    
    def test_audit_queryset_for_user(self):
        """Test filtering audit logs for specific user."""
        queryset = get_audit_logs().for_user(self.admin)
        logs = list(queryset.queryset)
        
        self.assertEqual(len(logs), 2)  # Only logs by admin
        for log in logs:
            self.assertEqual(log.user, self.admin)
    
    def test_audit_queryset_for_entity(self):
        """Test filtering audit logs for specific entity."""
        queryset = get_audit_logs().for_entity('user', str(self.user1.id))
        logs = list(queryset.queryset)
        
        self.assertEqual(len(logs), 1)
        self.assertEqual(logs[0].entity_id, str(self.user1.id))
    
    def test_audit_queryset_by_action(self):
        """Test filtering audit logs by action type."""
        queryset = get_audit_logs().by_action('GRANT')
        logs = list(queryset.queryset)
        
        self.assertEqual(len(logs), 1)
        self.assertEqual(logs[0].action, 'GRANT')
    
    def test_audit_queryset_security_events(self):
        """Test filtering for security-related events."""
        queryset = get_audit_logs().security_events()
        logs = list(queryset.queryset)
        
        self.assertEqual(len(logs), 1)
        self.assertEqual(logs[0].action, 'SECURITY_VIOLATION')
    
    def test_audit_queryset_permission_changes(self):
        """Test filtering for permission-related changes."""
        queryset = get_audit_logs().permission_changes()
        logs = list(queryset.queryset)
        
        # Should include GRANT and REVOKE actions
        self.assertEqual(len(logs), 2)
        actions = [log.action for log in logs]
        self.assertIn('GRANT', actions)
        self.assertIn('REVOKE', actions)
    
    def test_audit_queryset_aggregate_by_action(self):
        """Test action aggregation functionality."""
        queryset = get_audit_logs()
        aggregated = queryset.aggregate_by_action()
        
        self.assertEqual(aggregated['GRANT'], 1)
        self.assertEqual(aggregated['REVOKE'], 1)
        self.assertEqual(aggregated['SECURITY_VIOLATION'], 1)
    
    def test_audit_queryset_summary(self):
        """Test comprehensive summary functionality."""
        queryset = get_audit_logs()
        summary = queryset.get_summary()
        
        self.assertEqual(summary['total_entries'], 3)
        self.assertIn('date_range', summary)
        self.assertIn('action_distribution', summary)
        self.assertEqual(summary['action_distribution']['GRANT'], 1)
        self.assertEqual(summary['action_distribution']['REVOKE'], 1)
        self.assertEqual(summary['action_distribution']['SECURITY_VIOLATION'], 1)


class AuditConvenienceFunctionsTest(TestCase):
    """Test convenience functions for common audit operations."""
    
    def setUp(self):
        """Set up test data for convenience function tests."""
        self.user = User.objects.create_user(username='testuser', password='pass123')
        self.admin = User.objects.create_superuser(username='admin', password='admin123')
        
        self.permission = Permission.objects.create(
            module='test',
            resource='sample',
            action='view',
            name='Test Permission'
        )
        
        self.group = UserGroup.objects.create(name='Test Group')
        
        # Set up request context
        factory = RequestFactory()
        request = factory.get('/test/')
        request.user = self.admin
        set_current_request(request)
    
    def tearDown(self):
        """Clean up after convenience function tests."""
        set_current_request(None)
    
    def test_log_permission_grant_function(self):
        """Test log_permission_grant convenience function."""
        audit_log = log_permission_grant(
            user=self.admin,
            permission=self.permission,
            target_user=self.user
        )
        
        self.assertIsNotNone(audit_log)
        self.assertEqual(audit_log.action, 'GRANT')
        self.assertEqual(audit_log.user, self.admin)
        self.assertEqual(audit_log.permission, self.permission)
        self.assertEqual(audit_log.entity_id, str(self.user.id))
    
    def test_log_permission_revoke_function(self):
        """Test log_permission_revoke convenience function."""
        audit_log = log_permission_revoke(
            user=self.admin,
            permission=self.permission,
            target_user=self.user
        )
        
        self.assertIsNotNone(audit_log)
        self.assertEqual(audit_log.action, 'REVOKE')
        self.assertEqual(audit_log.user, self.admin)
        self.assertEqual(audit_log.permission, self.permission)
    
    def test_log_group_assignment_function(self):
        """Test log_group_assignment convenience function."""
        audit_log = log_group_assignment(
            user=self.admin,
            group=self.group,
            target_user=self.user
        )
        
        self.assertIsNotNone(audit_log)
        self.assertEqual(audit_log.action, 'GRANT')
        self.assertEqual(audit_log.entity_type, 'group_membership')
        self.assertEqual(audit_log.entity_id, f"{self.user.id}:{self.group.id}")
    
    def test_log_security_violation_function(self):
        """Test log_security_violation convenience function."""
        audit_log = log_security_violation(
            user=self.user,
            violation_type='unauthorized_access',
            details={'resource': 'admin_panel', 'ip': '192.168.1.100'}
        )
        
        self.assertIsNotNone(audit_log)
        self.assertEqual(audit_log.action, 'SECURITY_VIOLATION')
        self.assertEqual(audit_log.entity_id, 'unauthorized_access')
        self.assertIn('violation_type', audit_log.details)
    
    def test_log_access_attempt_function(self):
        """Test log_access_attempt convenience function."""
        audit_log = log_access_attempt(
            user=self.user,
            permission=self.permission,
            success=True
        )
        
        self.assertIsNotNone(audit_log)
        self.assertEqual(audit_log.action, 'ACCESS_ATTEMPT')
        self.assertEqual(audit_log.user, self.user)
        self.assertEqual(audit_log.permission, self.permission)
        self.assertTrue(audit_log.details['success'])


class AuditPerformanceTest(TestCase):
    """Test audit system performance under load."""
    
    def setUp(self):
        """Set up test data for performance tests."""
        self.user = User.objects.create_user(username='testuser', password='pass123')
        self.permission = Permission.objects.create(
            module='test',
            resource='sample',
            action='view',
            name='Test Permission'
        )
    
    def test_high_volume_audit_logging_performance(self):
        """Test audit logging performance with high volume."""
        import time
        
        start_time = time.time()
        
        # Log 50 audit entries (simulating high-frequency logging)
        for i in range(50):
            audit_logger.log_permission_change(
                action='ACCESS_ATTEMPT',
                entity_type='permission',
                entity_id=str(self.permission.id),
                user=self.user,
                permission=self.permission,
                details={'attempt': i}
            )
        
        end_time = time.time()
        total_duration = (end_time - start_time) * 1000  # Convert to milliseconds
        avg_per_log = total_duration / 50
        
        # Performance requirement: avg < 100ms per log
        self.assertLess(avg_per_log, 100)
        
        # Verify all logs were created
        audit_count = PermissionAuditLog.objects.filter(
            action='ACCESS_ATTEMPT',
            permission=self.permission
        ).count()
        self.assertEqual(audit_count, 50)
    
    def test_audit_query_performance(self):
        """Test audit log querying performance."""
        # Create test data
        for i in range(20):
            PermissionAuditLog.objects.create(
                action='GRANT' if i % 2 == 0 else 'REVOKE',
                entity_type='user',
                entity_id=str(self.user.id),
                user=self.user,
                permission=self.permission
            )
        
        import time
        
        # Test query performance
        start_time = time.time()
        
        queryset = get_audit_logs().for_user(self.user).permission_changes()
        results = list(queryset.queryset)
        
        end_time = time.time()
        query_duration = (end_time - start_time) * 1000  # Convert to milliseconds
        
        # Query should complete in under 50ms for 20 records
        self.assertLess(query_duration, 50)
        self.assertEqual(len(results), 20)
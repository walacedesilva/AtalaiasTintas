"""
Unit Tests for Model Managers - T006 Basic Unit Testing Framework

Tests the functionality of all custom managers for the permission system,
including permission checking logic, caching, and hierarchical operations.

Feature: 8-user-permissions-system
Task: T006 - Basic Unit Testing Framework (moved from T003)
Created: 2026-04-18
"""

from django.test import TestCase
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.utils import timezone
from datetime import timedelta
from unittest.mock import patch, MagicMock
from apps.core.models import (
    UserGroup, Permission, GroupMembership, 
    UserPermission, GroupPermission, PermissionAuditLog
)

User = get_user_model()


class CustomUserManagerTest(TestCase):
    """Test CustomUserManager methods"""

    def setUp(self):
        """Set up test data"""
        cache.clear()  # Clear cache for clean tests
        
        # Create test users
        self.admin_user = User.objects.create_user(
            username='admin',
            email='admin@test.com',
            password='testpass123',
            pode_administrar=True
        )
        
        self.regular_user = User.objects.create_user(
            username='regular',
            email='regular@test.com',
            password='testpass123'
        )
        
        # Create test permission
        self.permission = Permission.objects.create(
            module='tintometry',
            resource='formula',
            action='create',
            name='Create Formula',
            description='Permission to create tintometry formulas'
        )
        
        # Create test group
        self.test_group = UserGroup.objects.create(
            name='Test Group',
            description='Test group for unit tests',
            created_by=self.admin_user
        )

    def test_create_user(self):
        """Test user creation with CustomUserManager"""
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='securepass123'
        )
        
        self.assertEqual(user.username, 'testuser')
        self.assertEqual(user.email, 'test@example.com')
        self.assertTrue(user.check_password('securepass123'))
        self.assertFalse(user.is_superuser)

    def test_create_superuser(self):
        """Test superuser creation with CustomUserManager"""
        superuser = User.objects.create_superuser(
            username='superuser',
            email='super@example.com',
            password='superpass123'
        )
        
        self.assertEqual(superuser.username, 'superuser')
        self.assertTrue(superuser.is_superuser)
        self.assertTrue(superuser.is_staff)
        self.assertTrue(superuser.pode_administrar)

    def test_with_permission_queryset(self):
        """Test with_permission queryset method"""
        # Grant permission to user
        UserPermission.objects.create(
            user=self.regular_user,
            permission=self.permission,
            grant_type='allow',
            granted_by=self.admin_user,
            reason='Test permission grant'
        )
        
        # Test queryset
        users_with_permission = User.objects.with_permission('tintometry.formula.create')
        self.assertIn(self.regular_user, users_with_permission)
        self.assertNotIn(self.admin_user, users_with_permission)

    def test_with_group_queryset(self):
        """Test with_group queryset method"""
        # Add user to group
        GroupMembership.objects.create(
            user=self.regular_user,
            group=self.test_group,
            is_active=True,
            added_by=self.admin_user
        )
        
        # Test queryset
        users_in_group = User.objects.with_group('Test Group')
        self.assertIn(self.regular_user, users_in_group)
        self.assertNotIn(self.admin_user, users_in_group)

    def test_active_users_only(self):
        """Test filtering to active users only"""
        # Deactivate regular user
        self.regular_user.ativo = False
        self.regular_user.save()
        
        active_users = User.objects.active_users_only()
        self.assertNotIn(self.regular_user, active_users)
        self.assertIn(self.admin_user, active_users)

    def test_bulk_permission_grant(self):
        """Test bulk permission granting through manager"""
        users = [self.admin_user, self.regular_user]
        
        # Test bulk grant
        granted_count = User.objects.bulk_grant_permission(
            users=users,
            permission_code='tintometry.formula.create',
            granted_by=self.admin_user,
            reason='Bulk test grant'
        )
        
        self.assertEqual(granted_count, 2)
        
        # Verify permissions were granted
        for user in users:
            self.assertTrue(user.has_permission_new('tintometry.formula.create'))


class PermissionManagerTest(TestCase):
    """Test PermissionManager functionality"""
    
    def setUp(self):
        """Set up test data"""
        cache.clear()
        
        self.permission1 = Permission.objects.create(
            module='sales',
            resource='order',
            action='create',
            name='Create Order',
            description='Permission to create sales orders',
            is_active=True
        )
        
        self.permission2 = Permission.objects.create(
            module='sales',
            resource='order',
            action='view',
            name='View Order',
            description='Permission to view sales orders',
            is_active=True
        )
        
        self.inactive_permission = Permission.objects.create(
            module='sales',
            resource='order',
            action='delete',
            name='Delete Order',
            description='Permission to delete sales orders',
            is_active=False
        )
    
    def test_get_by_code(self):
        """Test getting permission by code"""
        permission = Permission.objects.get_by_code('sales.order.create')
        self.assertEqual(permission, self.permission1)
        
        # Test non-existent permission
        with self.assertRaises(Permission.DoesNotExist):
            Permission.objects.get_by_code('nonexistent.permission.code')
    
    def test_by_module(self):
        """Test filtering permissions by module"""
        sales_permissions = Permission.objects.by_module('sales')
        
        self.assertIn(self.permission1, sales_permissions)
        self.assertIn(self.permission2, sales_permissions)
        # Inactive permission should be excluded by default
        self.assertNotIn(self.inactive_permission, sales_permissions)
    
    def test_active_permissions_only(self):
        """Test filtering to active permissions only"""
        active_permissions = Permission.objects.active_permissions_only()
        
        self.assertIn(self.permission1, active_permissions)
        self.assertIn(self.permission2, active_permissions)
        self.assertNotIn(self.inactive_permission, active_permissions)
    
    def test_for_user_with_caching(self):
        """Test getting user permissions with caching"""
        user = User.objects.create_user(
            username='testuser',
            email='test@test.com',
            password='testpass123'
        )
        
        # Grant permission
        UserPermission.objects.create(
            user=user,
            permission=self.permission1,
            grant_type='allow'
        )
        
        with patch('django.core.cache.cache') as mock_cache:
            mock_cache.get.return_value = None  # Simulate cache miss
            
            permissions = Permission.objects.for_user(user, use_cache=True)
            
            # Should call cache.set
            mock_cache.set.assert_called_once()
            self.assertIn(self.permission1, permissions)
    
    def test_create_module_permissions(self):
        """Test bulk creation of module permissions"""
        actions = ['create', 'read', 'update', 'delete']
        
        created_permissions = Permission.objects.create_module_permissions(
            module='inventory',
            resource='product',
            actions=actions,
            created_by_username='admin'
        )
        
        self.assertEqual(len(created_permissions), 4)
        
        for action in actions:
            permission_exists = Permission.objects.filter(
                module='inventory',
                resource='product',
                action=action
            ).exists()
            self.assertTrue(permission_exists)


class UserGroupManagerTest(TestCase):
    """Test UserGroupManager functionality"""
    
    def setUp(self):
        """Set up test data"""
        self.admin_user = User.objects.create_user(
            username='admin',
            email='admin@test.com',
            password='testpass123'
        )
        
        self.parent_group = UserGroup.objects.create(
            name='Company',
            description='Root company group',
            created_by=self.admin_user
        )
        
        self.child_group = UserGroup.objects.create(
            name='Sales Department',
            description='Sales team',
            parent=self.parent_group,
            created_by=self.admin_user
        )
    
    def test_root_groups_only(self):
        """Test filtering to root groups only"""
        root_groups = UserGroup.objects.root_groups_only()
        
        self.assertIn(self.parent_group, root_groups)
        self.assertNotIn(self.child_group, root_groups)
    
    def test_with_user_queryset(self):
        """Test filtering groups by user membership"""
        user = User.objects.create_user(
            username='testuser',
            email='test@test.com',
            password='testpass123'
        )
        
        # Add user to child group
        GroupMembership.objects.create(
            user=user,
            group=self.child_group,
            added_by=self.admin_user
        )
        
        user_groups = UserGroup.objects.with_user(user)
        self.assertIn(self.child_group, user_groups)
        self.assertNotIn(self.parent_group, user_groups)
    
    def test_by_depth_level(self):
        """Test filtering groups by hierarchy depth"""
        # Create grandchild
        grandchild_group = UserGroup.objects.create(
            name='Regional Sales',
            description='Regional sales team',
            parent=self.child_group,
            created_by=self.admin_user
        )
        
        depth_0_groups = UserGroup.objects.by_depth_level(0)
        depth_1_groups = UserGroup.objects.by_depth_level(1)
        depth_2_groups = UserGroup.objects.by_depth_level(2)
        
        self.assertIn(self.parent_group, depth_0_groups)
        self.assertIn(self.child_group, depth_1_groups)
        self.assertIn(grandchild_group, depth_2_groups)
    
    def test_get_descendants(self):
        """Test getting all descendants of a group"""
        # Create grandchild
        grandchild_group = UserGroup.objects.create(
            name='Regional Sales',
            description='Regional sales team',
            parent=self.child_group,
            created_by=self.admin_user
        )
        
        descendants = UserGroup.objects.get_descendants(self.parent_group)
        
        self.assertIn(self.child_group, descendants)
        self.assertIn(grandchild_group, descendants)
        self.assertNotIn(self.parent_group, descendants)
    
    def test_bulk_assign_users(self):
        """Test bulk user assignment to groups"""
        users = [
            User.objects.create_user(
                username=f'user{i}',
                email=f'user{i}@test.com',
                password='testpass123'
            ) for i in range(3)
        ]
        
        memberships = UserGroup.objects.bulk_assign_users(
            group=self.child_group,
            users=users,
            added_by=self.admin_user,
            reason='Bulk assignment test'
        )
        
        self.assertEqual(len(memberships), 3)
        
        # Verify all users are now members
        for user in users:
            self.assertTrue(
                self.child_group.memberships.filter(user=user, is_active=True).exists()
            )


class PermissionAuditLogManagerTest(TestCase):
    """Test PermissionAuditLogManager functionality"""
    
    def setUp(self):
        """Set up test data"""
        self.actor = User.objects.create_user(
            username='admin',
            email='admin@test.com',
            password='testpass123'
        )
        
        self.target_user = User.objects.create_user(
            username='target',
            email='target@test.com',
            password='testpass123'
        )
        
        self.permission = Permission.objects.create(
            module='test',
            resource='audit',
            action='test',
            name='Test Permission'
        )
    
    def test_log_action_creation(self):
        """Test creating audit log through manager method"""
        log_entry = PermissionAuditLog.objects.log_action(
            action='grant_user',
            actor=self.actor,
            target_user=self.target_user,
            permission=self.permission,
            reason='Testing audit functionality'
        )
        
        self.assertEqual(log_entry.action, 'grant_user')
        self.assertEqual(log_entry.actor, self.actor)
        self.assertEqual(log_entry.target_user, self.target_user)
        self.assertEqual(log_entry.permission, self.permission)
        self.assertEqual(log_entry.result, 'success')
    
    def test_for_user_filtering(self):
        """Test filtering audit logs for specific user"""
        # Create audit log for target user
        PermissionAuditLog.objects.log_action(
            action='grant_user',
            actor=self.actor,
            target_user=self.target_user,
            permission=self.permission
        )
        
        # Create audit log for different user
        other_user = User.objects.create_user(
            username='other',
            email='other@test.com',
            password='testpass123'
        )
        
        PermissionAuditLog.objects.log_action(
            action='revoke_user',
            actor=self.actor,
            target_user=other_user,
            permission=self.permission
        )
        
        # Test filtering
        target_user_logs = PermissionAuditLog.objects.for_user(self.target_user)
        self.assertEqual(target_user_logs.count(), 1)
        self.assertEqual(target_user_logs.first().target_user, self.target_user)
    
    def test_within_timeframe(self):
        """Test filtering audit logs within timeframe"""
        # Create old log
        old_log = PermissionAuditLog.objects.log_action(
            action='grant_user',
            actor=self.actor,
            target_user=self.target_user
        )
        old_log.created_at = timezone.now() - timedelta(days=30)
        old_log.save()
        
        # Create recent log
        recent_log = PermissionAuditLog.objects.log_action(
            action='revoke_user',
            actor=self.actor,
            target_user=self.target_user
        )
        
        # Test filtering
        start_time = timezone.now() - timedelta(days=7)
        end_time = timezone.now()
        
        recent_logs = PermissionAuditLog.objects.within_timeframe(start_time, end_time)
        
        self.assertNotIn(old_log, recent_logs)
        self.assertIn(recent_log, recent_logs)
    
    def test_by_action_type(self):
        """Test filtering audit logs by action type"""
        grant_log = PermissionAuditLog.objects.log_action(
            action='grant_user',
            actor=self.actor,
            target_user=self.target_user
        )
        
        revoke_log = PermissionAuditLog.objects.log_action(
            action='revoke_user',
            actor=self.actor,
            target_user=self.target_user
        )
        
        grant_logs = PermissionAuditLog.objects.by_action_type('grant_user')
        revoke_logs = PermissionAuditLog.objects.by_action_type('revoke_user')
        
        self.assertIn(grant_log, grant_logs)
        self.assertNotIn(revoke_log, grant_logs)
        
        self.assertIn(revoke_log, revoke_logs)
        self.assertNotIn(grant_log, revoke_logs)
    
    def test_security_events_filtering(self):
        """Test filtering security-related events"""
        # Create various log types
        grant_log = PermissionAuditLog.objects.log_action(
            action='grant_user',
            actor=self.actor,
            target_user=self.target_user
        )
        
        admin_log = PermissionAuditLog.objects.log_action(
            action='create_group',
            actor=self.actor,
            details={'security_level': 'high'}
        )
        
        security_logs = PermissionAuditLog.objects.security_events()
        
        # Assuming security events include create_group, delete_group, etc.
        self.assertIn(admin_log, security_logs)


class GroupMembershipManagerTest(TestCase):
    """Test GroupMembershipManager functionality"""
    
    def setUp(self):
        """Set up test data"""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@test.com',
            password='testpass123'
        )
        
        self.group = UserGroup.objects.create(
            name='Test Group',
            description='Test group for membership'
        )
        
        self.admin_user = User.objects.create_user(
            username='admin',
            email='admin@test.com',
            password='testpass123'
        )
    
    def test_active_memberships_only(self):
        """Test filtering to active memberships only"""
        active_membership = GroupMembership.objects.create(
            user=self.user,
            group=self.group,
            is_active=True,
            added_by=self.admin_user
        )
        
        inactive_membership = GroupMembership.objects.create(
            user=self.user,
            group=self.group,
            is_active=False,
            added_by=self.admin_user
        )
        
        active_memberships = GroupMembership.objects.active_memberships_only()
        
        self.assertIn(active_membership, active_memberships)
        self.assertNotIn(inactive_membership, active_memberships)
    
    def test_primary_memberships_only(self):
        """Test filtering to primary memberships only"""
        primary_membership = GroupMembership.objects.create(
            user=self.user,
            group=self.group,
            is_primary=True,
            added_by=self.admin_user
        )
        
        secondary_membership = GroupMembership.objects.create(
            user=self.user,
            group=self.group,
            is_primary=False,
            added_by=self.admin_user
        )
        
        primary_memberships = GroupMembership.objects.primary_memberships_only()
        
        self.assertIn(primary_membership, primary_memberships)
        self.assertNotIn(secondary_membership, primary_memberships)
    
    def test_expiring_soon(self):
        """Test filtering memberships expiring soon"""
        soon_to_expire = GroupMembership.objects.create(
            user=self.user,
            group=self.group,
            valid_until=timezone.now() + timedelta(days=1),
            added_by=self.admin_user
        )
        
        long_term_membership = GroupMembership.objects.create(
            user=self.user,
            group=self.group,
            valid_until=timezone.now() + timedelta(days=30),
            added_by=self.admin_user
        )
        
        expiring_memberships = GroupMembership.objects.expiring_soon(days=7)
        
        self.assertIn(soon_to_expire, expiring_memberships)
        self.assertNotIn(long_term_membership, expiring_memberships)
    
    def test_bulk_deactivate_memberships(self):
        """Test bulk deactivation of memberships"""
        memberships = [
            GroupMembership.objects.create(
                user=self.user,
                group=self.group,
                added_by=self.admin_user
            ) for _ in range(3)
        ]
        
        deactivated_count = GroupMembership.objects.bulk_deactivate_memberships(
            memberships=memberships,
            reason='Bulk test deactivation'
        )
        
        self.assertEqual(deactivated_count, 3)
        
        # Verify deactivation
        for membership in memberships:
            membership.refresh_from_db()
            self.assertFalse(membership.is_active)


class ManagerPerformanceTest(TestCase):
    """Test manager performance and caching behavior"""
    
    def setUp(self):
        """Set up performance test data"""
        cache.clear()
        
        # Create test data
        self.users = [
            User.objects.create_user(
                username=f'user{i}',
                email=f'user{i}@test.com',
                password='testpass123'
            ) for i in range(10)
        ]
        
        self.permissions = [
            Permission.objects.create(
                module='test',
                resource='performance',
                action=f'action{i}',
                name=f'Test Action {i}'
            ) for i in range(5)
        ]
    
    @patch('django.core.cache.cache')
    def test_permission_caching_behavior(self, mock_cache):
        """Test that permission queries use caching appropriately"""
        mock_cache.get.return_value = None  # Simulate cache miss
        
        user = self.users[0]
        permission_code = 'test.performance.action0'
        
        # Grant permission
        UserPermission.objects.create(
            user=user,
            permission=self.permissions[0]
        )
        
        # First call should hit database and set cache
        has_permission = user.has_permission_new(permission_code)
        
        # Should have called cache.get and cache.set
        mock_cache.get.assert_called()
        mock_cache.set.assert_called()
        
        self.assertTrue(has_permission)
    
    def test_bulk_operations_performance(self):
        """Test performance of bulk operations"""
        # Measure time for bulk permission grant
        import time
        
        start_time = time.time()
        
        # Bulk grant permissions to multiple users
        granted_count = User.objects.bulk_grant_permission(
            users=self.users[:5],
            permission_code='test.performance.action0',
            granted_by=self.users[0],
            reason='Performance test'
        )
        
        end_time = time.time()
        execution_time = end_time - start_time
        
        # Should complete bulk operation in reasonable time
        self.assertLess(execution_time, 1.0)  # Less than 1 second
        self.assertEqual(granted_count, 5)


if __name__ == '__main__':
    import django
    from django.conf import settings
    from django.test.utils import get_runner
    
    django.setup()
    TestRunner = get_runner(settings)
    test_runner = TestRunner()
    failures = test_runner.run_tests(['tests.core.test_managers'])
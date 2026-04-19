"""
Unit tests for Model Managers - T003 Model Managers and Core Methods
Tests the functionality of all custom managers for the permission system.

Created: 2026-04-18
Author: Sistema de Tintas - Spec Kit Implementation T003
"""

from django.test import TestCase
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.utils import timezone
from datetime import timedelta
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

    def test_with_module_access_queryset(self):
        """Test with_module_access queryset method"""
        # Grant permission to user
        UserPermission.objects.create(
            user=self.regular_user,
            permission=self.permission,
            grant_type='allow',
            granted_by=self.admin_user,
            reason='Test module access'
        )
        
        # Test queryset
        users_with_module = User.objects.with_module_access('tintometry')
        self.assertIn(self.regular_user, users_with_module)

    def test_active_users_queryset(self):
        """Test active_users queryset with prefetch optimization"""
        # Deactivate one user
        self.regular_user.is_active = False
        self.regular_user.save()
        
        active_users = User.objects.active_users()
        self.assertIn(self.admin_user, active_users)
        self.assertNotIn(self.regular_user, active_users)


class PermissionManagerTest(TestCase):
    """Test PermissionManager methods"""

    def setUp(self):
        """Set up test data"""
        cache.clear()
        
        # Create test user and permissions
        self.user = User.objects.create_user(
            username='testuser',
            email='test@test.com',
            password='testpass123'
        )
        
        self.permission1 = Permission.objects.create(
            module='tintometry',
            resource='formula',
            action='create',
            name='Create Formula',
            is_system=True
        )
        
        self.permission2 = Permission.objects.create(
            module='sales',
            resource='order',
            action='view',
            name='View Order',
            is_system=False
        )

    def test_get_by_code(self):
        """Test get_by_code method with caching"""
        # First call - should query database
        permission = Permission.objects.get_by_code('tintometry.formula.create')
        self.assertEqual(permission, self.permission1)
        
        # Second call - should use cache
        permission_cached = Permission.objects.get_by_code('tintometry.formula.create')
        self.assertEqual(permission_cached, self.permission1)

    def test_get_by_code_invalid_format(self):
        """Test get_by_code with invalid permission code format"""
        with self.assertRaises(ValueError):
            Permission.objects.get_by_code('invalid.format')

    def test_by_module_queryset(self):
        """Test by_module queryset method"""
        tintometry_perms = Permission.objects.by_module('tintometry')
        self.assertIn(self.permission1, tintometry_perms)
        self.assertNotIn(self.permission2, tintometry_perms)

    def test_system_permissions_queryset(self):
        """Test system_permissions queryset method"""
        system_perms = Permission.objects.system_permissions()
        self.assertIn(self.permission1, system_perms)
        self.assertNotIn(self.permission2, system_perms)

    def test_user_creatable_permissions_queryset(self):
        """Test user_creatable_permissions queryset method"""
        user_perms = Permission.objects.user_creatable_permissions()
        self.assertNotIn(self.permission1, user_perms)
        self.assertIn(self.permission2, user_perms)

    def test_resolve_user_permissions(self):
        """Test resolve_user_permissions method"""
        # Grant direct permission
        UserPermission.objects.create(
            user=self.user,
            permission=self.permission1,
            grant_type='allow',
            granted_by=self.user,
            reason='Test direct permission'
        )
        
        permissions = Permission.objects.resolve_user_permissions(self.user)
        self.assertIn('tintometry.formula.create', permissions)


class UserGroupManagerTest(TestCase):
    """Test UserGroupManager methods"""

    def setUp(self):
        """Set up test data"""
        cache.clear()
        
        self.admin_user = User.objects.create_user(
            username='admin',
            email='admin@test.com',
            password='testpass123'
        )
        
        # Create hierarchical groups
        self.parent_group = UserGroup.objects.create(
            name='Parent Group',
            description='Top level group',
            created_by=self.admin_user
        )
        
        self.child_group = UserGroup.objects.create(
            name='Child Group',
            description='Child of parent group',
            parent=self.parent_group,
            created_by=self.admin_user
        )

    def test_active_groups_queryset(self):
        """Test active_groups queryset"""
        active_groups = UserGroup.objects.active_groups()
        self.assertIn(self.parent_group, active_groups)
        self.assertIn(self.child_group, active_groups)

    def test_root_groups_queryset(self):
        """Test root_groups queryset"""
        root_groups = UserGroup.objects.root_groups()
        self.assertIn(self.parent_group, root_groups)
        self.assertNotIn(self.child_group, root_groups)

    def test_get_children(self):
        """Test get_children method"""
        children = UserGroup.objects.get_children(self.parent_group)
        self.assertIn(self.child_group, children)

    def test_get_descendants(self):
        """Test get_descendants recursive method"""
        # Create grandchild
        grandchild_group = UserGroup.objects.create(
            name='Grandchild Group',
            parent=self.child_group,
            created_by=self.admin_user
        )
        
        descendants = UserGroup.objects.get_descendants(self.parent_group)
        self.assertIn(self.child_group, descendants)
        self.assertIn(grandchild_group, descendants)

    def test_get_ancestors(self):
        """Test get_ancestors method"""
        ancestors = UserGroup.objects.get_ancestors(self.child_group)
        self.assertIn(self.parent_group, ancestors)

    def test_validate_hierarchy(self):
        """Test validate_hierarchy method for circular reference prevention"""
        # Valid hierarchy change
        self.assertTrue(UserGroup.objects.validate_hierarchy(self.child_group, None))
        
        # Invalid hierarchy (would create circular reference)
        self.assertFalse(UserGroup.objects.validate_hierarchy(self.parent_group, self.child_group))


class PermissionAuditLogManagerTest(TestCase):
    """Test PermissionAuditLogManager methods"""

    def setUp(self):
        """Set up test data"""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@test.com',
            password='testpass123'
        )
        
        self.permission = Permission.objects.create(
            module='tintometry',
            resource='formula',
            action='create',
            name='Create Formula'
        )

    def test_log_permission_change(self):
        """Test log_permission_change method"""
        audit_entry = PermissionAuditLog.objects.log_permission_change(
            action='user_permission_granted',
            actor=self.user,
            target_user=self.user,
            permission=self.permission,
            details={'test': 'data'},
            reason='Test permission grant',
            ip_address='127.0.0.1',
        )
        
        self.assertEqual(audit_entry.action, 'user_permission_granted')
        self.assertEqual(audit_entry.actor, self.user)
        self.assertEqual(audit_entry.target_user, self.user)
        self.assertEqual(audit_entry.permission, self.permission)
        self.assertEqual(audit_entry.details['test'], 'data')

    def test_log_permission_change_invalid_action(self):
        """Test log_permission_change with invalid action"""
        with self.assertRaises(ValueError):
            PermissionAuditLog.objects.log_permission_change(
                action='invalid_action',
                actor=self.user,
                details={}
            )

    def test_log_permission_check(self):
        """Test log_permission_check method"""
        audit_entry = PermissionAuditLog.objects.log_permission_check(
            user=self.user,
            permission_code='tintometry.formula.create',
            granted=True,
            ip_address='127.0.0.1'
        )
        
        self.assertEqual(audit_entry.action, 'permission_checked')
        self.assertEqual(audit_entry.actor, self.user)
        self.assertTrue(audit_entry.details['granted'])

    def test_log_access_attempt(self):
        """Test log_access_attempt method"""
        audit_entry = PermissionAuditLog.objects.log_access_attempt(
            user=self.user,
            resource='/tintometry/formulas/',
            granted=False,
            reason='Access denied - insufficient permissions',
            ip_address='192.168.1.100'
        )
        
        self.assertEqual(audit_entry.action, 'access_denied')
        self.assertEqual(audit_entry.actor, self.user)
        self.assertFalse(audit_entry.details['granted'])

    def test_get_user_activity(self):
        """Test get_user_activity method"""
        # Create audit entry
        PermissionAuditLog.objects.log_permission_check(
            user=self.user,
            permission_code='tintometry.formula.create',
            granted=True
        )
        
        activity = PermissionAuditLog.objects.get_user_activity(self.user, days=30)
        self.assertTrue(activity.exists())

    def test_validate_audit_integrity(self):
        """Test validate_audit_integrity method"""
        # Create some audit entries
        PermissionAuditLog.objects.log_permission_check(
            user=self.user,
            permission_code='tintometry.formula.create',
            granted=True
        )
        
        integrity_report = PermissionAuditLog.objects.validate_audit_integrity()
        
        self.assertIn('total_entries', integrity_report)
        self.assertIn('integrity_score', integrity_report)
        self.assertGreaterEqual(integrity_report['integrity_score'], 90)


class GroupMembershipManagerTest(TestCase):
    """Test GroupMembershipManager methods"""

    def setUp(self):
        """Set up test data"""
        cache.clear()
        
        self.admin_user = User.objects.create_user(
            username='admin',
            email='admin@test.com',
            password='testpass123'
        )
        
        self.regular_user = User.objects.create_user(
            username='regular',
            email='regular@test.com',
            password='testpass123'
        )
        
        self.test_group = UserGroup.objects.create(
            name='Test Group',
            description='Test group for unit tests',
            max_users=5,
            created_by=self.admin_user
        )

    def test_add_user_to_group(self):
        """Test add_user_to_group method"""
        membership = GroupMembership.objects.add_user_to_group(
            user=self.regular_user,
            group=self.test_group,
            added_by=self.admin_user,
            is_primary=True,
            notes='Test membership'
        )
        
        self.assertEqual(membership.user, self.regular_user)
        self.assertEqual(membership.group, self.test_group)
        self.assertTrue(membership.is_primary)
        self.assertTrue(membership.is_active)

    def test_add_user_to_group_capacity_limit(self):
        """Test add_user_to_group with group capacity limit"""
        # Set group to max capacity of 1
        self.test_group.max_users = 1
        self.test_group.save()
        
        # Add first user successfully
        GroupMembership.objects.add_user_to_group(
            user=self.regular_user,
            group=self.test_group,
            added_by=self.admin_user
        )
        
        # Attempt to add second user should fail
        another_user = User.objects.create_user(
            username='another',
            email='another@test.com',
            password='testpass123'
        )
        
        with self.assertRaises(ValueError):
            GroupMembership.objects.add_user_to_group(
                user=another_user,
                group=self.test_group,
                added_by=self.admin_user
            )

    def test_remove_user_from_group(self):
        """Test remove_user_from_group method"""
        # Add user first
        GroupMembership.objects.add_user_to_group(
            user=self.regular_user,
            group=self.test_group,
            added_by=self.admin_user
        )
        
        # Remove user
        result = GroupMembership.objects.remove_user_from_group(
            user=self.regular_user,
            group=self.test_group,
            removed_by=self.admin_user,
            reason='Test removal'
        )
        
        self.assertTrue(result)
        
        # Check membership is deactivated
        membership = GroupMembership.objects.get(
            user=self.regular_user,
            group=self.test_group
        )
        self.assertFalse(membership.is_active)

    def test_cleanup_expired_memberships(self):
        """Test cleanup_expired_memberships method"""
        # Create expired membership
        expired_date = timezone.now() - timedelta(days=1)
        
        membership = GroupMembership.objects.create(
            user=self.regular_user,
            group=self.test_group,
            added_by=self.admin_user,
            valid_until=expired_date,
            is_active=True
        )
        
        # Run cleanup
        count = GroupMembership.objects.cleanup_expired_memberships()
        
        self.assertEqual(count, 1)
        
        # Check membership is deactivated
        membership.refresh_from_db()
        self.assertFalse(membership.is_active)
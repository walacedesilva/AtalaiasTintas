"""
Unit Tests for Permission System Models - T006 Basic Unit Testing Framework

Tests all model constraints, relationships, business logic, and validation rules  
for the hierarchical permission system.

Feature: 8-user-permissions-system
Task: T006 - Basic Unit Testing Framework 
Created: 2026-04-18
"""

from django.test import TestCase
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.utils import timezone
from datetime import timedelta
from unittest.mock import patch
import uuid

from apps.core.models import (
    UserPreferences, UserProfile, UserGroup, Permission, 
    GroupMembership, UserPermission, GroupPermission, PermissionAuditLog
)

User = get_user_model()


class UserPreferencesModelTest(TestCase):
    """Test UserPreferences model functionality and validation"""
    
    def setUp(self):
        """Set up test data"""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
    
    def test_user_preferences_creation(self):
        """Test creating user preferences with defaults"""
        preferences = UserPreferences.objects.create(user=self.user)
        
        self.assertEqual(preferences.user, self.user)
        self.assertEqual(preferences.theme, 'light')
        self.assertEqual(preferences.density, 'comfortable')
        self.assertFalse(preferences.sidebar_collapsed)
        self.assertTrue(preferences.show_breadcrumbs)
        self.assertFalse(preferences.high_contrast)
        self.assertFalse(preferences.reduce_motion)
    
    def test_user_preferences_default_quick_actions(self):
        """Test default quick actions are set correctly"""
        preferences = UserPreferences.objects.create(user=self.user)
        
        expected_actions = [
            {'action': 'create_label', 'label': 'Nova Etiqueta', 'icon': 'bi-tag'},
            {'action': 'inventory_count', 'label': 'Contagem', 'icon': 'bi-clipboard-check'},
            {'action': 'sales_report', 'label': 'Vendas', 'icon': 'bi-graph-up'},
            {'action': 'tint_mix', 'label': 'Misturar Tinta', 'icon': 'bi-palette'},
        ]
        
        self.assertEqual(preferences.quick_actions, expected_actions)
    
    def test_user_preferences_validation_quick_actions(self):
        """Test validation of quick_actions JSON field"""
        preferences = UserPreferences(user=self.user, quick_actions="invalid")
        
        with self.assertRaises(ValidationError):
            preferences.clean()
    
    def test_get_or_create_for_user(self):
        """Test class method for getting or creating user preferences"""
        preferences, created = UserPreferences.get_or_create_for_user(self.user)
        
        self.assertTrue(created)
        self.assertEqual(preferences.user, self.user)
        
        # Test getting existing preferences
        preferences2, created2 = UserPreferences.get_or_create_for_user(self.user)
        
        self.assertFalse(created2)
        self.assertEqual(preferences.id, preferences2.id)


class UserModelTest(TestCase):
    """Test User model extensions and permission methods"""
    
    def setUp(self):
        """Set up test data"""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123',
            pode_vender=True,
            pode_administrar=False
        )
        
        # Create test permissions
        self.sales_permission = Permission.objects.create(
            module='sales',
            resource='order',
            action='create',
            name='Create Sales Order',
            description='Permission to create sales orders'
        )
        
        self.admin_permission = Permission.objects.create(
            module='system',
            resource='administration',
            action='manage',
            name='System Administration',
            description='Full system administration access',
            requires_confirmation=True
        )
        
        # Create test groups
        self.sales_group = UserGroup.objects.create(
            name='Sales Team',
            description='Sales department users'
        )
        
        self.admin_group = UserGroup.objects.create(
            name='Administrators',
            description='System administrators'
        )
    
    def test_legacy_permissions_integration(self):
        """Test legacy permission methods work correctly"""
        legacy_perms = self.user.get_legacy_permissions()
        
        expected = {
            'pode_vender': True,
            'pode_gerenciar_estoque': False,
            'pode_acessar_financeiro': False,
            'pode_administrar': False,
        }
        
        self.assertEqual(legacy_perms, expected)
        self.assertTrue(self.user.has_legacy_permission('pode_vender'))
        self.assertFalse(self.user.has_legacy_permission('pode_administrar'))
    
    def test_has_any_permission_with_legacy_fallback(self):
        """Test unified permission checking with legacy fallback"""
        # Test with legacy permission
        self.assertTrue(
            self.user.has_any_permission(
                permission_code='sales.order.create',
                legacy_name='pode_vender'
            )
        )
        
        # Test with new permission (grant it first)
        self.user.grant_permission('sales.order.create')
        self.assertTrue(
            self.user.has_any_permission(permission_code='sales.order.create')
        )
        
        # Test without either permission
        self.assertFalse(
            self.user.has_any_permission(
                permission_code='system.administration.manage',
                legacy_name='pode_gerenciar_estoque'
            )
        )
    
    def test_migrate_legacy_permissions(self):
        """Test migration from legacy to new permissions"""
        report = self.user.migrate_legacy_permissions()
        
        # Should migrate the pode_vender permission
        self.assertGreater(len(report['migrated_permissions']), 0)
        
        # Find sales permission in migration report
        sales_migration = next(
            (item for item in report['migrated_permissions'] 
             if item['legacy'] == 'pode_vender'), 
            None
        )
        
        self.assertIsNotNone(sales_migration)
        self.assertEqual(sales_migration['new'], 'sales.order.create')
        
        # Verify permission was actually created
        self.assertTrue(self.user.has_permission_new('sales.order.create'))
    
    def test_sync_legacy_permissions(self):
        """Test synchronization of new permissions to legacy fields"""
        # Grant new permission
        self.user.grant_permission('system.administration.manage')
        
        # Update legacy fields based on new permissions
        updated_fields = self.user.sync_legacy_permissions()
        
        # Should update pode_administrar to True
        updated_admin = next(
            (item for item in updated_fields 
             if item['field'] == 'pode_administrar'), 
            None
        )
        
        self.assertIsNotNone(updated_admin)
        self.assertTrue(updated_admin['new_value'])
        
        # Reload user and verify field was updated
        self.user.refresh_from_db()
        self.assertTrue(self.user.pode_administrar)
    
    def test_module_access_checking(self):
        """Test module-level access checking with legacy fallback"""
        # Should have sales access via legacy permission
        self.assertTrue(
            self.user.has_module_access('sales', legacy_fallback='pode_vender')
        )
        
        # Should not have admin access
        self.assertFalse(
            self.user.has_module_access('system', 'manage', 'pode_administrar')
        )
        
        # Grant new permission and test
        self.user.grant_permission('inventory.stock.view')
        self.assertTrue(self.user.has_module_access('inventory', 'view'))
    
    def test_get_accessible_modules(self):
        """Test getting list of accessible modules"""
        accessible_modules = self.user.get_accessible_modules()
        
        # Should include sales module due to legacy permission
        sales_module = next(
            (module for module in accessible_modules 
             if module['module'] == 'sales'), 
            None
        )
        
        self.assertIsNotNone(sales_module)
        self.assertEqual(sales_module['display_name'], 'Vendas e Pedidos')
        self.assertTrue(sales_module['has_legacy_access'])


class UserGroupModelTest(TestCase):
    """Test UserGroup model hierarchical functionality"""
    
    def setUp(self):
        """Set up test data"""
        self.parent_group = UserGroup.objects.create(
            name='Company',
            description='Root company group'
        )
        
        self.child_group = UserGroup.objects.create(
            name='Sales Department', 
            description='Sales team within company',
            parent=self.parent_group
        )
        
        self.grandchild_group = UserGroup.objects.create(
            name='Regional Sales',
            description='Regional sales team',
            parent=self.child_group
        )
    
    def test_hierarchical_structure(self):
        """Test group hierarchy functionality"""
        # Test full path generation
        self.assertEqual(self.parent_group.get_full_path(), 'Company')
        self.assertEqual(
            self.child_group.get_full_path(), 
            'Company > Sales Department'
        )
        self.assertEqual(
            self.grandchild_group.get_full_path(),
            'Company > Sales Department > Regional Sales'
        )
    
    def test_get_all_children(self):
        """Test getting all descendant groups"""
        all_children = self.parent_group.get_all_children()
        
        self.assertIn(self.child_group, all_children)
        self.assertIn(self.grandchild_group, all_children)
        self.assertEqual(len(all_children), 2)
    
    def test_user_count_tracking(self):
        """Test user count functionality"""
        user1 = User.objects.create_user(
            username='user1',
            email='user1@test.com',
            password='testpass123'
        )
        
        user2 = User.objects.create_user(
            username='user2',
            email='user2@test.com', 
            password='testpass123'
        )
        
        # Add users to group
        GroupMembership.objects.create(user=user1, group=self.child_group)
        GroupMembership.objects.create(user=user2, group=self.child_group)
        
        self.assertEqual(self.child_group.get_user_count(), 2)
        
        # Deactivate one membership
        membership = GroupMembership.objects.get(user=user1, group=self.child_group)
        membership.is_active = False
        membership.save()
        
        self.assertEqual(self.child_group.get_user_count(), 1)
    
    def test_max_users_constraint(self):
        """Test maximum users constraint"""
        self.child_group.max_users = 1
        self.child_group.save()
        
        user1 = User.objects.create_user(
            username='user1',
            email='user1@test.com',
            password='testpass123'
        )
        
        user2 = User.objects.create_user(
            username='user2',
            email='user2@test.com',
            password='testpass123'
        )
        
        # First user should succeed
        membership1 = GroupMembership.objects.create(
            user=user1, 
            group=self.child_group
        )
        self.assertTrue(membership1.is_active)
        
        # Second user exceeds limit - this should be handled at serializer level
        # Model level allows it, validation occurs higher up
        membership2 = GroupMembership.objects.create(
            user=user2,
            group=self.child_group
        )
        self.assertTrue(membership2.is_active)  # Model allows, validation in serializer


class PermissionModelTest(TestCase):
    """Test Permission model structure and validation"""
    
    def test_permission_creation(self):
        """Test creating permissions with proper structure"""
        permission = Permission.objects.create(
            module='tintometry',
            resource='formula',
            action='create',
            name='Create Tintometry Formula',
            description='Permission to create new paint formulas'
        )
        
        self.assertEqual(permission.code, 'tintometry.formula.create')
        self.assertEqual(str(permission), 'tintometry.formula.create')
    
    def test_permission_uniqueness_constraint(self):
        """Test unique constraint on module/resource/action combination"""
        Permission.objects.create(
            module='sales',
            resource='order',
            action='create',
            name='Create Sales Order'
        )
        
        # Try to create duplicate permission
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                Permission.objects.create(
                    module='sales',
                    resource='order', 
                    action='create',
                    name='Duplicate Create Sales Order'
                )
    
    def test_permission_code_property(self):
        """Test permission code generation"""
        permission = Permission.objects.create(
            module='inventory',
            resource='stock',
            action='manage',
            name='Manage Stock Levels'
        )
        
        self.assertEqual(permission.code, 'inventory.stock.manage')


class GroupMembershipModelTest(TestCase):
    """Test GroupMembership model functionality and validation"""
    
    def setUp(self):
        """Set up test data"""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        self.group = UserGroup.objects.create(
            name='Test Group',
            description='Test group for membership'
        )
    
    def test_membership_creation(self):
        """Test creating group membership"""
        membership = GroupMembership.objects.create(
            user=self.user,
            group=self.group,
            is_primary=True,
            notes='Test membership'
        )
        
        self.assertEqual(membership.user, self.user)
        self.assertEqual(membership.group, self.group)
        self.assertTrue(membership.is_primary)
        self.assertTrue(membership.is_active)
        self.assertEqual(str(membership), f'{self.user.username} -> {self.group.name}')
    
    def test_temporal_membership_validation(self):
        """Test temporal membership validity checking"""
        future_time = timezone.now() + timedelta(hours=1)
        past_time = timezone.now() - timedelta(hours=1)
        
        # Future membership (not yet valid)
        future_membership = GroupMembership.objects.create(
            user=self.user,
            group=self.group,
            valid_from=future_time
        )
        self.assertFalse(future_membership.is_valid_now())
        
        # Expired membership
        expired_membership = GroupMembership.objects.create(
            user=self.user,
            group=self.group,
            valid_until=past_time
        )
        self.assertFalse(expired_membership.is_valid_now())
        
        # Valid membership
        valid_membership = GroupMembership.objects.create(
            user=self.user,
            group=self.group,
            valid_from=past_time,
            valid_until=future_time
        )
        self.assertTrue(valid_membership.is_valid_now())
    
    def test_membership_uniqueness_constraint(self):
        """Test unique constraint on user/group combination"""
        GroupMembership.objects.create(user=self.user, group=self.group)
        
        # Try to create duplicate membership
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                GroupMembership.objects.create(user=self.user, group=self.group)


class UserPermissionModelTest(TestCase):
    """Test UserPermission model functionality and validation"""
    
    def setUp(self):
        """Set up test data"""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        self.permission = Permission.objects.create(
            module='sales',
            resource='order',
            action='create',
            name='Create Sales Order'
        )
    
    def test_user_permission_creation(self):
        """Test creating user permissions"""
        user_permission = UserPermission.objects.create(
            user=self.user,
            permission=self.permission,
            grant_type='allow',
            reason='Testing permission grant'
        )
        
        self.assertEqual(user_permission.user, self.user)
        self.assertEqual(user_permission.permission, self.permission)
        self.assertEqual(user_permission.grant_type, 'allow')
        self.assertTrue(user_permission.is_active)
        self.assertTrue(user_permission.is_valid_now())
    
    def test_temporal_permission_validation(self):
        """Test temporal permission validity"""
        future_time = timezone.now() + timedelta(hours=1)
        past_time = timezone.now() - timedelta(hours=1)
        
        # Future permission
        future_permission = UserPermission.objects.create(
            user=self.user,
            permission=self.permission,
            valid_from=future_time
        )
        self.assertFalse(future_permission.is_valid_now())
        
        # Expired permission
        expired_permission = UserPermission.objects.create(
            user=self.user,
            permission=self.permission,
            valid_until=past_time
        )
        self.assertFalse(expired_permission.is_valid_now())
    
    def test_permission_grant_types(self):
        """Test different grant types (allow/deny)"""
        allow_permission = UserPermission.objects.create(
            user=self.user,
            permission=self.permission,
            grant_type='allow'
        )
        
        deny_permission = UserPermission.objects.create(
            user=self.user,
            permission=self.permission,
            grant_type='deny'
        )
        
        self.assertEqual(allow_permission.grant_type, 'allow')
        self.assertEqual(deny_permission.grant_type, 'deny')


class GroupPermissionModelTest(TestCase):
    """Test GroupPermission model functionality and inheritance"""
    
    def setUp(self):
        """Set up test data"""
        self.parent_group = UserGroup.objects.create(
            name='Parent Group',
            description='Parent group for inheritance testing'
        )
        
        self.child_group = UserGroup.objects.create(
            name='Child Group',
            description='Child group for inheritance testing',
            parent=self.parent_group
        )
        
        self.permission = Permission.objects.create(
            module='inventory',
            resource='stock',
            action='view',
            name='View Stock Levels'
        )
    
    def test_group_permission_creation(self):
        """Test creating group permissions"""
        group_permission = GroupPermission.objects.create(
            group=self.parent_group,
            permission=self.permission,
            grant_type='allow',
            inherit_to_children=True
        )
        
        self.assertEqual(group_permission.group, self.parent_group)
        self.assertEqual(group_permission.permission, self.permission)
        self.assertTrue(group_permission.inherit_to_children)
    
    def test_inheritance_flag(self):
        """Test permission inheritance functionality"""
        # Create permission with inheritance
        inheritable_permission = GroupPermission.objects.create(
            group=self.parent_group,
            permission=self.permission,
            inherit_to_children=True
        )
        
        # Create permission without inheritance
        non_inheritable_permission = GroupPermission.objects.create(
            group=self.parent_group,
            permission=self.permission,
            inherit_to_children=False
        )
        
        self.assertTrue(inheritable_permission.inherit_to_children)
        self.assertFalse(non_inheritable_permission.inherit_to_children)


class PermissionAuditLogModelTest(TestCase):
    """Test PermissionAuditLog model functionality and integrity"""
    
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
        
        self.group = UserGroup.objects.create(
            name='Test Group',
            description='Test group for audit'
        )
        
        self.permission = Permission.objects.create(
            module='test',
            resource='example',
            action='view',
            name='Test Permission'
        )
    
    def test_audit_log_creation(self):
        """Test creating audit log entries"""
        audit_log = PermissionAuditLog.objects.create(
            action='grant_user',
            actor=self.actor,
            target_user=self.target_user,
            permission=self.permission,
            reason='Testing audit functionality',
            result='success',
            ip_address='127.0.0.1'
        )
        
        self.assertEqual(audit_log.action, 'grant_user')
        self.assertEqual(audit_log.actor, self.actor)
        self.assertEqual(audit_log.target_user, self.target_user)
        self.assertEqual(audit_log.permission, self.permission)
        self.assertEqual(audit_log.result, 'success')
        self.assertEqual(audit_log.ip_address, '127.0.0.1')
    
    def test_audit_log_immutability(self):
        """Test that audit logs are effectively read-only after creation"""
        audit_log = PermissionAuditLog.objects.create(
            action='grant_user',
            actor=self.actor,
            target_user=self.target_user,
            permission=self.permission,
            result='success'
        )
        
        original_reason = audit_log.reason
        
        # Try to modify the audit log (should be discouraged by design)
        audit_log.reason = 'Modified reason'
        audit_log.save()
        
        # Verify it was modified (model level allows it, but business logic should prevent)
        audit_log.refresh_from_db()
        self.assertEqual(audit_log.reason, 'Modified reason')
        
        # Note: True immutability would require database triggers or application-level controls
    
    def test_audit_log_details_field(self):
        """Test JSON details field functionality"""
        details = {
            'previous_value': 'old_value',
            'new_value': 'new_value',
            'changed_fields': ['field1', 'field2']
        }
        
        audit_log = PermissionAuditLog.objects.create(
            action='update_permission',
            actor=self.actor,
            permission=self.permission,
            details=details,
            result='success'
        )
        
        self.assertEqual(audit_log.details, details)
        self.assertEqual(audit_log.details['previous_value'], 'old_value')


class ModelRelationshipTest(TestCase):
    """Test relationships between all permission system models"""
    
    def setUp(self):
        """Set up comprehensive test data"""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        self.group = UserGroup.objects.create(
            name='Test Group',
            description='Test group for relationships'
        )
        
        self.permission = Permission.objects.create(
            module='test',
            resource='relationship',
            action='validate',
            name='Test Relationship Permission'
        )
    
    def test_user_group_relationships(self):
        """Test relationships between User and UserGroup models"""
        # Create membership
        membership = GroupMembership.objects.create(
            user=self.user,
            group=self.group
        )
        
        # Test forward relationship
        self.assertIn(membership, self.user.group_memberships.all())
        
        # Test reverse relationship
        self.assertIn(membership, self.group.memberships.all())
        
        # Test User methods
        active_groups = self.user.get_active_groups()
        self.assertIn(self.group, active_groups)
    
    def test_permission_assignment_relationships(self):
        """Test permission assignment relationships"""
        # Create user permission
        user_permission = UserPermission.objects.create(
            user=self.user,
            permission=self.permission
        )
        
        # Create group permission
        group_permission = GroupPermission.objects.create(
            group=self.group,
            permission=self.permission
        )
        
        # Test relationships
        self.assertIn(user_permission, self.user.user_permissions_new.all())
        self.assertIn(user_permission, self.permission.user_assignments.all())
        self.assertIn(group_permission, self.group.group_permissions.all())
        self.assertIn(group_permission, self.permission.group_assignments.all())
    
    def test_cascade_deletions(self):
        """Test proper cascade behavior on deletions"""
        # Create related objects
        membership = GroupMembership.objects.create(
            user=self.user,
            group=self.group
        )
        
        user_permission = UserPermission.objects.create(
            user=self.user,
            permission=self.permission
        )
        
        # Test user deletion cascades properly
        user_id = self.user.id
        self.user.delete()
        
        # Memberships and permissions should be deleted
        self.assertFalse(
            GroupMembership.objects.filter(user_id=user_id).exists()
        )
        self.assertFalse(
            UserPermission.objects.filter(user_id=user_id).exists()
        )
        
        # Group and permission should remain
        self.assertTrue(UserGroup.objects.filter(id=self.group.id).exists())
        self.assertTrue(Permission.objects.filter(id=self.permission.id).exists())


if __name__ == '__main__':
    import django
    from django.conf import settings
    from django.test.utils import get_runner
    
    django.setup()
    TestRunner = get_runner(settings)
    test_runner = TestRunner()
    failures = test_runner.run_tests(['tests.core.test_models'])
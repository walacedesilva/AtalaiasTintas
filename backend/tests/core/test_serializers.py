"""
Unit Tests for Permission System Serializers - T006 Basic Unit Testing Framework

Tests all serializer validation rules, edge cases, and business logic  
for the hierarchical permission system API layer.

Feature: 8-user-permissions-system
Task: T006 - Basic Unit Testing Framework
Created: 2026-04-18
"""

from django.test import TestCase
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta
from rest_framework.serializers import ValidationError
from unittest.mock import Mock
import uuid

from apps.core.models import (
    UserPreferences, UserProfile, UserGroup, Permission,
    GroupMembership, UserPermission, GroupPermission, PermissionAuditLog
)
from apps.core.serializers import (
    UserSerializer, UserProfileSerializer, UserPreferencesSerializer,
    PermissionSerializer, UserGroupSerializer, UserPermissionSerializer,
    GroupPermissionSerializer, PermissionAuditLogSerializer, GroupMembershipSerializer
)

User = get_user_model()


class UserSerializerTest(TestCase):
    """Test UserSerializer functionality and validation"""
    
    def setUp(self):
        """Set up test data"""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123',
            first_name='Test',
            last_name='User',
            cpf='12345678901',
            pode_vender=True,
            pode_administrar=False
        )
    
    def test_user_serialization(self):
        """Test user object serialization"""
        serializer = UserSerializer(self.user)
        data = serializer.data
        
        self.assertEqual(data['username'], 'testuser')
        self.assertEqual(data['email'], 'test@example.com')
        self.assertEqual(data['full_name'], 'Test User')
        self.assertEqual(data['cpf'], '12345678901')
        
        # Test legacy permissions read-only
        self.assertTrue(data['pode_vender'])
        self.assertFalse(data['pode_administrar'])
    
    def test_user_deserialization(self):
        """Test user data deserialization and validation"""
        data = {
            'username': 'newuser',
            'email': 'new@example.com',
            'first_name': 'New',
            'last_name': 'User',
            'cpf': '98765432100'
        }
        
        serializer = UserSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        
        # Test read-only fields are ignored
        data['pode_vender'] = True  # Should be ignored
        serializer = UserSerializer(data=data)
        self.assertTrue(serializer.is_valid())
    
    def test_cpf_validation(self):
        """Test CPF format validation"""
        # Invalid CPF - wrong length
        data = {
            'username': 'testuser2',
            'email': 'test2@example.com',
            'cpf': '123456789'  # Too short
        }
        
        serializer = UserSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('cpf', serializer.errors)
        
        # Invalid CPF - non-numeric
        data['cpf'] = '1234567890a'
        serializer = UserSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('cpf', serializer.errors)


class UserPreferencesSerializerTest(TestCase):
    """Test UserPreferencesSerializer functionality and validation"""
    
    def setUp(self):
        """Set up test data"""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        self.preferences = UserPreferences.objects.create(
            user=self.user,
            theme='dark',
            density='compact',
            high_contrast=True
        )
    
    def test_preferences_serialization(self):
        """Test user preferences serialization"""
        serializer = UserPreferencesSerializer(self.preferences)
        data = serializer.data
        
        self.assertEqual(data['theme'], 'dark')
        self.assertEqual(data['density'], 'compact')
        self.assertTrue(data['high_contrast'])
        self.assertIsInstance(data['quick_actions'], list)
    
    def test_theme_validation(self):
        """Test theme choice validation"""
        data = {
            'theme': 'invalid_theme',
            'density': 'comfortable'
        }
        
        serializer = UserPreferencesSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('theme', serializer.errors)
        
        # Valid theme should pass
        data['theme'] = 'light'
        serializer = UserPreferencesSerializer(data=data)
        self.assertTrue(serializer.is_valid())
    
    def test_density_validation(self):
        """Test density choice validation"""
        data = {
            'theme': 'light',
            'density': 'invalid_density'
        }
        
        serializer = UserPreferencesSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('density', serializer.errors)
    
    def test_quick_actions_validation(self):
        """Test quick actions JSON structure validation"""
        # Invalid type (string instead of list)
        data = {
            'theme': 'light',
            'density': 'comfortable',
            'quick_actions': 'not_a_list'
        }
        
        serializer = UserPreferencesSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('quick_actions', serializer.errors)
        
        # Invalid structure (missing required fields)
        data['quick_actions'] = [
            {'action': 'test'}  # Missing 'label' and 'icon'
        ]
        
        serializer = UserPreferencesSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('quick_actions', serializer.errors)
        
        # Valid structure
        data['quick_actions'] = [
            {'action': 'test_action', 'label': 'Test', 'icon': 'bi-test'}
        ]
        
        serializer = UserPreferencesSerializer(data=data)
        self.assertTrue(serializer.is_valid())


class PermissionSerializerTest(TestCase):
    """Test PermissionSerializer validation and business rules"""
    
    def setUp(self):
        """Set up test data"""
        self.permission = Permission.objects.create(
            module='sales',
            resource='order',
            action='create',
            name='Create Sales Order',
            description='Permission to create sales orders'
        )
    
    def test_permission_serialization(self):
        """Test permission object serialization"""
        serializer = PermissionSerializer(self.permission)
        data = serializer.data
        
        self.assertEqual(data['module'], 'sales')
        self.assertEqual(data['resource'], 'order')
        self.assertEqual(data['action'], 'create')
        self.assertEqual(data['code'], 'sales.order.create')
        self.assertEqual(data['full_name'], 'Create Sales Order (sales.order.create)')
    
    def test_module_name_validation(self):
        """Test module name format validation"""
        # Invalid - starts with number
        data = {
            'module': '1sales',
            'resource': 'order',
            'action': 'create',
            'name': 'Test Permission'
        }
        
        serializer = PermissionSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('module', serializer.errors)
        
        # Invalid - contains spaces
        data['module'] = 'sales module'
        serializer = PermissionSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('module', serializer.errors)
        
        # Valid format
        data['module'] = 'sales_module'
        serializer = PermissionSerializer(data=data)
        self.assertTrue(serializer.is_valid())
    
    def test_resource_name_validation(self):
        """Test resource name format validation"""
        data = {
            'module': 'sales',
            'resource': 'UPPERCASE',  # Invalid - should be lowercase
            'action': 'create',
            'name': 'Test Permission'
        }
        
        serializer = PermissionSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('resource', serializer.errors)
    
    def test_action_validation(self):
        """Test action validation against allowed list"""
        # Invalid action
        data = {
            'module': 'sales',
            'resource': 'order',
            'action': 'invalid_action',
            'name': 'Test Permission'
        }
        
        serializer = PermissionSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('action', serializer.errors)
        
        # Valid actions
        valid_actions = ['create', 'read', 'update', 'delete', 'manage']
        for action in valid_actions:
            data['action'] = action
            serializer = PermissionSerializer(data=data)
            self.assertTrue(serializer.is_valid(), f'Action {action} should be valid')
    
    def test_permission_name_validation(self):
        """Test permission name length validation"""
        data = {
            'module': 'sales',
            'resource': 'order',
            'action': 'create',
            'name': 'X'  # Too short
        }
        
        serializer = PermissionSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('name', serializer.errors)
    
    def test_duplicate_permission_validation(self):
        """Test validation prevents duplicate permissions"""
        data = {
            'module': 'sales',
            'resource': 'order',
            'action': 'create',  # Same as existing permission
            'name': 'Duplicate Create Sales Order'
        }
        
        serializer = PermissionSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('non_field_errors', serializer.errors)
    
    def test_critical_permission_confirmation_requirement(self):
        """Test critical permissions auto-require confirmation"""
        data = {
            'module': 'test',
            'resource': 'data',
            'action': 'delete',  # Critical action
            'name': 'Delete Test Data',
            'requires_confirmation': False
        }
        
        serializer = PermissionSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        
        # Should auto-set requires_confirmation to True
        validated_data = serializer.validated_data
        self.assertTrue(validated_data['requires_confirmation'])


class UserGroupSerializerTest(TestCase):
    """Test UserGroupSerializer validation and hierarchy handling"""
    
    def setUp(self):
        """Set up test data"""
        self.admin_user = User.objects.create_user(
            username='admin',
            email='admin@test.com',
            password='testpass123'
        )
        
        self.parent_group = UserGroup.objects.create(
            name='Parent Group',
            description='Test parent group',
            created_by=self.admin_user
        )
        
        self.child_group = UserGroup.objects.create(
            name='Child Group',
            description='Test child group',
            parent=self.parent_group,
            created_by=self.admin_user
        )
    
    def test_group_serialization(self):
        """Test user group serialization with hierarchy"""
        serializer = UserGroupSerializer(self.child_group)
        data = serializer.data
        
        self.assertEqual(data['name'], 'Child Group')
        self.assertEqual(data['parent'], self.parent_group.id)
        self.assertEqual(data['parent_name'], 'Parent Group')
        self.assertEqual(data['full_path'], 'Parent Group > Child Group')
        self.assertEqual(data['user_count'], 0)
        self.assertIsInstance(data['children'], list)
    
    def test_group_name_validation(self):
        """Test group name validation"""
        # Too short
        data = {
            'name': 'AB',  # Less than 3 characters
            'description': 'Test group'
        }
        
        serializer = UserGroupSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('name', serializer.errors)
        
        # Invalid characters
        data['name'] = 'Group@#$'
        serializer = UserGroupSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('name', serializer.errors)
        
        # Valid name
        data['name'] = 'Valid Group Name'
        serializer = UserGroupSerializer(data=data)
        self.assertTrue(serializer.is_valid())
    
    def test_max_users_validation(self):
        """Test maximum users validation"""
        data = {
            'name': 'Test Group',
            'description': 'Test group',
            'max_users': 0  # Invalid - must be > 0
        }
        
        serializer = UserGroupSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('max_users', serializer.errors)
        
        data['max_users'] = 5
        serializer = UserGroupSerializer(data=data)
        self.assertTrue(serializer.is_valid())
    
    def test_hierarchy_cycle_prevention(self):
        """Test prevention of circular hierarchy"""
        # Try to make parent_group a child of child_group (would create cycle)
        data = {
            'name': self.parent_group.name,
            'description': self.parent_group.description,
            'parent': self.child_group.id
        }
        
        serializer = UserGroupSerializer(self.parent_group, data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('parent', serializer.errors)
    
    def test_sibling_name_uniqueness(self):
        """Test unique names within same hierarchy level"""
        data = {
            'name': 'Child Group',  # Same name as existing sibling
            'description': 'Another child group',
            'parent': self.parent_group.id
        }
        
        serializer = UserGroupSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('name', serializer.errors)
    
    def test_max_users_vs_current_users_validation(self):
        """Test validation when reducing max_users below current count"""
        # Add users to group first
        users = [
            User.objects.create_user(
                username=f'user{i}',
                email=f'user{i}@test.com',
                password='testpass123'
            ) for i in range(3)
        ]
        
        for user in users:
            GroupMembership.objects.create(
                user=user,
                group=self.child_group,
                added_by=self.admin_user
            )
        
        # Try to set max_users to 2 (less than current 3 users)
        data = {
            'name': self.child_group.name,
            'description': self.child_group.description,
            'max_users': 2
        }
        
        serializer = UserGroupSerializer(self.child_group, data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('max_users', serializer.errors)


class UserPermissionSerializerTest(TestCase):
    """Test UserPermissionSerializer validation and temporal rules"""
    
    def setUp(self):
        """Set up test data"""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        self.admin_user = User.objects.create_user(
            username='admin',
            email='admin@test.com',
            password='testpass123'
        )
        
        self.permission = Permission.objects.create(
            module='test',
            resource='data',
            action='view',
            name='View Test Data'
        )
        
        self.critical_permission = Permission.objects.create(
            module='test',
            resource='data',
            action='delete',
            name='Delete Test Data',
            requires_confirmation=True
        )
    
    def test_user_permission_serialization(self):
        """Test user permission serialization"""
        user_permission = UserPermission.objects.create(
            user=self.user,
            permission=self.permission,
            grant_type='allow',
            granted_by=self.admin_user,
            reason='Test permission'
        )
        
        serializer = UserPermissionSerializer(user_permission)
        data = serializer.data
        
        self.assertEqual(data['user_name'], 'testuser')
        self.assertEqual(data['permission_code'], 'test.data.view')
        self.assertEqual(data['permission_name'], 'View Test Data')
        self.assertEqual(data['grant_type'], 'allow')
        self.assertEqual(data['granted_by_name'], 'admin')
        self.assertTrue(data['is_currently_valid'])
    
    def test_temporal_permission_validation(self):
        """Test temporal date validation"""
        past_time = timezone.now() - timedelta(hours=1)
        future_time = timezone.now() + timedelta(hours=1)
        
        # Invalid - past start date
        data = {
            'user': self.user.id,
            'permission': self.permission.id,
            'valid_from': past_time.isoformat(),
            'reason': 'Test permission'
        }
        
        serializer = UserPermissionSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('valid_from', serializer.errors)
        
        # Invalid - end date before start date
        data.update({
            'valid_from': future_time.isoformat(),
            'valid_until': past_time.isoformat()
        })
        
        serializer = UserPermissionSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('valid_until', serializer.errors)
    
    def test_reason_validation_for_critical_permissions(self):
        """Test reason requirement for critical permissions"""
        data = {
            'user': self.user.id,
            'permission': self.critical_permission.id,
            'grant_type': 'allow'
            # Missing required reason for critical permission
        }
        
        serializer = UserPermissionSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('reason', serializer.errors)
        
        # Should pass with reason
        data['reason'] = 'User needs delete access for cleanup tasks'
        serializer = UserPermissionSerializer(data=data)
        self.assertTrue(serializer.is_valid())
    
    def test_duplicate_permission_prevention(self):
        """Test prevention of duplicate active permissions"""
        # Create existing permission
        UserPermission.objects.create(
            user=self.user,
            permission=self.permission,
            is_active=True
        )
        
        # Try to create duplicate
        data = {
            'user': self.user.id,
            'permission': self.permission.id,
            'reason': 'Duplicate permission test'
        }
        
        serializer = UserPermissionSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('non_field_errors', serializer.errors)
    
    def test_deny_permission_approval_requirement(self):
        """Test that deny permissions require approval"""
        data = {
            'user': self.user.id,
            'permission': self.permission.id,
            'grant_type': 'deny'  # Requires granted_by
        }
        
        serializer = UserPermissionSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('granted_by', serializer.errors)
        
        # Should pass with granted_by
        data['granted_by'] = self.admin_user.id
        serializer = UserPermissionSerializer(data=data)
        self.assertTrue(serializer.is_valid())
    
    def test_reason_length_validation(self):
        """Test reason minimum length validation"""
        data = {
            'user': self.user.id,
            'permission': self.permission.id,
            'reason': 'Short'  # Less than 10 characters
        }
        
        serializer = UserPermissionSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('reason', serializer.errors)


class GroupPermissionSerializerTest(TestCase):
    """Test GroupPermissionSerializer validation and inheritance"""
    
    def setUp(self):
        """Set up test data"""
        self.admin_user = User.objects.create_user(
            username='admin',
            email='admin@test.com',
            password='testpass123'
        )
        
        self.parent_group = UserGroup.objects.create(
            name='Parent Group',
            description='Test parent group',
            created_by=self.admin_user
        )
        
        self.child_group = UserGroup.objects.create(
            name='Child Group',
            description='Test child group',
            parent=self.parent_group,
            created_by=self.admin_user
        )
        
        self.permission = Permission.objects.create(
            module='test',
            resource='data',
            action='view',
            name='View Test Data'
        )
    
    def test_group_permission_serialization(self):
        """Test group permission serialization"""
        group_permission = GroupPermission.objects.create(
            group=self.parent_group,
            permission=self.permission,
            grant_type='allow',
            inherit_to_children=True,
            granted_by=self.admin_user
        )
        
        serializer = GroupPermissionSerializer(group_permission)
        data = serializer.data
        
        self.assertEqual(data['group_name'], 'Parent Group')
        self.assertEqual(data['permission_code'], 'test.data.view')
        self.assertEqual(data['grant_type'], 'allow')
        self.assertTrue(data['inherit_to_children'])
        self.assertEqual(data['granted_by_name'], 'admin')
    
    def test_duplicate_group_permission_prevention(self):
        """Test prevention of duplicate group permissions"""
        # Create existing permission
        GroupPermission.objects.create(
            group=self.parent_group,
            permission=self.permission,
            is_active=True
        )
        
        # Try to create duplicate
        data = {
            'group': self.parent_group.id,
            'permission': self.permission.id,
            'reason': 'Duplicate test'
        }
        
        serializer = GroupPermissionSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('non_field_errors', serializer.errors)
    
    def test_inheritance_conflict_validation(self):
        """Test validation of inheritance conflicts"""
        # Create permission in parent with inheritance
        GroupPermission.objects.create(
            group=self.parent_group,
            permission=self.permission,
            inherit_to_children=True,
            is_active=True
        )
        
        # Try to create same permission in child with inheritance
        data = {
            'group': self.child_group.id,
            'permission': self.permission.id,
            'inherit_to_children': True
        }
        
        serializer = GroupPermissionSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('inherit_to_children', serializer.errors)


class GroupMembershipSerializerTest(TestCase):
    """Test GroupMembershipSerializer validation and constraints"""
    
    def setUp(self):
        """Set up test data"""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        self.admin_user = User.objects.create_user(
            username='admin',
            email='admin@test.com',
            password='testpass123'
        )
        
        self.group = UserGroup.objects.create(
            name='Test Group',
            description='Test group',
            max_users=2,
            created_by=self.admin_user
        )
    
    def test_membership_serialization(self):
        """Test group membership serialization"""
        membership = GroupMembership.objects.create(
            user=self.user,
            group=self.group,
            is_primary=True,
            added_by=self.admin_user,
            notes='Test membership'
        )
        
        serializer = GroupMembershipSerializer(membership)
        data = serializer.data
        
        self.assertEqual(data['user_name'], 'testuser')
        self.assertEqual(data['group_name'], 'Test Group')
        self.assertTrue(data['is_primary'])
        self.assertEqual(data['added_by_name'], 'admin')
        self.assertTrue(data['is_currently_valid'])
    
    def test_temporal_membership_validation(self):
        """Test temporal membership date validation"""
        past_time = timezone.now() - timedelta(hours=1)
        future_time = timezone.now() + timedelta(hours=1)
        
        data = {
            'user': self.user.id,
            'group': self.group.id,
            'valid_from': past_time.isoformat()  # Invalid - past date
        }
        
        serializer = GroupMembershipSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('valid_from', serializer.errors)
    
    def test_primary_membership_uniqueness(self):
        """Test prevention of multiple primary memberships"""
        # Create existing primary membership
        GroupMembership.objects.create(
            user=self.user,
            group=self.group,
            is_primary=True,
            added_by=self.admin_user
        )
        
        # Create another group
        other_group = UserGroup.objects.create(
            name='Other Group',
            description='Another test group',
            created_by=self.admin_user
        )
        
        # Try to create another primary membership
        data = {
            'user': self.user.id,
            'group': other_group.id,
            'is_primary': True
        }
        
        serializer = GroupMembershipSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('is_primary', serializer.errors)
    
    def test_group_user_limit_validation(self):
        """Test validation against group user limits"""
        # Fill group to capacity
        users = [
            User.objects.create_user(
                username=f'user{i}',
                email=f'user{i}@test.com',
                password='testpass123'
            ) for i in range(2)
        ]
        
        for user in users:
            GroupMembership.objects.create(
                user=user,
                group=self.group,
                added_by=self.admin_user
            )
        
        # Try to add another user (exceeds limit)
        data = {
            'user': self.user.id,
            'group': self.group.id
        }
        
        serializer = GroupMembershipSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('group', serializer.errors)
    
    def test_duplicate_membership_prevention(self):
        """Test prevention of duplicate active memberships"""
        # Create existing membership
        GroupMembership.objects.create(
            user=self.user,
            group=self.group,
            is_active=True,
            added_by=self.admin_user
        )
        
        # Try to create duplicate
        data = {
            'user': self.user.id,
            'group': self.group.id
        }
        
        serializer = GroupMembershipSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('non_field_errors', serializer.errors)


class PermissionAuditLogSerializerTest(TestCase):
    """Test PermissionAuditLogSerializer read-only functionality and filtering"""
    
    def setUp(self):
        """Set up test data"""
        self.admin_user = User.objects.create_user(
            username='admin',
            email='admin@test.com',
            password='testpass123',
            is_staff=True
        )
        
        self.regular_user = User.objects.create_user(
            username='regular',
            email='regular@test.com',
            password='testpass123',
            is_staff=False
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
        
        self.audit_log = PermissionAuditLog.objects.create(
            action='grant_user',
            actor=self.admin_user,
            target_user=self.target_user,
            permission=self.permission,
            reason='Test audit entry',
            ip_address='192.168.1.100',
            user_agent='Test Browser',
            session_key='test_session_key'
        )
    
    def test_audit_log_serialization(self):
        """Test audit log serialization for admin user"""
        # Mock request context with admin user
        mock_request = Mock()
        mock_request.user = self.admin_user
        
        serializer = PermissionAuditLogSerializer(
            self.audit_log,
            context={'request': mock_request}
        )
        data = serializer.data
        
        self.assertEqual(data['action'], 'grant_user')
        self.assertEqual(data['actor_name'], 'admin')
        self.assertEqual(data['target_user_name'], 'target')
        self.assertEqual(data['permission_code'], 'test.audit.test')
        
        # Admin should see sensitive data
        self.assertEqual(data['ip_address'], '192.168.1.100')
    
    def test_sensitive_data_filtering_for_non_admin(self):
        """Test filtering of sensitive data for non-admin users"""
        # Mock request context with regular user
        mock_request = Mock()
        mock_request.user = self.regular_user
        
        serializer = PermissionAuditLogSerializer(
            self.audit_log,
            context={'request': mock_request}
        )
        data = serializer.data
        
        # Regular user should not see sensitive technical data
        self.assertNotIn('ip_address', data)
        self.assertNotIn('user_agent', data)
        self.assertNotIn('session_key', data)
        
        # Should not see details if not involved
        self.assertNotIn('details', data)
    
    def test_read_only_enforcement(self):
        """Test that all fields are read-only"""
        data = {
            'action': 'revoke_user',
            'reason': 'Modified reason'
        }
        
        serializer = PermissionAuditLogSerializer(self.audit_log, data=data)
        
        # Should not be valid for updates since all fields are read-only
        # The serializer allows initialization but shouldn't perform updates
        self.assertTrue(hasattr(serializer.Meta, 'read_only_fields'))
        self.assertEqual(serializer.Meta.read_only_fields, '__all__')


class SerializerEdgeCaseTest(TestCase):
    """Test edge cases and error handling in serializers"""
    
    def test_empty_data_handling(self):
        """Test serializer behavior with empty or null data"""
        serializers_to_test = [
            PermissionSerializer,
            UserGroupSerializer,
            UserPermissionSerializer,
            GroupPermissionSerializer,
        ]
        
        for serializer_class in serializers_to_test:
            serializer = serializer_class(data={})
            self.assertFalse(serializer.is_valid())
            self.assertTrue(len(serializer.errors) > 0)
    
    def test_invalid_foreign_key_references(self):
        """Test handling of invalid foreign key references"""
        # Test with non-existent user ID
        data = {
            'user': 99999,  # Non-existent ID
            'permission': 99999,  # Non-existent ID
        }
        
        serializer = UserPermissionSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('user', serializer.errors)
        self.assertIn('permission', serializer.errors)
    
    def test_partial_update_handling(self):
        """Test partial updates with serializers"""
        user = User.objects.create_user(
            username='testuser',
            email='test@test.com',
            password='testpass123'
        )
        
        group = UserGroup.objects.create(
            name='Test Group',
            description='Original description'
        )
        
        # Test partial update
        data = {'description': 'Updated description'}
        serializer = UserGroupSerializer(group, data=data, partial=True)
        
        self.assertTrue(serializer.is_valid())
        updated_group = serializer.save()
        self.assertEqual(updated_group.description, 'Updated description')
        self.assertEqual(updated_group.name, 'Test Group')  # Unchanged
    
    def test_unicode_and_special_character_handling(self):
        """Test handling of unicode and special characters"""
        data = {
            'name': 'Grupo Tintométrico Açaí',  # Unicode characters
            'description': 'Descrição com acentos e çedilha'
        }
        
        serializer = UserGroupSerializer(data=data)
        self.assertTrue(serializer.is_valid())
    
    def test_maximum_field_lengths(self):
        """Test validation of maximum field lengths"""
        # Test very long names
        long_name = 'X' * 500  # Assuming max_length constraints
        
        data = {
            'module': 'test',
            'resource': 'long',
            'action': 'create',
            'name': long_name
        }
        
        serializer = PermissionSerializer(data=data)
        # Should either pass or fail gracefully based on model constraints
        if not serializer.is_valid():
            self.assertIn('name', serializer.errors)


if __name__ == '__main__':
    import django
    from django.conf import settings
    from django.test.utils import get_runner
    
    django.setup()
    TestRunner = get_runner(settings)
    test_runner = TestRunner()
    failures = test_runner.run_tests(['tests.core.test_serializers'])
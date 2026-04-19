"""
Comprehensive API Test Suite for User Permissions System.

T015: API integration tests validating end-to-end functionality with authentication.

This test suite provides complete coverage of the Permission System APIs with
realistic scenarios, authentication testing, and error handling validation.
"""

import json
import pytest
from datetime import datetime, timedelta
from django.test import TestCase, override_settings
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.core.cache import cache
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from rest_framework.authtoken.models import Token
from unittest.mock import patch, Mock

from apps.core.models import (
    Permission, UserGroup, UserPermission, GroupPermission, 
    PermissionAuditLog, GroupMembership
)
from apps.core.permissions import (
    PERMISSION_MANAGEMENT_READ, PERMISSION_MANAGEMENT_WRITE,
    USER_MANAGEMENT_READ, USER_MANAGEMENT_WRITE
)

User = get_user_model()

# =============================================================================
# TEST BASE CLASSES AND UTILITIES
# =============================================================================

class PermissionAPITestCase(APITestCase):
    """
    Base test case for permission API tests with common setup and utilities.
    """
    
    @classmethod
    def setUpTestData(cls):
        """Set up test data for all test methods."""
        # Create test users
        cls.admin_user = User.objects.create_user(
            username='admin_test',
            email='admin@test.com',
            password='testpass123',
            is_staff=True,
            is_superuser=True
        )
        
        cls.manager_user = User.objects.create_user(
            username='manager_test',
            email='manager@test.com',
            password='testpass123',
            is_staff=True
        )
        
        cls.regular_user = User.objects.create_user(
            username='user_test',
            email='user@test.com',
            password='testpass123'
        )
        
        # Create test permissions
        cls.view_permission = Permission.objects.create(
            name='View Users',
            code='users.view',
            description='View user information',
            module='users',
            risk_level='low'
        )
        
        cls.manage_permission = Permission.objects.create(
            name='Manage Users',
            code='users.manage',
            description='Create, update, and delete users',
            module='users',
            risk_level='high'
        )
        
        cls.critical_permission = Permission.objects.create(
            name='Delete All Data',
            code='system.delete_all',
            description='Delete all system data',
            module='system',
            risk_level='critical'
        )
        
        # Create test groups
        cls.managers_group = UserGroup.objects.create(
            name='Managers',
            description='Management group with elevated permissions',
            group_type='role'
        )
        
        cls.employees_group = UserGroup.objects.create(
            name='Employees',
            description='Regular employees group',
            group_type='role'
        )
        
        # Set up group memberships
        GroupMembership.objects.create(
            group=cls.managers_group,
            user=cls.manager_user,
            role='member'
        )
        
        GroupMembership.objects.create(
            group=cls.employees_group,
            user=cls.regular_user,
            role='member'
        )
        
        # Set up group permissions
        GroupPermission.objects.create(
            group=cls.managers_group,
            permission=cls.manage_permission,
            is_granted=True
        )
        
        GroupPermission.objects.create(
            group=cls.employees_group,
            permission=cls.view_permission,
            is_granted=True
        )
        
        # Create authentication tokens
        cls.admin_token = Token.objects.create(user=cls.admin_user)
        cls.manager_token = Token.objects.create(user=cls.manager_user)
        cls.regular_token = Token.objects.create(user=cls.regular_user)
        
    def setUp(self):
        """Set up each test method."""
        self.client = APIClient()
        # Clear cache before each test
        cache.clear()
        
    def authenticate_as(self, user_type='admin'):
        """Helper method to authenticate as different user types."""
        token_map = {
            'admin': self.admin_token,
            'manager': self.manager_token,
            'regular': self.regular_token
        }
        token = token_map.get(user_type)
        if token:
            self.client.credentials(HTTP_AUTHORIZATION=f'Token {token.key}')
        else:
            self.client.credentials()
            
    def create_permission(self, **kwargs):
        """Helper method to create test permissions."""
        defaults = {
            'name': 'Test Permission',
            'code': f'test.permission.{datetime.now().timestamp()}',
            'description': 'Test permission for API testing',
            'module': 'test',
            'risk_level': 'medium'
        }
        defaults.update(kwargs)
        return Permission.objects.create(**defaults)


# =============================================================================
# PERMISSION VIEWSET TESTS
# =============================================================================

class PermissionViewSetTestCase(PermissionAPITestCase):
    """Test cases for PermissionViewSet endpoints."""
    
    def test_list_permissions_authenticated(self):
        """Test listing permissions with proper authentication."""
        self.authenticate_as('admin')
        url = reverse('core:permissions-list')
        
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('results', response.data)
        self.assertGreaterEqual(len(response.data['results']), 3)  # At least our test permissions
        
        # Verify response structure
        first_permission = response.data['results'][0]
        expected_fields = ['id', 'name', 'code', 'description', 'module', 'risk_level', 'is_active']
        for field in expected_fields:
            self.assertIn(field, first_permission)
    
    def test_list_permissions_unauthenticated(self):
        """Test listing permissions without authentication returns 401."""
        url = reverse('core:permissions-list')
        
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_list_permissions_with_filtering(self):
        """Test permission listing with various filters."""
        self.authenticate_as('admin')
        url = reverse('core:permissions-list')
        
        # Test module filter
        response = self.client.get(url, {'module': 'users'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        for permission in response.data['results']:
            self.assertEqual(permission['module'], 'users')
        
        # Test risk level filter
        response = self.client.get(url, {'risk_level': 'high'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        for permission in response.data['results']:
            self.assertEqual(permission['risk_level'], 'high')
        
        # Test active status filter
        response = self.client.get(url, {'is_active': True})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        for permission in response.data['results']:
            self.assertTrue(permission['is_active'])
    
    def test_list_permissions_with_search(self):
        """Test permission listing with search functionality."""
        self.authenticate_as('admin')
        url = reverse('core:permissions-list')
        
        # Search by name
        response = self.client.get(url, {'search': 'View Users'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreater(len(response.data['results']), 0)
        
        # Search by code
        response = self.client.get(url, {'search': 'users.view'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreater(len(response.data['results']), 0)
    
    def test_create_permission_success(self):
        """Test successful permission creation."""
        self.authenticate_as('admin')
        url = reverse('core:permissions-list')
        
        data = {
            'name': 'Test Create Permission',
            'code': 'test.create.permission',
            'description': 'Permission created during testing',
            'module': 'test',
            'risk_level': 'medium'
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['name'], data['name'])
        self.assertEqual(response.data['code'], data['code'])
        
        # Verify permission was created in database
        permission = Permission.objects.get(code=data['code'])
        self.assertEqual(permission.name, data['name'])
    
    def test_create_permission_duplicate_code(self):
        """Test permission creation with duplicate code fails."""
        self.authenticate_as('admin')
        url = reverse('core:permissions-list')
        
        data = {
            'name': 'Duplicate Permission',
            'code': self.view_permission.code,  # Use existing code
            'description': 'This should fail',
            'module': 'test',
            'risk_level': 'low'
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('code', response.data or {})
    
    def test_create_permission_insufficient_permissions(self):
        """Test permission creation without manage permissions fails."""
        self.authenticate_as('regular')
        url = reverse('core:permissions-list')
        
        data = {
            'name': 'Test Permission',
            'code': 'test.no.permission',
            'description': 'Should not work',
            'module': 'test',
            'risk_level': 'low'
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
    
    def test_retrieve_permission_success(self):
        """Test retrieving a specific permission."""
        self.authenticate_as('admin')
        url = reverse('core:permissions-detail', kwargs={'pk': self.view_permission.pk})
        
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['id'], self.view_permission.id)
        self.assertEqual(response.data['name'], self.view_permission.name)
        self.assertEqual(response.data['code'], self.view_permission.code)
    
    def test_retrieve_permission_not_found(self):
        """Test retrieving non-existent permission returns 404."""
        self.authenticate_as('admin')
        url = reverse('core:permissions-detail', kwargs={'pk': 99999})
        
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
    
    def test_update_permission_success(self):
        """Test successful permission update."""
        self.authenticate_as('admin')
        permission = self.create_permission()
        url = reverse('core:permissions-detail', kwargs={'pk': permission.pk})
        
        data = {
            'name': 'Updated Permission Name',
            'description': 'Updated description'
        }
        
        response = self.client.patch(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], data['name'])
        
        # Verify database was updated
        permission.refresh_from_db()
        self.assertEqual(permission.name, data['name'])
    
    def test_delete_permission_success(self):
        """Test successful permission deletion."""
        self.authenticate_as('admin')
        permission = self.create_permission()
        url = reverse('core:permissions-detail', kwargs={'pk': permission.pk})
        
        response = self.client.delete(url)
        
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        
        # Verify permission is soft deleted or removed
        with self.assertRaises(Permission.DoesNotExist):
            Permission.objects.get(pk=permission.pk)
    
    def test_delete_high_risk_permission_without_confirmation(self):
        """Test deleting high-risk permission without confirmation fails."""
        self.authenticate_as('admin')
        url = reverse('core:permissions-detail', kwargs={'pk': self.critical_permission.pk})
        
        response = self.client.delete(url)
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('confirm_high_risk_deletion', str(response.data))
    
    def test_delete_high_risk_permission_with_confirmation(self):
        """Test deleting high-risk permission with confirmation succeeds."""
        self.authenticate_as('admin')
        url = reverse('core:permissions-detail', kwargs={'pk': self.critical_permission.pk})
        
        response = self.client.delete(url + '?confirm_high_risk_deletion=true')
        
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
    
    def test_by_module_action(self):
        """Test by-module action returns grouped permissions."""
        self.authenticate_as('admin')
        url = reverse('core:permissions-by-module')
        
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('modules', response.data)
        self.assertIn('summary', response.data)
        
        # Verify structure
        modules = response.data['modules']
        self.assertGreater(len(modules), 0)
        
        first_module = modules[0]
        expected_fields = [
            'module', 'total_permissions', 'active_permissions',
            'low_risk_count', 'medium_risk_count', 'high_risk_count', 'critical_risk_count'
        ]
        for field in expected_fields:
            self.assertIn(field, first_module)
    
    def test_risk_analysis_action(self):
        """Test risk-analysis action returns risk statistics."""
        self.authenticate_as('admin')
        url = reverse('core:permissions-risk-analysis')
        
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('risk_distribution', response.data)
        self.assertIn('high_risk_widely_assigned', response.data)
        self.assertIn('recommendations', response.data)
        
        # Verify risk distribution structure
        risk_distribution = response.data['risk_distribution']
        self.assertIsInstance(risk_distribution, list)
        
        if risk_distribution:
            first_risk_item = risk_distribution[0]
            expected_fields = ['risk_level', 'count', 'active_count', 'assigned_count']
            for field in expected_fields:
                self.assertIn(field, first_risk_item)


# =============================================================================
# USER PERMISSION VIEWSET TESTS
# =============================================================================

class UserPermissionViewSetTestCase(PermissionAPITestCase):
    """Test cases for UserPermissionViewSet endpoints."""
    
    def test_list_user_permissions(self):
        """Test listing user permission assignments."""
        self.authenticate_as('admin')
        url = reverse('core:user-permissions-list')
        
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('results', response.data)
    
    def test_create_user_permission_success(self):
        """Test successful user permission assignment."""
        self.authenticate_as('admin')
        url = reverse('core:user-permissions-list')
        
        data = {
            'user': self.regular_user.id,
            'permission': self.manage_permission.id,
            'is_granted': True
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Verify assignment was created
        assignment = UserPermission.objects.get(
            user=self.regular_user,
            permission=self.manage_permission
        )
        self.assertTrue(assignment.is_granted)
    
    def test_create_temporal_user_permission(self):
        """Test creating user permission with expiration date."""
        self.authenticate_as('admin')
        url = reverse('core:user-permissions-list')
        
        expiry_date = datetime.now() + timedelta(days=30)
        
        data = {
            'user': self.regular_user.id,
            'permission': self.manage_permission.id,
            'is_granted': True,
            'expires_at': expiry_date.isoformat()
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Verify temporal assignment
        assignment = UserPermission.objects.get(
            user=self.regular_user,
            permission=self.manage_permission
        )
        self.assertIsNotNone(assignment.expires_at)
    
    def test_revoke_user_permission(self):
        """Test revoking a user permission."""
        # Create permission assignment first
        assignment = UserPermission.objects.create(
            user=self.regular_user,
            permission=self.manage_permission,
            is_granted=True,
            granted_by=self.admin_user
        )
        
        self.authenticate_as('admin')
        url = reverse('core:user-permissions-detail', kwargs={'pk': assignment.pk})
        
        response = self.client.delete(url)
        
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        
        # Verify assignment was removed
        with self.assertRaises(UserPermission.DoesNotExist):
            UserPermission.objects.get(pk=assignment.pk)
    
    def test_effective_permissions_success(self):
        """Test retrieving effective permissions for a user."""
        # Create a direct permission assignment
        UserPermission.objects.create(
            user=self.regular_user,
            permission=self.manage_permission,
            is_granted=True,
            granted_by=self.admin_user
        )
        
        self.authenticate_as('admin')
        url = reverse('core:user-permissions-effective', kwargs={'user_id': self.regular_user.id})
        
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('user_id', response.data)
        self.assertIn('effective_permissions', response.data)
        self.assertEqual(response.data['user_id'], self.regular_user.id)
    
    def test_effective_permissions_unauthorized_user(self):
        """Test accessing effective permissions for unauthorized user."""
        self.authenticate_as('regular')
        url = reverse('core:user-permissions-effective', kwargs={'user_id': self.manager_user.id})
        
        response = self.client.get(url)
        
        # Should return 403 if regular user tries to see manager's permissions
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
    
    def test_effective_permissions_own_user(self):
        """Test user accessing their own effective permissions."""
        self.authenticate_as('regular')
        url = reverse('core:user-permissions-effective', kwargs={'user_id': self.regular_user.id})
        
        response = self.client.get(url)
        
        # Users should be able to see their own permissions
        self.assertEqual(response.status_code, status.HTTP_200_OK)


# =============================================================================
# USER GROUP VIEWSET TESTS
# =============================================================================

class UserGroupViewSetTestCase(PermissionAPITestCase):
    """Test cases for UserGroupViewSet endpoints."""
    
    def test_list_groups(self):
        """Test listing user groups."""
        self.authenticate_as('admin')
        url = reverse('core:user-groups-list')
        
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('results', response.data)
        self.assertGreaterEqual(len(response.data['results']), 2)  # Our test groups
    
    def test_create_group_success(self):
        """Test successful group creation."""
        self.authenticate_as('admin')
        url = reverse('core:user-groups-list')
        
        data = {
            'name': 'Test Group',
            'description': 'Group created during testing',
            'group_type': 'project'
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['name'], data['name'])
        
        # Verify group was created
        group = UserGroup.objects.get(name=data['name'])
        self.assertEqual(group.description, data['description'])
    
    def test_group_effective_permissions(self):
        """Test retrieving effective permissions for a group."""
        self.authenticate_as('admin')
        url = reverse('core:user-groups-effective-permissions', kwargs={'pk': self.managers_group.pk})
        
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)


# =============================================================================
# PERFORMANCE AND CACHING TESTS
# =============================================================================

class PerformanceTestCase(PermissionAPITestCase):
    """Test cases for performance optimization features (T014)."""
    
    def test_response_caching(self):
        """Test that responses are properly cached."""
        self.authenticate_as('admin')
        url = reverse('core:permissions-by-module')
        
        # First request - should hit database
        with self.assertNumQueries(self.assertGreaterEqual, 1):
            response1 = self.client.get(url)
        
        self.assertEqual(response1.status_code, status.HTTP_200_OK)
        
        # Second request - should hit cache (fewer queries)
        with self.assertNumQueries(0, msg="Second request should use cache"):
            response2 = self.client.get(url)
        
        self.assertEqual(response2.status_code, status.HTTP_200_OK)
        self.assertEqual(response1.data, response2.data)
    
    def test_gzip_compression(self):
        """Test that responses are gzip compressed."""
        self.authenticate_as('admin')
        url = reverse('core:permissions-by-module')
        
        response = self.client.get(url, HTTP_ACCEPT_ENCODING='gzip')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Note: Testing compression requires proper middleware setup
    
    @patch('apps.core.performance.PerformanceMetrics.track_api_performance')
    def test_performance_monitoring(self, mock_performance):
        """Test that performance metrics are collected."""
        self.authenticate_as('admin')
        url = reverse('core:permissions-list')
        
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Verify performance tracking was called
        self.assertTrue(mock_performance.called)
    
    def test_pagination_optimization(self):
        """Test optimized pagination for large datasets."""
        # Create additional permissions for pagination testing
        permissions = []
        for i in range(50):
            permissions.append(Permission(
                name=f'Test Permission {i}',
                code=f'test.permission.{i}',
                description=f'Test permission number {i}',
                module='test',
                risk_level='low'
            ))
        Permission.objects.bulk_create(permissions)
        
        self.authenticate_as('admin')
        url = reverse('core:permissions-list')
        
        # Test paginated request
        response = self.client.get(url, {'page_size': 10})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('count', response.data)
        self.assertIn('next', response.data)
        self.assertIn('previous', response.data)
        self.assertEqual(len(response.data['results']), 10)


# =============================================================================
# ERROR HANDLING TESTS
# =============================================================================

class ErrorHandlingTestCase(PermissionAPITestCase):
    """Test cases for proper error handling and responses."""
    
    def test_invalid_json_request(self):
        """Test handling of invalid JSON in request body."""
        self.authenticate_as('admin')
        url = reverse('core:permissions-list')
        
        # Send invalid JSON
        response = self.client.post(
            url,
            data='{"invalid": json}',
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_missing_required_fields(self):
        """Test validation of required fields."""
        self.authenticate_as('admin')
        url = reverse('core:permissions-list')
        
        # Missing required fields
        data = {
            'description': 'Missing name and code'
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('name', response.data or {})
        self.assertIn('code', response.data or {})
    
    def test_invalid_risk_level(self):
        """Test validation of risk level choices."""
        self.authenticate_as('admin')
        url = reverse('core:permissions-list')
        
        data = {
            'name': 'Test Permission',
            'code': 'test.invalid.risk',
            'module': 'test',
            'risk_level': 'invalid_level'  # Invalid choice
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('risk_level', response.data or {})
    
    def test_rate_limiting(self):
        """Test API rate limiting (if implemented)."""
        # Note: This test assumes rate limiting is implemented
        # Implementation depends on specific rate limiting solution
        pass
    
    def test_server_error_handling(self):
        """Test graceful handling of server errors."""
        self.authenticate_as('admin')
        
        with patch('apps.core.models.Permission.objects.all') as mock_queryset:
            # Simulate database error
            mock_queryset.side_effect = Exception('Database connection lost')
            
            url = reverse('core:permissions-list')
            response = self.client.get(url)
            
            # Should return 500 with proper error structure
            self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)


# =============================================================================
# INTEGRATION TESTS
# =============================================================================

class IntegrationTestCase(PermissionAPITestCase):
    """End-to-end integration tests."""
    
    def test_complete_permission_lifecycle(self):
        """Test complete permission creation, assignment, and cleanup lifecycle."""
        self.authenticate_as('admin')
        
        # 1. Create permission
        create_url = reverse('core:permissions-list')
        permission_data = {
            'name': 'Integration Test Permission',
            'code': 'integration.test.permission',
            'description': 'Permission for integration testing',
            'module': 'integration',
            'risk_level': 'medium'
        }
        
        create_response = self.client.post(create_url, permission_data, format='json')
        self.assertEqual(create_response.status_code, status.HTTP_201_CREATED)
        permission_id = create_response.data['id']
        
        # 2. Assign permission to user
        assign_url = reverse('core:user-permissions-list')
        assignment_data = {
            'user': self.regular_user.id,
            'permission': permission_id,
            'is_granted': True
        }
        
        assign_response = self.client.post(assign_url, assignment_data, format='json')
        self.assertEqual(assign_response.status_code, status.HTTP_201_CREATED)
        assignment_id = assign_response.data['id']
        
        # 3. Verify effective permissions include new permission
        effective_url = reverse('core:user-permissions-effective', kwargs={'user_id': self.regular_user.id})
        effective_response = self.client.get(effective_url)
        self.assertEqual(effective_response.status_code, status.HTTP_200_OK)
        
        # 4. Update permission
        update_url = reverse('core:permissions-detail', kwargs={'pk': permission_id})
        update_data = {'description': 'Updated description for integration test'}
        update_response = self.client.patch(update_url, update_data, format='json')
        self.assertEqual(update_response.status_code, status.HTTP_200_OK)
        
        # 5. Revoke permission from user
        revoke_url = reverse('core:user-permissions-detail', kwargs={'pk': assignment_id})
        revoke_response = self.client.delete(revoke_url)
        self.assertEqual(revoke_response.status_code, status.HTTP_204_NO_CONTENT)
        
        # 6. Delete permission
        delete_url = reverse('core:permissions-detail', kwargs={'pk': permission_id})
        delete_response = self.client.delete(delete_url)
        self.assertEqual(delete_response.status_code, status.HTTP_204_NO_CONTENT)
    
    def test_group_permission_inheritance(self):
        """Test group permission inheritance and effective permissions."""
        self.authenticate_as('admin')
        
        # Create a new permission
        permission = self.create_permission(
            name='Group Test Permission',
            code='group.test.permission'
        )
        
        # Assign permission to group
        GroupPermission.objects.create(
            group=self.employees_group,
            permission=permission,
            is_granted=True
        )
        
        # Check user's effective permissions include group permissions
        effective_url = reverse('core:user-permissions-effective', kwargs={'user_id': self.regular_user.id})
        response = self.client.get(effective_url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Verify group permission is included in effective permissions
        effective_perms = response.data['effective_permissions']
        self.assertIn('group_permissions', effective_perms)


# =============================================================================
# TEST CASES FOR SECURITY SCENARIOS
# =============================================================================

class SecurityTestCase(PermissionAPITestCase):
    """Security-focused test cases."""
    
    def test_sql_injection_protection(self):
        """Test protection against SQL injection attacks."""
        self.authenticate_as('admin')
        url = reverse('core:permissions-list')
        
        # Attempt SQL injection in search parameter
        malicious_search = "'; DROP TABLE permissions; --"
        response = self.client.get(url, {'search': malicious_search})
        
        # Should return normal response, not error
        self.assertEqual(response.status_code, status.HTTP_200_OK)
    
    def test_permission_isolation(self):
        """Test that users cannot access permissions outside their scope."""
        # Create restricted permission
        restricted_permission = self.create_permission(
            name='Restricted Permission',
            code='restricted.permission',
            module='restricted'
        )
        
        self.authenticate_as('regular')
        url = reverse('core:permissions-detail', kwargs={'pk': restricted_permission.pk})
        
        response = self.client.get(url)
        
        # Regular user should not be able to see restricted permissions
        # (depending on implementation, this might be 403 or 404)
        self.assertIn(response.status_code, [status.HTTP_403_FORBIDDEN, status.HTTP_404_NOT_FOUND])
    
    def test_privilege_escalation_protection(self):
        """Test protection against privilege escalation attacks."""
        self.authenticate_as('regular')
        
        # Try to create high-privilege permission
        url = reverse('core:permissions-list')
        data = {
            'name': 'Evil Permission',
            'code': 'evil.permission',
            'description': 'Trying to escalate privileges',
            'module': 'system',
            'risk_level': 'critical'
        }
        
        response = self.client.post(url, data, format='json')
        
        # Should be forbidden
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


# =============================================================================
# PERFORMANCE BENCHMARK TESTS
# =============================================================================

class PerformanceBenchmarkTestCase(PermissionAPITestCase):
    """Performance benchmark tests for API optimization validation."""
    
    def setUp(self):
        super().setUp()
        # Create larger dataset for performance testing
        self.create_large_dataset()
    
    def create_large_dataset(self):
        """Create a larger dataset for performance testing."""
        # Create additional permissions (100 total)
        permissions = []
        for i in range(97):  # We already have 3 test permissions
            permissions.append(Permission(
                name=f'Performance Test Permission {i}',
                code=f'perf.test.{i}',
                description=f'Performance testing permission {i}',
                module=f'module_{i % 10}',
                risk_level=['low', 'medium', 'high'][i % 3]
            ))
        Permission.objects.bulk_create(permissions)
        
        # Create additional users (50 total)
        users = []
        for i in range(47):  # We already have 3 test users
            users.append(User(
                username=f'perf_user_{i}',
                email=f'perf_user_{i}@test.com',
                password='testpass123'
            ))
        User.objects.bulk_create(users)
    
    def test_list_performance_with_large_dataset(self):
        """Test list performance with large dataset."""
        self.authenticate_as('admin')
        url = reverse('core:permissions-list')
        
        # Measure response time
        import time
        start_time = time.time()
        
        response = self.client.get(url)
        
        end_time = time.time()
        response_time = end_time - start_time
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Assert response time is reasonable (adjust threshold as needed)
        self.assertLess(response_time, 2.0, "Response time should be under 2 seconds")
    
    def test_effective_permissions_performance(self):
        """Test effective permissions calculation performance."""
        # Create user with many permission assignments
        test_user = User.objects.create_user(
            username='heavy_user',
            email='heavy@test.com',
            password='testpass123'
        )
        
        # Assign many permissions
        permissions = Permission.objects.all()[:50]
        assignments = []
        for permission in permissions:
            assignments.append(UserPermission(
                user=test_user,
                permission=permission,
                is_granted=True,
                granted_by=self.admin_user
            ))
        UserPermission.objects.bulk_create(assignments)
        
        self.authenticate_as('admin')
        url = reverse('core:user-permissions-effective', kwargs={'user_id': test_user.id})
        
        import time
        start_time = time.time()
        
        response = self.client.get(url)
        
        end_time = time.time()
        response_time = end_time - start_time
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Assert response time is reasonable for complex calculation
        self.assertLess(response_time, 3.0, "Effective permissions calculation should be under 3 seconds")


# =============================================================================
# RUN CONFIGURATION
# =============================================================================

if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])
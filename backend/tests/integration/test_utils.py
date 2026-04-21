"""
T018: Integration Testing Utilities and Support Functions
Module: test_utils.py

Shared utilities, fixtures, and helper functions for permission API integration tests.
Provides common test setup, data factories, and assertion helpers.
"""

import json
import time
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Dict, List, Any, Optional
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.utils import timezone
from rest_framework.test import APIClient
from rest_framework import status
import factory
from factory.django import DjangoModelFactory

from apps.core.models import (
    Permission, UserGroup, UserPermission, GroupPermission,
    GroupMembership, PermissionAuditLog
)

User = get_user_model()


# =============================================================================
# FACTORY CLASSES FOR TEST DATA GENERATION
# =============================================================================

class UserFactory(DjangoModelFactory):
    """Factory for creating test users with realistic data."""
    
    class Meta:
        model = User
    
    username = factory.Sequence(lambda n: f'testuser{n}')
    email = factory.LazyAttribute(lambda obj: f'{obj.username}@test.com')
    first_name = factory.Faker('first_name')
    last_name = factory.Faker('last_name')
    is_active = True
    is_staff = False
    is_superuser = False
    
    @factory.post_generation
    def password(self, create, extracted, **kwargs):
        """Set a default password for test users."""
        if create:
            self.set_password('test_pass_123')
            self.save()


class AdminUserFactory(UserFactory):
    """Factory for creating admin users."""
    
    username = factory.Sequence(lambda n: f'admin{n}')
    is_staff = True
    is_superuser = True


class PermissionFactory(DjangoModelFactory):
    """Factory for creating test permissions."""
    
    class Meta:
        model = Permission
    
    code = factory.Sequence(lambda n: f'test.permission.{n}')
    name = factory.LazyAttribute(lambda obj: f'Test Permission {obj.code.split(".")[-1].title()}')
    description = factory.Faker('sentence')
    module = 'test'
    resource = 'permission'
    action = factory.Iterator(['view', 'create', 'update', 'delete', 'manage'])
    risk_level = factory.Iterator(['low', 'medium', 'high', 'critical'])
    is_active = True


class UserGroupFactory(DjangoModelFactory):
    """Factory for creating test user groups."""
    
    class Meta:
        model = UserGroup
    
    name = factory.Sequence(lambda n: f'Test Group {n}')
    description = factory.Faker('sentence')
    is_active = True


class UserPermissionFactory(DjangoModelFactory):
    """Factory for creating user permission assignments."""
    
    class Meta:
        model = UserPermission
    
    user = factory.SubFactory(UserFactory)
    permission = factory.SubFactory(PermissionFactory)
    is_granted = True
    granted_by = factory.SubFactory(AdminUserFactory)
    granted_at = factory.LazyFunction(timezone.now)
    reason = 'Test assignment'


class GroupPermissionFactory(DjangoModelFactory):
    """Factory for creating group permission assignments."""
    
    class Meta:
        model = GroupPermission
    
    group = factory.SubFactory(UserGroupFactory)
    permission = factory.SubFactory(PermissionFactory)
    is_granted = True
    granted_by = factory.SubFactory(AdminUserFactory)
    granted_at = factory.LazyFunction(timezone.now)
    reason = 'Test group assignment'


class GroupMembershipFactory(DjangoModelFactory):
    """Factory for creating group memberships."""
    
    class Meta:
        model = GroupMembership
    
    user = factory.SubFactory(UserFactory)
    group = factory.SubFactory(UserGroupFactory)
    added_by = factory.SubFactory(AdminUserFactory)
    added_at = factory.LazyFunction(timezone.now)


# =============================================================================
# TEST DATA BUILDERS
# =============================================================================

class PermissionTestDataBuilder:
    """Builder class for creating complex permission test scenarios."""
    
    def __init__(self):
        self.users = {}
        self.groups = {}
        self.permissions = {}
        self.assignments = []
    
    def add_user(self, role: str, **kwargs) -> User:
        """Add a user with a specific role."""
        defaults = {
            'regular_user': {'is_staff': False, 'is_superuser': False},
            'manager': {'is_staff': True, 'is_superuser': False},
            'admin': {'is_staff': True, 'is_superuser': True},
        }
        
        user_kwargs = defaults.get(role, {})
        user_kwargs.update(kwargs)
        
        user = UserFactory(**user_kwargs)
        self.users[role] = user
        return user
    
    def add_group(self, name: str, **kwargs) -> UserGroup:
        """Add a user group."""
        group = UserGroupFactory(name=name, **kwargs)
        self.groups[name] = group
        return group
    
    def add_permission(self, code: str, risk_level: str = 'low', **kwargs) -> Permission:
        """Add a permission with specified parameters."""
        parts = code.split('.')
        if len(parts) >= 3:
            module, resource, action = parts[0], parts[1], parts[2]
        else:
            module, resource, action = 'test', 'resource', 'action'
        
        permission = PermissionFactory(
            code=code,
            module=module,
            resource=resource,
            action=action,
            risk_level=risk_level,
            **kwargs
        )
        self.permissions[code] = permission
        return permission
    
    def grant_permission(self, user_role: str, permission_code: str, 
                        expires_at: Optional[datetime] = None, **kwargs):
        """Grant a permission to a user."""
        user = self.users[user_role]
        permission = self.permissions[permission_code]
        
        assignment = UserPermissionFactory(
            user=user,
            permission=permission,
            expires_at=expires_at,
            **kwargs
        )
        self.assignments.append(assignment)
        return assignment
    
    def grant_group_permission(self, group_name: str, permission_code: str, **kwargs):
        """Grant a permission to a group."""
        group = self.groups[group_name]
        permission = self.permissions[permission_code]
        
        assignment = GroupPermissionFactory(
            group=group,
            permission=permission,
            **kwargs
        )
        self.assignments.append(assignment)
        return assignment
    
    def add_user_to_group(self, user_role: str, group_name: str, **kwargs):
        """Add a user to a group."""
        user = self.users[user_role]
        group = self.groups[group_name]
        
        membership = GroupMembershipFactory(
            user=user,
            group=group,
            **kwargs
        )
        return membership
    
    def build_organizational_hierarchy(self):
        """Build a realistic organizational hierarchy for testing."""
        # Create users
        self.add_user('ceo', username='ceo_test')
        self.add_user('finance_manager', username='finance_mgr')
        self.add_user('sales_manager', username='sales_mgr')
        self.add_user('sales_rep1', username='sales_rep1')
        self.add_user('sales_rep2', username='sales_rep2')
        
        # Create groups
        self.add_group('Executives')
        self.add_group('Finance Department')
        self.add_group('Sales Department')
        self.add_group('Sales Team')
        
        # Create permissions
        self.add_permission('sales.order.view', 'low')
        self.add_permission('sales.order.create', 'medium')
        self.add_permission('sales.order.approve', 'high')
        self.add_permission('finance.report.view', 'medium')
        self.add_permission('finance.transaction.modify', 'critical')
        self.add_permission('admin.system.configure', 'critical')
        
        # Set up group memberships
        self.add_user_to_group('ceo', 'Executives')
        self.add_user_to_group('finance_manager', 'Finance Department')
        self.add_user_to_group('sales_manager', 'Sales Department')
        self.add_user_to_group('sales_rep1', 'Sales Team')
        self.add_user_to_group('sales_rep2', 'Sales Team')
        
        # Grant group permissions
        self.grant_group_permission('Sales Team', 'sales.order.view')
        self.grant_group_permission('Sales Team', 'sales.order.create')
        self.grant_group_permission('Sales Department', 'sales.order.approve')
        self.grant_group_permission('Finance Department', 'finance.report.view')
        self.grant_group_permission('Executives', 'admin.system.configure')
        
        return self


# =============================================================================
# TEST ASSERTION HELPERS
# =============================================================================

class PermissionAssertions:
    """Helper class for common permission test assertions."""
    
    @staticmethod
    def assert_permission_granted(user: User, permission_code: str, message: str = None):
        """Assert that a user has a specific permission."""
        if not message:
            message = f"User {user.username} should have permission {permission_code}"
        
        assert user.has_permission_new(permission_code), message
    
    @staticmethod
    def assert_permission_denied(user: User, permission_code: str, message: str = None):
        """Assert that a user does NOT have a specific permission."""
        if not message:
            message = f"User {user.username} should NOT have permission {permission_code}"
        
        assert not user.has_permission_new(permission_code), message
    
    @staticmethod
    def assert_api_response_format(response_data: Dict, required_fields: List[str]):
        """Assert that API response has required fields."""
        for field in required_fields:
            assert field in response_data, f"Response missing required field: {field}"
    
    @staticmethod
    def assert_error_response_format(response_data: Dict):
        """Assert that error response follows T017 error format."""
        required_error_fields = ['error', 'detail', 'timestamp', 'request_id']
        for field in required_error_fields:
            assert field in response_data, f"Error response missing field: {field}"
    
    @staticmethod
    def assert_audit_log_created(action: str, user: User = None, count: int = 1):
        """Assert that audit log entries were created."""
        logs = PermissionAuditLog.objects.filter(action=action)
        if user:
            logs = logs.filter(actor=user)
        
        assert logs.count() >= count, f"Expected at least {count} audit log(s) for action {action}"


# =============================================================================
# TEST PERFORMANCE UTILITIES
# =============================================================================

class PerformanceTimer:
    """Context manager for measuring test performance."""
    
    def __init__(self, max_duration: float = None):
        self.max_duration = max_duration
        self.start_time = None
        self.end_time = None
        self.duration = None
    
    def __enter__(self):
        self.start_time = time.time()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.end_time = time.time()
        self.duration = self.end_time - self.start_time
        
        if self.max_duration and self.duration > self.max_duration:
            raise AssertionError(
                f"Operation took {self.duration:.4f}s, expected < {self.max_duration}s"
            )


def measure_api_performance(client: APIClient, method: str, url: str, 
                          data: Dict = None, max_duration: float = 0.5):
    """Measure API endpoint performance."""
    with PerformanceTimer(max_duration) as timer:
        if method.upper() == 'GET':
            response = client.get(url, data or {})
        elif method.upper() == 'POST':
            response = client.post(url, data or {}, format='json')
        elif method.upper() == 'PUT':
            response = client.put(url, data or {}, format='json')
        elif method.upper() == 'PATCH':
            response = client.patch(url, data or {}, format='json')
        elif method.upper() == 'DELETE':
            response = client.delete(url)
        else:
            raise ValueError(f"Unsupported HTTP method: {method}")
    
    return response, timer.duration


# =============================================================================
# RATE LIMITING TEST UTILITIES
# =============================================================================

class RateLimitTester:
    """Utility for testing rate limiting behavior."""
    
    def __init__(self, client: APIClient):
        self.client = client
        self.original_limits = {}
    
    def test_rate_limit(self, url: str, method: str = 'GET', 
                       expected_limit: int = 60, data: Dict = None):
        """Test rate limiting for a specific endpoint."""
        responses = []
        
        for i in range(expected_limit + 10):  # Exceed limit
            if method.upper() == 'GET':
                response = self.client.get(url)
            elif method.upper() == 'POST':
                response = self.client.post(url, data or {}, format='json')
            else:
                raise ValueError(f"Method {method} not supported")
            
            responses.append(response)
            
            # Stop if we hit rate limit
            if response.status_code == status.HTTP_429_TOO_MANY_REQUESTS:
                break
        
        # Analyze results
        success_responses = [r for r in responses if r.status_code < 400]
        rate_limited_responses = [r for r in responses if r.status_code == 429]
        
        return {
            'total_requests': len(responses),
            'successful_requests': len(success_responses),
            'rate_limited_requests': len(rate_limited_responses),
            'rate_limit_triggered': len(rate_limited_responses) > 0,
            'last_response': responses[-1] if responses else None
        }


# =============================================================================
# MOCK EXTERNAL SYSTEM UTILITIES
# =============================================================================

class MockExternalSystem:
    """Mock external system for integration testing."""
    
    def __init__(self):
        self.permissions = {}
        self.call_log = []
    
    def sync_permission(self, user_id: int, permission_code: str, granted: bool):
        """Mock external system permission sync."""
        call_data = {
            'user_id': user_id,
            'permission_code': permission_code,
            'granted': granted,
            'timestamp': timezone.now(),
            'external_id': f'EXT-{user_id}-{len(self.call_log)}'
        }
        
        self.call_log.append(call_data)
        
        if granted:
            self.permissions[f"{user_id}:{permission_code}"] = call_data
        else:
            self.permissions.pop(f"{user_id}:{permission_code}", None)
        
        return {'status': 'success', 'external_id': call_data['external_id']}
    
    def check_permission(self, user_id: int, permission_code: str):
        """Mock external system permission check."""
        key = f"{user_id}:{permission_code}"
        has_permission = key in self.permissions
        
        call_data = {
            'user_id': user_id,
            'permission_code': permission_code,
            'check_result': has_permission,
            'timestamp': timezone.now()
        }
        
        self.call_log.append(call_data)
        
        return {
            'has_permission': has_permission,
            'external_id': self.permissions.get(key, {}).get('external_id')
        }
    
    def get_call_log(self):
        """Get log of all external system calls."""
        return self.call_log.copy()
    
    def reset(self):
        """Reset mock system state."""
        self.permissions.clear()
        self.call_log.clear()


# =============================================================================
# TEST CLEANUP UTILITIES
# =============================================================================

def cleanup_test_data():
    """Clean up test data between tests."""
    cache.clear()
    
    # Clean up any test-created database objects
    # Note: In practice, Django's TestCase handles this automatically
    pass


def reset_rate_limits():
    """Reset rate limiting cache for testing."""
    # Clear rate limiting cache entries
    cache_keys = cache.keys('rate_limit:*') if hasattr(cache, 'keys') else []
    for key in cache_keys:
        cache.delete(key)


# =============================================================================
# INTEGRATION TEST BASE CLASSES
# =============================================================================

class BasePermissionIntegrationTest:
    """Base class for permission integration tests with common setup."""
    
    def setUp(self):
        """Common setup for permission integration tests."""
        cache.clear()
        self.client = APIClient()
        self.builder = PermissionTestDataBuilder()
        self.assertions = PermissionAssertions()
        self.mock_external = MockExternalSystem()
        
        # Build basic test environment
        self.builder.build_organizational_hierarchy()
        
        # Store references to commonly used objects
        self.admin_user = self.builder.users.get('ceo')
        self.regular_user = self.builder.users.get('sales_rep1')
    
    def tearDown(self):
        """Common cleanup for permission integration tests."""
        cleanup_test_data()
        self.mock_external.reset()


# =============================================================================
# DEBUGGING AND LOGGING UTILITIES
# =============================================================================

def log_test_context(test_name: str, context: Dict[str, Any]):
    """Log test context for debugging."""
    print(f"\n=== TEST CONTEXT: {test_name} ===")
    for key, value in context.items():
        print(f"{key}: {value}")
    print("=" * (len(test_name) + 20))


def capture_api_calls(client: APIClient):
    """Capture all API calls made during test execution."""
    # This would require patching the client or using middleware
    # Implementation depends on specific debugging needs
    pass
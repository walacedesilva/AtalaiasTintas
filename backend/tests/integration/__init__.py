"""
T018: Integration Tests Module
Package: backend.tests.integration

Package initializer for permission system integration tests.
Provides shared imports and test configuration.
"""

# Import commonly used test utilities and classes
from .test_utils import (
    # Factory classes
    UserFactory,
    AdminUserFactory,
    PermissionFactory,
    UserGroupFactory,
    UserPermissionFactory,
    GroupPermissionFactory,
    GroupMembershipFactory,
    
    # Builder classes
    PermissionTestDataBuilder,
    
    # Assertion helpers
    PermissionAssertions,
    
    # Performance utilities
    PerformanceTimer,
    measure_api_performance,
    
    # Rate limiting utilities
    RateLimitTester,
    
    # Mock utilities
    MockExternalSystem,
    
    # Cleanup utilities
    cleanup_test_data,
    reset_rate_limits,
    
    # Base test class
    BasePermissionIntegrationTest,
    
    # Debugging utilities
    log_test_context,
)

__all__ = [
    'UserFactory',
    'AdminUserFactory', 
    'PermissionFactory',
    'UserGroupFactory',
    'UserPermissionFactory',
    'GroupPermissionFactory',
    'GroupMembershipFactory',
    'PermissionTestDataBuilder',
    'PermissionAssertions',
    'PerformanceTimer',
    'measure_api_performance',
    'RateLimitTester',
    'MockExternalSystem',
    'cleanup_test_data',
    'reset_rate_limits',
    'BasePermissionIntegrationTest',
    'log_test_context',
]

"""
OpenAPI 3.0 Schema Documentation for Permission System APIs.

T015: Comprehensive API documentation with complete schemas and examples.

This module defines the OpenAPI specification for the User Permissions System,
providing interactive documentation and testing capabilities via Swagger UI.
"""

from drf_spectacular.utils import (
    extend_schema, extend_schema_view, OpenApiParameter, OpenApiExample, 
    OpenApiResponse, inline_serializer
)
from drf_spectacular.types import OpenApiTypes
from rest_framework import serializers, status
from django.utils.translation import gettext_lazy as _

# =============================================================================
# OPENAPI SCHEMA DEFINITIONS
# =============================================================================

# Common parameters used across endpoints
COMMON_PARAMETERS = [
    OpenApiParameter(
        name='page',
        location=OpenApiParameter.QUERY,
        description='Page number for pagination',
        type=OpenApiTypes.INT,
        default=1,
    ),
    OpenApiParameter(
        name='page_size',
        location=OpenApiParameter.QUERY,
        description='Number of items per page',
        type=OpenApiTypes.INT,
        default=25,
    ),
    OpenApiParameter(
        name='ordering',
        location=OpenApiParameter.QUERY,
        description='Field to order results by. Prefix with "-" for descending order.',
        type=OpenApiTypes.STR,
        enum=['name', '-name', 'created_at', '-created_at', 'risk_level', '-risk_level'],
    ),
    OpenApiParameter(
        name='search',
        location=OpenApiParameter.QUERY,
        description='Search term to filter results',
        type=OpenApiTypes.STR,
    ),
]

# Error response schemas
ERROR_RESPONSES = {
    400: OpenApiResponse(
        response=inline_serializer(
            name='BadRequestError',
            fields={
                'error': serializers.CharField(),
                'detail': serializers.CharField(),
                'field_errors': serializers.DictField(child=serializers.ListField())
            }
        ),
        description='Bad Request - Invalid data provided',
        examples=[
            OpenApiExample(
                'Validation Error',
                value={
                    'error': 'Validation failed',
                    'detail': 'The provided data is invalid',
                    'field_errors': {
                        'name': ['This field is required.'],
                        'risk_level': ['Invalid choice: "invalid". Choose from: low, medium, high, critical.']
                    }
                }
            )
        ]
    ),
    401: OpenApiResponse(
        response=inline_serializer(
            name='UnauthorizedError',
            fields={
                'error': serializers.CharField(),
                'detail': serializers.CharField()
            }
        ),
        description='Unauthorized - Authentication required',
        examples=[
            OpenApiExample(
                'Authentication Required',
                value={
                    'error': 'Authentication required',
                    'detail': 'Please provide valid authentication credentials'
                }
            )
        ]
    ),
    403: OpenApiResponse(
        response=inline_serializer(
            name='ForbiddenError',
            fields={
                'error': serializers.CharField(),
                'detail': serializers.CharField() 
            }
        ),
        description='Forbidden - Insufficient permissions',
        examples=[
            OpenApiExample(
                'Insufficient Permissions',
                value={
                    'error': 'Insufficient permissions',
                    'detail': 'You do not have permission to perform this action'
                }
            )
        ]
    ),
    404: OpenApiResponse(
        response=inline_serializer(
            name='NotFoundError',
            fields={
                'error': serializers.CharField(),
                'detail': serializers.CharField()
            }
        ),
        description='Not Found - Resource does not exist',
        examples=[
            OpenApiExample(
                'Resource Not Found',
                value={
                    'error': 'Resource not found',
                    'detail': 'The requested resource was not found'
                }
            )
        ]
    ),
    500: OpenApiResponse(
        response=inline_serializer(
            name='ServerError',
            fields={
                'error': serializers.CharField(),
                'detail': serializers.CharField()
            }
        ),
        description='Internal Server Error',
        examples=[
            OpenApiExample(
                'Server Error',
                value={
                    'error': 'Internal server error',
                    'detail': 'An unexpected error occurred'
                }
            )
        ]
    )
}

# =============================================================================
# PERMISSION VIEWSET SCHEMA
# =============================================================================

@extend_schema_view(
    list=extend_schema(
        operation_id='permissions_list',
        summary='List Permissions',
        description="""
        Retrieve a paginated list of permissions with filtering and search capabilities.
        
        **Functionality:**
        - Supports pagination, filtering, and full-text search
        - Results are filtered based on user's permission scope
        - Administrative users can see all permissions
        - Regular users see only permissions within their scope
        
        **Performance Features (T014):**
        - Response caching for 5 minutes
        - Gzip compression enabled
        - Optimized database queries with prefetch/select_related
        - Performance metrics tracking
        
        **Security:**
        - Requires authentication
        - View permissions are required to access
        """,
        parameters=COMMON_PARAMETERS + [
            OpenApiParameter(
                name='module',
                location=OpenApiParameter.QUERY,
                description='Filter by module name',
                type=OpenApiTypes.STR,
            ),
            OpenApiParameter(
                name='risk_level',
                location=OpenApiParameter.QUERY,
                description='Filter by risk level',
                type=OpenApiTypes.STR,
                enum=['low', 'medium', 'high', 'critical'],
            ),
            OpenApiParameter(
                name='is_active',
                location=OpenApiParameter.QUERY,
                description='Filter by active status',
                type=OpenApiTypes.BOOL,
            ),
        ],
        responses={
            200: OpenApiResponse(
                description='Success - List of permissions',
                examples=[
                    OpenApiExample(
                        'Successful Response',
                        value={
                            'count': 150,
                            'next': 'http://localhost:8000/api/permissions/?page=2',
                            'previous': None,
                            'results': [
                                {
                                    'id': 1,
                                    'name': 'View Users',
                                    'code': 'users.view',
                                    'description': 'Allows viewing user information',
                                    'module': 'users',
                                    'risk_level': 'low',
                                    'is_active': True,
                                    'created_at': '2024-01-15T10:30:00Z',
                                    'updated_at': '2024-01-15T10:30:00Z'
                                }
                            ]
                        }
                    )
                ]
            ),
            **ERROR_RESPONSES
        },
        tags=['Permissions']
    ),
    create=extend_schema(
        operation_id='permissions_create',
        summary='Create Permission',
        description="""
        Create a new permission in the system.
        
        **Functionality:**
        - Creates new system permission with specified attributes
        - Automatically assigns created_by field to current user
        - Validates permission code uniqueness
        - Supports risk level assignment for security auditing
        
        **Security:**
        - Requires authentication
        - Manage permissions required
        - Admin-only operation in most cases
        
        **Validation Rules:**
        - Permission code must be unique
        - Risk level must be valid choice
        - Module and name are required
        """,
        responses={
            201: OpenApiResponse(
                description='Created - Permission created successfully',
                examples=[
                    OpenApiExample(
                        'Permission Created',
                        value={
                            'id': 151,
                            'name': 'Delete Reports',
                            'code': 'reports.delete',
                            'description': 'Allows deletion of system reports',
                            'module': 'reports',
                            'risk_level': 'high',
                            'is_active': True,
                            'created_at': '2024-01-15T11:00:00Z',
                            'updated_at': '2024-01-15T11:00:00Z',
                            'created_by': {
                                'id': 1,
                                'username': 'admin',
                                'email': 'admin@example.com'
                            }
                        }
                    )
                ]
            ),
            **ERROR_RESPONSES
        },
        tags=['Permissions']
    ),
    retrieve=extend_schema(
        operation_id='permissions_retrieve',
        summary='Get Permission Details',
        description="""
        Retrieve detailed information about a specific permission.
        
        **Functionality:**
        - Returns complete permission details with relationships
        - Includes audit information (created_by, updated_by)
        - Shows current assignment statistics
        - Provides related permissions suggestions
        
        **Performance Features (T014):**
        - Response caching for 10 minutes
        - Optimized database queries
        - Gzip compression enabled
        """,
        responses={
            200: OpenApiResponse(
                description='Success - Permission details',
                examples=[
                    OpenApiExample(
                        'Permission Details',
                        value={
                            'id': 1,
                            'name': 'View Users',
                            'code': 'users.view',
                            'description': 'Allows viewing user information and basic details',
                            'module': 'users',
                            'risk_level': 'low',
                            'is_active': True,
                            'created_at': '2024-01-15T10:30:00Z',
                            'updated_at': '2024-01-15T10:30:00Z',
                            'created_by': {
                                'id': 1,
                                'username': 'admin',
                                'email': 'admin@example.com'
                            },
                            'assignment_stats': {
                                'total_users': 25,
                                'total_groups': 5,
                                'active_assignments': 22
                            }
                        }
                    )
                ]
            ),
            **ERROR_RESPONSES
        },
        tags=['Permissions']
    ),
    update=extend_schema(
        operation_id='permissions_update',
        summary='Update Permission',
        description="""
        Update an existing permission's attributes.
        
        **Functionality:**
        - Updates permission details while maintaining audit trail
        - Validates changes against business rules
        - Supports partial updates (PATCH) and full updates (PUT)
        - Automatically updates modified timestamp
        
        **Security Considerations:**
        - Risk level changes trigger additional validation
        - Code changes require careful consideration of existing assignments
        - High-risk permissions require additional confirmation
        """,
        responses={
            200: OpenApiResponse(description='Success - Permission updated'),
            **ERROR_RESPONSES
        },
        tags=['Permissions']
    ),
    destroy=extend_schema(
        operation_id='permissions_delete',
        summary='Delete Permission',
        description="""
        Delete a permission from the system.
        
        **Functionality:**
        - Soft delete with audit trail preservation
        - Cascades to related permission assignments
        - High-risk permissions require explicit confirmation
        - Validates no critical dependencies exist
        
        **Safety Features:**
        - High-risk permissions require confirm_high_risk_deletion=true
        - System permissions cannot be deleted
        - Validates impact on existing user/group assignments
        """,
        parameters=[
            OpenApiParameter(
                name='confirm_high_risk_deletion',
                location=OpenApiParameter.QUERY,
                description='Required confirmation for high-risk permission deletion',
                type=OpenApiTypes.BOOL,
                default=False,
            ),
        ],
        responses={
            204: OpenApiResponse(description='No Content - Permission deleted successfully'),
            **ERROR_RESPONSES
        },
        tags=['Permissions']
    ),
    by_module=extend_schema(
        operation_id='permissions_by_module',
        summary='Group Permissions by Module',
        description="""
        Retrieve permissions organized by module with statistics.
        
        **Functionality:**
        - Groups all permissions by their module
        - Provides count statistics for each module
        - Includes risk level distribution per module
        - Useful for administrative dashboards
        
        **Performance Features (T014):**
        - Response caching for 5 minutes
        - Gzip compression
        - Optimized aggregation queries
        - Performance metrics tracking
        
        **Use Cases:**
        - Administrative overview of system permissions
        - Module-based permission management
        - Security auditing and risk analysis
        """,
        responses={
            200: OpenApiResponse(
                description='Success - Permissions grouped by module',
                examples=[
                    OpenApiExample(
                        'Module Grouping',
                        value={
                            'modules': [
                                {
                                    'module': 'users',
                                    'total_permissions': 15,
                                    'active_permissions': 14,
                                    'low_risk_count': 8,
                                    'medium_risk_count': 5,
                                    'high_risk_count': 2,
                                    'critical_risk_count': 0
                                },
                                {
                                    'module': 'reports',
                                    'total_permissions': 10,
                                    'active_permissions': 9,
                                    'low_risk_count': 5,
                                    'medium_risk_count': 3,
                                    'high_risk_count': 2,
                                    'critical_risk_count': 0
                                }
                            ],
                            'summary': {
                                'total_modules': 8,
                                'total_permissions': 150,
                                'active_permissions': 145
                            }
                        }
                    )
                ]
            ),
            **ERROR_RESPONSES
        },
        tags=['Permissions']
    ),
    risk_analysis=extend_schema(
        operation_id='permissions_risk_analysis',
        summary='Permission Risk Analysis',
        description="""
        Analyze permission Risk levels and identify security concerns.
        
        **Functionality:**
        - Provides risk level distribution across all permissions
        - Identifies high-risk permissions with wide assignment
        - Generates security recommendations
        - Useful for security auditing and compliance
        
        **Performance Features (T014):**
        - Response caching for 10 minutes (slower changing data)
        - Gzip compression
        - Optimized queries with prefetch/select_related
        - Performance metrics tracking
        
        **Security Insights:**
        - Risk distribution analysis
        - Over-privileged permission identification
        - Compliance gap analysis
        - Recommendations for permission consolidation
        """,
        responses={
            200: OpenApiResponse(
                description='Success - Risk analysis results',
                examples=[
                    OpenApiExample(
                        'Risk Analysis',
                        value={
                            'risk_distribution': [
                                {
                                    'risk_level': 'low',
                                    'count': 80,
                                    'active_count': 78,
                                    'assigned_count': 60
                                },
                                {
                                    'risk_level': 'medium',
                                    'count': 45,
                                    'active_count': 43,
                                    'assigned_count': 35
                                },
                                {
                                    'risk_level': 'high',
                                    'count': 20,
                                    'active_count': 19,
                                    'assigned_count': 12
                                },
                                {
                                    'risk_level': 'critical',
                                    'count': 5,
                                    'active_count': 5,
                                    'assigned_count': 3
                                }
                            ],
                            'high_risk_widely_assigned': [
                                {
                                    'id': 45,
                                    'name': 'Delete All Data',
                                    'code': 'system.delete_all',
                                    'risk_level': 'critical',
                                    'user_count': 3,
                                    'group_count': 1
                                }
                            ],
                            'recommendations': [
                                'Review critical permissions with multiple assignments',
                                'Consider creating specialized groups for high-risk permissions',
                                'Implement time-limited assignments for critical permissions'
                            ]
                        }
                    )
                ]
            ),
            **ERROR_RESPONSES
        },
        tags=['Permissions']
    )
)
class PermissionViewSetSchema:
    """OpenAPI schema definitions for PermissionViewSet."""
    pass


# =============================================================================
# USER PERMISSION VIEWSET SCHEMA
# =============================================================================

@extend_schema_view(
    list=extend_schema(
        operation_id='user_permissions_list',
        summary='List User Permission Assignments',
        description="""
        Retrieve user-permission assignments with filtering capabilities.
        
        **Functionality:**
        - Lists all user-permission relationships
        - Supports filtering by user, permission, and grant status
        - Shows temporal permissions with expiration dates
        - Includes audit information
        
        **Access Control:**
        - Users can see their own permissions
        - Managers can see permissions for users they manage
        - Admins can see all permission assignments
        """,
        parameters=COMMON_PARAMETERS + [
            OpenApiParameter(
                name='user',
                location=OpenApiParameter.QUERY,
                description='Filter by user ID',
                type=OpenApiTypes.INT,
            ),
            OpenApiParameter(
                name='permission',
                location=OpenApiParameter.QUERY,
                description='Filter by permission ID',
                type=OpenApiTypes.INT,
            ),
            OpenApiParameter(
                name='is_granted',
                location=OpenApiParameter.QUERY,
                description='Filter by grant status',
                type=OpenApiTypes.BOOL,
            ),
        ],
        responses={
            200: OpenApiResponse(description='Success - User permission assignments'),
            **ERROR_RESPONSES
        },
        tags=['User Permissions']
    ),
    create=extend_schema(
        operation_id='user_permissions_create',
        summary='Grant Permission to User',
        description="""
        Grant a specific permission to a user with optional expiration.
        
        **Functionality:**
        - Creates direct user-permission assignment
        - Supports temporal permissions with expiration dates
        - Validates permission compatibility and conflicts
        - Records audit trail with granting user
        
        **Security Features:**
        - Validates user has authority to grant the permission
        - Checks for conflicting permissions
        - High-risk permissions require additional confirmation
        - Automatic notification to user and managers
        """,
        responses={
            201: OpenApiResponse(description='Created - Permission granted successfully'),
            **ERROR_RESPONSES
        },
        tags=['User Permissions']
    ),
    destroy=extend_schema(
        operation_id='user_permissions_revoke',
        summary='Revoke Permission from User',
        description="""
        Revoke a previously granted permission from a user.
        
        **Functionality:**
        - Removes direct user-permission assignment
        - Maintains audit trail of revocation
        - Validates authority to revoke the permission
        - Automatic notification to affected parties
        
        **Safety Features:**
        - Cannot revoke system-critical permissions
        - Validates impact on user's other permissions
        - Records reason for revocation in audit log
        """,
        responses={
            204: OpenApiResponse(description='No Content - Permission revoked successfully'),
            **ERROR_RESPONSES
        },
        tags=['User Permissions']
    ),
    effective=extend_schema(
        operation_id='user_permissions_effective',
        summary='Get Effective User Permissions',
        description="""
        Retrieve all effective permissions for a user (direct + group permissions).
        
        **Functionality:**
        - Combines direct user permissions with group-inherited permissions
        - Resolves permission conflicts and precedence
        - Shows permission sources (direct vs group)
        - Includes temporal permission status
        
        **Performance Features (T014):**
        - Response caching for 3 minutes
        - Gzip compression
        - Optimized database queries
        - Multi-level caching strategy
        
        **Use Cases:**
        - Permission verification for authorization
        - User permission auditing
        - Troubleshooting access issues
        - Compliance reporting
        """,
        parameters=[
            OpenApiParameter(
                name='user_id',
                location=OpenApiParameter.PATH,
                description='ID of the user to get permissions for',
                required=True,
                type=OpenApiTypes.INT,
            ),
        ],
        responses={
            200: OpenApiResponse(
                description='Success - Effective permissions for user',
                examples=[
                    OpenApiExample(
                        'Effective Permissions',
                        value={
                            'user_id': 123,
                            'username': 'john_doe',
                            'effective_permissions': {
                                'direct_permissions': [
                                    {
                                        'id': 1,
                                        'name': 'View Reports',
                                        'code': 'reports.view',
                                        'source': 'direct',
                                        'expires_at': '2024-12-31T23:59:59Z'
                                    }
                                ],
                                'group_permissions': [
                                    {
                                        'id': 2,
                                        'name': 'Manage Users',
                                        'code': 'users.manage',
                                        'source': 'group',
                                        'group_name': 'Managers'
                                    }
                                ],
                                'last_updated': '2024-01-15T12:00:00Z'
                            },
                            'cached': True,
                            'cache_timestamp': '2024-01-15T12:00:00Z'
                        }
                    )
                ]
            ),
            **ERROR_RESPONSES
        },
        tags=['User Permissions']
    )
)
class UserPermissionViewSetSchema:
    """OpenAPI schema definitions for UserPermissionViewSet."""
    pass


# =============================================================================
# USER GROUP VIEWSET SCHEMA
# =============================================================================

@extend_schema_view(
    list=extend_schema(
        operation_id='user_groups_list',
        summary='List User Groups',
        description="""
        Retrieve a list of user groups with member and permission information.
        
        **Functionality:**
        - Lists all user groups with basic information
        - Includes member count and permission statistics
        - Supports filtering by group type and status
        - Shows group hierarchy relationships
        """,
        parameters=COMMON_PARAMETERS + [
            OpenApiParameter(
                name='is_active',
                location=OpenApiParameter.QUERY,
                description='Filter by active status',
                type=OpenApiTypes.BOOL,
            ),
            OpenApiParameter(
                name='group_type',
                location=OpenApiParameter.QUERY,
                description='Filter by group type',
                type=OpenApiTypes.STR,
                enum=['role', 'department', 'project', 'temporary'],
            ),
        ],
        responses={
            200: OpenApiResponse(description='Success - List of user groups'),
            **ERROR_RESPONSES
        },
        tags=['User Groups']
    ),
    create=extend_schema(
        operation_id='user_groups_create',
        summary='Create User Group',
        description="""
        Create a new user group with specified permissions and settings.
        
        **Functionality:**
        - Creates new group with name, description, and type
        - Allows initial permission assignment during creation
        - Supports group hierarchy with parent-child relationships
        - Automatic audit trail creation
        """,
        responses={
            201: OpenApiResponse(description='Created - Group created successfully'),
            **ERROR_RESPONSES
        },
        tags=['User Groups']
    ),
    effective_permissions=extend_schema(
        operation_id='user_groups_effective_permissions',
        summary='Get Group Effective Permissions',
        description="""
        Retrieve all effective permissions for a group including inherited permissions.
        
        **Functionality:**
        - Shows direct group permissions
        - Includes permissions inherited from parent groups
        - Resolves permission conflicts and precedence
        - Provides permission source attribution
        """,
        responses={
            200: OpenApiResponse(description='Success - Group effective permissions'),
            **ERROR_RESPONSES
        },
        tags=['User Groups']
    )
)
class UserGroupViewSetSchema:
    """OpenAPI schema definitions for UserGroupViewSet."""
    pass


# =============================================================================
# PERFORMANCE METRICS SCHEMA
# =============================================================================

@extend_schema_view(
    list=extend_schema(
        operation_id='performance_metrics_list',
        summary='API Performance Metrics',
        description="""
        Retrieve API performance metrics and monitoring data.
        
        **T014 Performance Monitoring:**
        - Response time statistics by endpoint
        - Cache hit/miss ratios
        - Database Query performance
        - Error rate monitoring
        - Throughput analysis
        
        **Use Cases:**
        - Performance monitoring and optimization
        - SLA compliance tracking
        - Bottleneck identification
        - Capacity planning
        """,
        parameters=[
            OpenApiParameter(
                name='endpoint',
                location=OpenApiParameter.QUERY,
                description='Filter metrics by specific endpoint',
                type=OpenApiTypes.STR,
            ),
            OpenApiParameter(
                name='time_range',
                location=OpenApiParameter.QUERY,
                description='Time range for metrics',
                type=OpenApiTypes.STR,
                enum=['1h', '24h', '7d', '30d'],
                default='24h',
            ),
        ],
        responses={
            200: OpenApiResponse(
                description='Success - Performance metrics data',
                examples=[
                    OpenApiExample(
                        'Performance Metrics',
                        value={
                            'time_range': '24h',
                            'summary': {
                                'total_requests': 15420,
                                'avg_response_time': 185.7,
                                'cache_hit_rate': 78.5,
                                'error_rate': 0.3
                            },
                            'endpoints': [
                                {
                                    'endpoint': '/api/permissions/',
                                    'method': 'GET',
                                    'request_count': 3240,
                                    'avg_response_time': 142.3,
                                    'cache_hit_rate': 85.2
                                }
                            ]
                        }
                    )
                ]
            ),
            **ERROR_RESPONSES
        },
        tags=['Performance']
    )
)
class PerformanceMetricsViewSetSchema:
    """OpenAPI schema definitions for PerformanceMetricsViewSet."""
    pass


# =============================================================================
# SCHEMA EXTENSIONS AND CUSTOMIZATIONS
# =============================================================================

# Custom schema generator settings
SPECTACULAR_SETTINGS = {
    'TITLE': 'AtalaiasTintas Permission System API',
    'DESCRIPTION': '''
    **AtalaiasTintas User Permissions System API Documentation**
    
    This API provides comprehensive permission management capabilities for the 
    AtalaiasTintas paint store system, featuring enterprise-grade security, 
    performance optimization, and extensive audit capabilities.
    
    ## Features
    
    ### 🔐 Permission Management
    - Granular permission system with risk-based classification
    - Role-based access control (RBAC) with group inheritance
    - Temporal permissions with automatic expiration
    - Permission conflict resolution and validation
    
    ### 🚀 Performance Optimization (T014)
    - Response caching with intelligent invalidation
    - Database query optimization with prefetch/select_related
    - Gzip compression for all responses
    - Real-time performance monitoring and metrics
    - Connection pooling and query optimization
    
    ### 🛡️ Security Features
    - Multi-level authentication and authorization
    - Audit trail for all permission changes
    - Risk-based permission classification
    - Security monitoring and alerting
    
    ### 📊 Analytics & Monitoring
    - Permission usage analytics
    - Risk analysis and recommendations
    - Performance metrics and bottleneck identification
    - Compliance reporting and auditing
    
    ## Authentication
    
    All API endpoints require authentication using one of the following methods:
    
    - **Token Authentication**: Include `Authorization: Token <your-token>` header
    - **Session Authentication**: Use Django session cookies (for web interface)
    
    ## Rate Limiting
    
    API endpoints are rate limited to ensure system stability:
    - **Authenticated users**: 1000 requests per hour
    - **Anonymous users**: 100 requests per hour
    - **Administrative operations**: 500 requests per hour
    
    ## Error Handling
    
    All errors follow RFC 7807 Problem Details format with consistent structure:
    
    ```json
    {
        "error": "Error category",
        "detail": "Human-readable description",
        "field_errors": {
            "field_name": ["Field-specific error messages"]
        }
    }
    ```
    
    ## API Versioning
    
    - **Current Version**: v1
    - **Versioning Strategy**: URL path versioning (`/api/v1/`)
    - **Deprecation Policy**: 6 months notice for breaking changes
    - **Migration Guides**: Available in documentation for version transitions
    
    ## Support
    
    - **Documentation**: Complete API reference with examples
    - **Issue Tracking**: GitHub Issues for bug reports and feature requests
    - **Support Contact**: technical-support@atalaiaspintas.com
    ''',
    'VERSION': '1.0.0',
    'SERVE_INCLUDE_SCHEMA': False,
    'SWAGGER_UI_SETTINGS': {
        'deepLinking': True,
        'persistAuthorization': True,
        'displayOperationId': True,
        'defaultModelsExpandDepth': 2,
        'defaultModelExpandDepth': 2,
        'displayRequestDuration': True,
        'docExpansion': 'list',
        'filter': True,
        'showExtensions': True,
        'showCommonExtensions': True,
        'tryItOutEnabled': True
    },
    'REDOC_UI_SETTINGS': {
        'nativeScrollbars': True,
        'theme': {
            'colors': {
                'primary': {
                    'main': '#1976d2'
                }
            },
            'typography': {
                'fontSize': '14px',
                'lineHeight': '1.5em',
                'code': {
                    'fontSize': '13px'
                }
            }
        }
    },
    'COMPONENT_SPLIT_REQUEST': True,
    'SORT_OPERATIONS': False,
    'ENABLE_DJANGO_DEPLOY_CHECK': True,
    'SERVE_PERMISSIONS': ['rest_framework.permissions.IsAuthenticated'],
    'SERVE_AUTHENTICATION': [
        'rest_framework.authentication.TokenAuthentication',
        'rest_framework.authentication.SessionAuthentication',
    ],
}

# API Documentation metadata
API_INFO = {
    'title': 'AtalaiasTintas Permission System API',
    'version': '1.0.0',
    'description': 'Enterprise-grade permission management system with performance optimization',
    'termsOfService': 'https://atalaiaspintas.com/terms/',
    'contact': {
        'name': 'AtalaiasTintas Technical Team',
        'email': 'technical-support@atalaiaspintas.com',
        'url': 'https://atalaiaspintas.com/support/'
    },
    'license': {
        'name': 'Proprietary License',
        'url': 'https://atalaiaspintas.com/license/'
    }
}

# API Server configurations
API_SERVERS = [
    {
        'url': 'http://localhost:8000',
        'description': 'Development Server'
    },
    {
        'url': 'https://api-staging.atalaiaspintas.com',
        'description': 'Staging Server'
    },
    {
        'url': 'https://api.atalaiaspintas.com',
        'description': 'Production Server'
    }
]

# =============================================================================
# SCHEMA PREPROCESSING HOOKS
# =============================================================================

def preprocess_openapi_spec(result, generator, request, public):
    """
    Preprocess the OpenAPI specification before serving.
    
    This function allows customization of the generated schema, including:
    - Adding custom security requirements
    - Modifying endpoint descriptions
    - Adding custom examples
    - Filtering endpoints based on user permissions
    """
    # Add global security requirements
    if 'security' not in result:
        result['security'] = []
    
    # Add default security schemes
    result['security'].append({'tokenAuth': []})
    result['security'].append({'jwtAuth': []})
    
    # Add custom headers to all endpoints
    if 'paths' in result:
        for path, methods in result['paths'].items():
            for method, operation in methods.items():
                if isinstance(operation, dict):
                    # Add common response headers
                    if 'responses' in operation:
                        for status_code, response in operation['responses'].items():
                            if isinstance(response, dict) and 'headers' not in response:
                                response['headers'] = {
                                    'X-RateLimit-Limit': {
                                        'description': 'Request limit per time window',
                                        'schema': {'type': 'integer'}
                                    },
                                    'X-RateLimit-Remaining': {
                                        'description': 'Requests remaining in current window', 
                                        'schema': {'type': 'integer'}
                                    },
                                    'X-Response-Time': {
                                        'description': 'Response processing time in milliseconds',
                                        'schema': {'type': 'integer'}
                                    }
                                }
    
    # Filter endpoints based on user permissions if authenticated
    if request and hasattr(request, 'user') and request.user.is_authenticated:
        # Add user context to the schema if needed
        pass
    
    # Add custom API information
    result['info']['x-api-features'] = {
        'performance_optimization': True,
        'response_caching': True,
        'gzip_compression': True,
        'rate_limiting': True,
        'authentication_methods': ['token', 'jwt', 'session', 'api_key'],
        'permission_system': 'rbac',
        'audit_logging': True
    }
    
    return result
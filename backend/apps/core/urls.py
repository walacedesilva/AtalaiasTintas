"""
URL configuration for core app.

T016: Enhanced URL configuration with RESTful patterns, proper namespacing,
permission-based access control, and health check endpoints.

Features:
- RESTful API design following Django best practices
- Proper API versioning and namespace organization  
- Permission-based access control integration
- Health check endpoints for permission system monitoring
- Future extensibility and backward compatibility support
"""
from django.urls import path, include, re_path
from rest_framework.routers import DefaultRouter
from rest_framework.schemas import get_schema_view
from . import views

# T016: Enhanced REST API Router with proper configuration
router = DefaultRouter(
    trailing_slash=True,  # Enforce consistent trailing slashes
    use_regex_path=False  # Use path() instead of re_path() for better performance
)

# Feature: 3-modern-web-interface
# Task: T007 - User Preferences API Endpoints
router.register(r'preferences', views.UserPreferencesViewSet, basename='user-preferences')

# Feature: 2-core-infrastructure
# Task: T032 & T033 - User Management Views
router.register(r'users', views.UserManagementViewSet, basename='user-management')

# Task: T045 - Configuration Management Views
router.register(r'config', views.ConfiguracaoViewSet, basename='configuration')

# =============================================================================
# T016: PERMISSION SYSTEM API ENDPOINTS - RESTful Design
# =============================================================================

# Feature: 8-user-permissions-system
# T009: Permission Management ViewSets (T014 Performance Optimized)
router.register(
    r'permissions', 
    views.PermissionViewSet, 
    basename='permissions'
)
router.register(
    r'user-permissions', 
    views.UserPermissionViewSet, 
    basename='user-permissions'
)
router.register(
    r'groups', 
    views.UserGroupViewSet, 
    basename='user-groups'
)
router.register(
    r'permission-audit', 
    views.PermissionAuditViewSet, 
    basename='permission-audit'
)

# T014: Performance Monitoring Endpoints - Comentado: view não implementada ainda
# router.register(
#     r'performance-metrics', 
#     views.PerformanceMetricsView, 
#     basename='performance-metrics'
# )

# =============================================================================
# T016: ENHANCED URL PATTERNS WITH ACCESS CONTROL
# =============================================================================

app_name = 'core'

urlpatterns = [
    # =============================================================================
    # AUTHENTICATION & AUTHORIZATION ENDPOINTS
    # =============================================================================
    
    # Primary authentication endpoints
    path('auth/login/', views.LoginView.as_view(), name='login'),
    path('auth/logout/', views.LogoutView.as_view(), name='logout'),
    
    # User profile and management
    path('auth/profile/', views.UserProfileView.as_view(), name='user_profile'),
    path('auth/user/', views.UserProfileView.as_view(), name='user_current'),
    path('auth/change-password/', views.ChangePasswordView.as_view(), name='change_password'),
    
    # Advanced authentication (T013 enhancements) - Comentado: views não implementadas ainda
    # path('auth/mfa/setup/', views.MFASetupView.as_view(), name='mfa_setup'),
    # path('auth/mfa/verify/', views.MFAVerifyView.as_view(), name='mfa_verify'),
    # path('auth/api-key/generate/', views.APIKeyGenerateView.as_view(), name='api_key_generate'),
    
    # =============================================================================
    # T016: PERMISSION SYSTEM HEALTH CHECK ENDPOINTS
    # =============================================================================
    
    # System health and monitoring
    path('health/permissions/', views.PermissionSystemHealthView.as_view(), name='permissions_health'),
    path('health/cache/', views.CacheHealthView.as_view(), name='cache_health'), 
    path('health/database/', views.DatabaseHealthView.as_view(), name='database_health'),
    path('health/performance/', views.PerformanceHealthView.as_view(), name='performance_health'),
    
    # Permission system status endpoints
    path('status/permissions/summary/', views.PermissionsSummaryView.as_view(), name='permissions_summary'),
    path('status/permissions/integrity/', views.PermissionsIntegrityView.as_view(), name='permissions_integrity'),
    path('status/cache/stats/', views.CacheStatsView.as_view(), name='cache_stats'),
    
    # =============================================================================
    # DEPLOYMENT & OPERATIONS ENDPOINTS  
    # =============================================================================
    
    # Deployment coordination endpoints (Task T060)
    path('deployment/status/', views.DeploymentStatusView.as_view(), name='deployment_status'),
    path('deployment/health/', views.DeploymentHealthView.as_view(), name='deployment_health'),
    path('deployment/lock/', views.DeploymentLockView.as_view(), name='deployment_lock'),
    
    # =============================================================================
    # API VERSIONING AND BACKWARD COMPATIBILITY
    # =============================================================================
    
    # Current version (v1) - primary API endpoints
    path('', include(router.urls)),
    
    # Legacy compatibility redirects (for future use)
    # path('v1/', include(router.urls)),  # Explicit v1 routing if needed
    
    # =============================================================================
    # FUTURE EXTENSIBILITY HOOKS
    # =============================================================================
    
    # Webhook endpoints (placeholder for future features)
    # path('webhooks/permissions/', views.PermissionWebhookView.as_view(), name='permission_webhooks'),
    
    # Bulk operations endpoints (placeholder for future features)  
    # path('bulk/permissions/', views.BulkPermissionOpsView.as_view(), name='bulk_permissions'),
]
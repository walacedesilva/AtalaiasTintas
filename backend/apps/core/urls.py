"""
URL configuration for core app.
Handles authentication and user management endpoints.
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

# REST API Router
router = DefaultRouter()

# Feature: 3-modern-web-interface
# Task: T007 - User Preferences API Endpoints
router.register(r'preferences', views.UserPreferencesViewSet, basename='user-preferences')

# Feature: 2-core-infrastructure
# Task: T032 & T033 - User Management Views
router.register(r'users', views.UserManagementViewSet, basename='user-management')

# Task: T045 - Configuration Management Views
router.register(r'config', views.ConfiguracaoViewSet, basename='configuration')

app_name = 'core'

urlpatterns = [
    # Authentication endpoints  
    path('auth/login/', views.LoginView.as_view(), name='login'),
    path('auth/logout/', views.LogoutView.as_view(), name='logout'),
    path('auth/profile/', views.UserProfileView.as_view(), name='user_profile'),
    path('auth/user/', views.UserProfileView.as_view(), name='user_current'),
    path('auth/change-password/', views.ChangePasswordView.as_view(), name='change_password'),
    
    # Deployment coordination endpoints (Task T060)
    path('deployment/status/', views.DeploymentStatusView.as_view(), name='deployment_status'),
    path('deployment/health/', views.DeploymentHealthView.as_view(), name='deployment_health'),
    path('deployment/lock/', views.DeploymentLockView.as_view(), name='deployment_lock'),
    
    # Include router URLs
    path('', include(router.urls)),
]
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

app_name = 'core'

urlpatterns = [
    # Authentication endpoints  
    path('auth/login/', views.LoginView.as_view(), name='login'),
    path('auth/logout/', views.LogoutView.as_view(), name='logout'),
    path('auth/profile/', views.UserProfileView.as_view(), name='user_profile'),
    path('auth/change-password/', views.ChangePasswordView.as_view(), name='change_password'),
    
    # Demo Pages
    # Feature: 3-modern-web-interface | Task: T009 - Typography Scale System
    path('demo/typography/', views.typography_demo, name='typography-demo'),
    # Feature: 3-modern-web-interface | Task: T010 - Form Components Styling
    path('demo/forms/', views.forms_demo, name='forms-demo'),
    # Feature: 3-modern-web-interface | Task: T014 - Progressive Enhancement Layer
    path('demo/progressive-enhancement/', views.progressive_enhancement_test, name='progressive-enhancement-test'),
    
    # Include router URLs
    path('', include(router.urls)),
]
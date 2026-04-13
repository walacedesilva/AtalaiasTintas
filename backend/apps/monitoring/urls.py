"""
URL configuration for monitoring app
User Story 2: Data Integrity and Backup
Task: T042 - Health check API endpoints
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

# REST API Router
router = DefaultRouter()
router.register(r'health', views.SystemHealthViewSet, basename='systemhealth')
router.register(r'alerts', views.AlertNotificationViewSet, basename='alertnotification')

app_name = 'monitoring'

urlpatterns = [
    # Main monitoring endpoints
    path('dashboard/', views.HealthDashboardView.as_view(), name='dashboard'),
    path('metrics/', views.MetricsView.as_view(), name='metrics'),
    path('backup/', views.BackupManagementView.as_view(), name='backup'),
    
    # Include router URLs (health/ and alerts/ endpoints)
    path('', include(router.urls)),
]
"""
URL configuration for monitoring app.
Handles system health monitoring and alerting endpoints.
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

# REST API Router
router = DefaultRouter()
# ViewSets will be registered here in User Story 2 tasks

app_name = 'monitoring'

urlpatterns = [
    # Monitoring endpoints (will be implemented in US2)
    path('system-health/', views.SystemHealthView.as_view(), name='system-health'),
    path('alerts/', views.AlertListView.as_view(), name='alerts'),
    path('metrics/', views.MetricsView.as_view(), name='metrics'),
    
    # Include router URLs
    path('', include(router.urls)),
]
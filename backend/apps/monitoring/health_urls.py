"""
Health check URLs for system monitoring.
Provides endpoints for load balancers and monitoring tools.
"""
from django.urls import path
from . import health_views

app_name = 'health'

urlpatterns = [
    # Basic health check
    path('', health_views.HealthCheckView.as_view(), name='health-check'),
    
    # Detailed health checks
    path('database/', health_views.DatabaseHealthView.as_view(), name='database-health'),
    path('redis/', health_views.RedisHealthView.as_view(), name='redis-health'),
    path('celery/', health_views.CeleryHealthView.as_view(), name='celery-health'),
    
    # Readiness and liveness probes (Kubernetes-style)
    path('ready/', health_views.ReadinessProbeView.as_view(), name='readiness'),
    path('live/', health_views.LivenessProbeView.as_view(), name='liveness'),
]
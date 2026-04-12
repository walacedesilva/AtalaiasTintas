"""
Health check views for system monitoring.
Provides endpoints for load balancers and monitoring tools.
"""
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status


class HealthCheckView(APIView):
    """Basic health check - will be implemented in User Story 2"""
    
    def get(self, request):
        return Response(
            {'status': 'ok', 'detail': 'Basic health check - implementation pending'}, 
            status=status.HTTP_200_OK
        )


class DatabaseHealthView(APIView):
    """Database health check - will be implemented in User Story 2"""
    
    def get(self, request):
        return Response(
            {'status': 'ok', 'detail': 'Database health check - implementation pending'}, 
            status=status.HTTP_200_OK
        )


class RedisHealthView(APIView):
    """Redis health check - will be implemented in User Story 2"""
    
    def get(self, request):
        return Response(
            {'status': 'ok', 'detail': 'Redis health check - implementation pending'}, 
            status=status.HTTP_200_OK
        )


class CeleryHealthView(APIView):
    """Celery health check - will be implemented in User Story 2"""
    
    def get(self, request):
        return Response(
            {'status': 'ok', 'detail': 'Celery health check - implementation pending'}, 
            status=status.HTTP_200_OK
        )


class ReadinessProbeView(APIView):
    """Kubernetes readiness probe - will be implemented in User Story 2"""
    
    def get(self, request):
        return Response(
            {'status': 'ready', 'detail': 'Readiness probe - implementation pending'}, 
            status=status.HTTP_200_OK
        )


class LivenessProbeView(APIView):
    """Kubernetes liveness probe - will be implemented in User Story 2"""
    
    def get(self, request):
        return Response(
            {'status': 'alive', 'detail': 'Liveness probe - implementation pending'}, 
            status=status.HTTP_200_OK
        )
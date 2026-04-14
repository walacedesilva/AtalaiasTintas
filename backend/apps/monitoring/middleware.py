"""
Monitoring middleware for health checks and metrics collection.
"""
from django.http import JsonResponse


class HealthCheckMiddleware:
    """Pass-through middleware that allows the health check endpoint to work."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        return self.get_response(request)

"""
Monitoring application views.
System health monitoring and alerting views will be implemented here.
"""
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status


class SystemHealthView(APIView):
    """System health view - will be implemented in User Story 2"""
    
    def get(self, request):
        return Response(
            {'detail': 'System health endpoint - implementation pending'}, 
            status=status.HTTP_501_NOT_IMPLEMENTED
        )


class AlertListView(APIView):
    """Alert list view - will be implemented in User Story 2"""
    
    def get(self, request):
        return Response(
            {'detail': 'Alert list endpoint - implementation pending'}, 
            status=status.HTTP_501_NOT_IMPLEMENTED
        )


class MetricsView(APIView):
    """Metrics view - will be implemented in User Story 2"""
    
    def get(self, request):
        return Response(
            {'detail': 'Metrics endpoint - implementation pending'}, 
            status=status.HTTP_501_NOT_IMPLEMENTED
        )
"""
URL configuration for tintas_system project.

T016: Enhanced URL routing with proper API versioning, namespace organization,
health checks, and future extensibility support.

Features:
- RESTful URL design following Django and API best practices
- Comprehensive API versioning with namespace organization
- Health check endpoints for all system components
- Future extensibility and backward compatibility
- Proper static file handling for development and production
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import RedirectView, TemplateView
from django.http import JsonResponse
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page

# T015: API Documentation imports
from drf_spectacular.views import (
    SpectacularAPIView, SpectacularRedocView, SpectacularSwaggerView
)

# =============================================================================
# T016: SYSTEM-WIDE HEALTH CHECK FUNCTION
# =============================================================================

def system_health_check(request):
    """
    Simple system health check endpoint.
    Returns basic system status for load balancer health checks.
    """
    return JsonResponse({
        'status': 'healthy',
        'service': 'atalaia-tintas-api',
        'version': '1.0.0',
        'timestamp': '2024-04-18T00:00:00Z'
    })

# =============================================================================
# T016: ENHANCED URL PATTERNS WITH PROPER ORGANIZATION
# =============================================================================

urlpatterns = [
    # =============================================================================
    # ADMINISTRATIVE INTERFACE
    # =============================================================================
    path('admin/', admin.site.urls),
    
    # =============================================================================
    # API VERSIONING AND NAMESPACE ORGANIZATION
    # =============================================================================
    
    # API Version 1 (Current) - Core functionality  
    path('api/v1/core/', include(('apps.core.urls', 'core'), namespace='v1-core')),
    path('api/v1/monitoring/', include('apps.monitoring.urls')),
    path('api/v1/companies/', include('apps.companies.urls')),
    path('api/v1/inventory/', include('apps.inventory.urls')),
    path('api/v1/sales/', include('apps.sales.urls')),
    path('api/v1/tintometry/', include('apps.tintometry.urls')),
    path('api/v1/fiscal/', include('apps.fiscal.urls')),
    path('api/v1/marketplaces/', include('apps.marketplaces.urls')),
    
    # Legacy API routing (backward compatibility)
    path('api/v1/', include('apps.core.urls')),  # Default core routes for backward compatibility
    
    # =============================================================================
    # API DOCUMENTATION (T015)
    # =============================================================================
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
    
    # =============================================================================
    # HEALTH CHECK ENDPOINTS (T016)
    # =============================================================================
    
    # System-wide health checks
    path('health/', system_health_check, name='health_check'),
    path('health/detailed/', include('apps.monitoring.health_urls')),
    path('ping/', system_health_check, name='ping'),  # Simple ping endpoint
    
    # =============================================================================
    # WEB INTERFACE AND FRONTEND
    # =============================================================================
    
    # Web interface for labels
    path('etiquetas/', include('apps.tintometry.urls_web')),
    
    # Root - performance-optimized landing page (also serves frontend entry point)
    path('', TemplateView.as_view(template_name='index.html'), name='index'),
    
    # =============================================================================
    # FUTURE API VERSIONS (EXTENSIBILITY)
    # =============================================================================
    
    # API Version 2 (Future) - placeholder for breaking changes
    # path('api/v2/', include('apps.core.urls_v2', namespace='v2')),
    
    # =============================================================================
    # REDIRECTS AND COMPATIBILITY
    # =============================================================================
    
    # Redirect legacy paths to new API structure
    path('core/', RedirectView.as_view(url='/api/v1/core/', permanent=False), name='legacy_core_redirect'),
]

# Serve static and media files in development
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    
    # Add debug toolbar URLs if available
    try:
        import debug_toolbar
        urlpatterns = [
            path('__debug__/', include(debug_toolbar.urls)),
        ] + urlpatterns
    except ImportError:
        pass

# Customize admin site headers
admin.site.site_header = "Sistema de Tintas - Administração"
admin.site.site_title = "Sistema de Tintas"
admin.site.index_title = "Painel de Controle"

"""
URL configuration for tintas_system project.

Main URL routing for the paint store management system.
Includes API endpoints, admin interface, and health checks.
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import RedirectView

urlpatterns = [
    # Admin interface
    path('admin/', admin.site.urls),
    
    # API endpoints
    path('api/v1/', include('apps.core.urls')),
    path('api/v1/monitoring/', include('apps.monitoring.urls')),
    path('api/v1/companies/', include('apps.companies.urls')),
    path('api/v1/inventory/', include('apps.inventory.urls')),
    path('api/v1/sales/', include('apps.sales.urls')),
    path('api/v1/tintometry/', include('apps.tintometry.urls')),
    path('api/v1/fiscal/', include('apps.fiscal.urls')),
    path('api/v1/marketplaces/', include('apps.marketplaces.urls')),
    
    # Web interface for labels
    path('etiquetas/', include('apps.tintometry.urls_web')),
    
    # Health check endpoints
    path('health/', include('apps.monitoring.health_urls')),
    
    # Root redirect to admin (temporary)
    path('', RedirectView.as_view(url='/admin/', permanent=False)),
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

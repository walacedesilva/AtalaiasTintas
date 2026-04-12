"""
Tintometry URL Configuration

REST API endpoints for tintometric system:
- /api/tintometry/pigmentos/ - Pigment CRUD and operations
- /api/tintometry/cores/ - Color fan CRUD and matching
- /api/tintometry/formulas/ - Formula CRUD and calculations
- /api/tintometry/misturas/ - Mixture workflow and operations
- /api/tintometry/estoque/ - Stock management
- /api/tintometry/colors/ - Color science analysis
- /api/tintometry/labels/ - Label generation and management
- /api/tintometry/etiquetas/ - Label history and tracking
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views, web_views
from .labels.views import LabelGenerationViewSet, EtiquetaHistoryViewSet

# Configure router for ViewSets
router = DefaultRouter()

# Register tintometric ViewSets
router.register(r'pigmentos', views.PigmentoViewSet, basename='pigmento')
router.register(r'cores', views.LequeCorDefinidaViewSet, basename='cor-definida')
router.register(r'formulas', views.FormulaTintometricaViewSet, basename='formula')
router.register(r'misturas', views.MisturaTintaViewSet, basename='mistura')
router.register(r'estoque', views.EstoquePigmentoViewSet, basename='estoque')
router.register(r'colors', views.ColorAnalysisAPIView, basename='color-analysis')

# Register label system ViewSets
router.register(r'labels', LabelGenerationViewSet, basename='label-generation')
router.register(r'etiquetas', EtiquetaHistoryViewSet, basename='etiqueta-history')

app_name = 'tintometry'

# URL patterns (API only)
urlpatterns = [
    # Include router URLs
    path('', include(router.urls)),
    
    # Custom endpoints could be added here in the future
    # Example: path('reports/', views.ReportsView.as_view(), name='reports')
]
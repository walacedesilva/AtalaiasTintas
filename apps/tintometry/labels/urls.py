"""
URLs para o sistema de etiquetas de tintas
"""
from django.urls import path
from . import web_views

app_name = 'etiquetas'

urlpatterns = [
    # Views principais
    path('', web_views.dashboard_view, name='dashboard'),
    path('misturas/', web_views.misturas_list_view, name='misturas'),
    path('nova-mistura/', web_views.nova_mistura_view, name='nova_mistura'),
    
    # Preview e geração de etiquetas
    path('preview/<int:mistura_id>/', web_views.preview_etiqueta_view, name='preview_etiqueta'),
    path('gerar/', web_views.gerar_etiqueta_view, name='gerar_etiquetas'),
    path('gerar/<int:mistura_id>/', web_views.gerar_etiqueta_view, name='gerar_etiqueta'),
    
    # Gerenciamento de templates
    path('templates/', web_views.templates_management_view, name='templates'),
    
    # API endpoints (AJAX)
    path('api/batch-action/', web_views.batch_action_view, name='batch_action'),
    path('api/search-formulas/', web_views.search_formulas, name='search_formulas'),
    path('api/update-status/<int:mistura_id>/', web_views.update_mistura_status, name='update_status'),
    
    # Geradores de código
    path('api/qr-code/<int:mistura_id>/', web_views.get_qr_code, name='get_qr_code'),
    path('api/barcode/<int:mistura_id>/', web_views.get_barcode, name='get_barcode'),
]
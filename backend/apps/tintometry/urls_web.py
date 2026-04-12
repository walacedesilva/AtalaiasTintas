"""
URLs Web para o sistema de etiquetas
"""
from django.urls import path
from . import web_views

app_name = 'etiquetas'

urlpatterns = [
    # Dashboard principal
    path('', web_views.dashboard, name='dashboard'),
    
    # Templates
    path('templates/', web_views.templates_list, name='templates'),
    path('templates/create/', web_views.template_create, name='template_create'),
    path('templates/<int:template_id>/', web_views.template_detail, name='template_detail'),
    
    # Misturas
    path('misturas/', web_views.misturas_list, name='misturas'),
    path('misturas/nova/', web_views.nova_mistura_etiqueta, name='nova_mistura'),
    path('misturas/<str:mistura_id>/preview/', web_views.preview_etiqueta, name='preview_etiqueta'),
    
    # Geração de etiquetas
    path('gerar/', web_views.gerar_etiquetas, name='gerar'),
    path('jobs/', web_views.jobs_list, name='jobs'),
    path('jobs/<uuid:job_id>/', web_views.job_status, name='job_status'),
    path('print-queue/', web_views.print_queue, name='print_queue'),
    
    # APIs AJAX
    path('api/etiqueta-simples/', web_views.api_gerar_etiqueta_simples, name='api_etiqueta_simples'),
    path('api/jobs/<uuid:job_id>/progress/', web_views.api_job_progress, name='api_job_progress'),
    path('api/search-misturas/', web_views.api_search_misturas, name='api_search_misturas'),
]
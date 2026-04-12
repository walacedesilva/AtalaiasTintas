"""
URLs da aplicação tintometry
"""
from django.urls import path, include
from . import views

app_name = 'tintometry'

urlpatterns = [
    # URLs principais da tintometry
    path('', views.dashboard, name='dashboard'),
    
    # URLs do sistema de etiquetas
    path('etiquetas/', include('apps.tintometry.labels.urls')),
    
    # Outras URLs da tintometry podem ser adicionadas aqui
    # path('formulas/', views.formulas_list, name='formulas'),
    # path('misturas/', views.misturas_list, name='misturas'),
]
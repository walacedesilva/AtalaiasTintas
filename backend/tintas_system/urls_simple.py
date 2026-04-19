"""
URLs básicas para desenvolvimento
Versão simplificada sem apis complexas
"""

from django.contrib import admin
from django.urls import path, include
from django.shortcuts import render
from django.http import JsonResponse

def home_view(request):
    """View básica de home"""
    return render(request, 'index.html', {
        'title': 'Sistema de Tintas - AtalaiasTintas',
        'status': 'Rodando com configuração simplificada'
    })

def health_check(request):
    """Health check básico"""
    return JsonResponse({
        'status': 'ok',
        'message': 'Sistema funcionando',
        'version': '1.0.0'
    })

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', home_view, name='home'),
    path('health/', health_check, name='health'),
    
    # APIs necessárias para o frontend
    path('api/v1/auth/', include(('apps.core.urls', 'core'), namespace='auth')),  # Rotas de autenticação
    path('api/v1/', include('apps.core.urls')),  # Rotas do core para backward compatibility
]
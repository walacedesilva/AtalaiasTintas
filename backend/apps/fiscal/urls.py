from django.urls import path
from rest_framework.routers import DefaultRouter

from apps.fiscal.apis import (
    NotaFiscalViewSet,
    NFEAutomacaoViewSet,
    SefazIntegracaoAPIView,
)
from apps.fiscal.views import nfe_dashboard, retry_queue

router = DefaultRouter()
router.register(r'notas-fiscais', NotaFiscalViewSet, basename='notafiscal')
router.register(r'nfe-automacao', NFEAutomacaoViewSet, basename='nfe-automacao')

app_name = 'fiscal'

urlpatterns = [
    # REST API
    path('sefaz/', SefazIntegracaoAPIView.as_view(), name='sefaz-status'),
    # Django HTML views
    path('dashboard/', nfe_dashboard, name='nfe-dashboard'),
    path('retry-queue/', retry_queue, name='retry-queue'),
] + router.urls


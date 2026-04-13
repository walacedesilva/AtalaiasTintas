from django.urls import path
from rest_framework.routers import DefaultRouter

from apps.inventory.apis import (
    ConversaoUnidadeViewSet,
    EstoqueConsultaAPIView,
    EstoqueLojaViewSet,
    EstoqueReservaViewSet,
    EntradaMercadoriaViewSet,
    LoteViewSet,
)

router = DefaultRouter()
router.register(r'conversao', ConversaoUnidadeViewSet, basename='conversao-unidade')
router.register(r'reservas', EstoqueReservaViewSet, basename='estoque-reserva')
router.register(r'lotes', LoteViewSet, basename='lote-produto')
router.register(r'entradas', EntradaMercadoriaViewSet, basename='entrada-mercadoria')
router.register(r'estoque-loja', EstoqueLojaViewSet, basename='estoque-loja')

app_name = 'inventory'

urlpatterns = [
    path('estoque/disponibilidade/', EstoqueConsultaAPIView.as_view(), name='estoque-disponibilidade'),
] + router.urls

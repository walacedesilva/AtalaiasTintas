from django.urls import path
from rest_framework.routers import DefaultRouter

from apps.sales.apis import (
    ClienteViewSet,
    DashboardMetricsAPIView,
    NFeElegibilidadeAPIView,
    NFeStatusAPIView,
    MultiUnitPriceAPIView,
    PDVCheckoutAPIView,
    PedidoVendaViewSet,
    RastreabilidadeAPIView,
    RecebivelViewSet,
    StockAvailabilityAPIView,
    VendaViewSet,
)

router = DefaultRouter()
router.register(r'clientes', ClienteViewSet, basename='cliente')
router.register(r'pedidos', PedidoVendaViewSet, basename='pedido')
router.register(r'vendas', VendaViewSet, basename='venda')
router.register(r'recebiveis', RecebivelViewSet, basename='recebivel')

app_name = 'sales'

urlpatterns = [
    path('dashboard/', DashboardMetricsAPIView.as_view(), name='dashboard-metrics'),
    path('estoque-disponivel/', StockAvailabilityAPIView.as_view(), name='estoque-disponivel'),
    path('preco-multiunit/', MultiUnitPriceAPIView.as_view(), name='preco-multiunit'),
    path('rastreabilidade/', RastreabilidadeAPIView.as_view(), name='rastreabilidade'),
    path('pdv/checkout/', PDVCheckoutAPIView.as_view(), name='pdv-checkout'),
    path('vendas/<str:venda_id>/nfe-status/', NFeStatusAPIView.as_view(), name='nfe-status'),
    path('vendas/<str:venda_id>/nfe-elegibilidade/', NFeElegibilidadeAPIView.as_view(), name='nfe-elegibilidade'),
] + router.urls

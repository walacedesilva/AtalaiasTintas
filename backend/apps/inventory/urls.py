from django.urls import path
from rest_framework.routers import DefaultRouter

from apps.inventory.apis import (
    CategoriaViewSet,
    ConversaoUnidadeViewSet,
    EstoqueConsultaAPIView,
    EstoqueLojaViewSet,
    EstoqueReservaViewSet,
    EntradaMercadoriaViewSet,
    LoteViewSet,
    MarcaViewSet,
    ProdutoBaseViewSet,
    ProdutoVariacaoViewSet,
)

router = DefaultRouter()
router.register(r'conversao', ConversaoUnidadeViewSet, basename='conversao-unidade')
router.register(r'reservas', EstoqueReservaViewSet, basename='estoque-reserva')
router.register(r'lotes', LoteViewSet, basename='lote-produto')
router.register(r'entradas', EntradaMercadoriaViewSet, basename='entrada-mercadoria')
router.register(r'estoque-loja', EstoqueLojaViewSet, basename='estoque-loja')
router.register(r'produtos', ProdutoBaseViewSet, basename='produto')
router.register(r'variacoes', ProdutoVariacaoViewSet, basename='produto-variacao')
router.register(r'categorias', CategoriaViewSet, basename='categoria')
router.register(r'marcas', MarcaViewSet, basename='marca')

app_name = 'inventory'

urlpatterns = [
    path('estoque/disponibilidade/', EstoqueConsultaAPIView.as_view(), name='estoque-disponibilidade'),
] + router.urls

from django.urls import path
from rest_framework.routers import DefaultRouter

from apps.companies.apis import LojaViewSet

router = DefaultRouter()
router.register(r'lojas', LojaViewSet, basename='loja')

app_name = 'companies'

urlpatterns = [] + router.urls
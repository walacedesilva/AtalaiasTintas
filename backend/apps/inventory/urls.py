from django.urls import path
from rest_framework.routers import DefaultRouter

router = DefaultRouter()
app_name = 'inventory'

urlpatterns = [
    # Inventory endpoints will be implemented in future user stories
] + router.urls
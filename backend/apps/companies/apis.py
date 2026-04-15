"""Companies REST APIs — read-only Loja listing."""
from rest_framework import permissions, serializers
from rest_framework.viewsets import ReadOnlyModelViewSet

from apps.companies.models import Loja


class LojaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Loja
        fields = ['id', 'nome', 'uf', 'cidade', 'ativa']


class LojaViewSet(ReadOnlyModelViewSet):
    """GET /api/v1/companies/lojas/ — list stores available to the current user."""
    serializer_class = LojaSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Loja.objects.filter(ativa=True).order_by('nome')

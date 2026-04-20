"""Companies REST APIs — read-only Loja listing."""
from rest_framework import permissions, serializers
from rest_framework.viewsets import ReadOnlyModelViewSet

from apps.companies.models import Empresa, Loja


class EmpresaResumoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Empresa
        fields = ['id', 'razao_social', 'nome_fantasia', 'cnpj']


class LojaSerializer(serializers.ModelSerializer):
    empresa_data = EmpresaResumoSerializer(source='empresa', read_only=True)

    class Meta:
        model = Loja
        fields = [
            'id', 'nome', 'uf', 'cidade', 'ativa',
            'endereco', 'numero', 'bairro', 'telefone',
            'empresa_data',
        ]


class LojaViewSet(ReadOnlyModelViewSet):
    """GET /api/v1/companies/lojas/ — list stores available to the current user."""
    serializer_class = LojaSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Loja.objects.filter(ativa=True).order_by('nome')

"""
Inventory REST APIs
===================
ConversaoUnidadeViewSet — unit conversion (T024)
EstoqueReservaViewSet   — reservation management (T027)
EstoqueConsultaAPIView  — real-time stock queries (T032)
LoteViewSet             — batch / expiry management (new)
EntradaMercadoriaViewSet — goods receipt + XML import (T034)
"""
from __future__ import annotations

import logging
from decimal import Decimal

from django.shortcuts import get_object_or_404
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from rest_framework import permissions, serializers, status, viewsets
from rest_framework.decorators import action
from rest_framework.parsers import MultiPartParser
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.inventory.models import (
    Categoria,
    EntradaMercadoria,
    EntradaMercadoriaItem,
    EstoqueLoja,
    EstoqueReserva,
    LoteProduto,
    Marca,
    ProdutoBase,
    ProdutoUnidade,
    ProdutoVariacao,
    UnidadeMedida,
)
from apps.inventory.services import ConversaoService, EstoqueService, LoteService

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Serializers
# ---------------------------------------------------------------------------

class UnidadeMedidaSerializer(serializers.ModelSerializer):
    class Meta:
        model = UnidadeMedida
        fields = ['id', 'codigo', 'nome', 'sigla', 'tipo']


class ProdutoUnidadeSerializer(serializers.ModelSerializer):
    unidade = UnidadeMedidaSerializer(read_only=True)

    class Meta:
        model = ProdutoUnidade
        fields = ['id', 'unidade', 'unidade_base', 'fator_conversao', 'preco_diferenciado', 'ativa']


class ConversaoRequestSerializer(serializers.Serializer):
    produto_variacao_id = serializers.UUIDField()
    quantidade = serializers.DecimalField(max_digits=10, decimal_places=4)
    unidade_origem_id = serializers.IntegerField()


class EstoqueReservaSerializer(serializers.ModelSerializer):
    class Meta:
        model = EstoqueReserva
        fields = ['id', 'produto', 'quantidade_reservada', 'unidade', 'sessao_checkout',
                  'expira_em', 'status', 'venda']
        read_only_fields = ['id', 'status', 'expira_em']


class CriarReservaSerializer(serializers.Serializer):
    produto_variacao_id = serializers.UUIDField()
    loja_id = serializers.IntegerField()
    quantidade = serializers.DecimalField(max_digits=10, decimal_places=4)
    unidade_id = serializers.IntegerField()
    sessao_checkout = serializers.CharField(max_length=100)
    minutos_expiracao = serializers.IntegerField(default=30, min_value=5, max_value=120)


class LoteSerializer(serializers.ModelSerializer):
    esta_vencido = serializers.ReadOnlyField()
    dias_para_vencer = serializers.ReadOnlyField()

    class Meta:
        model = LoteProduto
        fields = [
            'id', 'produto', 'loja', 'numero_lote', 'data_fabricacao', 'data_validade',
            'data_entrada', 'quantidade_inicial', 'quantidade_atual', 'unidade',
            'custo_unitario', 'status', 'documento_entrada', 'observacoes',
            'esta_vencido', 'dias_para_vencer',
        ]
        read_only_fields = ['id']


class EntradaMercadoriaItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = EntradaMercadoriaItem
        fields = [
            'id', 'produto', 'descricao_nfe', 'codigo_nfe', 'ncm', 'cfop', 'cean',
            'quantidade', 'unidade', 'unidade_nfe', 'valor_unitario', 'valor_total',
            'desconto', 'valor_icms', 'valor_ipi', 'valor_pis', 'valor_cofins',
            'lote', 'status',
        ]


class EntradaMercadoriaSerializer(serializers.ModelSerializer):
    itens = EntradaMercadoriaItemSerializer(many=True, read_only=True)

    class Meta:
        model = EntradaMercadoria
        fields = [
            'id', 'loja', 'tipo_entrada', 'fornecedor_cnpj', 'fornecedor_nome',
            'chave_acesso_nfe', 'numero_nfe', 'serie_nfe', 'data_emissao_nfe',
            'data_entrada', 'valor_total_nfe', 'valor_total_entrada', 'status',
            'origem_entrada', 'observacoes', 'itens',
        ]
        read_only_fields = ['id', 'status', 'valor_total_entrada']


class EntradaMercadoriaItemManualSerializer(serializers.Serializer):
    """Write-only serializer for inline items in manual goods entry."""
    descricao_nfe = serializers.CharField(max_length=200)
    codigo_nfe = serializers.CharField(max_length=60, required=False, allow_blank=True)
    ncm = serializers.CharField(max_length=10, required=False, allow_blank=True)
    cfop = serializers.CharField(max_length=4, required=False, allow_blank=True)
    quantidade = serializers.DecimalField(max_digits=10, decimal_places=4, min_value=0)
    unidade_nfe = serializers.CharField(max_length=6, required=False, allow_blank=True)
    valor_unitario = serializers.DecimalField(max_digits=10, decimal_places=4, min_value=0)


class EntradaMercadoriaManualSerializer(serializers.Serializer):
    """Serializer for manual NF-e entry (no XML file required)."""
    loja_id = serializers.IntegerField()
    numero_nfe = serializers.CharField(max_length=9)
    serie_nfe = serializers.CharField(max_length=3, default='1')
    fornecedor_cnpj = serializers.CharField(max_length=18)  # with or without formatting
    fornecedor_nome = serializers.CharField(max_length=200, required=False, allow_blank=True)
    fornecedor_uf = serializers.CharField(max_length=2, required=False, allow_blank=True)
    data_emissao_nfe = serializers.DateField(required=False, allow_null=True)
    valor_total_nfe = serializers.DecimalField(
        max_digits=12, decimal_places=2, required=False, allow_null=True
    )
    chave_acesso_nfe = serializers.CharField(
        max_length=44, required=False, allow_blank=True, allow_null=True
    )
    observacoes = serializers.CharField(required=False, allow_blank=True, default='')
    itens = EntradaMercadoriaItemManualSerializer(many=True)


# ---------------------------------------------------------------------------
# ConversaoUnidadeViewSet — T024
# ---------------------------------------------------------------------------

class ConversaoUnidadeViewSet(viewsets.ViewSet):
    """Unit conversion queries and product unit configuration."""
    permission_classes = [permissions.IsAuthenticated]

    @action(detail=False, methods=['post'], url_path='converter')
    def converter(self, request):
        """Convert a quantity from one unit to the product's base unit.

        POST /api/v1/inventory/conversao/converter/
        """
        serializer = ConversaoRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        try:
            qtd_base = ConversaoService.converter_quantidade(
                str(data['produto_variacao_id']),
                data['quantidade'],
                data['unidade_origem_id'],
            )
            unidade_base = ConversaoService.obter_unidade_base(str(data['produto_variacao_id']))
        except ValueError as exc:
            return Response({'detail': str(exc)}, status=status.HTTP_400_BAD_REQUEST)

        return Response({
            'quantidade_original': str(data['quantidade']),
            'unidade_origem_id': data['unidade_origem_id'],
            'quantidade_base': str(qtd_base),
            'unidade_base': UnidadeMedidaSerializer(unidade_base).data,
        })

    @action(detail=False, methods=['get'], url_path=r'produto/(?P<produto_id>[^/.]+)/unidades')
    def unidades_produto(self, request, produto_id=None):
        """List all configured units for a product variant.

        GET /api/v1/inventory/conversao/produto/{produto_id}/unidades/
        """
        get_object_or_404(ProdutoVariacao, pk=produto_id)
        qs = ProdutoUnidade.objects.filter(produto_id=produto_id, ativa=True).select_related('unidade')
        return Response(ProdutoUnidadeSerializer(qs, many=True).data)


# ---------------------------------------------------------------------------
# EstoqueReservaViewSet — T027
# ---------------------------------------------------------------------------

class EstoqueReservaViewSet(viewsets.ViewSet):
    """Create, list, confirm and cancel stock reservations."""
    permission_classes = [permissions.IsAuthenticated]

    @action(detail=False, methods=['post'], url_path='criar')
    def criar(self, request):
        """Create a new reservation.

        POST /api/v1/inventory/reservas/criar/
        """
        serializer = CriarReservaSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        try:
            reserva = EstoqueService.criar_reserva(
                produto_variacao_id=str(data['produto_variacao_id']),
                loja_id=data['loja_id'],
                quantidade=data['quantidade'],
                unidade_id=data['unidade_id'],
                sessao_checkout=data['sessao_checkout'],
                usuario=request.user,
                minutos_expiracao=data.get('minutos_expiracao', 30),
            )
        except (ValueError, Exception) as exc:
            return Response({'detail': str(exc)}, status=status.HTTP_400_BAD_REQUEST)

        return Response(EstoqueReservaSerializer(reserva).data, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=['post'], url_path='confirmar')
    def confirmar(self, request):
        """Confirm all reservations for a checkout session.

        POST /api/v1/inventory/reservas/confirmar/
        Body: { "sessao_checkout": "...", "venda_id": "..." }
        """
        sessao = request.data.get('sessao_checkout')
        venda_id = request.data.get('venda_id')
        if not sessao or not venda_id:
            return Response(
                {'detail': 'sessao_checkout e venda_id são obrigatórios'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        confirmadas = EstoqueService.confirmar_reservas(sessao, venda_id)
        return Response({'confirmadas': len(confirmadas)})

    @action(detail=False, methods=['post'], url_path='cancelar')
    def cancelar(self, request):
        """Cancel all reservations for a checkout session.

        POST /api/v1/inventory/reservas/cancelar/
        Body: { "sessao_checkout": "..." }
        """
        sessao = request.data.get('sessao_checkout')
        if not sessao:
            return Response(
                {'detail': 'sessao_checkout é obrigatório'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        EstoqueService.cancelar_reservas(sessao)
        return Response({'detail': 'Reservas canceladas'})

    @action(detail=False, methods=['get'], url_path='ativas')
    def ativas(self, request):
        """List active reservations for the current user's session.

        GET /api/v1/inventory/reservas/ativas/?sessao_checkout=xxx
        """
        sessao = request.query_params.get('sessao_checkout')
        qs = EstoqueReserva.objects.filter(status='ATIVA')
        if sessao:
            qs = qs.filter(sessao_checkout=sessao)
        return Response(EstoqueReservaSerializer(qs, many=True).data)


# ---------------------------------------------------------------------------
# EstoqueConsultaAPIView — T032
# ---------------------------------------------------------------------------

class EstoqueConsultaAPIView(APIView):
    """Real-time stock availability query.

    GET /api/v1/inventory/estoque/disponibilidade/
    Params: produto_variacao_id, loja_id, quantidade (optional), unidade_id (optional)
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        produto_id = request.query_params.get('produto_variacao_id')
        loja_id = request.query_params.get('loja_id')

        if not produto_id or not loja_id:
            return Response(
                {'detail': 'produto_variacao_id e loja_id são obrigatórios'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        disponivel = EstoqueService.calcular_disponibilidade(produto_id, int(loja_id))

        resultado = {
            'produto_variacao_id': produto_id,
            'loja_id': loja_id,
            'quantidade_disponivel': str(disponivel),
        }

        # Optional: check if a specific quantity is available
        qtd_str = request.query_params.get('quantidade')
        unidade_id = request.query_params.get('unidade_id')
        if qtd_str and unidade_id:
            qtd = Decimal(qtd_str)
            resultado['quantidade_solicitada'] = str(qtd)
            resultado['unidade_id'] = unidade_id
            try:
                resultado['disponivel'] = EstoqueService.verificar_disponibilidade(
                    produto_id, int(loja_id), qtd, int(unidade_id)
                )
            except ValueError as exc:
                resultado['disponivel'] = False
                resultado['detalhe'] = str(exc)

        return Response(resultado)


# ---------------------------------------------------------------------------
# LoteViewSet — new feature
# ---------------------------------------------------------------------------

class LoteViewSet(viewsets.ModelViewSet):
    """CRUD + queries for batch/expiry control."""
    serializer_class = LoteSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        qs = LoteProduto.objects.select_related('produto__produto_base', 'unidade', 'loja')
        loja_id = self.request.query_params.get('loja_id')
        produto_id = self.request.query_params.get('produto_id')
        status_param = self.request.query_params.get('status')
        if loja_id:
            qs = qs.filter(loja_id=loja_id)
        if produto_id:
            qs = qs.filter(produto_id=produto_id)
        if status_param:
            qs = qs.filter(status=status_param)
        return qs

    @action(detail=False, methods=['get'], url_path='proximos-vencimento')
    def proximos_vencimento(self, request):
        """List batches expiring soon.

        GET /api/v1/inventory/lotes/proximos-vencimento/?loja_id=1&dias=30
        """
        loja_id = request.query_params.get('loja_id')
        dias = int(request.query_params.get('dias', 30))
        if not loja_id:
            return Response(
                {'detail': 'loja_id é obrigatório'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        lotes = LoteService.listar_lotes_proximos_vencimento(int(loja_id), dias)
        return Response(LoteSerializer(lotes, many=True).data)

    @action(detail=False, methods=['post'], url_path='marcar-vencidos')
    def marcar_vencidos(self, request):
        """Manually trigger expiry marking (normally done via Celery task).

        POST /api/v1/inventory/lotes/marcar-vencidos/
        """
        loja_id = request.data.get('loja_id')
        count = LoteService.marcar_lotes_vencidos(int(loja_id) if loja_id else None)
        return Response({'marcados': count})


# ---------------------------------------------------------------------------
# EntradaMercadoriaViewSet — T034 + XML import
# ---------------------------------------------------------------------------

class EntradaMercadoriaViewSet(viewsets.ModelViewSet):
    """Goods receipt management including XML NF-e import."""
    serializer_class = EntradaMercadoriaSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        qs = EntradaMercadoria.objects.prefetch_related('itens').select_related('loja', 'usuario')
        loja_id = self.request.query_params.get('loja_id')
        if loja_id:
            qs = qs.filter(loja_id=loja_id)
        return qs

    @action(
        detail=False,
        methods=['post'],
        url_path='importar-xml',
        parser_classes=[MultiPartParser],
    )
    def importar_xml(self, request):
        """Import a supplier NF-e XML file and create an EntradaMercadoria.

        POST /api/v1/inventory/entradas/importar-xml/
        Multipart field: xml_file (file) OR xml_content (plain text)
        loja_id (form field) required.
        """
        from apps.fiscal.services import EntradaMercadoriaService

        loja_id = request.data.get('loja_id')
        if not loja_id:
            return Response(
                {'detail': 'loja_id é obrigatório'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        xml_file = request.FILES.get('xml_file')
        xml_content_raw = request.data.get('xml_content')

        if xml_file:
            try:
                xml_content = xml_file.read().decode('utf-8', errors='replace')
            except Exception as exc:
                return Response(
                    {'detail': f'Erro ao ler arquivo: {exc}'},
                    status=status.HTTP_400_BAD_REQUEST,
                )
        elif xml_content_raw:
            xml_content = xml_content_raw
        else:
            return Response(
                {'detail': 'Envie xml_file (arquivo) ou xml_content (texto)'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            entrada = EntradaMercadoriaService.importar_xml(
                xml_content=xml_content,
                loja_id=int(loja_id),
                usuario=request.user,
            )
        except ValueError as exc:
            return Response({'detail': str(exc)}, status=status.HTTP_422_UNPROCESSABLE_ENTITY)
        except Exception as exc:
            logger.exception("Erro ao importar XML NF-e: %s", exc)
            return Response(
                {'detail': 'Erro interno ao processar XML'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        return Response(
            EntradaMercadoriaSerializer(entrada).data,
            status=status.HTTP_201_CREATED,
        )

    @action(detail=True, methods=['post'], url_path='confirmar')
    def confirmar(self, request, pk=None):
        """Confirm a goods receipt: update stock for all linked items.

        POST /api/v1/inventory/entradas/{id}/confirmar/
        """
        from apps.fiscal.services import EntradaMercadoriaService

        try:
            entrada = EntradaMercadoriaService.confirmar_entrada(pk, request.user)
        except (ValueError, EntradaMercadoria.DoesNotExist) as exc:
            return Response({'detail': str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as exc:
            logger.exception("Erro ao confirmar entrada: %s", exc)
            return Response({'detail': str(exc)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        return Response(EntradaMercadoriaSerializer(entrada).data)

    @action(detail=True, methods=['patch'], url_path=r'itens/(?P<item_id>[^/.]+)/vincular')
    def vincular_item(self, request, pk=None, item_id=None):
        """Link an item to an existing ProdutoVariacao.

        PATCH /api/v1/inventory/entradas/{id}/itens/{item_id}/vincular/
        Body: { "produto_id": "...", "unidade_id": 1 }
        """
        item = get_object_or_404(EntradaMercadoriaItem, pk=item_id, entrada_id=pk)
        produto_id = request.data.get('produto_id')
        unidade_id = request.data.get('unidade_id')

        if not produto_id:
            return Response(
                {'detail': 'produto_id é obrigatório'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        get_object_or_404(ProdutoVariacao, pk=produto_id)

        item.produto_id = produto_id
        if unidade_id:
            item.unidade_id = unidade_id
        item.status = 'VINCULADO'
        item.save(update_fields=['produto', 'unidade', 'status', 'updated_at'])

        return Response(EntradaMercadoriaItemSerializer(item).data)

    @action(detail=False, methods=['post'], url_path='criar-manual')
    def criar_manual(self, request):
        """Create a goods receipt from manual form data (no XML required).

        POST /api/v1/inventory/entradas/criar-manual/
        Body: EntradaMercadoriaManualSerializer fields.
        """
        from apps.fiscal.services import EntradaMercadoriaService

        serializer = EntradaMercadoriaManualSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        try:
            entrada = EntradaMercadoriaService.criar_manual(
                loja_id=data['loja_id'],
                usuario=request.user,
                numero_nfe=data['numero_nfe'],
                serie_nfe=data.get('serie_nfe', '1'),
                fornecedor_cnpj=data['fornecedor_cnpj'],
                fornecedor_nome=data.get('fornecedor_nome') or None,
                fornecedor_uf=data.get('fornecedor_uf') or None,
                data_emissao_nfe=data.get('data_emissao_nfe'),
                valor_total_nfe=data.get('valor_total_nfe'),
                chave_acesso_nfe=data.get('chave_acesso_nfe') or None,
                observacoes=data.get('observacoes', ''),
                itens=data['itens'],
            )
        except ValueError as exc:
            return Response({'detail': str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as exc:
            logger.exception("Erro ao criar entrada manual: %s", exc)
            return Response(
                {'detail': 'Erro interno ao criar entrada'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        return Response(
            EntradaMercadoriaSerializer(entrada).data,
            status=status.HTTP_201_CREATED,
        )


# ---------------------------------------------------------------------------
# EstoqueLojaViewSet — stock listing + summary (frontend inventory page)
# ---------------------------------------------------------------------------

class EstoqueLojaSerializer(serializers.ModelSerializer):
    produto_id = serializers.UUIDField(source='produto_variacao.id', read_only=True)
    produto_codigo = serializers.CharField(source='produto_variacao.codigo_variacao', read_only=True)
    produto_nome = serializers.CharField(source='produto_variacao.nome_variacao', read_only=True)
    produto_base_nome = serializers.CharField(source='produto_variacao.produto_base.nome', read_only=True)
    marca_nome = serializers.CharField(source='produto_variacao.produto_base.marca.nome', read_only=True)
    unidade_sigla = serializers.CharField(source='produto_variacao.unidade_estoque.sigla', read_only=True)
    estoque_minimo = serializers.DecimalField(
        source='produto_variacao.estoque_minimo', max_digits=10, decimal_places=2, read_only=True
    )
    preco_custo = serializers.DecimalField(
        source='produto_variacao.preco_custo', max_digits=10, decimal_places=2, read_only=True
    )
    preco_venda = serializers.DecimalField(
        source='produto_variacao.preco_venda', max_digits=10, decimal_places=2, read_only=True
    )
    quantidade_disponivel = serializers.ReadOnlyField()
    status_estoque = serializers.SerializerMethodField()

    def get_status_estoque(self, obj):
        disponivel = obj.quantidade_disponivel
        minimo = obj.produto_variacao.estoque_minimo
        if disponivel <= 0:
            return 'ZERADO'
        if minimo and disponivel <= minimo:
            return 'BAIXO'
        return 'NORMAL'

    class Meta:
        model = EstoqueLoja
        fields = [
            'id', 'loja',
            'produto_id', 'produto_codigo', 'produto_nome', 'produto_base_nome', 'marca_nome',
            'unidade_sigla', 'estoque_minimo', 'preco_custo', 'preco_venda',
            'quantidade_atual', 'quantidade_reservada', 'quantidade_disponivel',
            'status_estoque', 'localizacao', 'data_ultima_movimentacao', 'bloqueado_venda',
        ]


class EstoqueLojaViewSet(viewsets.ReadOnlyModelViewSet):
    """Read-only listing of EstoqueLoja records with search, filter and summary action."""
    serializer_class = EstoqueLojaSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        from django.db.models import Q
        qs = EstoqueLoja.objects.select_related(
            'produto_variacao__produto_base__marca',
            'produto_variacao__unidade_estoque',
            'loja',
        )
        loja_id = self.request.query_params.get('loja_id')
        search = self.request.query_params.get('search')
        status_param = self.request.query_params.get('status')

        if loja_id:
            qs = qs.filter(loja_id=loja_id)
        if search:
            qs = qs.filter(
                Q(produto_variacao__nome_variacao__icontains=search) |
                Q(produto_variacao__codigo_variacao__icontains=search) |
                Q(produto_variacao__produto_base__nome__icontains=search)
            )
        from django.db.models import F
        if status_param == 'ZERADO':
            qs = qs.filter(quantidade_atual__lte=0)
        elif status_param == 'BAIXO':
            qs = qs.filter(
                quantidade_atual__gt=0,
                quantidade_atual__lte=F('produto_variacao__estoque_minimo'),
            )
        return qs.order_by('produto_variacao__produto_base__nome', 'produto_variacao__nome_variacao')

    @method_decorator(cache_page(30))  # 30 s cache — summary is expensive
    @action(detail=False, methods=['get'], url_path='resumo')
    def resumo(self, request):
        """Stock summary stats.

        GET /api/v1/inventory/estoque-loja/resumo/?loja_id=1
        """
        from django.db.models import F, Sum, ExpressionWrapper
        from django.db.models import DecimalField as DField

        loja_id = self.request.query_params.get('loja_id')
        qs = EstoqueLoja.objects.select_related('produto_variacao')
        if loja_id:
            qs = qs.filter(loja_id=loja_id)

        total = qs.count()
        zerado = qs.filter(quantidade_atual__lte=0).count()
        baixo = qs.filter(
            quantidade_atual__gt=0,
            quantidade_atual__lte=F('produto_variacao__estoque_minimo'),
        ).count()
        valor_agg = qs.aggregate(
            v=Sum(
                ExpressionWrapper(
                    F('quantidade_atual') * F('produto_variacao__preco_custo'),
                    output_field=DField(max_digits=16, decimal_places=2),
                )
            )
        )
        valor = valor_agg['v'] or 0

        return Response({
            'total_itens': total,
            'estoque_zerado': zerado,
            'estoque_baixo': baixo,
            'valor_total_custo': str(valor),
        })


# ---------------------------------------------------------------------------
# ProdutoBaseViewSet + ProdutoVariacaoViewSet — Product CRUD
# ---------------------------------------------------------------------------

class CategoriaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Categoria
        fields = ['id', 'nome', 'codigo', 'nivel', 'parent', 'permite_tintometria', 'exige_formula', 'ativa']


class MarcaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Marca
        fields = ['id', 'nome', 'codigo', 'ativa']


class ProdutoVariacaoListSerializer(serializers.ModelSerializer):
    unidade_venda_nome = serializers.CharField(source='unidade_venda.nome', read_only=True)
    unidade_estoque_nome = serializers.CharField(source='unidade_estoque.nome', read_only=True)

    class Meta:
        model = ProdutoVariacao
        fields = [
            'id', 'codigo_variacao', 'nome_variacao', 'cor', 'cor_codigo', 'tamanho',
            'unidade_venda', 'unidade_venda_nome', 'unidade_estoque', 'unidade_estoque_nome',
            'fator_conversao_venda', 'ncm', 'cest',
            'preco_custo', 'preco_venda', 'margem_lucro',
            'estoque_minimo', 'estoque_maximo', 'ativo',
        ]


class ProdutoVariacaoWriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProdutoVariacao
        fields = [
            'codigo_variacao', 'nome_variacao', 'cor', 'cor_codigo', 'tamanho',
            'unidade_venda', 'unidade_estoque', 'fator_conversao_venda',
            'ncm', 'cest', 'preco_custo', 'preco_venda', 'margem_lucro',
            'estoque_minimo', 'estoque_maximo', 'ativo',
        ]


class ProdutoBaseSerializer(serializers.ModelSerializer):
    variacoes = ProdutoVariacaoListSerializer(many=True, read_only=True)
    categoria_nome = serializers.CharField(source='categoria.nome', read_only=True)
    marca_nome = serializers.CharField(source='marca.nome', read_only=True)

    class Meta:
        model = ProdutoBase
        fields = [
            'id', 'codigo', 'nome', 'descricao',
            'categoria', 'categoria_nome', 'marca', 'marca_nome',
            'tipo_produto', 'base_tintometrica', 'linha_produto',
            'ativo', 'variacoes',
        ]
        read_only_fields = ['id']


class ProdutoBaseWriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProdutoBase
        fields = [
            'codigo', 'nome', 'descricao',
            'categoria', 'marca', 'tipo_produto',
            'base_tintometrica', 'linha_produto',
            'especificacoes_tecnicas', 'ativo',
        ]

    def validate_codigo(self, value):
        qs = ProdutoBase.objects.filter(codigo=value)
        if self.instance:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise serializers.ValidationError('Já existe um produto com este código.')
        return value


class ProdutoBaseViewSet(viewsets.ModelViewSet):
    """Full CRUD for ProdutoBase (produto mãe + variações).

    GET    /api/v1/inventory/produtos/              — lista
    POST   /api/v1/inventory/produtos/              — criar
    GET    /api/v1/inventory/produtos/{id}/         — detalhe com variações
    PATCH  /api/v1/inventory/produtos/{id}/         — editar
    DELETE /api/v1/inventory/produtos/{id}/         — desativar (soft-delete)
    GET    /api/v1/inventory/produtos/{id}/variacoes/ — listar variações
    POST   /api/v1/inventory/produtos/{id}/variacoes/ — criar variação
    """
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        qs = ProdutoBase.objects.select_related('categoria', 'marca').prefetch_related('variacoes')
        search = self.request.query_params.get('search')
        categoria_id = self.request.query_params.get('categoria_id')
        marca_id = self.request.query_params.get('marca_id')
        tipo = self.request.query_params.get('tipo_produto')
        ativo = self.request.query_params.get('ativo')

        if search:
            from django.db.models import Q
            qs = qs.filter(Q(nome__icontains=search) | Q(codigo__icontains=search))
        if categoria_id:
            qs = qs.filter(categoria_id=categoria_id)
        if marca_id:
            qs = qs.filter(marca_id=marca_id)
        if tipo:
            qs = qs.filter(tipo_produto=tipo)
        if ativo is not None:
            qs = qs.filter(ativo=ativo.lower() == 'true')

        return qs.order_by('nome')

    def get_serializer_class(self):
        if self.action in ('create', 'update', 'partial_update'):
            return ProdutoBaseWriteSerializer
        return ProdutoBaseSerializer

    def destroy(self, request, *args, **kwargs):
        """Soft-delete: mark ativo=False instead of deleting."""
        produto = self.get_object()
        produto.ativo = False
        produto.save(update_fields=['ativo'])
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=['get', 'post'], url_path='variacoes')
    def variacoes(self, request, pk=None):
        """List or create variations for a product.

        GET  /api/v1/inventory/produtos/{id}/variacoes/
        POST /api/v1/inventory/produtos/{id}/variacoes/
        """
        produto = self.get_object()

        if request.method == 'GET':
            qs = ProdutoVariacao.objects.filter(produto_base=produto).select_related(
                'unidade_venda', 'unidade_estoque'
            )
            return Response(ProdutoVariacaoListSerializer(qs, many=True).data)

        serializer = ProdutoVariacaoWriteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        variacao = serializer.save(produto_base=produto)
        return Response(
            ProdutoVariacaoListSerializer(variacao).data,
            status=status.HTTP_201_CREATED,
        )


class ProdutoVariacaoViewSet(viewsets.ModelViewSet):
    """CRUD for ProdutoVariacao standalone.

    Supports patch and delete by variacao ID directly without going through ProdutoBase.

    PATCH  /api/v1/inventory/variacoes/{id}/
    DELETE /api/v1/inventory/variacoes/{id}/
    """
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        qs = ProdutoVariacao.objects.select_related(
            'produto_base', 'unidade_venda', 'unidade_estoque'
        )
        produto_id = self.request.query_params.get('produto_id')
        search = self.request.query_params.get('search')
        ativo = self.request.query_params.get('ativo')

        if produto_id:
            qs = qs.filter(produto_base_id=produto_id)
        if search:
            from django.db.models import Q
            qs = qs.filter(
                Q(codigo_variacao__icontains=search) | Q(nome_variacao__icontains=search)
            )
        if ativo is not None:
            qs = qs.filter(ativo=ativo.lower() == 'true')

        return qs.order_by('nome_variacao')

    def get_serializer_class(self):
        if self.action in ('create', 'update', 'partial_update'):
            return ProdutoVariacaoWriteSerializer
        return ProdutoVariacaoListSerializer

    def destroy(self, request, *args, **kwargs):
        """Soft-delete: mark ativo=False."""
        variacao = self.get_object()
        variacao.ativo = False
        variacao.save(update_fields=['ativo'])
        return Response(status=status.HTTP_204_NO_CONTENT)


class CategoriaViewSet(viewsets.ReadOnlyModelViewSet):
    """Read-only list of categories for filters/dropdowns."""
    serializer_class = CategoriaSerializer
    permission_classes = [permissions.IsAuthenticated]
    queryset = Categoria.objects.filter(ativa=True).order_by('nivel', 'ordem', 'nome')


class MarcaViewSet(viewsets.ReadOnlyModelViewSet):
    """Read-only list of brands for filters/dropdowns."""
    serializer_class = MarcaSerializer
    permission_classes = [permissions.IsAuthenticated]
    queryset = Marca.objects.filter(ativa=True).order_by('nome')


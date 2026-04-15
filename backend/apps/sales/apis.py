"""Sales REST APIs — T061-T068.

VendaViewSet           — CRUD for Venda: create, retrieve, list, cancel (T061)
PedidoVendaViewSet     — CRUD + checkout / finalizar actions (T061, T058-T059)
StockAvailabilityAPIView — real-time stock for checkout frontend (T062)
RastreabilidadeAPIView   — full traceability query (T068)
"""
from __future__ import annotations

import logging
from decimal import Decimal

from rest_framework import permissions, serializers, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.viewsets import ModelViewSet, ViewSet

from apps.sales.models import Cliente, ItemPedidoVenda, PedidoVenda, Venda

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Serializers
# ---------------------------------------------------------------------------

class ClienteSerializer(serializers.ModelSerializer):
    nome_completo = serializers.SerializerMethodField()

    def get_nome_completo(self, obj):
        return obj.nome_completo

    class Meta:
        model = Cliente
        fields = [
            'id', 'codigo_cliente', 'tipo_cliente', 'nome', 'razao_social',
            'nome_fantasia', 'cnpj', 'cpf', 'nome_completo', 'email',
            'telefone_principal', 'celular', 'ativo', 'created_at',
        ]
        read_only_fields = ['id', 'codigo_cliente', 'nome_completo', 'created_at']

    # telefone_secundario maps to celular on the frontend side
    celular = serializers.CharField(
        source='telefone_secundario', allow_null=True, allow_blank=True, required=False
    )

    def validate(self, attrs):
        tipo = attrs.get('tipo_cliente', getattr(self.instance, 'tipo_cliente', None))
        if tipo == 'PJ' and not attrs.get('cnpj'):
            raise serializers.ValidationError({'cnpj': 'CNPJ obrigatório para Pessoa Jurídica.'})
        if tipo == 'PF' and not attrs.get('cpf'):
            raise serializers.ValidationError({'cpf': 'CPF obrigatório para Pessoa Física.'})
        return attrs

    def create(self, validated_data):
        import uuid
        validated_data['codigo_cliente'] = f'CLI{uuid.uuid4().hex[:8].upper()}'
        return super().create(validated_data)


class ClienteViewSet(ModelViewSet):
    serializer_class = ClienteSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        qs = Cliente.objects.order_by('nome')
        if search := self.request.query_params.get('search'):
            from django.db.models import Q
            qs = qs.filter(
                Q(nome__icontains=search) |
                Q(razao_social__icontains=search) |
                Q(cpf__icontains=search) |
                Q(cnpj__icontains=search) |
                Q(codigo_cliente__icontains=search)
            )
        if tipo := self.request.query_params.get('tipo_cliente'):
            qs = qs.filter(tipo_cliente=tipo)
        ativo = self.request.query_params.get('ativo')
        if ativo is not None:
            qs = qs.filter(ativo=(ativo.lower() in ('true', '1', 'yes')))
        return qs

    @action(detail=True, methods=['post'])
    def toggle_ativo(self, request, pk=None):
        cliente = self.get_object()
        cliente.ativo = not cliente.ativo
        cliente.save(update_fields=['ativo'])
        return Response(self.get_serializer(cliente).data)


class ItemPedidoVendaSerializer(serializers.ModelSerializer):
    class Meta:
        model = ItemPedidoVenda
        fields = [
            'id', 'produto_variacao', 'quantidade', 'preco_unitario', 'preco_total',
            'unidade_venda', 'quantidade_base', 'fator_conversao_aplicado',
            'desconto_valor', 'desconto_percentual', 'observacoes', 'sequencia',
        ]
        read_only_fields = ['id', 'quantidade_base', 'fator_conversao_aplicado', 'preco_total']


class PedidoVendaSerializer(serializers.ModelSerializer):
    itens = ItemPedidoVendaSerializer(many=True, read_only=True)
    cliente_nome = serializers.CharField(source='cliente.nome_completo', read_only=True)

    class Meta:
        model = PedidoVenda
        fields = [
            'id', 'numero_pedido', 'loja', 'cliente', 'cliente_nome', 'vendedor',
            'situacao', 'data_pedido', 'data_aprovacao', 'data_entrega_prevista',
            'valor_subtotal', 'valor_desconto', 'valor_total',
            'forma_pagamento', 'parcelas', 'tipo_entrega',
            'itens', 'observacoes',
        ]
        read_only_fields = ['id', 'numero_pedido', 'data_pedido', 'cliente_nome']


class VendaSerializer(serializers.ModelSerializer):
    cliente_nome = serializers.CharField(source='cliente.nome_completo', read_only=True)
    nfe_situacao_display = serializers.CharField(source='get_nfe_situacao_display', read_only=True)

    class Meta:
        model = Venda
        fields = [
            'id', 'numero_venda', 'loja', 'cliente', 'cliente_nome',
            'data_venda', 'valor_total', 'valor_desconto', 'valor_liquido',
            'nfe_situacao', 'nfe_situacao_display', 'nfe_tipo_emissao',
            'nfe_tentativas', 'nfe_ultima_tentativa', 'nfe_erro',
            'nfe_requer_retry_manual', 'nfe_protocolo', 'nfe_chave_acesso',
            'cancelada', 'motivo_cancelamento', 'data_cancelamento',
        ]
        read_only_fields = [
            'id', 'numero_venda', 'data_venda', 'cliente_nome',
            'nfe_situacao_display', 'nfe_tentativas', 'nfe_ultima_tentativa',
            'nfe_protocolo', 'nfe_chave_acesso',
        ]


# ---------------------------------------------------------------------------
# T061 — PedidoVendaViewSet: checkout + finalize actions
# ---------------------------------------------------------------------------

class PedidoVendaViewSet(ModelViewSet):
    serializer_class = PedidoVendaSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return (
            PedidoVenda.objects
            .select_related('loja', 'cliente', 'vendedor')
            .prefetch_related('itens')
            .order_by('-created_at')
        )

    # T058 — initiate checkout with stock reservation
    @action(detail=True, methods=['post'], url_path='iniciar-checkout')
    def iniciar_checkout(self, request, pk=None):
        pedido = self.get_object()
        sessao = request.data.get('sessao_checkout', '')
        if not sessao:
            import uuid
            sessao = f'checkout_{uuid.uuid4().hex}'

        from apps.sales.services import VendaService, CheckoutInsuficienteError

        try:
            resultado = VendaService.iniciar_checkout(
                pedido_id=str(pedido.pk),
                sessao_checkout=sessao,
                usuario=request.user,
                override_estoque=False,
            )
        except CheckoutInsuficienteError as exc:
            return Response(
                {'erro': 'Estoque insuficiente', 'faltas': exc.faltas},
                status=status.HTTP_422_UNPROCESSABLE_ENTITY,
            )

        return Response({
            'sessao_checkout': resultado['sessao_checkout'],
            'reservas_criadas': len(resultado['reservas']),
            'avisos': resultado['avisos'],
        })

    # T064 — manager override for insufficient stock
    @action(detail=True, methods=['post'], url_path='iniciar-checkout-override')
    def iniciar_checkout_override(self, request, pk=None):
        if not request.user.has_perm('inventory.override_estoque_insuficiente'):
            return Response({'erro': 'Permissão negada'}, status=status.HTTP_403_FORBIDDEN)

        pedido = self.get_object()
        sessao = request.data.get('sessao_checkout', f'checkout_{pedido.pk}')

        from apps.sales.services import VendaService

        resultado = VendaService.checkout_com_override(
            pedido_id=str(pedido.pk),
            sessao_checkout=sessao,
            usuario=request.user,
        )
        return Response({
            'sessao_checkout': resultado['sessao_checkout'],
            'reservas_criadas': len(resultado['reservas']),
            'avisos_override': resultado['avisos'],
        })

    # T059 — finalise sale: commit stock + trigger NF-e
    @action(detail=True, methods=['post'], url_path='finalizar')
    def finalizar(self, request, pk=None):
        pedido = self.get_object()
        sessao   = request.data.get('sessao_checkout', '')
        num_venda = request.data.get('numero_venda', '')

        if not sessao:
            return Response({'erro': 'sessao_checkout obrigatória'}, status=status.HTTP_400_BAD_REQUEST)
        if not num_venda:
            import uuid
            num_venda = f'VND-{uuid.uuid4().hex[:8].upper()}'

        from apps.sales.services import VendaService

        try:
            venda = VendaService.finalizar_venda(
                pedido_id=str(pedido.pk),
                sessao_checkout=sessao,
                usuario=request.user,
                numero_venda=num_venda,
            )
        except Exception as exc:
            logger.error("Erro ao finalizar venda pedido=%s: %s", pedido.pk, exc)
            return Response({'erro': str(exc)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        return Response(VendaSerializer(venda).data, status=status.HTTP_201_CREATED)


# ---------------------------------------------------------------------------
# T061 — VendaViewSet: list, retrieve, cancel
# ---------------------------------------------------------------------------

class VendaViewSet(ModelViewSet):
    serializer_class = VendaSerializer
    permission_classes = [permissions.IsAuthenticated]
    http_method_names = ['get', 'patch', 'delete', 'head', 'options']  # no POST/PUT: created via PedidoVenda

    def get_queryset(self):
        qs = Venda.objects.select_related('loja', 'cliente', 'vendedor').order_by('-created_at')
        # Filters
        if nfe_sit := self.request.query_params.get('nfe_situacao'):
            qs = qs.filter(nfe_situacao=nfe_sit)
        if cancelada := self.request.query_params.get('cancelada'):
            qs = qs.filter(cancelada=cancelada.lower() in ('true', '1'))
        if cliente_id := self.request.query_params.get('cliente'):
            qs = qs.filter(cliente_id=cliente_id)
        return qs

    # T060 — cancel a sale
    @action(detail=True, methods=['post'], url_path='cancelar')
    def cancelar(self, request, pk=None):
        venda = self.get_object()
        motivo = request.data.get('motivo', '').strip()
        if len(motivo) < 10:
            return Response(
                {'erro': 'motivo deve ter no mínimo 10 caracteres'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        from apps.sales.services import VendaService

        try:
            venda = VendaService.cancelar_venda(
                venda_id=str(venda.pk),
                motivo=motivo,
                usuario=request.user,
            )
        except ValueError as exc:
            return Response({'erro': str(exc)}, status=status.HTTP_422_UNPROCESSABLE_ENTITY)

        return Response(VendaSerializer(venda).data)


# ---------------------------------------------------------------------------
# T062 — StockAvailabilityAPIView: real-time stock check for checkout frontend
# ---------------------------------------------------------------------------

class StockAvailabilityAPIView(APIView):
    """GET stock availability for one or multiple products in a loja.

    GET /api/sales/estoque-disponivel/
        ?produto_variacao=<pk>
        &loja=<pk>
        &quantidade=<decimal>  (optional)
        &unidade=<pk>          (optional)
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        produto_id = request.query_params.get('produto_variacao')
        loja_id    = request.query_params.get('loja')
        quantidade = request.query_params.get('quantidade')
        unidade_id = request.query_params.get('unidade')

        if not produto_id or not loja_id:
            return Response(
                {'erro': 'produto_variacao e loja são obrigatórios'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        from apps.inventory.services import ConversaoService, EstoqueService

        try:
            disponivel = EstoqueService.calcular_disponibilidade(produto_id, int(loja_id))
        except Exception as exc:
            return Response({'erro': str(exc)}, status=status.HTTP_400_BAD_REQUEST)

        result: dict = {
            'produto_variacao': produto_id,
            'loja': loja_id,
            'quantidade_disponivel': str(disponivel),
            'disponivel': disponivel > Decimal('0'),
        }

        if quantidade and unidade_id:
            try:
                qtd = Decimal(quantidade)
                qtd_base = ConversaoService.converter_quantidade(produto_id, qtd, int(unidade_id))
                result['quantidade_solicitada_base'] = str(qtd_base)
                result['disponivel_para_quantidade'] = disponivel >= qtd_base
            except Exception as exc:
                result['aviso_conversao'] = str(exc)

        return Response(result)


# ---------------------------------------------------------------------------
# T063 — NFeStatusAPIView: NFe status for a sale (used in the checkout UI)
# ---------------------------------------------------------------------------

class NFeStatusAPIView(APIView):
    """GET NF-e status for a specific Venda.

    GET /api/sales/<venda_id>/nfe-status/
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, venda_id):
        try:
            venda = Venda.objects.get(pk=venda_id)
        except Venda.DoesNotExist:
            return Response({'erro': 'Venda não encontrada'}, status=status.HTTP_404_NOT_FOUND)

        return Response({
            'venda_id': str(venda.pk),
            'numero_venda': venda.numero_venda,
            'nfe_situacao': venda.nfe_situacao,
            'nfe_situacao_display': venda.get_nfe_situacao_display(),
            'nfe_tipo_emissao': venda.nfe_tipo_emissao,
            'nfe_tentativas': venda.nfe_tentativas,
            'nfe_ultima_tentativa': venda.nfe_ultima_tentativa,
            'nfe_protocolo': venda.nfe_protocolo,
            'nfe_chave_acesso': venda.nfe_chave_acesso,
            'nfe_erro': venda.nfe_erro,
            'nfe_requer_retry_manual': venda.nfe_requer_retry_manual,
        })


# ---------------------------------------------------------------------------
# T065 — B2B vs B2C NFe differentiation (info endpoint)
# ---------------------------------------------------------------------------

class NFeElegibilidadeAPIView(APIView):
    """Check if a sale qualifies for automatic B2B NF-e emission.

    GET /api/sales/<venda_id>/nfe-elegibilidade/
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, venda_id):
        try:
            venda = Venda.objects.select_related('cliente').get(pk=venda_id)
        except Venda.DoesNotExist:
            return Response({'erro': 'Venda não encontrada'}, status=status.HTTP_404_NOT_FOUND)

        from apps.fiscal.services import NFEService

        deve_emitir = NFEService.deve_emitir_nfe_automatica(venda)
        tipo = 'AUTOMATICA_B2B' if deve_emitir else (
            'MANUAL_B2C' if venda.cliente.tipo_cliente == 'PF' else 'AVALIAR_MANUALMENTE'
        )
        return Response({
            'venda_id': str(venda.pk),
            'cliente_tipo': venda.cliente.tipo_cliente,
            'cliente_cnpj': bool(venda.cliente.cnpj),
            'deve_emitir_automaticamente': deve_emitir,
            'tipo_emissao_recomendado': tipo,
        })


# ---------------------------------------------------------------------------
# T067 — Multi-unit price calculation for sales items
# ---------------------------------------------------------------------------

class MultiUnitPriceAPIView(APIView):
    """Calculate unit price in any available unit for a product.

    GET /api/sales/preco-multiunit/
        ?produto_variacao=<pk>
        &preco_base=<decimal>  (price in base unit)
        &unidade=<pk>
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        produto_id   = request.query_params.get('produto_variacao')
        preco_base_s = request.query_params.get('preco_base')
        unidade_id   = request.query_params.get('unidade')

        if not produto_id or not preco_base_s or not unidade_id:
            return Response(
                {'erro': 'produto_variacao, preco_base e unidade são obrigatórios'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        from apps.inventory.services import ConversaoService

        try:
            preco_base = Decimal(preco_base_s)
            unidade_id_int = int(unidade_id)
            qtd_1_em_base = ConversaoService.converter_quantidade(
                produto_id, Decimal('1'), unidade_id_int
            )
            preco_na_unidade = (preco_base * qtd_1_em_base).quantize(Decimal('0.01'))
        except Exception as exc:
            return Response({'erro': str(exc)}, status=status.HTTP_400_BAD_REQUEST)

        return Response({
            'produto_variacao': produto_id,
            'unidade': unidade_id_int,
            'preco_base_por_unidade_base': str(preco_base),
            'preco_por_unidade': str(preco_na_unidade),
            'fator_conversao': str(qtd_1_em_base),
        })


# ---------------------------------------------------------------------------
# T068 — RastreabilidadeAPIView: full traceability query
# ---------------------------------------------------------------------------

class RastreabilidadeAPIView(APIView):
    """Return the full movement history for a product or sale.

    GET /api/sales/rastreabilidade/
        ?produto_variacao=<pk>&loja=<pk>   — product history
        ?venda=<pk>                        — sale-specific movements
        ?lote=<pk>                         — all movements of a lot
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        from apps.inventory.models import MovimentacaoEstoque

        qs = MovimentacaoEstoque.objects.select_related(
            'produto', 'usuario', 'unidade_original', 'unidade_base'
        ).order_by('-created_at')

        if produto_id := request.query_params.get('produto_variacao'):
            qs = qs.filter(produto_id=produto_id)
        if loja_id := request.query_params.get('loja'):
            qs = qs.filter(produto__estoque_lojas__loja_id=loja_id).distinct()
        if venda_id := request.query_params.get('venda'):
            qs = qs.filter(venda_id=venda_id)
        if lote_id := request.query_params.get('lote'):
            qs = qs.filter(lote_id=lote_id)

        qs = qs[:200]

        data = [
            {
                'id': str(m.pk),
                'tipo': m.tipo_movimentacao,
                'produto': str(m.produto_id),
                'quantidade_base': str(m.quantidade_base),
                'unidade_base': m.unidade_base.sigla if m.unidade_base else '',
                'estoque_antes': str(m.estoque_antes),
                'estoque_depois': str(m.estoque_depois),
                'venda': str(m.venda_id) if m.venda_id else None,
                'nfe': str(m.nfe_id) if hasattr(m, 'nfe_id') and m.nfe_id else None,
                'usuario': str(m.usuario) if m.usuario else None,
                'data': m.created_at.isoformat() if m.created_at else None,
            }
            for m in qs
        ]

        return Response({'total': len(data), 'movimentacoes': data})

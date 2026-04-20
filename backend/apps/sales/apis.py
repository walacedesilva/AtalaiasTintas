"""Sales REST APIs — T061-T068.

VendaViewSet           — CRUD for Venda: create, retrieve, list, cancel (T061)
PedidoVendaViewSet     — CRUD + checkout / finalizar actions (T061, T058-T059)
StockAvailabilityAPIView — real-time stock for checkout frontend (T062)
RastreabilidadeAPIView   — full traceability query (T068)
"""
from __future__ import annotations

import logging
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.db import transaction
from rest_framework import permissions, serializers, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.throttling import UserRateThrottle
from rest_framework.views import APIView
from rest_framework.viewsets import ModelViewSet, ViewSet

from apps.sales.models import Cliente, ItemPedidoVenda, PagamentoVenda, PedidoVenda, Recebivel, Venda

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# T031 — Rate-limiting throttle classes
# ---------------------------------------------------------------------------

class PDVCheckoutThrottle(UserRateThrottle):
    rate = '60/min'
    scope = 'pdv_checkout'


class AprovarDescontoThrottle(UserRateThrottle):
    rate = '10/min'
    scope = 'aprovar_desconto'


def _recalcular_totais_pedido(pedido: PedidoVenda) -> None:
    """Recompute subtotal, desconto and total from current items."""
    from django.db.models import Sum
    agg = pedido.itens.aggregate(
        subtotal=Sum('preco_total'),
        desconto=Sum('desconto_valor'),
    )
    pedido.valor_subtotal = agg['subtotal'] or Decimal('0.00')
    pedido.valor_desconto = agg['desconto'] or Decimal('0.00')
    pedido.valor_total = pedido.valor_subtotal - pedido.valor_desconto
    pedido.save(update_fields=['valor_subtotal', 'valor_desconto', 'valor_total'])


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

    @action(detail=True, methods=['get'], url_path='historico')
    def historico(self, request, pk=None):
        """T026 — Paginated purchase history for a customer, no N+1."""
        cliente = self.get_object()
        qs = (
            PedidoVenda.objects
            .filter(cliente=cliente)
            .select_related('loja', 'vendedor')
            .prefetch_related('itens__produto_variacao', 'itens__unidade_venda')
            .order_by('-data_pedido')
        )
        from rest_framework.pagination import PageNumberPagination
        paginator = PageNumberPagination()
        try:
            page_size = int(request.query_params.get('page_size', 10))
        except (TypeError, ValueError):
            page_size = 10
        paginator.page_size = min(max(page_size, 1), 100)
        page = paginator.paginate_queryset(qs, request)
        return paginator.get_paginated_response(PedidoVendaSerializer(page, many=True).data)


class ItemPedidoVendaSerializer(serializers.ModelSerializer):
    nome_produto = serializers.SerializerMethodField()
    unidade_sigla = serializers.SerializerMethodField()

    def get_nome_produto(self, obj) -> str:
        try:
            base = obj.produto_variacao.produto_base.nome
            variacao = obj.produto_variacao.nome_variacao
            return f"{base} — {variacao}" if variacao else base
        except Exception:
            return ''

    def get_unidade_sigla(self, obj):
        # Prefer the item-level unit; fall back to the product's default unit
        if obj.unidade_venda_id:
            try:
                return obj.unidade_venda.sigla
            except Exception:
                pass
        try:
            return obj.produto_variacao.unidade_venda.sigla
        except Exception:
            return None

    class Meta:
        model = ItemPedidoVenda
        fields = [
            'id', 'produto_variacao', 'nome_produto', 'quantidade', 'preco_unitario', 'preco_total',
            'unidade_venda', 'unidade_sigla', 'quantidade_base', 'fator_conversao_aplicado',
            'desconto_valor', 'desconto_percentual', 'observacoes', 'sequencia',
        ]
        read_only_fields = ['id', 'quantidade_base', 'fator_conversao_aplicado', 'nome_produto', 'unidade_sigla']
        extra_kwargs = {
            'preco_total': {'required': False},
        }

    def validate(self, attrs):
        # Auto-compute preco_total if not provided
        if 'preco_total' not in attrs:
            qty = attrs.get('quantidade', Decimal('0'))
            unit_price = attrs.get('preco_unitario', Decimal('0'))
            desconto = attrs.get('desconto_valor', Decimal('0'))
            attrs['preco_total'] = qty * unit_price - desconto
        return attrs


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


class PagamentoVendaSerializer(serializers.ModelSerializer):
    class Meta:
        model = PagamentoVenda
        fields = ['id', 'forma', 'valor', 'valor_recebido', 'troco']


class VendaSerializer(serializers.ModelSerializer):
    cliente_nome = serializers.CharField(source='cliente.nome_completo', read_only=True)
    nfe_situacao_display = serializers.CharField(source='get_nfe_situacao_display', read_only=True)
    pagamentos = PagamentoVendaSerializer(many=True, read_only=True)
    pedido_origem_id = serializers.SerializerMethodField()
    pedido_origem_numero = serializers.SerializerMethodField()
    pedido_itens = serializers.SerializerMethodField()

    def get_pedido_origem_id(self, obj):
        return str(obj.pedido_origem.id) if obj.pedido_origem_id else None

    def get_pedido_origem_numero(self, obj):
        return obj.pedido_origem.numero_pedido if obj.pedido_origem_id else None

    def get_pedido_itens(self, obj):
        if not obj.pedido_origem_id:
            return []
        itens = obj.pedido_origem.itens.all()
        return ItemPedidoVendaSerializer(itens, many=True).data

    class Meta:
        model = Venda
        fields = [
            'id', 'numero_venda', 'loja', 'cliente', 'cliente_nome',
            'data_venda', 'valor_total', 'valor_desconto', 'valor_liquido',
            'nfe_situacao', 'nfe_situacao_display', 'nfe_tipo_emissao',
            'nfe_tentativas', 'nfe_ultima_tentativa', 'nfe_erro',
            'nfe_requer_retry_manual', 'nfe_protocolo', 'nfe_chave_acesso',
            'cancelada', 'motivo_cancelamento', 'data_cancelamento',
            'pagamentos', 'pedido_origem_id', 'pedido_origem_numero', 'pedido_itens',
        ]
        read_only_fields = [
            'id', 'numero_venda', 'data_venda', 'cliente_nome',
            'nfe_situacao_display', 'nfe_tentativas', 'nfe_ultima_tentativa',
            'nfe_protocolo', 'nfe_chave_acesso', 'pagamentos',
            'pedido_origem_id', 'pedido_origem_numero', 'pedido_itens',
        ]


# ---------------------------------------------------------------------------
# T061 — PedidoVendaViewSet: checkout + finalize actions
# ---------------------------------------------------------------------------

class PedidoVendaViewSet(ModelViewSet):
    serializer_class = PedidoVendaSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        qs = (
            PedidoVenda.objects
            .select_related('loja', 'cliente', 'vendedor')
            .prefetch_related(
                'itens__produto_variacao__produto_base',
                'itens__produto_variacao__unidade_venda',
                'itens__unidade_venda',
            )
            .order_by('-created_at')
        )
        if situacao := self.request.query_params.get('situacao'):
            qs = qs.filter(situacao=situacao)
        if search := self.request.query_params.get('search'):
            from django.db.models import Q
            qs = qs.filter(
                Q(numero_pedido__icontains=search) |
                Q(cliente__nome__icontains=search) |
                Q(cliente__razao_social__icontains=search)
            )
        return qs

    def create(self, request, *args, **kwargs):
        """Create a PedidoVenda; auto-sets vendedor and generates numero_pedido."""
        data = request.data.copy()
        data.setdefault('vendedor', request.user.pk)
        data.setdefault('situacao', 'ORCAMENTO')
        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    def perform_create(self, serializer):
        import uuid as _uuid
        serializer.save(numero_pedido=f'PED-{_uuid.uuid4().hex[:8].upper()}')

    @action(detail=True, methods=['post'], url_path='add-item')
    def add_item(self, request, pk=None):
        """Add an item to a PedidoVenda (must be in ORCAMENTO or APROVADO)."""
        pedido = self.get_object()
        if pedido.situacao not in ('ORCAMENTO', 'APROVADO'):
            return Response(
                {'erro': f'Pedido na situação {pedido.situacao} não aceita novos itens'},
                status=status.HTTP_422_UNPROCESSABLE_ENTITY,
            )
        ser = ItemPedidoVendaSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        next_seq = pedido.itens.count() + 1
        # Auto-set unidade_venda from the product's default unit if not provided
        save_kwargs: dict = {'pedido': pedido, 'sequencia': next_seq}
        pv = ser.validated_data.get('produto_variacao')
        if pv and not ser.validated_data.get('unidade_venda') and pv.unidade_venda_id:
            save_kwargs['unidade_venda_id'] = pv.unidade_venda_id
        item = ser.save(**save_kwargs)

        # Recalculate totals
        _recalcular_totais_pedido(pedido)
        pedido.refresh_from_db()
        return Response(ItemPedidoVendaSerializer(item).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['delete'], url_path=r'remove-item/(?P<item_pk>[0-9]+)')
    def remove_item(self, request, pk=None, item_pk=None):
        """Remove an item from a PedidoVenda."""
        pedido = self.get_object()
        if pedido.situacao not in ('ORCAMENTO', 'APROVADO'):
            return Response(
                {'erro': 'Pedido não pode ser alterado na situação atual'},
                status=status.HTTP_422_UNPROCESSABLE_ENTITY,
            )
        try:
            item = pedido.itens.get(pk=item_pk)
        except ItemPedidoVenda.DoesNotExist:
            return Response({'erro': 'Item não encontrado'}, status=status.HTTP_404_NOT_FOUND)
        item.delete()
        _recalcular_totais_pedido(pedido)
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=['post'], url_path='aprovar')
    def aprovar(self, request, pk=None):
        """T021 — ORCAMENTO → APROVADO with optional stock reservation."""
        pedido = self.get_object()
        if pedido.situacao != 'ORCAMENTO':
            return Response(
                {'erro': f'Apenas pedidos em ORCAMENTO podem ser aprovados (atual: {pedido.situacao})'},
                status=status.HTTP_422_UNPROCESSABLE_ENTITY,
            )
        from django.utils import timezone as tz

        update_fields = ['situacao', 'data_aprovacao', 'updated_at']
        pedido.situacao = 'APROVADO'
        pedido.data_aprovacao = tz.now()
        data_entrega = request.data.get('data_entrega_prevista')
        if data_entrega:
            pedido.data_entrega_prevista = data_entrega
            update_fields.append('data_entrega_prevista')
        pedido.save(update_fields=update_fields)

        # Create stock reservations for all items
        from apps.inventory.services import ConversaoService, EstoqueService

        sessao = f'pedido_{pedido.pk}'
        reservas_criadas = 0
        avisos_estoque = []
        for item in pedido.itens.select_related('produto_variacao', 'unidade_venda').all():
            unidade_id = (
                item.unidade_venda_id
                if item.unidade_venda_id
                else ConversaoService.obter_unidade_base(str(item.produto_variacao_id)).id
            )
            try:
                EstoqueService.criar_reserva(
                    produto_variacao_id=str(item.produto_variacao_id),
                    loja_id=pedido.loja_id,
                    quantidade=item.quantidade,
                    unidade_id=unidade_id,
                    sessao_checkout=sessao,
                    usuario=request.user,
                )
                reservas_criadas += 1
            except Exception as exc:
                avisos_estoque.append({'item': str(item.pk), 'aviso': str(exc)})

        resp = self.get_serializer(pedido).data
        resp['reservas_criadas'] = reservas_criadas
        if avisos_estoque:
            resp['avisos_estoque'] = avisos_estoque
        return Response(resp)

    @action(detail=True, methods=['post'], url_path='aprovar-desconto',
            throttle_classes=[AprovarDescontoThrottle])
    def aprovar_desconto(self, request, pk=None):
        """T022 — Apply a discount to a pedido or item via PIN approval."""
        pedido = self.get_object()
        data = request.data
        percentual_str = data.get('percentual')
        if not percentual_str:
            return Response({'erro': 'percentual é obrigatório'}, status=status.HTTP_400_BAD_REQUEST)

        motivo = data.get('motivo', '')
        pin = data.get('pin', '')
        aprovador_id = data.get('aprovador_id', request.user.pk)
        tipo = data.get('tipo', 'TOTAL')
        item_id = data.get('item_id')

        User = get_user_model()
        try:
            aprovador = User.objects.get(pk=aprovador_id)
        except User.DoesNotExist:
            return Response({'erro': 'aprovador_id inválido'}, status=status.HTTP_400_BAD_REQUEST)

        from apps.sales.services import (
            DescontoService,
            DescontoCooldownError,
            DescontoInsuficientePermissaoError,
            DescontoPINError,
        )

        try:
            percentual = Decimal(str(percentual_str))
            if tipo == 'ITEM' and item_id:
                item = ItemPedidoVenda.objects.get(pk=item_id, pedido=pedido)
                DescontoService.aplicar_desconto_item(
                    item, percentual, request.user, aprovador, pin=pin
                )
                pedido.refresh_from_db()
            else:
                DescontoService.aprovar_com_pin(
                    pedido, percentual, motivo, pin, aprovador
                )
        except DescontoInsuficientePermissaoError as exc:
            return Response({'erro': str(exc)}, status=status.HTTP_403_FORBIDDEN)
        except DescontoPINError as exc:
            return Response(
                {'erro': 'PIN incorreto', 'tentativas': exc.tentativas,
                 'max_tentativas': exc.max_tentativas},
                status=status.HTTP_403_FORBIDDEN,
            )
        except DescontoCooldownError as exc:
            return Response({'erro': str(exc)}, status=status.HTTP_429_TOO_MANY_REQUESTS)
        except (ItemPedidoVenda.DoesNotExist, ValueError) as exc:
            return Response({'erro': str(exc)}, status=status.HTTP_400_BAD_REQUEST)

        pedido.refresh_from_db()
        return Response(self.get_serializer(pedido).data)

    @action(detail=True, methods=['post'], url_path='finalizar-entrega')
    def finalizar_entrega(self, request, pk=None):
        """T023 — PRONTO → ENTREGUE: commit stock and create Venda."""
        pedido = self.get_object()
        if pedido.situacao != 'PRONTO':
            return Response(
                {'erro': f'Apenas pedidos em PRONTO podem ser finalizados (atual: {pedido.situacao})'},
                status=status.HTTP_422_UNPROCESSABLE_ENTITY,
            )
        import uuid as _uuid
        from apps.sales.services import VendaService

        num_venda = request.data.get('numero_venda') or f'VND-{_uuid.uuid4().hex[:8].upper()}'
        sessao = f'pedido_{pedido.pk}'

        try:
            venda = VendaService.finalizar_venda(
                pedido_id=str(pedido.pk),
                sessao_checkout=sessao,
                usuario=request.user,
                numero_venda=num_venda,
            )
        except Exception as exc:
            logger.error("Erro em finalizar_entrega pedido=%s: %s", pedido.pk, exc)
            return Response({'erro': str(exc)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        pedido.refresh_from_db()
        return Response({
            'pedido': self.get_serializer(pedido).data,
            'venda_id': str(venda.pk),
            'numero_venda': venda.numero_venda if hasattr(venda, 'numero_venda') else num_venda,
        })

    @action(detail=True, methods=['post'], url_path='cancelar')
    def cancelar(self, request, pk=None):
        """T024 — Cancel a PedidoVenda and release stock reservations."""
        pedido = self.get_object()
        motivo = request.data.get('motivo', '').strip()
        if len(motivo) < 10:
            return Response(
                {'erro': 'motivo deve ter no mínimo 10 caracteres'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if pedido.situacao == 'CANCELADO':
            return Response({'erro': 'Pedido já está cancelado'}, status=status.HTTP_400_BAD_REQUEST)
        if pedido.situacao == 'ENTREGUE':
            return Response(
                {'erro': 'Pedido entregue deve ser cancelado via cancelamento de Venda'},
                status=status.HTTP_422_UNPROCESSABLE_ENTITY,
            )
        from apps.inventory.services import EstoqueService

        sessao = f'pedido_{pedido.pk}'
        try:
            EstoqueService.cancelar_reservas(sessao)
        except Exception as exc:
            logger.warning("Erro ao cancelar reservas do pedido %s: %s", pedido.pk, exc)

        pedido.situacao = 'CANCELADO'
        pedido.save(update_fields=['situacao', 'updated_at'])
        return Response(self.get_serializer(pedido).data)

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
    http_method_names = ['get', 'post', 'patch', 'delete', 'head', 'options']

    def get_queryset(self):
        qs = (
            Venda.objects
            .select_related('loja', 'cliente', 'vendedor', 'pedido_origem')
            .prefetch_related(
                'pagamentos',
                'pedido_origem__itens__produto_variacao__produto_base',
                'pedido_origem__itens__produto_variacao__unidade_venda',
                'pedido_origem__itens__unidade_venda',
            )
            .order_by('-created_at')
        )
        # Filters
        if nfe_sit := self.request.query_params.get('nfe_situacao'):
            qs = qs.filter(nfe_situacao=nfe_sit)
        if cancelada := self.request.query_params.get('cancelada'):
            qs = qs.filter(cancelada=cancelada.lower() in ('true', '1'))
        if cliente_id := self.request.query_params.get('cliente'):
            qs = qs.filter(cliente_id=cliente_id)
        return qs

    # T060 / T025a — cancel a sale (D+0 only, PIN required)
    @action(detail=True, methods=['post'], url_path='cancelar')
    def cancelar(self, request, pk=None):
        """T025a — Cancel a Venda (same day only) with PIN verification."""
        venda = self.get_object()

        # Idempotency: already cancelled → 400
        if venda.cancelada:
            return Response(
                {'erro': 'Venda já está cancelada'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        motivo = request.data.get('motivo', '').strip()
        if len(motivo) < 10:
            return Response(
                {'erro': 'motivo deve ter no mínimo 10 caracteres'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # D+0 check: cancellation only allowed on the sale date
        from django.utils import timezone as tz
        if venda.data_venda.date() != tz.now().date():
            return Response(
                {'erro': 'Cancelamento permitido apenas no dia da venda (D+0). Use devolução para vendas anteriores.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # PIN verification
        pin = request.data.get('pin', '')
        if not pin:
            return Response({'erro': 'PIN obrigatório para cancelamento'}, status=status.HTTP_400_BAD_REQUEST)
        if not request.user.check_password(pin):
            return Response({'erro': 'PIN incorreto'}, status=status.HTTP_403_FORBIDDEN)

        from apps.sales.services import VendaService, RecebivelService

        nfe_situacao_antes = venda.nfe_situacao

        try:
            with transaction.atomic():
                venda = VendaService.cancelar_venda(
                    venda_id=str(venda.pk),
                    motivo=motivo,
                    usuario=request.user,
                )
                # Cancel any open crediário receivables
                for rec in Recebivel.objects.filter(
                    venda_id=venda.pk, situacao__in=('ABERTO', 'PARCIAL', 'VENCIDO')
                ):
                    RecebivelService.cancelar(rec, motivo, request.user)

        except ValueError as exc:
            return Response({'erro': str(exc)}, status=status.HTTP_422_UNPROCESSABLE_ENTITY)

        logger.info(
            "Venda %s cancelada por %s — motivo: %s — nfe_antes: %s",
            venda.pk, request.user, motivo, nfe_situacao_antes,
        )
        return Response({'status': 'cancelada', 'venda_id': str(venda.pk)})

    @action(detail=True, methods=['post'], url_path='devolver')
    def devolver(self, request, pk=None):
        """T025 — Return items from a sale: restore stock, mark tem_devolucao."""
        venda = self.get_object()
        motivo = request.data.get('motivo', '').strip()
        itens_data = request.data.get('itens', [])

        from apps.inventory.services import ConversaoService, EstoqueService

        movimentacoes = []
        with transaction.atomic():
            pedido = getattr(venda, 'pedido_origem', None)
            if not itens_data and pedido:
                # Return all items from the originating order
                for item in pedido.itens.select_related('produto_variacao', 'unidade_venda').all():
                    unidade_id = (
                        item.unidade_venda_id
                        if item.unidade_venda_id
                        else ConversaoService.obter_unidade_base(str(item.produto_variacao_id)).id
                    )
                    mov, _ = EstoqueService.processar_entrada(
                        produto_variacao_id=str(item.produto_variacao_id),
                        loja_id=venda.loja_id,
                        quantidade=item.quantidade,
                        unidade_id=unidade_id,
                        usuario=request.user,
                        tipo_movimentacao='DEVOLUCAO_VENDA',
                        documento_referencia=str(venda.pk),
                    )
                    movimentacoes.append({'item': str(item.pk), 'movimentacao': str(mov.pk)})
            else:
                for item_data in itens_data:
                    try:
                        item = ItemPedidoVenda.objects.get(pk=item_data['item_id'], pedido=pedido)
                    except ItemPedidoVenda.DoesNotExist:
                        return Response(
                            {'erro': f"Item {item_data['item_id']} não encontrado"},
                            status=status.HTTP_400_BAD_REQUEST,
                        )
                    unidade_id = (
                        item.unidade_venda_id
                        if item.unidade_venda_id
                        else ConversaoService.obter_unidade_base(str(item.produto_variacao_id)).id
                    )
                    qtd = Decimal(str(item_data.get('quantidade', item.quantidade)))
                    mov, _ = EstoqueService.processar_entrada(
                        produto_variacao_id=str(item.produto_variacao_id),
                        loja_id=venda.loja_id,
                        quantidade=qtd,
                        unidade_id=unidade_id,
                        usuario=request.user,
                        tipo_movimentacao='DEVOLUCAO_VENDA',
                        documento_referencia=str(venda.pk),
                    )
                    movimentacoes.append({'item': str(item.pk), 'movimentacao': str(mov.pk)})

            venda.tem_devolucao = True
            venda.save(update_fields=['tem_devolucao', 'updated_at'])

        return Response({
            'status': 'devolvida',
            'venda_id': str(venda.pk),
            'movimentacoes_entrada': movimentacoes,
        })


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


# ---------------------------------------------------------------------------
# T027-T029 — RecebivelViewSet: CRUD + baixar + cancelar
# ---------------------------------------------------------------------------

class RecebivelSerializer(serializers.ModelSerializer):
    cliente_nome = serializers.CharField(source='cliente.nome_completo', read_only=True)

    class Meta:
        model = Recebivel
        fields = [
            'id', 'cliente', 'cliente_nome', 'venda', 'loja',
            'valor_original', 'valor_pago', 'valor_saldo',
            'data_vencimento', 'situacao', 'observacoes',
            'criado_com_override', 'aprovador_override',
            'cancelado_por', 'data_cancelamento', 'motivo_cancelamento',
            'created_at', 'updated_at',
        ]
        read_only_fields = [
            'id', 'cliente_nome', 'valor_saldo', 'criado_com_override',
            'aprovador_override', 'cancelado_por', 'data_cancelamento',
            'motivo_cancelamento', 'created_at', 'updated_at',
        ]


class RecebivelViewSet(ModelViewSet):
    """T027 — Recebivel CRUD + baixar + cancelar actions."""

    serializer_class = RecebivelSerializer
    permission_classes = [permissions.IsAuthenticated]
    http_method_names = ['get', 'post', 'head', 'options']

    def get_queryset(self):
        from apps.companies.models import UsuarioLoja

        loja_ids = UsuarioLoja.objects.filter(
            usuario=self.request.user, ativo=True,
        ).values_list('loja_id', flat=True)

        qs = (
            Recebivel.objects
            .filter(loja__in=loja_ids)
            .select_related('cliente', 'venda', 'loja')
            .order_by('data_vencimento')
        )

        # Filters
        if cliente_id := self.request.query_params.get('cliente'):
            qs = qs.filter(cliente_id=cliente_id)
        if situacao := self.request.query_params.get('situacao'):
            qs = qs.filter(situacao=situacao)
        if loja_id := self.request.query_params.get('loja'):
            qs = qs.filter(loja_id=loja_id)
        if venc_lte := self.request.query_params.get('data_vencimento__lte'):
            qs = qs.filter(data_vencimento__lte=venc_lte)
        if venc_gte := self.request.query_params.get('data_vencimento__gte'):
            qs = qs.filter(data_vencimento__gte=venc_gte)
        return qs

    @action(detail=True, methods=['post'], url_path='baixar')
    def baixar(self, request, pk=None):
        """T028 — Register a payment on a Recebivel."""
        recebivel = self.get_object()
        valor_pago = request.data.get('valor_pago')
        if not valor_pago:
            return Response({'erro': 'valor_pago é obrigatório'}, status=status.HTTP_400_BAD_REQUEST)

        from apps.sales.services import RecebivelService

        try:
            recebivel = RecebivelService.baixar(recebivel, Decimal(str(valor_pago)), request.user)
        except ValueError as exc:
            return Response({'erro': str(exc)}, status=status.HTTP_400_BAD_REQUEST)

        return Response(RecebivelSerializer(recebivel).data)

    @action(detail=True, methods=['post'], url_path='cancelar')
    def cancelar(self, request, pk=None):
        """T029 — Cancel a Recebivel."""
        recebivel = self.get_object()
        motivo = request.data.get('motivo', '').strip()
        if len(motivo) < 5:
            return Response(
                {'erro': 'motivo deve ter no mínimo 5 caracteres'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        from apps.sales.services import RecebivelService

        try:
            recebivel = RecebivelService.cancelar(recebivel, motivo, request.user)
        except ValueError as exc:
            return Response({'erro': str(exc)}, status=status.HTTP_400_BAD_REQUEST)

        return Response(RecebivelSerializer(recebivel).data)


# ---------------------------------------------------------------------------
# T030-T031 — PDVCheckoutAPIView: atomic PDV checkout with rate limiting
# ---------------------------------------------------------------------------

class PDVCheckoutAPIView(APIView):
    """T030 — Atomic PDV checkout: validate stock → create order → deduct stock → create sale.

    POST /sales/pdv/checkout/
    Body: {
        loja_id, cliente_id?, itens[], pagamentos[],
        desconto_total?, observacoes?,
        override_credito?: { pin, aprovador_id }
    }
    """
    permission_classes = [permissions.IsAuthenticated]
    throttle_classes = [PDVCheckoutThrottle]

    def post(self, request):
        from apps.companies.models import UsuarioLoja
        from apps.inventory.services import ConversaoService, EstoqueService
        from apps.sales.services import (
            CreditoInsuficienteError,
            CreditoService,
            RecebivelService,
        )
        import uuid as _uuid
        import datetime

        data = request.data
        loja_id = data.get('loja_id')
        if not loja_id:
            return Response({'erro': 'loja_id é obrigatório'}, status=status.HTTP_400_BAD_REQUEST)

        # SEC-3: validate loja belongs to user
        if not UsuarioLoja.objects.filter(
            usuario=request.user, loja_id=loja_id, ativo=True
        ).exists():
            return Response({'erro': 'Loja não autorizada'}, status=status.HTTP_403_FORBIDDEN)

        itens_data = data.get('itens', [])
        pagamentos_data = data.get('pagamentos', [])
        cliente_id = data.get('cliente_id')
        desconto_total = Decimal(str(data.get('desconto_total', '0')))
        observacoes = data.get('observacoes', '')

        if not itens_data:
            return Response({'erro': 'itens não pode ser vazio'}, status=status.HTTP_400_BAD_REQUEST)
        if not pagamentos_data:
            return Response({'erro': 'pagamentos não pode ser vazio'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            with transaction.atomic():
                from apps.sales.models import PagamentoVenda as PagVenda

                # 1. Validate stock for all items (raise before any writes)
                for item_d in itens_data:
                    prod_id = str(item_d['produto_variacao_id'])
                    unid_id = int(item_d.get('unidade_id', 0))
                    qtd = Decimal(str(item_d['quantidade']))
                    try:
                        unid_id = unid_id or ConversaoService.obter_unidade_base(prod_id).id
                        disponivel = EstoqueService.calcular_disponibilidade(prod_id, int(loja_id))
                        qtd_base = ConversaoService.converter_quantidade(prod_id, qtd, unid_id)
                        if qtd_base > disponivel:
                            return Response(
                                {'erro': f"Estoque insuficiente para produto {prod_id}. "
                                         f"Disponível: {disponivel}, Solicitado: {qtd_base}"},
                                status=status.HTTP_400_BAD_REQUEST,
                            )
                    except Exception as exc:
                        return Response({'erro': str(exc)}, status=status.HTTP_400_BAD_REQUEST)

                # 2. Create PedidoVenda in ENTREGUE state
                num_pedido = f'PDV-{_uuid.uuid4().hex[:8].upper()}'
                pedido = PedidoVenda.objects.create(
                    loja_id=loja_id,
                    cliente_id=cliente_id,
                    vendedor=request.user,
                    numero_pedido=num_pedido,
                    situacao='ENTREGUE',
                    data_aprovacao=None,
                    valor_subtotal=Decimal('0'),
                    valor_desconto=desconto_total,
                    valor_total=Decimal('0'),
                    observacoes=observacoes,
                )

                # 3. Create ItemPedidoVenda for each item
                subtotal = Decimal('0')
                for seq, item_d in enumerate(itens_data, 1):
                    prod_id = str(item_d['produto_variacao_id'])
                    unid_id = int(item_d.get('unidade_id', 0)) or ConversaoService.obter_unidade_base(prod_id).id
                    qtd = Decimal(str(item_d['quantidade']))
                    preco_unit = Decimal(str(item_d['preco_unitario']))
                    desc_item = Decimal(str(item_d.get('desconto_valor', '0')))
                    preco_total = (qtd * preco_unit - desc_item).quantize(Decimal('0.01'))
                    preco_total = max(Decimal('0'), preco_total)
                    ItemPedidoVenda.objects.create(
                        pedido=pedido,
                        produto_variacao_id=prod_id,
                        quantidade=qtd,
                        unidade_venda_id=unid_id,
                        preco_unitario=preco_unit,
                        desconto_valor=desc_item,
                        preco_total=preco_total,
                        sequencia=seq,
                    )
                    subtotal += preco_total

                # Update pedido totals
                total = max(Decimal('0'), subtotal - desconto_total)
                pedido.valor_subtotal = subtotal
                pedido.valor_total = total
                pedido.save(update_fields=['valor_subtotal', 'valor_total', 'updated_at'])

                # 4. Create Venda
                num_venda = f'VND-{_uuid.uuid4().hex[:8].upper()}'
                venda = Venda.objects.create(
                    pedido_origem=pedido,
                    loja_id=loja_id,
                    cliente_id=cliente_id,
                    vendedor=request.user,
                    numero_venda=num_venda,
                    valor_total=total,
                    valor_desconto=desconto_total,
                    valor_liquido=total,
                    nfe_situacao='NAO_APLICAVEL',
                )

                # 5. Create PagamentoVenda
                troco = Decimal('0')
                recebiveis = []
                for pag_d in pagamentos_data:
                    forma = pag_d['forma']
                    valor_pag = Decimal(str(pag_d['valor']))
                    valor_recebido = Decimal(str(pag_d.get('valor_recebido', valor_pag)))
                    troco_pag = max(Decimal('0'), valor_recebido - valor_pag) if forma == 'DINHEIRO' else Decimal('0')
                    troco += troco_pag
                    PagVenda.objects.create(
                        venda=venda,
                        forma=forma,
                        valor=valor_pag,
                        valor_recebido=valor_recebido if forma == 'DINHEIRO' else None,
                        troco=troco_pag,
                        referencia_externa=pag_d.get('referencia_externa'),
                        observacoes=pag_d.get('observacoes'),
                    )

                    # 7. Crediário handling
                    if forma == 'CREDIARIO' and cliente_id:
                        from django.contrib.auth import get_user_model as _get_user
                        from apps.sales.models import Cliente as ClienteModel
                        cliente_obj = ClienteModel.objects.get(pk=cliente_id)
                        override_data = data.get('override_credito')
                        try:
                            rec = CreditoService.bloquear_para_venda(cliente_obj, valor_pag, venda)
                            recebiveis.append(str(rec.pk))
                        except CreditoInsuficienteError as exc:
                            if not override_data:
                                raise  # will be caught by outer try/except
                            # Override with PIN
                            _User = _get_user()
                            aprovador = _User.objects.get(pk=override_data['aprovador_id'])
                            rec = CreditoService.override_com_pin(
                                cliente_obj, valor_pag, venda,
                                pin=override_data['pin'],
                                aprovador=aprovador,
                            )
                            recebiveis.append(str(rec.pk))

                # 6. Deduct stock for each item
                for item_d in itens_data:
                    prod_id = str(item_d['produto_variacao_id'])
                    unid_id = int(item_d.get('unidade_id', 0)) or ConversaoService.obter_unidade_base(prod_id).id
                    qtd = Decimal(str(item_d['quantidade']))
                    EstoqueService.processar_baixa_venda(
                        produto_variacao_id=prod_id,
                        loja_id=int(loja_id),
                        quantidade=qtd,
                        unidade_id=unid_id,
                        venda_id=venda.pk,
                        usuario=request.user,
                    )

        except CreditoInsuficienteError as exc:
            return Response(
                {'erro': 'Limite de crédito insuficiente',
                 'disponivel': str(exc.disponivel),
                 'solicitado': str(exc.solicitado)},
                status=status.HTTP_402_PAYMENT_REQUIRED,
            )
        except Exception as exc:
            logger.error("Erro no PDV checkout loja=%s usuario=%s: %s", loja_id, request.user, exc)
            return Response({'erro': str(exc)}, status=status.HTTP_400_BAD_REQUEST)

        return Response({
            'pedido_id': str(pedido.pk),
            'venda_id': str(venda.pk),
            'numero_venda': venda.numero_venda,
            'troco': str(troco),
            'recebiveis': recebiveis,
        }, status=status.HTTP_201_CREATED)


"""Fiscal API views — T040: SefazIntegracaoAPIView, T046: NFEAutomacaoViewSet."""
from __future__ import annotations

import logging

from rest_framework import serializers, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.viewsets import ModelViewSet, ViewSet

from apps.fiscal.models import NotaFiscal, LogEventosFiscais
from apps.fiscal.services import NFEService

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Serializers
# ---------------------------------------------------------------------------

class NotaFiscalSerializer(serializers.ModelSerializer):
    class Meta:
        model = NotaFiscal
        fields = [
            'id', 'loja', 'venda', 'tipo_nota', 'serie', 'numero',
            'chave_acesso', 'situacao', 'protocolo_autorizacao',
            'data_emissao', 'data_envio', 'data_autorizacao',
            'valor_total_produtos', 'valor_total_nota', 'valor_desconto',
            'motivo_cancelamento',
        ]
        read_only_fields = [
            'id', 'chave_acesso', 'protocolo_autorizacao',
            'data_emissao', 'data_envio', 'data_autorizacao',
        ]


class LogEventosFiscaisSerializer(serializers.ModelSerializer):
    class Meta:
        model = LogEventosFiscais
        fields = [
            'id', 'nota_fiscal', 'tipo_evento', 'descricao',
            'codigo_retorno', 'mensagem_retorno', 'created_at',
        ]
        read_only_fields = ['id', 'created_at']


# ---------------------------------------------------------------------------
# T040 — SefazIntegracaoAPIView: status checks and manual operations
# ---------------------------------------------------------------------------

class SefazIntegracaoAPIView(APIView):
    """SEFAZ integration status and operations.

    GET  /api/v1/fiscal/sefaz/status/          — check SEFAZ service availability
    POST /api/v1/fiscal/sefaz/consultar/        — query status of a specific NF-e
    POST /api/v1/fiscal/sefaz/cancelar/         — cancel an authorized NF-e
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        """Return SEFAZ service availability status."""
        from apps.fiscal.sefaz.client import criar_sefaz_client
        from apps.fiscal.sefaz.exceptions import SefazCertificadoError

        try:
            client = criar_sefaz_client()
            resultado = client.verificar_status_servico()
        except SefazCertificadoError as exc:
            return Response(
                {"disponivel": False, "erro": "Certificado digital não configurado", "detalhe": str(exc)},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )
        except Exception as exc:
            logger.error("Erro ao verificar status SEFAZ: %s", exc)
            return Response(
                {"disponivel": False, "erro": str(exc)},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )

        return Response(resultado)

    def post(self, request):
        """Dispatch to consultar or cancelar based on ``acao`` body field."""
        acao = request.data.get('acao', '').lower()
        if acao == 'consultar':
            return self._consultar(request)
        if acao == 'cancelar':
            return self._cancelar(request)
        return Response(
            {"erro": "Campo 'acao' deve ser 'consultar' ou 'cancelar'"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    def _consultar(self, request):
        chave = request.data.get('chave_acesso', '').strip()
        if not chave:
            return Response({"erro": "chave_acesso obrigatória"}, status=status.HTTP_400_BAD_REQUEST)

        from apps.fiscal.sefaz.client import criar_sefaz_client
        from apps.fiscal.sefaz.exceptions import SefazError

        try:
            resultado = criar_sefaz_client().consultar_situacao(chave)
        except SefazError as exc:
            return Response({"erro": str(exc)}, status=status.HTTP_502_BAD_GATEWAY)

        return Response(resultado)

    def _cancelar(self, request):
        chave = request.data.get('chave_acesso', '').strip()
        justificativa = request.data.get('justificativa', '').strip()
        protocolo = request.data.get('numero_protocolo', '').strip()

        if not chave:
            return Response({"erro": "chave_acesso obrigatória"}, status=status.HTTP_400_BAD_REQUEST)
        if len(justificativa) < 15:
            return Response(
                {"erro": "justificativa deve ter no mínimo 15 caracteres"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        from apps.fiscal.sefaz.client import criar_sefaz_client
        from apps.fiscal.sefaz.exceptions import SefazCancelamentoError, SefazError

        try:
            resultado = criar_sefaz_client().cancelar_nfe(chave, justificativa, protocolo)
        except SefazCancelamentoError as exc:
            return Response({"erro": str(exc), "codigo": exc.codigo}, status=status.HTTP_422_UNPROCESSABLE_ENTITY)
        except SefazError as exc:
            return Response({"erro": str(exc)}, status=status.HTTP_502_BAD_GATEWAY)

        # Update NotaFiscal record if found
        nota = NotaFiscal.objects.filter(chave_acesso=chave).first()
        if nota:
            nota.situacao = 'CANCELADA'
            nota.motivo_cancelamento = justificativa
            nota.save(update_fields=['situacao', 'motivo_cancelamento', 'updated_at'])

        return Response(resultado)


# ---------------------------------------------------------------------------
# T046 — NFEAutomacaoViewSet
# ---------------------------------------------------------------------------

class NFEAutomacaoViewSet(ViewSet):
    """ViewSet for NF-e automation operations.

    POST /api/v1/fiscal/nfe-automacao/emitir/             — emit NF-e for a sale
    POST /api/v1/fiscal/nfe-automacao/reprocessar/        — reprocess failed NF-e
    POST /api/v1/fiscal/nfe-automacao/retry-manual/       — clear manual retry flag
    GET  /api/v1/fiscal/nfe-automacao/pendentes/          — list sales pending NF-e
    GET  /api/v1/fiscal/nfe-automacao/falhadas/           — list failed NF-e records
    """

    permission_classes = [IsAuthenticated]

    @action(detail=False, methods=['post'], url_path='emitir')
    def emitir(self, request):
        """Manually trigger NF-e emission for a sale."""
        venda_id = request.data.get('venda_id')
        if not venda_id:
            return Response({"erro": "venda_id obrigatório"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            NFEService.processar_nfe_venda(str(venda_id), request.user)
        except Exception as exc:
            logger.error("Erro ao emitir NF-e para venda %s: %s", venda_id, exc)
            return Response({"erro": str(exc)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        return Response({"mensagem": f"NF-e agendada para venda {venda_id}"})

    @action(detail=False, methods=['post'], url_path='reprocessar')
    def reprocessar(self, request):
        """Re-queue a failed NF-e for reprocessing."""
        venda_id = request.data.get('venda_id')
        if not venda_id:
            return Response({"erro": "venda_id obrigatório"}, status=status.HTTP_400_BAD_REQUEST)

        from apps.sales.models import Venda
        try:
            venda = Venda.objects.get(pk=venda_id)
        except Venda.DoesNotExist:
            return Response({"erro": "Venda não encontrada"}, status=status.HTTP_404_NOT_FOUND)

        if venda.nfe_situacao not in ('ERRO_TECNICO', 'REJEITADA', 'AGUARDANDO_RETRY'):
            return Response(
                {"erro": f"Venda não está em estado reprocessável (situação: {venda.nfe_situacao})"},
                status=status.HTTP_422_UNPROCESSABLE_ENTITY,
            )

        # Reset counter to allow retries
        Venda.objects.filter(pk=venda_id).update(
            nfe_situacao='PENDENTE',
            nfe_tentativas=0,
            nfe_requer_retry_manual=False,
            nfe_erro=None,
        )
        NFEService.processar_nfe_venda(str(venda_id), request.user)
        return Response({"mensagem": f"NF-e reenviada para reprocessamento: venda {venda_id}"})

    @action(detail=False, methods=['post'], url_path='retry-manual')
    def retry_manual(self, request):
        """Clear the manual retry flag and re-queue a specific sale's NF-e."""
        venda_id = request.data.get('venda_id')
        if not venda_id:
            return Response({"erro": "venda_id obrigatório"}, status=status.HTTP_400_BAD_REQUEST)

        from apps.sales.models import Venda
        updated = Venda.objects.filter(pk=venda_id, nfe_requer_retry_manual=True).update(
            nfe_requer_retry_manual=False,
            nfe_situacao='PENDENTE',
            nfe_tentativas=0,
        )
        if not updated:
            return Response(
                {"erro": "Venda não encontrada ou não está com retry manual pendente"},
                status=status.HTTP_404_NOT_FOUND,
            )

        NFEService.processar_nfe_venda(str(venda_id), request.user)
        return Response({"mensagem": f"Retry manual autorizado para venda {venda_id}"})

    @action(detail=False, methods=['get'], url_path='pendentes')
    def pendentes(self, request):
        """Return sales with NF-e in PENDENTE or PROCESSANDO state."""
        from apps.sales.models import Venda
        vendas = Venda.objects.filter(
            nfe_situacao__in=('PENDENTE', 'PROCESSANDO')
        ).values('id', 'numero_venda', 'nfe_situacao', 'nfe_tentativas', 'nfe_ultima_tentativa')[:100]
        return Response(list(vendas))

    @action(detail=False, methods=['get'], url_path='falhadas')
    def falhadas(self, request):
        """Return sales with failed or manual-retry NF-e."""
        from apps.sales.models import Venda
        vendas = Venda.objects.filter(
            nfe_situacao__in=('ERRO_TECNICO', 'REJEITADA', 'AGUARDANDO_RETRY')
        ).values(
            'id', 'numero_venda', 'nfe_situacao', 'nfe_erro',
            'nfe_tentativas', 'nfe_ultima_tentativa', 'nfe_requer_retry_manual',
        ).order_by('-nfe_ultima_tentativa')[:200]
        return Response(list(vendas))


# ---------------------------------------------------------------------------
# NotaFiscal CRUD ViewSet (reuse in admin / API)
# ---------------------------------------------------------------------------

class NotaFiscalViewSet(ModelViewSet):
    """CRUD + extra actions for fiscal notes."""

    serializer_class = NotaFiscalSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return (
            NotaFiscal.objects
            .select_related('loja', 'venda')
            .order_by('-created_at')
        )

    @action(detail=True, methods=['get'], url_path='logs')
    def logs(self, request, pk=None):
        nota = self.get_object()
        logs = LogEventosFiscais.objects.filter(nota_fiscal=nota).order_by('-created_at')
        serializer = LogEventosFiscaisSerializer(logs, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'], url_path='cancelar')
    def cancelar(self, request, pk=None):
        """Cancel an authorized NF-e via SEFAZ."""
        nota = self.get_object()
        if nota.situacao != 'AUTORIZADA':
            return Response(
                {"erro": f"Nota não está autorizada (situação: {nota.situacao})"},
                status=status.HTTP_422_UNPROCESSABLE_ENTITY,
            )

        justificativa = request.data.get('justificativa', '').strip()
        if len(justificativa) < 15:
            return Response(
                {"erro": "justificativa deve ter no mínimo 15 caracteres"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        from apps.fiscal.sefaz.client import criar_sefaz_client
        from apps.fiscal.sefaz.exceptions import SefazCancelamentoError, SefazError

        try:
            resultado = criar_sefaz_client().cancelar_nfe(
                nota.chave_acesso or '',
                justificativa,
                nota.protocolo_autorizacao or '',
            )
        except SefazCancelamentoError as exc:
            return Response({"erro": str(exc)}, status=status.HTTP_422_UNPROCESSABLE_ENTITY)
        except SefazError as exc:
            return Response({"erro": str(exc)}, status=status.HTTP_502_BAD_GATEWAY)

        nota.situacao = 'CANCELADA'
        nota.motivo_cancelamento = justificativa
        nota.save(update_fields=['situacao', 'motivo_cancelamento', 'updated_at'])

        # Also update the linked sale
        if nota.venda_id:
            nota.venda.__class__.objects.filter(pk=nota.venda_id).update(
                nfe_situacao='CANCELADA'
            )

        return Response(resultado)

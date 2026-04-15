"""Fiscal Django views — T055: NFe dashboard and manual retry queue."""
from __future__ import annotations

from django.contrib.auth.decorators import login_required, permission_required
from django.core.paginator import Paginator
from django.db.models import Count
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_http_methods


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------

def _nfe_notas_por_situacao():
    from apps.sales.models import Venda

    qs = (
        Venda.objects
        .exclude(nfe_situacao='NAO_APLICAVEL')
        .values('nfe_situacao')
        .annotate(total=Count('id'))
    )
    return {row['nfe_situacao']: row['total'] for row in qs}


# ---------------------------------------------------------------------------
# T052 — NFe Automation Dashboard
# ---------------------------------------------------------------------------

@login_required
@permission_required('fiscal.view_notafiscal', raise_exception=True)
def nfe_dashboard(request):
    from apps.sales.models import Venda

    notas_por_situacao = _nfe_notas_por_situacao()

    pendentes_list = (
        Venda.objects
        .filter(nfe_situacao__in=('PENDENTE',))
        .select_related('cliente')
        .order_by('-created_at')[:50]
    )
    processando_list = (
        Venda.objects
        .filter(nfe_situacao='PROCESSANDO')
        .select_related('cliente')
        .order_by('-nfe_ultima_tentativa')[:50]
    )
    falhadas_list = (
        Venda.objects
        .filter(nfe_situacao__in=('REJEITADA', 'ERRO_TECNICO', 'AGUARDANDO_RETRY'))
        .select_related('cliente')
        .order_by('-nfe_ultima_tentativa')[:50]
    )

    context = {
        'notas_por_situacao': notas_por_situacao,
        'pendentes_list': pendentes_list,
        'processando_list': processando_list,
        'falhadas_list': falhadas_list,
        'title': 'Dashboard NF-e',
    }
    return render(request, 'fiscal/nfe-automation-dashboard.html', context)


# ---------------------------------------------------------------------------
# T053/T055 — Manual Retry Queue
# ---------------------------------------------------------------------------

@login_required
@permission_required('fiscal.view_notafiscal', raise_exception=True)
def retry_queue(request):
    from apps.sales.models import Venda

    fila_qs = (
        Venda.objects
        .filter(nfe_requer_retry_manual=True)
        .select_related('cliente')
        .order_by('-nfe_ultima_tentativa', '-created_at')
    )

    paginator = Paginator(fila_qs, 30)
    page_obj = paginator.get_page(request.GET.get('page', 1))

    context = {
        'fila_retry': page_obj.object_list,
        'page_obj': page_obj,
        'title': 'Fila de Retry Manual — NF-e',
    }
    return render(request, 'fiscal/manual-retry-queue.html', context)


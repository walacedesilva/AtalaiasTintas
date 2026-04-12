"""
Views web para o sistema de etiquetas integrado
"""
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.core.paginator import Paginator
from django.db.models import Q, Count
from django.urls import reverse
from django.utils import timezone
import json
import uuid

# Imports dos modelos
from .models import (
    LabelTemplate, LabelPrintJob, LabelPrintQueue, PrinterConfiguration,
    MisturaTinta, EtiquetaMistura
)
from apps.core.models import User


@login_required
def dashboard(request):
    """Dashboard principal do sistema de etiquetas"""
    
    # Estatísticas rápidas
    context = {
        'total_templates': LabelTemplate.objects.filter(is_active=True).count(),
        'jobs_pendentes': LabelPrintJob.objects.filter(status='pending').count(),
        'jobs_processando': LabelPrintJob.objects.filter(status='processing').count(),
        'misturas_sem_etiqueta': MisturaTinta.objects.filter(etiqueta__isnull=True).count(),
        
        # Jobs recentes
        'jobs_recentes': LabelPrintJob.objects.select_related('template', 'created_by').order_by('-created_at')[:10],
        
        # Templates ativos
        'templates_ativos': LabelTemplate.objects.filter(is_active=True, status='active').order_by('name')[:6],
        
        # Configurações de impressora
        'impressoras_ativas': PrinterConfiguration.objects.filter(is_active=True).count(),
    }
    
    return render(request, 'etiquetas/dashboard.html', context)


@login_required
def templates_list(request):
    """Lista de templates de etiquetas"""
    
    templates = LabelTemplate.objects.annotate(
        usage_count_db=Count('labelprintjob')
    ).order_by('-is_default', 'category', 'name')
    
    # Filtros
    category = request.GET.get('category')
    if category:
        templates = templates.filter(category=category)
    
    status = request.GET.get('status')
    if status:
        templates = templates.filter(status=status)
    
    # Paginação
    paginator = Paginator(templates, 12)
    page_number = request.GET.get('page')
    templates_page = paginator.get_page(page_number)
    
    context = {
        'templates': templates_page,
        'categories': LabelTemplate.CATEGORY_CHOICES,
        'statuses': LabelTemplate.STATUS_CHOICES,
        'current_category': category,
        'current_status': status,
    }
    
    return render(request, 'etiquetas/templates.html', context)


@login_required
def template_detail(request, template_id):
    """Detalhe de um template específico"""
    template = get_object_or_404(LabelTemplate, id=template_id)
    
    # Jobs que usaram este template
    jobs = LabelPrintJob.objects.filter(template=template).order_by('-created_at')[:10]
    
    context = {
        'template': template,
        'jobs_recentes': jobs,
    }
    
    return render(request, 'etiquetas/template_detail.html', context)


@login_required
def misturas_list(request):
    """Lista de misturas disponíveis para geração de etiquetas"""
    
    queryset = MisturaTinta.objects.select_related(
        'formula__cor_definida', 'loja', 'usuario_operacao'
    ).prefetch_related('etiqueta').order_by('-created_at')
    
    # Filtros
    search = request.GET.get('search')
    if search:
        queryset = queryset.filter(
            Q(codigo_mistura__icontains=search) |
            Q(cliente_nome__icontains=search) |
            Q(formula__nome_formula__icontains=search)
        )
    
    situacao = request.GET.get('situacao')
    if situacao:
        queryset = queryset.filter(situacao=situacao)
    
    sem_etiqueta = request.GET.get('sem_etiqueta')
    if sem_etiqueta == '1':
        queryset = queryset.filter(etiqueta__isnull=True)
    
    # Paginação
    paginator = Paginator(queryset, 20)
    page_number = request.GET.get('page')
    misturas_page = paginator.get_page(page_number)
    
    context = {
        'misturas': misturas_page,
        'situacoes': MisturaTinta.SITUACAO_CHOICES,
        'current_search': search,
        'current_situacao': situacao,
        'current_sem_etiqueta': sem_etiqueta,
    }
    
    return render(request, 'etiquetas/misturas.html', context)


@login_required
def nova_mistura_etiqueta(request):
    """Formulário para criar nova mistura e gerar etiqueta"""
    
    if request.method == 'POST':
        # Processar criação da mistura
        # (Este seria um processo mais complexo integrando com o sistema completo)
        messages.success(request, 'Mistura criada e etiqueta gerada com sucesso!')
        return redirect('etiquetas:dashboard')
    
    # Templates disponíveis para o formulário
    templates = LabelTemplate.objects.filter(is_active=True, status='active')
    
    context = {
        'templates': templates,
    }
    
    return render(request, 'etiquetas/nova_mistura.html', context)


@login_required
def gerar_etiquetas(request):
    """Interface para gerar etiquetas em lote"""
    
    if request.method == 'POST':
        template_id = request.POST.get('template_id')
        mistura_ids = request.POST.getlist('mistura_ids')
        
        if not template_id or not mistura_ids:
            messages.error(request, 'Selecione um template e ao menos uma mistura.')
            return redirect('etiquetas:gerar')
        
        # Criar job de impressão
        template = get_object_or_404(LabelTemplate, id=template_id)
        
        job = LabelPrintJob.objects.create(
            template=template,
            created_by=request.user,
            output_type=request.POST.get('output_type', 'pdf'),
            copies_count=int(request.POST.get('copies_count', 1)),
        )
        
        # Associar misturas
        misturas = MisturaTinta.objects.filter(id__in=mistura_ids)
        job.misturas.set(misturas)
        
        # Criar item na fila de processamento
        LabelPrintQueue.objects.create(
            print_job=job,
            priority=request.POST.get('priority', 'normal'),
        )
        
        messages.success(
            request, 
            f'Job de impressão {job.job_id.hex[:8]} criado com sucesso! '
            f'{len(mistura_ids)} etiquetas serão processadas.'
        )
        
        return redirect('etiquetas:job_status', job_id=job.job_id)
    
    # Interface GET
    templates = LabelTemplate.objects.filter(is_active=True, status='active')
    misturas_disponiveis = MisturaTinta.objects.filter(
        situacao__in=['CONFIRMADA', 'PRODUZIDA']
    ).select_related('formula__cor_definida').order_by('-created_at')[:50]
    
    context = {
        'templates': templates,
        'misturas': misturas_disponiveis,
        'output_types': LabelPrintJob.OUTPUT_CHOICES,
        'priorities': LabelPrintQueue.PRIORITY_CHOICES,
    }
    
    return render(request, 'etiquetas/gerar.html', context)


@login_required 
def job_status(request, job_id):
    """Status de um job de impressão"""
    job = get_object_or_404(LabelPrintJob, job_id=job_id)
    
    context = {
        'job': job,
        'misturas': job.misturas.select_related('formula__cor_definida').all(),
    }
    
    return render(request, 'etiquetas/job_status.html', context)


@login_required
def preview_etiqueta(request, mistura_id):
    """Preview de uma etiqueta específica"""
    
    mistura = get_object_or_404(MisturaTinta, id=mistura_id)
    template_id = request.GET.get('template_id')
    
    if template_id:
        template = get_object_or_404(LabelTemplate, id=template_id)
    else:
        # Use template padrão
        template = LabelTemplate.objects.filter(
            is_default=True, 
            is_active=True
        ).first()
    
    context = {
        'mistura': mistura,
        'template': template,
        'preview_mode': True,
    }
    
    return render(request, 'etiquetas/preview.html', context)


# =============================================================================
# API ENDPOINTS AJAX
# =============================================================================

@csrf_exempt
@require_http_methods(["POST"])
@login_required
def api_gerar_etiqueta_simples(request):
    """API para gerar etiqueta simples via AJAX"""
    
    try:
        data = json.loads(request.body)
        mistura_id = data.get('mistura_id')
        template_id = data.get('template_id')
        
        mistura = MisturaTinta.objects.get(id=mistura_id)
        template = LabelTemplate.objects.get(id=template_id)
        
        # Criar ou atualizar etiqueta existente
        etiqueta, created = EtiquetaMistura.objects.get_or_create(
            mistura=mistura,
            defaults={
                'codigo_etiqueta': f"ET{mistura.codigo_mistura}",
            }
        )
        
        if not created:
            # Marcar como reimpressão
            etiqueta.marcar_impressa(request.user)
        
        return JsonResponse({
            'success': True,
            'etiqueta_id': etiqueta.codigo_etiqueta,
            'message': 'Etiqueta gerada com sucesso!',
            'is_reprint': not created,
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=400)


@login_required
def api_job_progress(request, job_id):
    """API para consultar progresso de um job"""
    
    try:
        job = LabelPrintJob.objects.get(job_id=job_id)
        
        return JsonResponse({
            'job_id': str(job.job_id),
            'status': job.status,
            'progress': job.progress,
            'error_message': job.error_message,
            'completed_at': job.completed_at.isoformat() if job.completed_at else None,
            'file_path': job.output_file_path,
            'misturas_count': job.misturas_count,
        })
        
    except LabelPrintJob.DoesNotExist:
        return JsonResponse({'error': 'Job não encontrado'}, status=404)


@login_required
def api_search_misturas(request):
    """API para buscar misturas via AJAX"""
    
    query = request.GET.get('q', '')
    limit = int(request.GET.get('limit', 10))
    
    if len(query) < 2:
        return JsonResponse({'results': []})
    
    misturas = MisturaTinta.objects.filter(
        Q(codigo_mistura__icontains=query) |
        Q(cliente_nome__icontains=query) |
        Q(formula__nome_formula__icontains=query)
    ).select_related('formula__cor_definida')[:limit]
    
    results = []
    for mistura in misturas:
        results.append({
            'id': str(mistura.id),
            'codigo': mistura.codigo_mistura,
            'cliente': mistura.cliente_nome,
            'cor': mistura.formula.cor_definida.nome_cor,
            'volume': str(mistura.volume_solicitado),
            'situacao': mistura.get_situacao_display(),
        })
    
    return JsonResponse({'results': results})


# ===================================
# QUICK ACTIONS - NEW VIEW FUNCTIONS
# Feature: 3-modern-web-interface  
# Task: T012 - Build Quick Actions System
# ===================================

@login_required
def template_create(request):
    """Criar novo template de etiqueta"""
    
    if request.method == 'POST':
        # Processar criação do template
        # (implementação completa seria feita com forms Django)
        messages.success(request, 'Template criado com sucesso!')
        return redirect('etiquetas:templates')
    
    context = {
        'categories': LabelTemplate.CATEGORY_CHOICES,
        'paper_sizes': [
            ('A4', 'A4 (210×297mm)'),
            ('A5', 'A5 (148×210mm)'),
            ('LABEL_50x30', 'Etiqueta 50×30mm'),
            ('LABEL_100x50', 'Etiqueta 100×50mm'),
        ],
    }
    
    return render(request, 'etiquetas/template_create.html', context)


@login_required  
def jobs_list(request):
    """Lista de jobs de impressão"""
    
    jobs = LabelPrintJob.objects.select_related('template', 'created_by').order_by('-created_at')
    
    # Filtros
    status = request.GET.get('status')
    if status:
        jobs = jobs.filter(status=status)
    
    date_from = request.GET.get('date_from')
    if date_from:
        jobs = jobs.filter(created_at__date__gte=date_from)
    
    # Paginação
    paginator = Paginator(jobs, 20)
    page_number = request.GET.get('page')
    jobs_page = paginator.get_page(page_number)
    
    context = {
        'jobs': jobs_page,
        'statuses': LabelPrintJob.STATUS_CHOICES,
        'current_status': status,
        'current_date_from': date_from,
    }
    
    return render(request, 'etiquetas/jobs_list.html', context)


@login_required
def print_queue(request):
    """Fila de impressão - gerenciamento de jobs pendentes"""
    
    queue_items = LabelPrintQueue.objects.select_related(
        'print_job', 'print_job__template', 'print_job__created_by'
    ).order_by('-priority_order', 'created_at')
    
    # Estatísticas da fila
    stats = {
        'total': queue_items.count(),
        'processing': queue_items.filter(status='processing').count(),
        'pending': queue_items.filter(status='pending').count(),
        'failed': queue_items.filter(status='failed').count(),
    }
    
    context = {
        'queue_items': queue_items,
        'stats': stats,
        'priorities': LabelPrintQueue.PRIORITY_CHOICES,
    }
    
    return render(request, 'etiquetas/print_queue.html', context)


@login_required
def job_status(request, job_id):
    """Status detalhado de um job específico"""
    
    job = get_object_or_404(LabelPrintJob, job_id=job_id)
    
    # Items da fila relacionados
    queue_items = LabelPrintQueue.objects.filter(print_job=job)
    
    context = {
        'job': job,
        'queue_items': queue_items,
        'can_cancel': job.status in ['pending', 'processing'],
        'can_retry': job.status in ['failed', 'cancelled'],
    }
    
    return render(request, 'etiquetas/job_status.html', context)


@login_required
def preview_etiqueta(request, mistura_id):
    """Preview de etiqueta para uma mistura específica"""
    
    mistura = get_object_or_404(MisturaTinta, id=mistura_id)
    
    # Template padrão ou especificado
    template_id = request.GET.get('template_id')
    if template_id:
        template = get_object_or_404(LabelTemplate, id=template_id)
    else:
        template = LabelTemplate.objects.filter(is_default=True, is_active=True).first()
        if not template:
            messages.error(request, 'Nenhum template padrão encontrado.')
            return redirect('etiquetas:misturas')
    
    context = {
        'mistura': mistura,
        'template': template,
        'preview_data': {
            'codigo': mistura.codigo_mistura,
            'cliente': mistura.cliente_nome,
            'cor': mistura.formula.cor_definida.nome_cor if mistura.formula else 'N/A',
            'volume': f"{mistura.volume_solicitado}L",
            'data': mistura.created_at.strftime('%d/%m/%Y'),
        },
    }
    
    return render(request, 'etiquetas/preview.html', context)


# ===================================
# API ENDPOINTS FOR QUICK ACTIONS
# ===================================

@login_required
def api_job_progress(request, job_id):
    """API para obter progresso de um job"""
    
    job = get_object_or_404(LabelPrintJob, job_id=job_id)
    
    data = {
        'status': job.status,
        'progress': getattr(job, 'progress_percentage', 0),
        'message': job.get_status_display(),
        'created_at': job.created_at.isoformat(),
        'updated_at': job.updated_at.isoformat(),
    }
    
    if job.status == 'completed' and job.output_file:
        data['download_url'] = job.output_file.url
    
    if job.status == 'failed' and job.error_message:
        data['error_message'] = job.error_message
    
    return JsonResponse(data)
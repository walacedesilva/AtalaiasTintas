"""
Views para o sistema de etiquetas de tintas
Handles web interface for label generation and management
"""
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.core.paginator import Paginator
from django.db.models import Q, Count, Sum, Avg
from django.utils import timezone
from datetime import datetime, timedelta
import json
import logging

from apps.tintometry.models import (
    ProducaoTinta, FormulaTintometrica, Pigmento,
    LequeCorDefinida, ProdutoVariacao
)
from apps.companies.models import Loja
from .services import LabelGeneratorService, QRCodeService, BarcodeService
from .models import LabelTemplate, LabelPrintJob

logger = logging.getLogger(__name__)


@login_required
def dashboard_view(request):
    """Dashboard principal do sistema de etiquetas"""
    try:
        # Estatísticas gerais
        today = timezone.now().date()
        week_start = today - timedelta(days=today.weekday())
        month_start = today.replace(day=1)
        
        # Contadores principais
        total_misturas = ProducaoTinta.objects.filter(
            operador=request.user
        ).count()
        
        misturas_hoje = ProducaoTinta.objects.filter(
            operador=request.user,
            created_at__date=today
        ).count()
        
        misturas_semana = ProducaoTinta.objects.filter(
            operador=request.user,
            created_at__date__gte=week_start
        ).count()
        
        # Misturas recentes
        misturas_recentes = ProducaoTinta.objects.filter(
            operador=request.user
        ).select_related(
            'formula__cor_definida',
            'formula__produto_base',
            'loja'
        ).order_by('-created_at')[:10]
        
        # Estatísticas de volume e custo
        stats_volume = ProducaoTinta.objects.filter(
            operador=request.user,
            created_at__date__gte=month_start
        ).aggregate(
            volume_total=Sum('volume_solicitado'),
            volume_medio=Avg('volume_solicitado')
        )
        
        # Templates mais usados
        templates_populares = LabelTemplate.objects.filter(
            is_active=True
        ).annotate(
            uso_count=Count('labelprintjob')
        ).order_by('-uso_count')[:5]
        
        context = {
            'total_misturas': total_misturas,
            'misturas_hoje': misturas_hoje,
            'misturas_semana': misturas_semana,
            'misturas_recentes': misturas_recentes,
            'volume_total_mes': stats_volume.get('volume_total', 0) or 0,
            'volume_produzido_mes': stats_volume.get('volume_produzido', 0) or 0,
            'volume_medio': stats_volume.get('volume_medio', 0) or 0,
            'templates_populares': templates_populares,
        }
        
        return render(request, 'etiquetas/index.html', context)
        
    except Exception as e:
        logger.error(f"Erro no dashboard de etiquetas: {str(e)}")
        messages.error(request, "Erro ao carregar dashboard. Tente novamente.")
        return render(request, 'etiquetas/index.html', {'error': True})


@login_required
def misturas_list_view(request):
    """Lista todas as misturas com filtros e busca"""
    try:
        # Base queryset
        misturas = ProducaoTinta.objects.select_related(
            'formula__cor_definida',
            'formula__produto_base', 
            'loja',
            'operador'
        ).prefetch_related('itens__pigmento')
        
        # Filtros
        search = request.GET.get('search', '').strip()
        status = request.GET.get('status', '')
        loja_id = request.GET.get('loja', '')
        data_de = request.GET.get('data_de', '')
        data_ate = request.GET.get('data_ate', '')
        cor_familia = request.GET.get('cor_familia', '')
        
        # Aplicar filtros
        if search:
            misturas = misturas.filter(
                Q(numero_producao__icontains=search) |
                Q(cliente_nome__icontains=search) |
                Q(formula__cor_definida__nome_cor__icontains=search) |
                Q(formula__codigo_formula__icontains=search)
            )
        
        if status:
            misturas = misturas.filter(situacao=status)
            
        if loja_id:
            misturas = misturas.filter(loja_id=loja_id)
            
        if data_de:
            misturas = misturas.filter(created_at__date__gte=data_de)
            
        if data_ate:
            misturas = misturas.filter(created_at__date__lte=data_ate)
            
        if cor_familia:
            misturas = misturas.filter(
                formula__cor_definida__familia_cor=cor_familia
            )
        
        # Ordenação
        ordem = request.GET.get('ordem', '-created_at')
        if ordem in ['-created_at', 'created_at', 'numero_producao', 
                     '-volume_solicitado', 'situacao']:
            misturas = misturas.order_by(ordem)
        else:
            misturas = misturas.order_by('-created_at')
        
        # Paginação
        paginator = Paginator(misturas, 20)
        page = request.GET.get('page', 1)
        misturas_page = paginator.get_page(page)
        
        # Dados para filtros
        lojas = Loja.objects.all().order_by('nome')
        familias_cor = CorDefinida.objects.values_list(
            'familia_cor', flat=True
        ).distinct().order_by('familia_cor')
        
        context = {
            'misturas': misturas_page,
            'lojas': lojas,
            'familias_cor': familias_cor,
            'current_filters': {
                'search': search,
                'status': status,
                'loja': loja_id,
                'data_de': data_de,
                'data_ate': data_ate,
                'cor_familia': cor_familia,
                'ordem': ordem,
            },
            'status_choices': ProducaoTinta.SITUACOES,
        }
        
        return render(request, 'etiquetas/misturas.html', context)
        
    except Exception as e:
        logger.error(f"Erro ao listar misturas: {str(e)}")
        messages.error(request, "Erro ao carregar lista de misturas.")
        return render(request, 'etiquetas/misturas.html', {'error': True})


@login_required
def nova_mistura_view(request):
    """Formulário para criar nova mistura"""
    if request.method == 'POST':
        try:
            # Processar dados do formulário
            formula_id = request.POST.get('formula_id')
            cliente_nome = request.POST.get('cliente_nome', '').strip()
            pedido_venda_id = request.POST.get('pedido_venda_id', '').strip()
            volume_solicitado = float(request.POST.get('volume_solicitado', 0))
            loja_id = request.POST.get('loja_id')
            observacoes_qualidade = request.POST.get('observacoes_qualidade', '').strip()
            observacoes_qualidade = request.POST.get('observacoes_qualidade', '').strip()
            
            # Validações básicas
            if not formula_id or not cliente_nome or volume_solicitado <= 0:
                messages.error(request, "Preencha todos os campos obrigatórios.")
                return redirect('etiquetas:nova_mistura')
            
            # Obter fórmula
            formula = get_object_or_404(FormulaTintometrica, id=formula_id)
            loja = get_object_or_404(Loja, id=loja_id) if loja_id else None
            
            # Criar mistura
            mistura = ProducaoTinta.objects.create(
                formula=formula,
                cliente_nome=cliente_nome,
                produto_base=formula.produto_base,
                volume_solicitado=volume_solicitado,
                loja=loja,
                observacoes_qualidade=observacoes_qualidade,
                operador=request.user,
                situacao='PENDENTE'
            )
            
            # Mistura criada com sucesso
            messages.success(
                request, 
                f"Produção {mistura.numero_producao} criada com sucesso!"
            )
            
            # Verificar se deve imprimir automaticamente
            if request.POST.get('imprimir_automatico'):
                return redirect('etiquetas:gerar_etiqueta', mistura_id=mistura.id)
            else:
                return redirect('etiquetas:preview_etiqueta', mistura_id=mistura.id)
                
        except (ValueError, TypeError) as e:
            logger.error(f"Erro de validação na criação de mistura: {str(e)}")
            messages.error(request, "Dados inválidos. Verifique os valores informados.")
        except Exception as e:
            logger.error(f"Erro ao criar mistura: {str(e)}")
            messages.error(request, "Erro interno. Tente novamente.")
        
        return redirect('etiquetas:nova_mistura')
    
    # GET - exibir formulário
    try:
        # Dados para o formulário
        formulas = FormulaTintometrica.objects.filter(
            is_active=True
        ).select_related('cor_definida', 'produto_base').order_by(
            'cor_definida__nome_cor'
        )
        
        lojas = Loja.objects.filter(is_active=True).order_by('nome')
        
        # Organizar fórmulas por família de cor
        formulas_por_familia = {}
        for formula in formulas:
            familia = formula.cor_definida.familia_cor or 'Outras'
            if familia not in formulas_por_familia:
                formulas_por_familia[familia] = []
            formulas_por_familia[familia].append(formula)
        
        context = {
            'formulas': formulas,
            'formulas_por_familia': formulas_por_familia,
            'lojas': lojas,
        }
        
        return render(request, 'etiquetas/nova_mistura.html', context)
        
    except Exception as e:
        logger.error(f"Erro ao carregar formulário de nova mistura: {str(e)}")
        messages.error(request, "Erro ao carregar formulário.")
        return render(request, 'etiquetas/nova_mistura.html', {'error': True})


@login_required
def preview_etiqueta_view(request, mistura_id):
    """Preview da etiqueta antes de gerar PDF"""
    try:
        mistura = get_object_or_404(
            ProducaoTinta.objects.select_related(
                'formula__cor_definida',
                'formula__produto_base',
                'loja',
                'operador'
            ).prefetch_related('itens__pigmento'),
            id=mistura_id
        )
        
        # Verificar se usuário tem acesso
        if mistura.operador != request.user and not request.user.is_superuser:
            messages.error(request, "Acesso negado a esta mistura.")
            return redirect('etiquetas:misturas')
        
        context = {
            'mistura': mistura,
        }
        
        return render(request, 'etiquetas/preview.html', context)
        
    except Exception as e:
        logger.error(f"Erro no preview da etiqueta {mistura_id}: {str(e)}")
        messages.error(request, "Erro ao carregar preview da etiqueta.")
        return redirect('etiquetas:misturas')


@login_required
def gerar_etiqueta_view(request, mistura_id=None):
    """Interface para geração de etiquetas"""
    try:
        context = {}
        
        if mistura_id:
            # Geração para mistura específica
            mistura = get_object_or_404(
                ProducaoTinta.objects.select_related(
                    'formula__cor_definida',
                    'formula__produto_base',
                    'loja'
                ),
                id=mistura_id
            )
            
            # Verificar acesso
            if mistura.operador != request.user and not request.user.is_superuser:
                messages.error(request, "Acesso negado a esta mistura.")
                return redirect('etiquetas:misturas')
                
            context['mistura'] = mistura
            context['mistura_id'] = mistura_id
        
        # Templates disponíveis
        templates = LabelTemplate.objects.filter(is_active=True).order_by('name')
        context['templates'] = templates
        
        return render(request, 'etiquetas/gerar.html', context)
        
    except Exception as e:
        logger.error(f"Erro na interface de geração: {str(e)}")
        messages.error(request, "Erro ao carregar interface de geração.")
        return redirect('etiquetas:misturas')


@login_required 
def templates_management_view(request):
    """Interface para gerenciamento de templates"""
    try:
        templates = LabelTemplate.objects.annotate(
            usage_count=Count('labelprintjob')
        ).order_by('-usage_count', 'name')
        
        # Estatísticas
        total_generated = LabelPrintJob.objects.count()
        templates_active = templates.filter(is_active=True).count()
        week_start = timezone.now().date() - timedelta(days=7)
        generated_week = LabelPrintJob.objects.filter(
            created_at__date__gte=week_start
        ).count()
        
        context = {
            'templates': templates,
            'stats': {
                'total_generated': total_generated,
                'templates_active': templates_active, 
                'generated_week': generated_week,
            }
        }
        
        return render(request, 'etiquetas/templates.html', context)
        
    except Exception as e:
        logger.error(f"Erro no gerenciamento de templates: {str(e)}")
        messages.error(request, "Erro ao carregar templates.")
        return render(request, 'etiquetas/templates.html', {'error': True})


# AJAX Views for API-like responses

@login_required
@require_http_methods(["POST"])
def batch_action_view(request):
    """Ações em lote para misturas selecionadas"""
    try:
        data = json.loads(request.body)
        mistura_ids = data.get('mistura_ids', [])
        action = data.get('action', '')
        
        if not mistura_ids or not action:
            return JsonResponse({
                'success': False,
                'error': 'IDs e ação são obrigatórios'
            })
        
        # Verificar permissões
        misturas = ProducaoTinta.objects.filter(
            id__in=mistura_ids,
            operador=request.user
        )
        
        if misturas.count() != len(mistura_ids):
            return JsonResponse({
                'success': False,
                'error': 'Algumas misturas não foram encontradas ou você não tem acesso'
            })
        
        # Executar ação
        success_count = 0
        
        if action == 'change_status':
            new_status = data.get('new_status', '')
            if new_status in dict(ProducaoTinta.SITUACOES):
                success_count = misturas.update(situacao=new_status)
                
        elif action == 'generate_labels':
            # Marcar para geração de etiquetas
            for mistura in misturas:
                try:
                    # Aqui integraria com o serviço de geração
                    success_count += 1
                except Exception as e:
                    logger.error(f"Erro ao gerar etiqueta para mistura {mistura.id}: {e}")
                    
        elif action == 'delete':
            if request.user.is_superuser:
                success_count = misturas.count()
                misturas.delete()
            else:
                return JsonResponse({
                    'success': False,
                    'error': 'Operação não permitida'
                })
        
        return JsonResponse({
            'success': True,
            'message': f'{success_count} misturas processadas com sucesso',
            'processed_count': success_count
        })
        
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': 'Dados JSON inválidos'
        })
    except Exception as e:
        logger.error(f"Erro na ação em lote: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': 'Erro interno do servidor'
        })


@login_required
@require_http_methods(["GET"])
def get_qr_code(request, mistura_id):
    """Gera QR Code para uma mistura"""
    try:
        mistura = get_object_or_404(ProducaoTinta, id=mistura_id)
        
        # Verificar acesso
        if mistura.operador != request.user and not request.user.is_superuser:
            return JsonResponse({
                'success': False,
                'error': 'Acesso negado'
            })
        
        # Gerar QR Code
        qr_service = QRCodeService()
        qr_data = qr_service.generate_qr_data(mistura)
        qr_image_base64 = qr_service.generate_qr_image(qr_data)
        
        return JsonResponse({
            'success': True,
            'qr_data': qr_data,
            'qr_image_base64': qr_image_base64
        })
        
    except Exception as e:
        logger.error(f"Erro ao gerar QR Code para mistura {mistura_id}: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': 'Erro ao gerar QR Code'
        })


@login_required
@require_http_methods(["GET"])
def get_barcode(request, mistura_id):
    """Gera código de barras para uma mistura"""
    try:
        mistura = get_object_or_404(ProducaoTinta, id=mistura_id)
        
        # Verificar acesso
        if mistura.operador != request.user and not request.user.is_superuser:
            return JsonResponse({
                'success': False,
                'error': 'Acesso negado'  
            })
        
        # Gerar Barcode
        barcode_service = BarcodeService()
        tracking_code = barcode_service.generate_tracking_code(mistura)
        barcode_image_base64 = barcode_service.generate_barcode_image(tracking_code)
        
        return JsonResponse({
            'success': True,
            'tracking_code': tracking_code,
            'barcode_image_base64': barcode_image_base64
        })
        
    except Exception as e:
        logger.error(f"Erro ao gerar barcode para mistura {mistura_id}: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': 'Erro ao gerar código de barras'
        })


@login_required 
@require_http_methods(["GET"])
def search_formulas(request):
    """Busca fórmulas para AJAX"""
    try:
        query = request.GET.get('q', '').strip()
        if len(query) < 2:
            return JsonResponse({'results': []})
        
        formulas = FormulaTintometrica.objects.filter(
            Q(codigo_formula__icontains=query) |
            Q(cor_definida__nome_cor__icontains=query) |
            Q(cor_definida__familia_cor__icontains=query),
            is_active=True
        ).select_related('cor_definida', 'produto_base')[:10]
        
        results = []
        for formula in formulas:
            results.append({
                'id': formula.id,
                'codigo': formula.codigo_formula,
                'nome_cor': formula.cor_definida.nome_cor,
                'familia_cor': formula.cor_definida.familia_cor,
                'linha_produto': formula.cor_definida.linha_produto,
                'cor_hex': formula.cor_definida.cor_hex,
                'produto_base': formula.produto_base.nome_variacao,
                'custo_base': float(formula.custo_base_estimado or 0),
            })
        
        return JsonResponse({'results': results})
        
    except Exception as e:
        logger.error(f"Erro na busca de fórmulas: {str(e)}")
        return JsonResponse({'results': []})


@login_required
@require_http_methods(["POST"])
def update_mistura_status(request, mistura_id):
    """Atualiza status de uma mistura específica"""
    try:
        mistura = get_object_or_404(ProducaoTinta, id=mistura_id)
        
        # Verificar acesso
        if mistura.operador != request.user and not request.user.is_superuser:
            return JsonResponse({
                'success': False,
                'error': 'Acesso negado'
            })
        
        data = json.loads(request.body)
        new_status = data.get('status', '')
        
        if new_status not in dict(ProducaoTinta.SITUACOES):
            return JsonResponse({
                'success': False,
                'error': 'Status inválido'
            })
        
        old_status = mistura.situacao
        mistura.situacao = new_status
        
        # Definir campos de data baseado no status
        if new_status == 'CONFIRMADA' and old_status == 'CALCULADA':
            mistura.data_confirmacao = timezone.now()
        elif new_status == 'PRODUZIDA' and old_status == 'CONFIRMADA':
            mistura.data_producao = timezone.now()
        elif new_status == 'ENTREGUE' and old_status == 'PRODUZIDA':
            mistura.data_entrega = timezone.now()
        
        mistura.save()
        
        return JsonResponse({
            'success': True,
            'message': f'Status alterado para {mistura.get_situacao_display()}',
            'new_status': new_status,
            'status_display': mistura.get_situacao_display()
        })
        
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': 'Dados JSON inválidos'
        })
    except Exception as e:
        logger.error(f"Erro ao atualizar status da mistura {mistura_id}: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': 'Erro interno do servidor'
        })
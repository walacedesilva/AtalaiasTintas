"""
Mixture Service

Orchestrates the complete tintometric mixing process:
- Coordinates between formula calculation, stock management, and color science
- Manages mixture workflow from calculation to completion
- Handles business rules and validations
- Provides high-level API for tintometric operations
"""

from decimal import Decimal, ROUND_HALF_UP
from typing import Dict, List, Optional, Tuple
import logging
import uuid

from django.db import transaction
from django.utils import timezone
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError

from ..models import (
    FormulaTintometrica, 
    MisturaTinta, 
    ItemMistura,
    EtiquetaMistura,
    EstoquePigmento,
    LequeCorDefinida
)
from .formula_calculator import FormulaCalculatorService
from .stock_manager import StockManagerService
from .color_science import ColorScienceService

User = get_user_model()
logger = logging.getLogger(__name__)


class MixtureService:
    """Serviço principal para gerenciamento do processo completo de misturas tintométricas"""
    
    def __init__(self):
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        self.calculator = FormulaCalculatorService()
        self.stock_manager = StockManagerService()
        self.color_science = ColorScienceService()
    
    @transaction.atomic
    def create_mixture_calculation(
        self,
        formula_id: str,
        volume_requested: Decimal,
        loja_id: int,
        user_id: str,
        customer_data: Dict,
        validate_stock: bool = True,
        observations: str = None
    ) -> Dict:
        """
        Cria uma nova mistura com cálculo completo
        
        Args:
            formula_id: ID da fórmula tintométrica
            volume_requested: Volume solicitado em litros
            loja_id: ID da loja
            user_id: ID do usuário operador
            customer_data: Dados do cliente {'nome', 'documento', 'telefone', 'email'}
            validate_stock: Se deve validar estoque
            observations: Observações do cliente
            
        Returns:
            Dict: Resultado completo da criação da mistura
        """
        self.logger.info(
            f"Iniciando criação de mistura - Fórmula: {formula_id}, "
            f"Volume: {volume_requested}L, Loja: {loja_id}"
        )
        
        try:
            # Validar inputs
            formula = self._validate_formula(formula_id)
            user = self._validate_user(user_id)
            
            # Calcular quantidades e custos
            calculation_result = self.calculator.calculate_mixture_quantities(
                formula=formula,
                target_volume=volume_requested,
                loja_id=loja_id,
                validate_stock=validate_stock
            )
            
            if not calculation_result['validacao']['stock_ok'] and validate_stock:
                return {
                    'success': False,
                    'error': 'Estoque insuficiente para alguns pigmentos',
                    'details': calculation_result['validacao']['warnings'],
                    'calculation': calculation_result
                }
            
            # Criar registro da mistura
            mistura = MisturaTinta.objects.create(
                formula=formula,
                loja_id=loja_id,
                usuario_operacao=user,
                cliente_nome=customer_data.get('nome', ''),
                cliente_documento=customer_data.get('documento'),
                cliente_telefone=customer_data.get('telefone'),
                cliente_email=customer_data.get('email'),
                volume_solicitado=volume_requested,
                custo_total=calculation_result['custos']['total'],
                custo_base=calculation_result['custos']['base'],
                custo_pigmentos=calculation_result['custos']['pigmentos'],
                observacoes_cliente=observations,
                situacao='CALCULADA'
            )
            
            # Criar itens da mistura
            items_created = []
            for pigment_calc in calculation_result['pigmentos']:
                item = ItemMistura.objects.create(
                    mistura=mistura,
                    pigmento_id=pigment_calc['pigmento']['id'],
                    quantidade_calculada=Decimal(str(pigment_calc['quantidades']['calculada_final'])),
                    custo_unitario=pigment_calc['custos']['unitario'],
                    custo_total=Decimal(str(pigment_calc['custos']['total'])),
                    sequencia=pigment_calc.get('sequencia', 1)
                )
                items_created.append(item)
            
            # Análise científica de cor
            color_analysis = None
            if formula.cor_definida:
                target_lab = (
                    formula.cor_definida.l_value,
                    formula.cor_definida.a_value,
                    formula.cor_definida.b_value
                )
                
                color_analysis = {
                    'target_color': {
                        'codigo': formula.cor_definida.codigo_cor,
                        'nome': formula.cor_definida.nome_cor,
                        'lab': {
                            'L': float(target_lab[0]),
                            'a': float(target_lab[1]),
                            'b': float(target_lab[2])
                        }
                    },
                    'rgb_conversion': self.color_science.lab_to_rgb(*target_lab)
                }
            
            result = {
                'success': True,
                'mistura': {
                    'id': str(mistura.id),
                    'codigo': mistura.codigo_mistura,
                    'situacao': mistura.situacao,
                    'created_at': mistura.created_at.isoformat()
                },
                'calculation': calculation_result,
                'color_analysis': color_analysis,
                'items_created': len(items_created),
                'next_steps': [
                    'Confirmar mistura para reservar estoque',
                    'Executar mistura física',
                    'Gerar etiqueta de identificação'
                ]
            }
            
            self.logger.info(
                f"Mistura criada com sucesso - Código: {mistura.codigo_mistura}, "
                f"Itens: {len(items_created)}, Custo: R${calculation_result['custos']['total']}"
            )
            
            return result
            
        except Exception as e:
            self.logger.error(f"Erro na criação da mistura: {str(e)}")
            raise
    
    @transaction.atomic
    def confirm_mixture(
        self, 
        mixture_id: str,
        user_id: str,
        reserve_stock: bool = True
    ) -> Dict:
        """
        Confirma uma mistura e reserva estoque
        
        Args:
            mixture_id: ID da mistura
            user_id: ID do usuário confirmando
            reserve_stock: Se deve reservar estoque
            
        Returns:
            Dict: Resultado da confirmação
        """
        self.logger.info(f"Confirmando mistura {mixture_id}")
        
        try:
            mistura = MisturaTinta.objects.select_related('formula', 'loja').get(id=mixture_id)
            user = User.objects.get(id=user_id)
            
            if mistura.situacao != 'CALCULADA':
                raise ValidationError(f"Mistura não pode ser confirmada. Status atual: {mistura.situacao}")
            
            # Preparar dados para reserva de estoque
            if reserve_stock:
                pigment_requirements = []
                for item in mistura.itens.all():
                    pigment_requirements.append({
                        'pigmento_id': item.pigmento.id,
                        'quantidade': item.quantidade_calculada
                    })
                
                # Reservar estoque
                stock_reserved, stock_errors = self.stock_manager.reserve_stock(
                    pigment_requirements=pigment_requirements,
                    loja_id=mistura.loja.id,
                    reference_code=mistura.codigo_mistura
                )
                
                if not stock_reserved:
                    return {
                        'success': False,
                        'error': 'Falha na reserva de estoque',
                        'details': stock_errors
                    }
                
                # Atualizar itens com informações de estoque
                for item in mistura.itens.select_related('pigmento').all():
                    try:
                        estoque = EstoquePigmento.objects.get(
                            pigmento=item.pigmento,
                            loja=mistura.loja
                        )
                        item.estoque_antes = estoque.saldo_ml + item.quantidade_calculada  # Antes da reserva
                        item.estoque_depois = estoque.saldo_ml  # Após a reserva
                        item.lote_utilizado = estoque.lote_atual
                        item.save(update_fields=['estoque_antes', 'estoque_depois', 'lote_utilizado'])
                    except EstoquePigmento.DoesNotExist:
                        self.logger.warning(f"Estoque não encontrado para item {item.id}")
            
            # Atualizar status da mistura
            mistura.situacao = 'CONFIRMADA'
            mistura.data_confirmacao = timezone.now()
            mistura.save(update_fields=['situacao', 'data_confirmacao'])
            
            # Gerar etiqueta automaticamente
            etiqueta = self._create_mixture_label(mistura)
            
            result = {
                'success': True,
                'mistura': {
                    'id': str(mistura.id),
                    'codigo': mistura.codigo_mistura,
                    'situacao': mistura.situacao,
                    'data_confirmacao': mistura.data_confirmacao.isoformat()
                },
                'estoque': {
                    'reservado': reserve_stock,
                    'itens_atualizados': mistura.itens.count()
                },
                'etiqueta': {
                    'codigo': etiqueta.codigo_etiqueta,
                    'qr_data': etiqueta.qr_code_data
                },
                'next_steps': [
                    'Imprimir etiqueta',
                    'Executar mistura física',
                    'Confirmar produção'
                ]
            }
            
            self.logger.info(f"Mistura {mistura.codigo_mistura} confirmada com sucesso")
            return result
            
        except Exception as e:
            self.logger.error(f"Erro na confirmação da mistura: {str(e)}")
            raise
    
    @transaction.atomic
    def execute_mixture(
        self,
        mixture_id: str,
        user_id: str,
        actual_quantities: List[Dict] = None,
        actual_volume: Decimal = None,
        quality_approved: bool = True,
        observations: str = None
    ) -> Dict:
        """
        Registra a execução física da mistura
        
        Args:
            mixture_id: ID da mistura
            user_id: ID do usuário executando
            actual_quantities: Quantidades reais utilizadas [{'pigmento_id': int, 'quantidade': Decimal}]
            actual_volume: Volume real produzido
            quality_approved: Se a cor foi aprovada
            observations: Observações da produção
            
        Returns:
            Dict: Resultado da execução
        """
        self.logger.info(f"Executando mistura física {mixture_id}")
        
        try:
            mistura = MisturaTinta.objects.select_related('formula').get(id=mixture_id)
            user = User.objects.get(id=user_id)
            
            if mistura.situacao != 'CONFIRMADA':
                raise ValidationError(f"Mistura não confirmada. Status: {mistura.situacao}")
            
            # Atualizar quantidades executadas se fornecidas
            if actual_quantities:
                for qty_data in actual_quantities:
                    try:
                        item = mistura.itens.get(pigmento_id=qty_data['pigmento_id'])
                        item.quantidade_executada = Decimal(str(qty_data['quantidade']))
                        item.save(update_fields=['quantidade_executada'])
                    except ItemMistura.DoesNotExist:
                        self.logger.warning(
                            f"Item não encontrado para pigmento {qty_data['pigmento_id']}"
                        )
            
            # Atualizar volume produzido
            if actual_volume:
                mistura.volume_produzido = actual_volume
            else:
                mistura.volume_produzido = mistura.volume_solicitado
            
            # Atualizar status e qualidade
            mistura.situacao = 'PRODUZIDA'
            mistura.data_producao = timezone.now()
            mistura.cor_aprovada_cliente = quality_approved
            
            if quality_approved:
                mistura.data_aprovacao_cor = timezone.now()
            
            if observations:
                current_obs = mistura.observacoes_internas or ""
                mistura.observacoes_internas = f"{current_obs}\n[Produção] {observations}".strip()
            
            mistura.save()
            
            # Análise de variações
            variation_analysis = self._analyze_execution_variations(mistura)
            
            # Análise colorimétrica se cor foi aprovada
            color_evaluation = None
            if quality_approved and mistura.formula.cor_definida:
                color_evaluation = self._evaluate_color_quality(mistura)
            
            result = {
                'success': True,
                'mistura': {
                    'id': str(mistura.id),
                    'codigo': mistura.codigo_mistura,
                    'situacao': mistura.situacao,
                    'volume_produzido': float(mistura.volume_produzido),
                    'cor_aprovada': quality_approved,
                    'data_producao': mistura.data_producao.isoformat()
                },
                'execution_analysis': variation_analysis,
                'color_evaluation': color_evaluation,
                'next_steps': [
                    'Entregar ao cliente' if quality_approved else 'Revisar cor com cliente',
                    'Registrar entrega',
                    'Atualizar histórico do cliente'
                ]
            }
            
            self.logger.info(
                f"Execução da mistura {mistura.codigo_mistura} registrada - "
                f"Volume: {mistura.volume_produzido}L, Aprovada: {quality_approved}"
            )
            
            return result
            
        except Exception as e:
            self.logger.error(f"Erro na execução da mistura: {str(e)}")
            raise
    
    @transaction.atomic
    def complete_mixture(
        self,
        mixture_id: str,
        user_id: str,
        delivery_confirmed: bool = True,
        customer_feedback: str = None
    ) -> Dict:
        """
        Finaliza uma mistura marcando como entregue
        
        Args:
            mixture_id: ID da mistura
            user_id: ID do usuário finalizando
            delivery_confirmed: Se a entrega foi confirmada
            customer_feedback: Feedback do cliente
            
        Returns:
            Dict: Resultado da finalização
        """
        try:
            mistura = MisturaTinta.objects.get(id=mixture_id)
            user = User.objects.get(id=user_id)
            
            if mistura.situacao != 'PRODUZIDA':
                raise ValidationError(f"Mistura não produzida. Status: {mistura.situacao}")
            
            mistura.situacao = 'ENTREGUE'
            mistura.data_entrega = timezone.now()
            
            if customer_feedback:
                current_obs = mistura.observacoes_cliente or ""
                mistura.observacoes_cliente = f"{current_obs}\n[Entrega] {customer_feedback}".strip()
            
            mistura.save()
            
            # Atualizar histórico do cliente
            customer_history = self._update_customer_history(mistura)
            
            result = {
                'success': True,
                'mistura': {
                    'id': str(mistura.id),
                    'codigo': mistura.codigo_mistura,
                    'situacao': mistura.situacao,
                    'data_entrega': mistura.data_entrega.isoformat(),
                    'completed': True
                },
                'customer_history': customer_history,
                'summary': {
                    'volume_final': float(mistura.volume_produzido or mistura.volume_solicitado),
                    'custo_total': float(mistura.custo_total),
                    'cor_formula': mistura.formula.nome_formula,
                    'tempo_total': (mistura.data_entrega - mistura.created_at).total_seconds() / 3600  # horas
                }
            }
            
            self.logger.info(f"Mistura {mistura.codigo_mistura} finalizada com sucesso")
            return result
            
        except Exception as e:
            self.logger.error(f"Erro na finalização da mistura: {str(e)}")
            raise

    @transaction.atomic
    def cancel_mixture(
        self,
        mixture_id: str,
        motivo: str,
        user_id: str,
    ) -> Dict:
        """
        Cancela uma mistura e restaura o estoque reservado.

        Apenas misturas com situação CALCULADA ou CONFIRMADA podem ser canceladas.
        Se a mistura estava CONFIRMADA, o estoque dos pigmentos reservados é devolvido.

        Args:
            mixture_id: ID (UUID) da mistura
            motivo: Motivo obrigatório do cancelamento
            user_id: ID do usuário que está cancelando

        Returns:
            Dict: Resultado do cancelamento com detalhes do estoque restaurado
        """
        CANCELABLE_STATUSES = {'CALCULADA', 'CONFIRMADA'}

        try:
            mistura = MisturaTinta.objects.select_related(
                'formula', 'loja'
            ).prefetch_related('itens__pigmento').get(id=mixture_id)
            User.objects.get(id=user_id)
        except MisturaTinta.DoesNotExist:
            raise ValidationError(f"Mistura não encontrada: {mixture_id}")
        except User.DoesNotExist:
            raise ValidationError(f"Usuário não encontrado: {user_id}")

        if mistura.situacao not in CANCELABLE_STATUSES:
            raise ValidationError(
                f"Mistura não pode ser cancelada. Status atual: {mistura.situacao}. "
                f"Apenas {', '.join(CANCELABLE_STATUSES)} podem ser canceladas."
            )

        if not motivo or not motivo.strip():
            raise ValidationError("Motivo do cancelamento é obrigatório.")

        estoque_restaurado = []

        # Restore stock only if already reserved (CONFIRMADA)
        if mistura.situacao == 'CONFIRMADA':
            for item in mistura.itens.all():
                try:
                    estoque = EstoquePigmento.objects.get(
                        pigmento=item.pigmento,
                        loja=mistura.loja
                    )
                    quantidade_a_restaurar = item.quantidade_calculada
                    estoque.adicionar_estoque(quantidade=quantidade_a_restaurar)
                    estoque_restaurado.append({
                        'pigmento': item.pigmento.nome,
                        'quantidade_restaurada_ml': float(quantidade_a_restaurar),
                        'saldo_apos': float(estoque.saldo_ml),
                    })
                    self.logger.info(
                        f"Estoque restaurado — pigmento {item.pigmento.nome}: "
                        f"+{quantidade_a_restaurar}ml"
                    )
                except EstoquePigmento.DoesNotExist:
                    self.logger.warning(
                        f"Estoque não encontrado para pigmento {item.pigmento.nome} "
                        f"ao cancelar mistura {mistura.codigo_mistura}"
                    )

        mistura.situacao = 'CANCELADA'
        mistura.motivo_cancelamento = motivo.strip()[:200]
        mistura.data_cancelamento = timezone.now()
        mistura.save(update_fields=['situacao', 'motivo_cancelamento', 'data_cancelamento'])

        self.logger.info(
            f"Mistura {mistura.codigo_mistura} cancelada. "
            f"Motivo: {motivo}. Itens com estoque restaurado: {len(estoque_restaurado)}"
        )

        return {
            'success': True,
            'mistura': {
                'id': str(mistura.id),
                'codigo': mistura.codigo_mistura,
                'situacao': mistura.situacao,
                'motivo_cancelamento': mistura.motivo_cancelamento,
                'data_cancelamento': mistura.data_cancelamento.isoformat(),
            },
            'estoque_restaurado': estoque_restaurado,
            'itens_restaurados': len(estoque_restaurado),
        }

    def get_mixture_status(self, mixture_id: str) -> Dict:
        """
        Obtém status completo de uma mistura
        
        Args:
            mixture_id: ID da mistura
            
        Returns:
            Dict: Status detalhado da mistura
        """
        try:
            mistura = MisturaTinta.objects.select_related(
                'formula', 'formula__cor_definida', 'loja', 'usuario_operacao'
            ).prefetch_related('itens__pigmento').get(id=mixture_id)
            
            # Informações básicas
            status = {
                'mistura': {
                    'id': str(mistura.id),
                    'codigo': mistura.codigo_mistura,
                    'situacao': mistura.situacao,
                    'created_at': mistura.created_at.isoformat(),
                    'data_confirmacao': mistura.data_confirmacao.isoformat() if mistura.data_confirmacao else None,
                    'data_producao': mistura.data_producao.isoformat() if mistura.data_producao else None,
                    'data_entrega': mistura.data_entrega.isoformat() if mistura.data_entrega else None
                },
                'formula': {
                    'codigo': mistura.formula.codigo_formula,
                    'nome': mistura.formula.nome_formula,
                    'cor': mistura.formula.cor_definida.nome_cor if mistura.formula.cor_definida else None
                },
                'volume': {
                    'solicitado': float(mistura.volume_solicitado),
                    'produzido': float(mistura.volume_produzido) if mistura.volume_produzido else None
                },
                'custos': {
                    'base': float(mistura.custo_base),
                    'pigmentos': float(mistura.custo_pigmentos),
                    'total': float(mistura.custo_total)
                },
                'cliente': {
                    'nome': mistura.cliente_nome,
                    'documento': mistura.cliente_documento,
                    'telefone': mistura.cliente_telefone,
                    'email': mistura.cliente_email
                },
                'loja': {
                    'id': mistura.loja.id,
                    'nome': mistura.loja.nome
                },
                'operador': {
                    'nome': mistura.usuario_operacao.get_full_name(),
                    'username': mistura.usuario_operacao.username
                }
            }
            
            # Itens detalhados
            status['pigmentos'] = []
            for item in mistura.itens.all():
                pigment_info = {
                    'pigmento': {
                        'codigo': item.pigmento.codigo,
                        'nome': item.pigmento.nome,
                        'cor_base': item.pigmento.cor_base
                    },
                    'quantidades': {
                        'calculada': float(item.quantidade_calculada),
                        'executada': float(item.quantidade_executada) if item.quantidade_executada else None,
                        'final': float(item.quantidade_final)
                    },
                    'custos': {
                        'unitario': float(item.custo_unitario),
                        'total': float(item.custo_total)
                    },
                    'lote': item.lote_utilizado,
                    'sequencia': item.sequencia
                }
                
                if item.quantidade_executada:
                    pigment_info['variacao_percentual'] = float(item.variacao_percentual)
                
                status['pigmentos'].append(pigment_info)
            
            # Etiqueta se existir
            try:
                etiqueta = mistura.etiqueta
                status['etiqueta'] = {
                    'codigo': etiqueta.codigo_etiqueta,
                    'impressa': etiqueta.impressa,
                    'data_impressao': etiqueta.data_impressao.isoformat() if etiqueta.data_impressao else None,
                    'reimpressoes': etiqueta.reimpressoes
                }
            except EtiquetaMistura.DoesNotExist:
                status['etiqueta'] = None
            
            # Análise de progresso
            status['progresso'] = self._calculate_mixture_progress(mistura)
            
            return status
            
        except MisturaTinta.DoesNotExist:
            raise ValidationError(f"Mistura não encontrada: {mixture_id}")
    
    def search_mixtures(
        self,
        loja_id: int = None,
        customer_phone: str = None,
        color_code: str = None,
        date_from: str = None,
        date_to: str = None,
        situations: List[str] = None,
        limit: int = 50
    ) -> Dict:
        """
        Busca misturas com filtros
        
        Returns:
            Dict: Resultados da busca
        """
        query = MisturaTinta.objects.select_related(
            'formula', 'formula__cor_definida', 'loja'
        ).all()
        
        # Aplicar filtros
        if loja_id:
            query = query.filter(loja_id=loja_id)
        
        if customer_phone:
            query = query.filter(cliente_telefone__icontains=customer_phone)
        
        if color_code and query.model.objects.filter(
            formula__cor_definida__codigo_cor__icontains=color_code
        ).exists():
            query = query.filter(formula__cor_definida__codigo_cor__icontains=color_code)
        
        if date_from:
            query = query.filter(created_at__date__gte=date_from)
        
        if date_to:
            query = query.filter(created_at__date__lte=date_to)
        
        if situations:
            query = query.filter(situacao__in=situations)
        
        # Ordenar e limitar
        query = query.order_by('-created_at')[:limit]
        
        results = []
        for mistura in query:
            results.append({
                'id': str(mistura.id),
                'codigo': mistura.codigo_mistura,
                'situacao': mistura.situacao,
                'cliente_nome': mistura.cliente_nome,
                'cliente_telefone': mistura.cliente_telefone,
                'formula_nome': mistura.formula.nome_formula,
                'cor_nome': mistura.formula.cor_definida.nome_cor if mistura.formula.cor_definida else None,
                'volume': float(mistura.volume_solicitado),
                'custo_total': float(mistura.custo_total),
                'loja_nome': mistura.loja.nome,
                'created_at': mistura.created_at.isoformat(),
                'data_entrega': mistura.data_entrega.isoformat() if mistura.data_entrega else None
            })
        
        return {
            'total_results': len(results),
            'misturas': results,
            'filters_applied': {
                'loja_id': loja_id,
                'customer_phone': customer_phone,
                'color_code': color_code,
                'date_from': date_from,
                'date_to': date_to,
                'situations': situations
            }
        }
    
    def _validate_formula(self, formula_id: str) -> FormulaTintometrica:
        """Valida e obtém fórmula"""
        try:
            return FormulaTintometrica.objects.select_related('cor_definida', 'base_produto').get(
                id=formula_id, 
                ativa=True
            )
        except FormulaTintometrica.DoesNotExist:
            raise ValidationError(f"Fórmula não encontrada ou inativa: {formula_id}")
    
    def _validate_user(self, user_id: str) -> User:
        """Valida e obtém usuário"""
        try:
            return User.objects.get(id=user_id, ativo=True)
        except User.DoesNotExist:
            raise ValidationError(f"Usuário não encontrado ou inativo: {user_id}")
    
    def _create_mixture_label(self, mistura: MisturaTinta) -> EtiquetaMistura:
        """Cria etiqueta para a mistura"""
        etiqueta, created = EtiquetaMistura.objects.get_or_create(
            mistura=mistura,
            defaults={
                'titulo_personalizado': f"Tinta {mistura.formula.cor_definida.nome_cor if mistura.formula.cor_definida else 'Personalizada'}",
                'observacoes_etiqueta': f"{mistura.volume_solicitado}L - {mistura.created_at.strftime('%d/%m/%Y')}"
            }
        )
        return etiqueta
    
    def _analyze_execution_variations(self, mistura: MisturaTinta) -> Dict:
        """Analisa variações entre quantidades calculadas e executadas"""
        analysis = {
            'total_items': mistura.itens.count(),
            'items_with_variations': 0,
            'average_variation': 0,
            'max_variation': 0,
            'variations_details': []
        }
        
        variations = []
        
        for item in mistura.itens.all():
            if item.quantidade_executada:
                variation = item.variacao_percentual
                variations.append(abs(variation))
                
                if abs(variation) > 1:  # Variação > 1%
                    analysis['items_with_variations'] += 1
                    analysis['variations_details'].append({
                        'pigmento': item.pigmento.nome,
                        'calculada': float(item.quantidade_calculada),
                        'executada': float(item.quantidade_executada),
                        'variacao_percent': round(variation, 2)
                    })
        
        if variations:
            analysis['average_variation'] = round(sum(variations) / len(variations), 2)
            analysis['max_variation'] = round(max(variations), 2)
        
        return analysis
    
    def _evaluate_color_quality(self, mistura: MisturaTinta) -> Dict:
        """Avalia qualidade da cor produzida"""
        if not mistura.formula.cor_definida:
            return {"error": "Cor alvo não definida para avaliação"}
        
        target_lab = (
            mistura.formula.cor_definida.l_value,
            mistura.formula.cor_definida.a_value,
            mistura.formula.cor_definida.b_value
        )
        
        # Para este exemplo, assumimos que a cor executada é próxima da alvo
        # Em um sistema real, isso viria de medições colorimétricas
        achieved_lab = target_lab  # Simplificação
        
        evaluation = self.color_science.evaluate_color_match(
            target_lab, achieved_lab, 'COMERCIAL'
        )
        
        return evaluation
    
    def _update_customer_history(self, mistura: MisturaTinta) -> Dict:
        """Atualiza histórico de cores do cliente"""
        # Buscar misturas anteriores do cliente
        customer_history = MisturaTinta.objects.filter(
            cliente_telefone=mistura.cliente_telefone,
            situacao='ENTREGUE'
        ).select_related('formula__cor_definida').order_by('-created_at')[:5]
        
        history_data = {
            'cliente': {
                'nome': mistura.cliente_nome,
                'telefone': mistura.cliente_telefone,
                'total_misturas': customer_history.count()
            },
            'cores_preferidas': [],
            'volume_total_historico': Decimal('0'),
            'valor_total_historico': Decimal('0')
        }
        
        cores_contagem = {}
        
        for hist_mistura in customer_history:
            # Contar cores
            cor_nome = hist_mistura.formula.cor_definida.nome_cor if hist_mistura.formula.cor_definida else 'Personalizada'
            cores_contagem[cor_nome] = cores_contagem.get(cor_nome, 0) + 1
            
            # Somar volumes e valores
            history_data['volume_total_historico'] += hist_mistura.volume_solicitado
            history_data['valor_total_historico'] += hist_mistura.custo_total
        
        # Cores mais usadas
        history_data['cores_preferidas'] = sorted(
            cores_contagem.items(),
            key=lambda x: x[1],
            reverse=True
        )[:3]
        
        # Converter Decimals para float
        history_data['volume_total_historico'] = float(history_data['volume_total_historico'])
        history_data['valor_total_historico'] = float(history_data['valor_total_historico'])
        
        return history_data
    
    def _calculate_mixture_progress(self, mistura: MisturaTinta) -> Dict:
        """Calcula progresso da mistura"""
        progress_stages = {
            'CALCULADA': {'step': 1, 'total': 4, 'percentage': 25, 'description': 'Fórmula calculada'},
            'CONFIRMADA': {'step': 2, 'total': 4, 'percentage': 50, 'description': 'Mistura confirmada, estoque reservado'},
            'PRODUZIDA': {'step': 3, 'total': 4, 'percentage': 75, 'description': 'Mistura executada'},
            'ENTREGUE': {'step': 4, 'total': 4, 'percentage': 100, 'description': 'Entregue ao cliente'},
            'CANCELADA': {'step': 0, 'total': 4, 'percentage': 0, 'description': 'Cancelada'}
        }
        
        current_progress = progress_stages.get(mistura.situacao, {
            'step': 0, 'total': 4, 'percentage': 0, 'description': 'Status desconhecido'
        })
        
        # Calcular tempo decorrido
        if mistura.data_entrega:
            total_time = (mistura.data_entrega - mistura.created_at).total_seconds() / 3600
        else:
            total_time = (timezone.now() - mistura.created_at).total_seconds() / 3600
        
        return {
            'current_stage': mistura.situacao,
            'step': current_progress['step'],
            'total_steps': current_progress['total'],
            'percentage': current_progress['percentage'],
            'description': current_progress['description'],
            'time_elapsed_hours': round(total_time, 1),
            'is_completed': mistura.situacao == 'ENTREGUE',
            'is_cancelled': mistura.situacao == 'CANCELADA'
        }
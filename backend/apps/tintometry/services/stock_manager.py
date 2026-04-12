"""
Stock Manager Service

Handles all stock management operations for tintometric pigments:
- Real-time stock validation
- Automatic stock alerts and notifications
- Stock movement tracking and auditing
- Reorder point management
- Batch/lot tracking
"""

from decimal import Decimal, ROUND_HALF_UP
from typing import Dict, List, Optional, Tuple
from datetime import datetime, date, timedelta
import logging

from django.db import transaction
from django.utils import timezone
from django.db.models import Sum, Q, F
from django.core.exceptions import ValidationError

from ..models import (
    EstoquePigmento,
    Pigmento, 
    MisturaTinta,
    ItemMistura
)

logger = logging.getLogger(__name__)


class StockManagerService:
    """Serviço para gerenciamento de estoque de pigmentos tintométricos"""
    
    def __init__(self):
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
    
    def validate_stock_availability(
        self, 
        pigment_requirements: List[Dict], 
        loja_id: int
    ) -> Tuple[bool, Dict]:
        """
        Valida se há estoque suficiente para todos os pigmentos necessários
        
        Args:
            pigment_requirements: Lista com [{'pigmento_id': int, 'quantidade': Decimal}]
            loja_id: ID da loja
            
        Returns:
            Tuple[bool, Dict]: (disponível, relatório_detalhado)
        """
        self.logger.info(f"Validando estoque para {len(pigment_requirements)} pigmentos na loja {loja_id}")
        
        validation_report = {
            'disponivel': True,
            'pigmentos': [],
            'resumo': {
                'total_pigmentos': len(pigment_requirements),
                'disponiveis': 0,
                'insuficientes': 0,
                'criticos': 0,
                'valor_total_necessario': Decimal('0')
            }
        }
        
        for requirement in pigment_requirements:
            pigmento_id = requirement['pigmento_id']
            quantidade_necessaria = Decimal(str(requirement['quantidade']))
            
            # Verificar estoque
            try:
                estoque = EstoquePigmento.objects.select_related('pigmento').get(
                    pigmento_id=pigmento_id,
                    loja_id=loja_id,
                    ativo=True
                )
                
                disponivel = estoque.saldo_ml >= quantidade_necessaria
                valor_necessario = quantidade_necessaria * estoque.custo_ml
                
                pigment_info = {
                    'pigmento': {
                        'id': estoque.pigmento.id,
                        'codigo': estoque.pigmento.codigo,
                        'nome': estoque.pigmento.nome,
                        'cor_base': estoque.pigmento.cor_base
                    },
                    'estoque': {
                        'saldo_atual': estoque.saldo_ml,
                        'quantidade_necessaria': quantidade_necessaria,
                        'disponivel': disponivel,
                        'sobra_apos_uso': estoque.saldo_ml - quantidade_necessaria,
                        'estoque_critico': estoque.estoque_critico,
                        'percentual_uso': float((quantidade_necessaria / estoque.saldo_ml) * 100) if estoque.saldo_ml > 0 else 0
                    },
                    'custo': {
                        'unitario': estoque.custo_ml,
                        'total_necessario': valor_necessario
                    },
                    'lote': {
                        'atual': estoque.lote_atual,
                        'validade': estoque.validade_lote.isoformat() if estoque.validade_lote else None,
                        'dias_para_vencer': self._calcular_dias_validade(estoque.validade_lote)
                    },
                    'alertas': self._get_stock_alerts(estoque, quantidade_necessaria)
                }
                
                validation_report['pigmentos'].append(pigment_info)
                validation_report['resumo']['valor_total_necessario'] += valor_necessario
                
                if disponivel:
                    validation_report['resumo']['disponiveis'] += 1
                else:
                    validation_report['resumo']['insuficientes'] += 1
                    validation_report['disponivel'] = False
                
                if estoque.estoque_critico:
                    validation_report['resumo']['criticos'] += 1
                
            except EstoquePigmento.DoesNotExist:
                self.logger.warning(f"Estoque não encontrado - Pigmento ID: {pigmento_id}, Loja: {loja_id}")
                
                # Adicionar informação de pigmento não cadastrado
                try:
                    pigmento = Pigmento.objects.get(id=pigmento_id)
                    pigment_info = {
                        'pigmento': {
                            'id': pigmento.id,
                            'codigo': pigmento.codigo,
                            'nome': pigmento.nome,
                            'cor_base': pigmento.cor_base
                        },
                        'estoque': {
                            'saldo_atual': Decimal('0'),
                            'quantidade_necessaria': quantidade_necessaria,
                            'disponivel': False,
                            'sobra_apos_uso': -quantidade_necessaria,
                            'estoque_critico': True,
                            'percentual_uso': 0
                        },
                        'error': 'Estoque não cadastrado para esta loja'
                    }
                    
                    validation_report['pigmentos'].append(pigment_info)
                    validation_report['resumo']['insuficientes'] += 1
                    validation_report['disponivel'] = False
                    
                except Pigmento.DoesNotExist:
                    self.logger.error(f"Pigmento não encontrado - ID: {pigmento_id}")
        
        self.logger.info(
            f"Validação concluída - Disponível: {validation_report['disponivel']}, "
            f"Pigmentos OK: {validation_report['resumo']['disponiveis']}/{validation_report['resumo']['total_pigmentos']}"
        )
        
        return validation_report['disponivel'], validation_report
    
    @transaction.atomic
    def reserve_stock(
        self, 
        pigment_requirements: List[Dict], 
        loja_id: int,
        reference_code: str = None
    ) -> Tuple[bool, List[str]]:
        """
        Reserva estoque para uma mistura (reduz saldo disponível)
        
        Args:
            pigment_requirements: Lista de requerimentos de pigmentos
            loja_id: ID da loja
            reference_code: Código de referência da mistura
            
        Returns:
            Tuple[bool, List[str]]: (sucesso, lista_de_erros)
        """
        errors = []
        
        try:
            self.logger.info(
                f"Iniciando reserva de estoque para {len(pigment_requirements)} pigmentos - "
                f"Referência: {reference_code}"
            )
            
            # Validar disponibilidade primeiro
            disponivel, validation_report = self.validate_stock_availability(
                pigment_requirements, loja_id
            )
            
            if not disponivel:
                errors.append("Estoque insuficiente detectado na pré-validação")
                for pigment in validation_report['pigmentos']:
                    if not pigment['estoque']['disponivel']:
                        errors.append(
                            f"{pigment['pigmento']['nome']}: necessário "
                            f"{pigment['estoque']['quantidade_necessaria']}ml, "
                            f"disponível {pigment['estoque']['saldo_atual']}ml"
                        )
                return False, errors
            
            # Efetuar as reservas
            reservas_realizadas = []
            
            for requirement in pigment_requirements:
                pigmento_id = requirement['pigmento_id']
                quantidade = Decimal(str(requirement['quantidade']))
                
                # Obter estoque com lock para evitar race conditions
                estoque = EstoquePigmento.objects.select_for_update().get(
                    pigmento_id=pigmento_id,
                    loja_id=loja_id,
                    ativo=True
                )
                
                # Verificar novamente (pode ter mudado desde a validação)
                if estoque.saldo_ml < quantidade:
                    errors.append(
                        f"Estoque alterado durante reserva - {estoque.pigmento.nome}: "
                        f"necessário {quantidade}ml, disponível {estoque.saldo_ml}ml"
                    )
                    # Rollback será automático devido ao @transaction.atomic
                    return False, errors
                
                # Salvar estado anterior para possível rollback manual
                saldo_anterior = estoque.saldo_ml
                
                # Efetuar a redução
                success = estoque.reduzir_estoque(
                    quantidade=quantidade,
                    lote=estoque.lote_atual
                )
                
                if success:
                    reservas_realizadas.append({
                        'estoque_id': estoque.id,
                        'pigmento': estoque.pigmento.nome,
                        'quantidade_reservada': quantidade,
                        'saldo_anterior': saldo_anterior,
                        'saldo_atual': estoque.saldo_ml
                    })
                    
                    self.logger.debug(
                        f"Reserva realizada - {estoque.pigmento.nome}: "
                        f"{quantidade}ml (saldo: {saldo_anterior} → {estoque.saldo_ml})"
                    )
                else:
                    errors.append(f"Falha ao reduzir estoque para {estoque.pigmento.nome}")
                    return False, errors
            
            self.logger.info(
                f"Reserva de estoque concluída com sucesso - "
                f"{len(reservas_realizadas)} pigmentos reservados"
            )
            
            return True, []
            
        except Exception as e:
            self.logger.error(f"Erro durante reserva de estoque: {str(e)}")
            return False, [f"Erro interno na reserva: {str(e)}"]
    
    def get_stock_status(self, loja_id: int, pigmento_ids: List[int] = None) -> Dict:
        """
        Obtém status detalhado de estoque para pigmentos específicos ou todos
        
        Args:
            loja_id: ID da loja
            pigmento_ids: Lista de IDs de pigmentos (None para todos)
            
        Returns:
            Dict: Status detalhado do estoque
        """
        query = EstoquePigmento.objects.select_related('pigmento').filter(
            loja_id=loja_id,
            ativo=True
        )
        
        if pigmento_ids:
            query = query.filter(pigmento_id__in=pigmento_ids)
        
        estoques = query.all()
        
        status = {
            'loja_id': loja_id,
            'timestamp': timezone.now().isoformat(),
            'pigmentos': [],
            'resumo': {
                'total_pigmentos': estoques.count(),
                'criticos': 0,
                'alertas_ativas': 0,
                'sem_estoque': 0,
                'valor_total_estoque': Decimal('0'),
                'vencimentos_proximos': 0
            }
        }
        
        for estoque in estoques:
            pigment_status = {
                'pigmento': {
                    'id': estoque.pigmento.id,
                    'codigo': estoque.pigmento.codigo,
                    'nome': estoque.pigmento.nome,
                    'cor_base': estoque.pigmento.cor_base,
                    'densidade': float(estoque.pigmento.densidade)
                },
                'estoque': {
                    'saldo_ml': float(estoque.saldo_ml),
                    'saldo_minimo': float(estoque.saldo_minimo),
                    'saldo_maximo': float(estoque.saldo_maximo),
                    'percentual_estoque': float(estoque.percentual_estoque),
                    'estoque_critico': estoque.estoque_critico,
                    'valor_total': float(estoque.valor_total_estoque)
                },
                'custo': {
                    'por_ml': float(estoque.custo_ml),
                    'data_ultimo_custo': estoque.data_ultimo_custo.isoformat()
                },
                'lote': {
                    'atual': estoque.lote_atual,
                    'validade': estoque.validade_lote.isoformat() if estoque.validade_lote else None,
                    'dias_para_vencer': self._calcular_dias_validade(estoque.validade_lote)
                },
                'alertas': {
                    'alerta_ativo': estoque.alerta_ativo,
                    'data_ultimo_alerta': estoque.data_ultimo_alerta.isoformat() if estoque.data_ultimo_alerta else None,
                    'reposicao_solicitada': estoque.reposicao_solicitada
                }
            }
            
            status['pigmentos'].append(pigment_status)
            
            # Atualizar resumo
            status['resumo']['valor_total_estoque'] += estoque.valor_total_estoque
            
            if estoque.estoque_critico:
                status['resumo']['criticos'] += 1
            
            if estoque.alerta_ativo:
                status['resumo']['alertas_ativas'] += 1
            
            if estoque.saldo_ml <= 0:
                status['resumo']['sem_estoque'] += 1
            
            if pigment_status['lote']['dias_para_vencer'] and pigment_status['lote']['dias_para_vencer'] <= 30:
                status['resumo']['vencimentos_proximos'] += 1
        
        # Converter Decimal para float no resumo
        status['resumo']['valor_total_estoque'] = float(status['resumo']['valor_total_estoque'])
        
        return status
    
    @transaction.atomic
    def add_stock(
        self, 
        loja_id: int,
        pigmento_id: int,
        quantidade: Decimal,
        custo_unitario: Decimal,
        lote: str = None,
        validade: date = None,
        observacoes: str = None
    ) -> Tuple[bool, str]:
        """
        Adiciona estoque para um pigmento
        
        Returns:
            Tuple[bool, str]: (sucesso, mensagem)
        """
        try:
            estoque, created = EstoquePigmento.objects.get_or_create(
                pigmento_id=pigmento_id,
                loja_id=loja_id,
                defaults={
                    'custo_ml': custo_unitario,
                    'lote_atual': lote,
                    'validade_lote': validade
                }
            )
            
            # Adicionar estoque
            estoque.adicionar_estoque(
                quantidade=quantidade,
                custo_unitario=custo_unitario,
                lote=lote,
                validade=validade
            )
            
            action = "criado" if created else "atualizado"
            message = (
                f"Estoque {action} com sucesso - "
                f"{estoque.pigmento.nome}: +{quantidade}ml "
                f"(saldo atual: {estoque.saldo_ml}ml)"
            )
            
            self.logger.info(message)
            return True, message
            
        except Exception as e:
            error_msg = f"Erro ao adicionar estoque: {str(e)}"
            self.logger.error(error_msg)
            return False, error_msg
    
    def get_low_stock_alerts(self, loja_id: int = None) -> Dict:
        """
        Obtém alertas de estoque baixo
        
        Args:
            loja_id: ID da loja específica (None para todas)
            
        Returns:
            Dict: Alertas de estoque baixo organizados
        """
        query = EstoquePigmento.objects.select_related('pigmento', 'loja').filter(
            estoque_critico=True,
            ativo=True
        )
        
        if loja_id:
            query = query.filter(loja_id=loja_id)
        
        estoques_criticos = query.order_by('loja__nome', 'pigmento__nome')
        
        alerts = {
            'timestamp': timezone.now().isoformat(),
            'total_alertas': estoques_criticos.count(),
            'por_loja': {},
            'resumo': {
                'lojas_afetadas': 0,
                'pigmentos_unicos': 0,
                'valor_total_necessario': Decimal('0')
            }
        }
        
        lojas_afetadas = set()
        pigmentos_unicos = set()
        
        for estoque in estoques_criticos:
            loja_nome = estoque.loja.nome
            
            if loja_nome not in alerts['por_loja']:
                alerts['por_loja'][loja_nome] = {
                    'loja_id': estoque.loja.id,
                    'pigmentos': [],
                    'total_pigmentos': 0,
                    'valor_reposicao_sugerida': Decimal('0')
                }
            
            # Calcular quantidade sugerida para reposição (até o máximo)
            quantidade_sugerida = estoque.saldo_maximo - estoque.saldo_ml
            valor_reposicao = quantidade_sugerida * estoque.custo_ml
            
            pigment_alert = {
                'pigmento': {
                    'id': estoque.pigmento.id,
                    'codigo': estoque.pigmento.codigo,
                    'nome': estoque.pigmento.nome,
                    'cor_base': estoque.pigmento.cor_base
                },
                'estoque': {
                    'saldo_atual': float(estoque.saldo_ml),
                    'saldo_minimo': float(estoque.saldo_minimo),
                    'saldo_maximo': float(estoque.saldo_maximo),
                    'quantidade_sugerida': float(quantidade_sugerida),
                    'valor_reposicao': float(valor_reposicao)
                },
                'alerta': {
                    'ativo_desde': estoque.data_ultimo_alerta.isoformat() if estoque.data_ultimo_alerta else None,
                    'reposicao_solicitada': estoque.reposicao_solicitada,
                    'data_solicitacao': estoque.data_solicitacao_reposicao.isoformat() if estoque.data_solicitacao_reposicao else None
                }
            }
            
            alerts['por_loja'][loja_nome]['pigmentos'].append(pigment_alert)
            alerts['por_loja'][loja_nome]['total_pigmentos'] += 1
            alerts['por_loja'][loja_nome]['valor_reposicao_sugerida'] += valor_reposicao
            
            lojas_afetadas.add(estoque.loja.id)
            pigmentos_unicos.add(estoque.pigmento.id)
            alerts['resumo']['valor_total_necessario'] += valor_reposicao
        
        # Converter valores Decimal para float
        for loja_data in alerts['por_loja'].values():
            loja_data['valor_reposicao_sugerida'] = float(loja_data['valor_reposicao_sugerida'])
        
        alerts['resumo']['lojas_afetadas'] = len(lojas_afetadas)
        alerts['resumo']['pigmentos_unicos'] = len(pigmentos_unicos)
        alerts['resumo']['valor_total_necessario'] = float(alerts['resumo']['valor_total_necessario'])
        
        return alerts
    
    def _calcular_dias_validade(self, validade: date = None) -> Optional[int]:
        """Calcula dias restantes para validade"""
        if not validade:
            return None
        
        hoje = timezone.now().date()
        dias_restantes = (validade - hoje).days
        
        return dias_restantes if dias_restantes >= 0 else 0
    
    def _get_stock_alerts(self, estoque: EstoquePigmento, quantidade_uso: Decimal) -> List[str]:
        """Gera alertas específicos para um estoque"""
        alerts = []
        
        # Alerta de estoque baixo
        if estoque.estoque_critico:
            alerts.append("CRÍTICO: Estoque abaixo do mínimo")
        
        # Alerta de uso que levará ao estoque crítico
        saldo_apos_uso = estoque.saldo_ml - quantidade_uso
        if saldo_apos_uso <= estoque.saldo_minimo and not estoque.estoque_critico:
            alerts.append("ATENÇÃO: Uso levará ao estoque crítico")
        
        # Alerta de validade
        dias_validade = self._calcular_dias_validade(estoque.validade_lote)
        if dias_validade is not None:
            if dias_validade <= 0:
                alerts.append("VENCIDO: Lote expirado")
            elif dias_validade <= 7:
                alerts.append(f"URGENTE: Vence em {dias_validade} dias")
            elif dias_validade <= 30:
                alerts.append(f"ATENÇÃO: Vence em {dias_validade} dias")
        
        # Alerta de uso excessivo
        if quantidade_uso > 0 and estoque.saldo_ml > 0:
            percentual_uso = (quantidade_uso / estoque.saldo_ml) * 100
            if percentual_uso > 50:
                alerts.append(f"USO ALTO: {percentual_uso:.1f}% do estoque")
        
        return alerts
    
    def get_stock_movement_history(
        self, 
        loja_id: int,
        pigmento_id: int = None,
        days_back: int = 30
    ) -> List[Dict]:
        """
        Obtém histórico de movimentação de estoque baseado nas misturas
        
        Args:
            loja_id: ID da loja
            pigmento_id: ID do pigmento específico (None para todos)
            days_back: Quantos dias para trás buscar
            
        Returns:
            List[Dict]: Histórico de movimentações
        """
        data_inicio = timezone.now() - timedelta(days=days_back)
        
        # Buscar itens de misturas que afetaram o estoque
        query = ItemMistura.objects.select_related(
            'mistura', 'pigmento', 'mistura__loja'
        ).filter(
            mistura__loja_id=loja_id,
            mistura__created_at__gte=data_inicio,
            mistura__situacao__in=['CONFIRMADA', 'PRODUZIDA', 'ENTREGUE']
        ).order_by('-mistura__created_at')
        
        if pigmento_id:
            query = query.filter(pigmento_id=pigmento_id)
        
        movements = []
        
        for item in query:
            movement = {
                'data': item.mistura.created_at.isoformat(),
                'tipo': 'SAIDA',
                'referencia': item.mistura.codigo_mistura,
                'pigmento': {
                    'id': item.pigmento.id,
                    'codigo': item.pigmento.codigo,
                    'nome': item.pigmento.nome
                },
                'quantidade': float(item.quantidade_final),
                'saldo_anterior': float(item.estoque_antes) if item.estoque_antes else None,
                'saldo_posterior': float(item.estoque_depois) if item.estoque_depois else None,
                'custo_unitario': float(item.custo_unitario),
                'custo_total': float(item.custo_total),
                'lote_utilizado': item.lote_utilizado,
                'cliente': item.mistura.cliente_nome,
                'operador': item.mistura.usuario_operacao.get_full_name()
            }
            
            movements.append(movement)
        
        return movements
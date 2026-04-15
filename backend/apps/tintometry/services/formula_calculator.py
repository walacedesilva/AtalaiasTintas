"""
Formula Calculator Service

Handles all mathematical calculations for tintometric mixing:
- Proportional scaling based on desired volume
- Density corrections for accurate measurements  
- Precision rounding to 0.1ml accuracy
- Cost calculations with real-time pricing
"""

from decimal import Decimal, ROUND_HALF_UP
from typing import Dict, List, Tuple, Optional
import logging

from django.db import transaction
from django.utils import timezone

from ..models import (
    FormulaTintometrica, 
    ItemFormula, 
    EstoquePigmento, 
    MisturaTinta, 
    ItemMistura,
    Pigmento
)

logger = logging.getLogger(__name__)


class FormulaCalculatorService:
    """Serviço para cálculos científicos de fórmulas tintométricas"""
    
    # Constantes para cálculos científicos
    PRECISION_ML = Decimal('0.1')  # Precisão de 0.1ml
    PRECISION_COST = Decimal('0.0001')  # Precisão de custo 4 casas
    MAX_VARIATION_PERCENT = Decimal('5.0')  # 5% máximo de variação
    
    def __init__(self):
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
    
    def calculate_mixture_quantities(
        self, 
        formula: FormulaTintometrica, 
        target_volume: Decimal,
        loja_id: int,
        validate_stock: bool = True
    ) -> Dict:
        """
        Calcula quantidades de pigmentos para um volume específico
        
        Args:
            formula: Fórmula tintométrica a ser calculada
            target_volume: Volume desejado em litros
            loja_id: ID da loja para verificação de estoque
            validate_stock: Se deve validar disponibilidade de estoque
            
        Returns:
            Dict com resultado do cálculo incluindo quantidades, custos e validações
        """
        self.logger.info(
            f"Iniciando cálculo - Fórmula: {formula.codigo_formula}, "
            f"Volume: {target_volume}L, Loja: {loja_id}"
        )
        
        try:
            # Calcular fator de proporção
            proportion_factor = self._calculate_proportion_factor(formula, target_volume)
            
            # Obter itens da fórmula
            formula_items = formula.itens.select_related('pigmento').all()
            
            if not formula_items.exists():
                raise ValueError(f"Fórmula {formula.codigo_formula} não possui pigmentos definidos")
            
            # Calcular quantidades para cada pigmento
            calculation_results = []
            total_pigment_cost = Decimal('0')
            
            for item in formula_items:
                item_result = self._calculate_item_quantity(
                    item, 
                    proportion_factor, 
                    loja_id,
                    validate_stock
                )
                calculation_results.append(item_result)
                total_pigment_cost += Decimal(str(item_result['custos']['total']))
            
            # Calcular custo da base
            base_cost = self._calculate_base_cost(formula, target_volume)
            
            # Resultado final
            result = {
                'formula': {
                    'id': str(formula.id),
                    'codigo': formula.codigo_formula,
                    'nome': formula.nome_formula,
                    'volume_base': formula.volume_base,
                    'cor': formula.cor_definida.nome_cor if formula.cor_definida else None
                },
                'volume': {
                    'solicitado': target_volume,
                    'base_formula': formula.volume_base,
                    'fator_proporcao': proportion_factor
                },
                'pigmentos': calculation_results,
                'custos': {
                    'base': base_cost,
                    'pigmentos': total_pigment_cost,
                    'total': base_cost + total_pigment_cost
                },
                'validacao': {
                    'stock_ok': all(item['stock_available'] for item in calculation_results),
                    'total_pigmentos': len(calculation_results),
                    'warnings': self._generate_warnings(calculation_results)
                },
                'timestamp': timezone.now().isoformat()
            }
            
            self.logger.info(
                f"Cálculo concluído - Custo total: R${result['custos']['total']}, "
                f"Pigmentos: {len(calculation_results)}"
            )
            
            return result
            
        except Exception as e:
            self.logger.error(f"Erro no cálculo da fórmula: {str(e)}")
            raise
    
    def _calculate_proportion_factor(
        self, 
        formula: FormulaTintometrica, 
        target_volume: Decimal
    ) -> Decimal:
        """Calcula o fator de proporção entre volume desejado e volume base"""
        if formula.volume_base <= 0:
            raise ValueError(f"Volume base da fórmula deve ser maior que zero: {formula.volume_base}")
        
        factor = target_volume / formula.volume_base
        
        # Log para auditoria científica
        self.logger.debug(
            f"Fator de proporção calculado: {factor} "
            f"(Volume alvo: {target_volume}L / Volume base: {formula.volume_base}L)"
        )
        
        return factor
    
    def _calculate_item_quantity(
        self,
        item: ItemFormula,
        proportion_factor: Decimal,
        loja_id: int,
        validate_stock: bool
    ) -> Dict:
        """Calcula quantidade e custo para um item específico da fórmula"""
        
        # Quantidade proporcional bruta
        raw_quantity = item.quantidade * proportion_factor
        
        # Arredondamento para precisão de 0.1ml
        calculated_quantity = raw_quantity.quantize(self.PRECISION_ML, rounding=ROUND_HALF_UP)
        
        # Aplicar correção de densidade se necessário
        density_corrected_quantity = self._apply_density_correction(
            calculated_quantity,
            item.pigmento
        )
        
        # Obter informações de estoque
        stock_info = self._get_stock_info(item.pigmento, loja_id, validate_stock)
        
        # Verificar suficiência do estoque para a quantidade calculada
        if validate_stock:
            stock_info['sufficient'] = (
                Decimal(str(stock_info['saldo_atual'])) >= density_corrected_quantity
            )
        
        # Calcular custos
        unit_cost = stock_info['unit_cost']
        total_cost = (density_corrected_quantity * unit_cost).quantize(
            self.PRECISION_COST, 
            rounding=ROUND_HALF_UP
        )
        
        result = {
            'pigmento': {
                'id': item.pigmento.id,
                'codigo': item.pigmento.codigo,
                'nome': item.pigmento.nome,
                'cor_base': item.pigmento.cor_base,
                'densidade': float(item.pigmento.densidade),
                'poder_tintorial': float(item.pigmento.poder_tintorial)
            },
            'quantidades': {
                'formula_base': float(item.quantidade),
                'calculada_bruta': float(raw_quantity),
                'calculada_final': float(density_corrected_quantity),
                'precisao_ml': float(self.PRECISION_ML)
            },
            'custos': {
                'unitario': float(unit_cost),
                'total': float(total_cost)
            },
            'estoque': stock_info,
            'stock_available': stock_info['sufficient'],
            'sequencia': item.sequencia,
            'observacoes': item.observacoes
        }
        
        self.logger.debug(
            f"Item calculado - {item.pigmento.nome}: "
            f"{density_corrected_quantity}ml, R${total_cost}"
        )
        
        return result
    
    def _apply_density_correction(
        self, 
        quantity: Decimal, 
        pigmento: Pigmento
    ) -> Decimal:
        """
        Aplica correção de densidade para medições precisas
        
        A densidade afeta o volume real ocupado pelo pigmento,
        permitindo cálculos mais precisos para pigmentos com 
        densidades significativamente diferentes.
        """
        if not pigmento.densidade or pigmento.densidade <= 0:
            self.logger.warning(
                f"Densidade inválida para pigmento {pigmento.codigo}: {pigmento.densidade}"
            )
            return quantity
        
        # Densidade de referência (água = 1.0 g/cm³)
        reference_density = Decimal('1.0')
        
        # Correção baseada na diferença de densidade
        # Para pigmentos mais densos, o volume real será menor
        if abs(pigmento.densidade - reference_density) > Decimal('0.1'):
            correction_factor = reference_density / pigmento.densidade
            corrected_quantity = quantity * correction_factor
            
            self.logger.debug(
                f"Correção de densidade aplicada - {pigmento.nome}: "
                f"Original: {quantity}ml, Corrigido: {corrected_quantity}ml "
                f"(Densidade: {pigmento.densidade})"
            )
            
            return corrected_quantity.quantize(self.PRECISION_ML, rounding=ROUND_HALF_UP)
        
        return quantity
    
    def _get_stock_info(
        self, 
        pigmento: Pigmento, 
        loja_id: int,
        validate_stock: bool
    ) -> Dict:
        """Obtém informações de estoque para o pigmento na loja específica"""
        try:
            estoque = EstoquePigmento.objects.get(
                pigmento=pigmento,
                loja_id=loja_id,
                ativo=True
            )
            
            return {
                'saldo_atual': float(estoque.saldo_ml),
                'saldo_minimo': float(estoque.saldo_minimo),
                'unit_cost': estoque.custo_ml,
                'lote_atual': estoque.lote_atual,
                'validade': estoque.validade_lote.isoformat() if estoque.validade_lote else None,
                'sufficient': True,  # Será calculado na validação de estoque
                'estoque_critico': estoque.estoque_critico,
                'alerta_ativo': estoque.alerta_ativo,
                'valor_total': float(estoque.valor_total_estoque)
            }
            
        except EstoquePigmento.DoesNotExist:
            self.logger.warning(
                f"Estoque não encontrado - Pigmento: {pigmento.codigo}, Loja: {loja_id}"
            )
            return {
                'saldo_atual': 0.0,
                'saldo_minimo': 0.0,
                'unit_cost': Decimal('0'),
                'lote_atual': None,
                'validade': None,
                'sufficient': False,
                'estoque_critico': True,
                'alerta_ativo': True,
                'valor_total': 0.0,
                'error': 'Estoque não cadastrado para esta loja'
            }
    
    def _calculate_base_cost(
        self, 
        formula: FormulaTintometrica, 
        target_volume: Decimal
    ) -> Decimal:
        """Calcula o custo da base para o volume desejado"""
        if not formula.base_produto:
            self.logger.warning(
                f"Fórmula {formula.codigo_formula} não possui produto base definido"
            )
            return Decimal('0')
        
        try:
            # Custo por litro da base
            base_cost_per_liter = formula.base_produto.preco_custo or Decimal('0')
            
            # Custo total proporcional
            total_base_cost = base_cost_per_liter * target_volume
            
            return total_base_cost.quantize(self.PRECISION_COST, rounding=ROUND_HALF_UP)
            
        except Exception as e:
            self.logger.error(f"Erro no cálculo do custo da base: {str(e)}")
            return Decimal('0')
    
    def _generate_warnings(self, calculation_results: List[Dict]) -> List[str]:
        """Gera avisos baseados nos resultados dos cálculos"""
        warnings = []
        
        for result in calculation_results:
            # Verificar estoque
            if not result['stock_available']:
                warnings.append(
                    f"Estoque insuficiente para {result['pigmento']['nome']}: "
                    f"Necessário {result['quantidades']['calculada_final']}ml, "
                    f"Disponível {result['estoque']['saldo_atual']}ml"
                )
            
            # Verificar estoque crítico
            elif result['estoque']['estoque_critico']:
                warnings.append(
                    f"Estoque crítico para {result['pigmento']['nome']}: "
                    f"Saldo atual {result['estoque']['saldo_atual']}ml está "
                    f"abaixo do mínimo {result['estoque']['saldo_minimo']}ml"
                )
            
            # Verificar validade do lote
            if result['estoque']['validade']:
                from datetime import datetime
                try:
                    validade = datetime.fromisoformat(result['estoque']['validade']).date()
                    hoje = timezone.now().date()
                    dias_restantes = (validade - hoje).days
                    
                    if dias_restantes <= 30:
                        warnings.append(
                            f"Lote próximo ao vencimento para {result['pigmento']['nome']}: "
                            f"Validade {validade.strftime('%d/%m/%Y')} ({dias_restantes} dias)"
                        )
                except Exception:
                    pass
        
        return warnings
    
    @transaction.atomic
    def validate_and_reserve_stock(
        self, 
        calculation_results: Dict, 
        loja_id: int
    ) -> Tuple[bool, List[str]]:
        """
        Valida disponibilidade e reserva estoque para a mistura
        
        Returns:
            Tuple[bool, List[str]]: (sucesso, lista_de_erros)
        """
        errors = []
        
        try:
            # Verificar disponibilidade de todos os pigmentos primeiro
            for pigment_result in calculation_results['pigmentos']:
                required_quantity = Decimal(str(pigment_result['quantidades']['calculada_final']))
                available_quantity = Decimal(str(pigment_result['estoque']['saldo_atual']))
                
                if required_quantity > available_quantity:
                    errors.append(
                        f"Estoque insuficiente para {pigment_result['pigmento']['nome']}: "
                        f"Necessário {required_quantity}ml, Disponível {available_quantity}ml"
                    )
            
            if errors:
                return False, errors
            
            # Se tudo OK, fazer a reserva (redução temporária do estoque)
            for pigment_result in calculation_results['pigmentos']:
                pigmento_id = pigment_result['pigmento']['id']
                required_quantity = Decimal(str(pigment_result['quantidades']['calculada_final']))
                
                estoque = EstoquePigmento.objects.select_for_update().get(
                    pigmento_id=pigmento_id,
                    loja_id=loja_id
                )
                
                success = estoque.reduzir_estoque(required_quantity)
                if not success:
                    errors.append(
                        f"Falha ao reservar estoque para {pigment_result['pigmento']['nome']}"
                    )
            
            if errors:
                # Se houve erro, fazer rollback será automático pelo @transaction.atomic
                return False, errors
            
            self.logger.info(f"Estoque reservado com sucesso para {len(calculation_results['pigmentos'])} pigmentos")
            return True, []
            
        except Exception as e:
            self.logger.error(f"Erro na validação/reserva de estoque: {str(e)}")
            return False, [f"Erro interno: {str(e)}"]
    
    def calculate_cost_breakdown(self, calculation_results: Dict) -> Dict:
        """Calcula detalhamento completo de custos"""
        breakdown = {
            'base': calculation_results['custos']['base'],
            'pigmentos': {},
            'totals': {
                'pigmentos': calculation_results['custos']['pigmentos'],
                'base': calculation_results['custos']['base'],
                'geral': calculation_results['custos']['total']
            },
            'analysis': {}
        }
        
        # Detalhar custos por pigmento
        total_pigment_volume = Decimal('0')
        for pigment in calculation_results['pigmentos']:
            pigment_name = pigment['pigmento']['nome']
            pigment_cost = Decimal(str(pigment['custos']['total']))
            pigment_volume = Decimal(str(pigment['quantidades']['calculada_final']))
            
            breakdown['pigmentos'][pigment_name] = {
                'volume_ml': float(pigment_volume),
                'custo_total': float(pigment_cost),
                'custo_unitario': float(pigment['custos']['unitario']),
                'percentual_custo': float((pigment_cost / breakdown['totals']['geral']) * 100) if breakdown['totals']['geral'] > 0 else 0
            }
            
            total_pigment_volume += pigment_volume
        
        # Análise de custos
        breakdown['analysis'] = {
            'custo_por_litro': float(breakdown['totals']['geral'] / calculation_results['volume']['solicitado']),
            'percentual_base': float((breakdown['totals']['base'] / breakdown['totals']['geral']) * 100) if breakdown['totals']['geral'] > 0 else 0,
            'percentual_pigmentos': float((breakdown['totals']['pigmentos'] / breakdown['totals']['geral']) * 100) if breakdown['totals']['geral'] > 0 else 0,
            'volume_total_pigmentos_ml': float(total_pigment_volume),
            'densidade_media_pigmentos': float(total_pigment_volume / len(calculation_results['pigmentos'])) if calculation_results['pigmentos'] else 0
        }
        
        return breakdown
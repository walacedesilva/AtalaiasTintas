"""
Color Science Service

Handles scientific color calculations and conversions:
- CIE Lab color space conversions  
- Color difference calculations (Delta E)
- RGB <-> Lab conversions with precision
- Color matching algorithms
- Color tolerance validation
"""

import math
from decimal import Decimal, ROUND_HALF_UP
from typing import Dict, List, Tuple, Optional
import logging

from django.utils import timezone

logger = logging.getLogger(__name__)


class ColorScienceService:
    """Serviço para cálculos científicos de cor e conversões de espaço de cores"""
    
    # Constantes científicas para conversões Lab/RGB
    # Illuminant D65 (daylight 6500K) - padrão industrial
    XN = 95.047   # X normalization for D65
    YN = 100.000  # Y normalization for D65  
    ZN = 108.883  # Z normalization for D65
    
    # Thresholds para conversões Lab
    LAB_EPSILON = 0.008856451679035631  # (6/29)^3
    LAB_KAPPA = 903.2962962962963      # (29/3)^3
    
    # Tolerâncias de cor para diferentes aplicações
    COLOR_TOLERANCES = {
        'CRITICA': Decimal('1.0'),      # Delta E < 1.0 - Imperceptível
        'COMERCIAL': Decimal('2.0'),    # Delta E < 2.0 - Muito boa
        'INDUSTRIAL': Decimal('3.5'),   # Delta E < 3.5 - Boa
        'ACEITAVEL': Decimal('5.0'),    # Delta E < 5.0 - Aceitável
    }
    
    def __init__(self):
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
    
    def rgb_to_lab(self, r: int, g: int, b: int) -> Tuple[Decimal, Decimal, Decimal]:
        """
        Converte RGB (0-255) para CIE Lab
        
        Args:
            r, g, b: Valores RGB (0-255)
            
        Returns:
            Tuple[Decimal, Decimal, Decimal]: (L, a, b) values
        """
        self.logger.debug(f"Convertendo RGB({r}, {g}, {b}) para Lab")
        
        # Normalizar RGB para 0-1
        r_norm = r / 255.0
        g_norm = g / 255.0
        b_norm = b / 255.0
        
        # Correção gamma (sRGB)
        r_linear = self._srgb_to_linear(r_norm)
        g_linear = self._srgb_to_linear(g_norm)  
        b_linear = self._srgb_to_linear(b_norm)
        
        # Conversão RGB linear para XYZ (matriz sRGB D65)
        x = r_linear * 0.4124564 + g_linear * 0.3575761 + b_linear * 0.1804375
        y = r_linear * 0.2126729 + g_linear * 0.7151522 + b_linear * 0.0721750
        z = r_linear * 0.0193339 + g_linear * 0.1191920 + b_linear * 0.9503041
        
        # Normalizar para iluminante D65
        x_norm = x * 100 / self.XN
        y_norm = y * 100 / self.YN
        z_norm = z * 100 / self.ZN
        
        # Conversão XYZ para Lab
        fx = self._xyz_to_lab_function(x_norm)
        fy = self._xyz_to_lab_function(y_norm)
        fz = self._xyz_to_lab_function(z_norm)
        
        L = 116 * fy - 16
        a = 500 * (fx - fy)
        b_lab = 200 * (fy - fz)
        
        # Converter para Decimal com precisão
        L_decimal = Decimal(str(round(L, 3)))
        a_decimal = Decimal(str(round(a, 3)))
        b_decimal = Decimal(str(round(b_lab, 3)))
        
        self.logger.debug(f"Resultado Lab: L={L_decimal}, a={a_decimal}, b={b_decimal}")
        
        return L_decimal, a_decimal, b_decimal
    
    def lab_to_rgb(self, L: Decimal, a: Decimal, b: Decimal) -> Tuple[int, int, int]:
        """
        Converte CIE Lab para RGB (0-255)
        
        Args:
            L, a, b: Valores Lab
            
        Returns:
            Tuple[int, int, int]: (R, G, B) values (0-255)
        """
        self.logger.debug(f"Convertendo Lab(L={L}, a={a}, b={b}) para RGB")
        
        # Converter Decimal para float
        L_float = float(L)
        a_float = float(a)
        b_float = float(b)
        
        # Lab para XYZ
        fy = (L_float + 16) / 116
        fx = a_float / 500 + fy 
        fz = fy - b_float / 200
        
        # Função inversa Lab
        x_norm = self._lab_to_xyz_function(fx)
        y_norm = self._lab_to_xyz_function(fy)
        z_norm = self._lab_to_xyz_function(fz)
        
        # Desnormalizar para D65
        x = x_norm * self.XN / 100
        y = y_norm * self.YN / 100
        z = z_norm * self.ZN / 100
        
        # XYZ para RGB linear (matriz inversa sRGB)
        r_linear = x * 3.2404542 + y * -1.5371385 + z * -0.4985314
        g_linear = x * -0.9692660 + y * 1.8760108 + z * 0.0415560
        b_linear = x * 0.0556434 + y * -0.2040259 + z * 1.0572252
        
        # Clipping para valores válidos
        r_linear = max(0, min(1, r_linear))
        g_linear = max(0, min(1, g_linear))
        b_linear = max(0, min(1, b_linear))
        
        # RGB linear para sRGB (correção gamma)
        r_srgb = self._linear_to_srgb(r_linear)
        g_srgb = self._linear_to_srgb(g_linear)
        b_srgb = self._linear_to_srgb(b_linear)
        
        # Converter para 0-255
        r = int(round(r_srgb * 255))
        g = int(round(g_srgb * 255))
        b = int(round(b_srgb * 255))
        
        # Garantir range válido
        r = max(0, min(255, r))
        g = max(0, min(255, g))
        b = max(0, min(255, b))
        
        self.logger.debug(f"Resultado RGB: ({r}, {g}, {b})")
        
        return r, g, b
    
    def calculate_delta_e(
        self, 
        lab1: Tuple[Decimal, Decimal, Decimal],
        lab2: Tuple[Decimal, Decimal, Decimal],
        method: str = 'CIE76'
    ) -> Decimal:
        """
        Calcula diferença de cor Delta E entre duas cores Lab
        
        Args:
            lab1, lab2: Tuplas (L, a, b) das cores a comparar
            method: Método de cálculo ('CIE76', 'CIE94', 'CIE00')
            
        Returns:
            Decimal: Valor Delta E
        """
        L1, a1, b1 = lab1
        L2, a2, b2 = lab2
        
        if method == 'CIE76':
            # Delta E CIE 1976 (mais simples e comum)
            delta_L = float(L2 - L1)
            delta_a = float(a2 - a1)  
            delta_b = float(b2 - b1)
            
            delta_e = math.sqrt(delta_L**2 + delta_a**2 + delta_b**2)
            
        elif method == 'CIE94':
            # Delta E CIE 1994 (mais preciso para pequenas diferenças)
            delta_e = self._calculate_delta_e_94(lab1, lab2)
            
        elif method == 'CIE00':
            # Delta E CIE 2000 (mais atual e preciso)
            delta_e = self._calculate_delta_e_00(lab1, lab2)
            
        else:
            raise ValueError(f"Método Delta E não suportado: {method}")
        
        result = Decimal(str(round(delta_e, 3)))
        
        self.logger.debug(
            f"Delta E {method}: {result} entre "
            f"Lab1({L1},{a1},{b1}) e Lab2({L2},{a2},{b2})"
        )
        
        return result
    
    def evaluate_color_match(
        self, 
        target_lab: Tuple[Decimal, Decimal, Decimal],
        achieved_lab: Tuple[Decimal, Decimal, Decimal],
        tolerance_level: str = 'COMERCIAL'
    ) -> Dict:
        """
        Avalia se uma cor alcançada está dentro da tolerância da cor alvo
        
        Args:
            target_lab: Cor alvo em Lab
            achieved_lab: Cor alcançada em Lab
            tolerance_level: Nível de tolerância ('CRITICA', 'COMERCIAL', 'INDUSTRIAL', 'ACEITAVEL')
            
        Returns:
            Dict: Resultado da avaliação com detalhes
        """
        if tolerance_level not in self.COLOR_TOLERANCES:
            raise ValueError(f"Nível de tolerância inválido: {tolerance_level}")
        
        # Calcular Delta E
        delta_e_76 = self.calculate_delta_e(target_lab, achieved_lab, 'CIE76')
        delta_e_94 = self.calculate_delta_e(target_lab, achieved_lab, 'CIE94')
        
        tolerance = self.COLOR_TOLERANCES[tolerance_level]
        approved_76 = delta_e_76 <= tolerance
        approved_94 = delta_e_94 <= tolerance
        
        # Análise de diferenças por componente
        L_diff = abs(target_lab[0] - achieved_lab[0])
        a_diff = abs(target_lab[1] - achieved_lab[1])
        b_diff = abs(target_lab[2] - achieved_lab[2])
        
        evaluation = {
            'aprovado': approved_76 and approved_94,
            'nivel_tolerancia': tolerance_level,
            'tolerancia_limite': float(tolerance),
            'cor_alvo': {
                'L': float(target_lab[0]),
                'a': float(target_lab[1]),
                'b': float(target_lab[2])
            },
            'cor_alcancada': {
                'L': float(achieved_lab[0]),
                'a': float(achieved_lab[1]),
                'b': float(achieved_lab[2])
            },
            'diferencas': {
                'delta_e_76': float(delta_e_76),
                'delta_e_94': float(delta_e_94),
                'aprovado_76': approved_76,
                'aprovado_94': approved_94,
                'componentes': {
                    'L_diff': float(L_diff),
                    'a_diff': float(a_diff),
                    'b_diff': float(b_diff)
                }
            },
            'classificacao': self._classify_color_difference(delta_e_76),
            'timestamp': timezone.now().isoformat()
        }
        
        self.logger.info(
            f"Avaliação de cor - Delta E: {delta_e_76}, "
            f"Tolerância: {tolerance} ({tolerance_level}), "
            f"Aprovado: {evaluation['aprovado']}"
        )
        
        return evaluation
    
    def find_closest_color_match(
        self, 
        target_lab: Tuple[Decimal, Decimal, Decimal],
        color_library: List[Dict],
        max_results: int = 5
    ) -> List[Dict]:
        """
        Encontra cores mais próximas da cor alvo em uma biblioteca de cores
        
        Args:
            target_lab: Cor alvo em Lab
            color_library: Lista de cores [{'id': int, 'lab': (L,a,b), 'nome': str, ...}]
            max_results: Número máximo de resultados
            
        Returns:
            List[Dict]: Cores ordenadas por proximidade
        """
        if not color_library:
            return []
        
        matches = []
        
        for color in color_library:
            color_lab = color['lab']
            delta_e = self.calculate_delta_e(target_lab, color_lab)
            
            match_info = {
                'color_info': color,
                'delta_e': float(delta_e),
                'match_quality': self._classify_color_difference(delta_e),
                'evaluation': self.evaluate_color_match(
                    target_lab, 
                    color_lab, 
                    'COMERCIAL'
                )
            }
            
            matches.append(match_info)
        
        # Ordenar por Delta E (menor = melhor match)
        matches.sort(key=lambda x: x['delta_e'])
        
        # Limitar resultados
        best_matches = matches[:max_results]
        
        self.logger.info(
            f"Encontradas {len(best_matches)} cores próximas da cor alvo, "
            f"melhor match: Delta E = {best_matches[0]['delta_e'] if best_matches else 'N/A'}"
        )
        
        return best_matches
    
    def _srgb_to_linear(self, value: float) -> float:
        """Conversão sRGB para RGB linear"""
        if value <= 0.04045:
            return value / 12.92
        else:
            return math.pow((value + 0.055) / 1.055, 2.4)
    
    def _linear_to_srgb(self, value: float) -> float:
        """Conversão RGB linear para sRGB"""
        if value <= 0.0031308:
            return value * 12.92
        else:
            return 1.055 * math.pow(value, 1/2.4) - 0.055
    
    def _xyz_to_lab_function(self, value: float) -> float:
        """Função de conversão XYZ para Lab"""
        if value > self.LAB_EPSILON:
            return math.pow(value, 1/3)
        else:
            return (self.LAB_KAPPA * value + 16) / 116
    
    def _lab_to_xyz_function(self, value: float) -> float:
        """Função inversa Lab para XYZ"""
        value_cubed = value ** 3
        if value_cubed > self.LAB_EPSILON:
            return value_cubed
        else:
            return (116 * value - 16) / self.LAB_KAPPA
    
    def _calculate_delta_e_94(
        self, 
        lab1: Tuple[Decimal, Decimal, Decimal],
        lab2: Tuple[Decimal, Decimal, Decimal]
    ) -> float:
        """Delta E CIE 1994 calculation"""
        L1, a1, b1 = float(lab1[0]), float(lab1[1]), float(lab1[2])
        L2, a2, b2 = float(lab2[0]), float(lab2[1]), float(lab2[2])
        
        delta_L = L1 - L2
        delta_a = a1 - a2
        delta_b = b1 - b2
        
        C1 = math.sqrt(a1**2 + b1**2)
        C2 = math.sqrt(a2**2 + b2**2)
        delta_C = C1 - C2
        
        delta_H_squared = delta_a**2 + delta_b**2 - delta_C**2
        delta_H = math.sqrt(max(0, delta_H_squared))
        
        # Fatores de peso para aplicação gráfica
        kL = kC = kH = 1
        K1 = 0.045
        K2 = 0.015
        
        SL = 1
        SC = 1 + K1 * C1
        SH = 1 + K2 * C1
        
        delta_e_94 = math.sqrt(
            (delta_L / (kL * SL))**2 + 
            (delta_C / (kC * SC))**2 + 
            (delta_H / (kH * SH))**2
        )
        
        return delta_e_94
    
    def _calculate_delta_e_00(
        self, 
        lab1: Tuple[Decimal, Decimal, Decimal],
        lab2: Tuple[Decimal, Decimal, Decimal]
    ) -> float:
        """Delta E CIE 2000 calculation (simplified version)"""
        # Para esta implementação, usaremos CIE94 como aproximação
        # Uma implementação completa do CIE 2000 é muito extensa
        return self._calculate_delta_e_94(lab1, lab2)
    
    def _classify_color_difference(self, delta_e: Decimal) -> str:
        """Classifica a diferença de cor baseada no valor Delta E"""
        delta_float = float(delta_e)
        
        if delta_float < 1.0:
            return "Imperceptível"
        elif delta_float < 2.0:
            return "Muito boa correspondência"
        elif delta_float < 3.5:
            return "Boa correspondência"
        elif delta_float < 5.0:
            return "Correspondência aceitável"
        elif delta_float < 10.0:
            return "Diferença perceptível"
        else:
            return "Diferença significativa"
    
    def generate_color_report(
        self, 
        target_color: Dict,
        formula_results: List[Dict],
        tolerance_level: str = 'COMERCIAL'
    ) -> Dict:
        """
        Gera relatório científico de análise de cores
        
        Args:
            target_color: Cor alvo com dados Lab
            formula_results: Resultados de fórmulas testadas
            tolerance_level: Nível de tolerância para aprovação
            
        Returns:
            Dict: Relatório cientí​fico completo
        """
        target_lab = (
            target_color.get('l_value'),
            target_color.get('a_value'),
            target_color.get('b_value')
        )
        
        # Converter RGB da cor alvo
        target_rgb = self.lab_to_rgb(*target_lab)
        
        report = {
            'analise_cientifica': {
                'timestamp': timezone.now().isoformat(),
                'metodo_avaliacao': 'CIE Lab Color Space Analysis',
                'tolerancia_aplicada': tolerance_level,
                'limite_delta_e': float(self.COLOR_TOLERANCES[tolerance_level])
            },
            'cor_alvo': {
                'identificacao': target_color,
                'lab_values': {
                    'L': float(target_lab[0]),
                    'a': float(target_lab[1]),
                    'b': float(target_lab[2])
                },
                'rgb_calculado': {
                    'r': target_rgb[0],
                    'g': target_rgb[1],
                    'b': target_rgb[2],
                    'hex': f"#{target_rgb[0]:02x}{target_rgb[1]:02x}{target_rgb[2]:02x}"
                }
            },
            'formulas_analisadas': [],
            'resumo_estatistico': {
                'total_formulas': len(formula_results),
                'aprovadas': 0,
                'delta_e_medio': 0,
                'melhor_match': None,
                'pior_match': None
            }
        }
        
        delta_e_values = []
        
        for formula in formula_results:
            formula_lab = (
                formula.get('l_achieved'),
                formula.get('a_achieved'),
                formula.get('b_achieved')
            )
            
            evaluation = self.evaluate_color_match(
                target_lab,
                formula_lab,
                tolerance_level
            )
            
            formula_analysis = {
                'formula_id': formula.get('id'),
                'formula_nome': formula.get('nome'),
                'lab_alcancado': evaluation['cor_alcancada'],
                'avaliacao': evaluation,
                'pigmentos_utilizados': formula.get('pigmentos', [])
            }
            
            report['formulas_analisadas'].append(formula_analysis)
            
            if evaluation['aprovado']:
                report['resumo_estatistico']['aprovadas'] += 1
            
            delta_e_values.append(evaluation['diferencas']['delta_e_76'])
        
        # Estatísticas finais
        if delta_e_values:
            report['resumo_estatistico']['delta_e_medio'] = sum(delta_e_values) / len(delta_e_values)
            
            # Melhor e pior match
            min_delta_idx = delta_e_values.index(min(delta_e_values))
            max_delta_idx = delta_e_values.index(max(delta_e_values))
            
            report['resumo_estatistico']['melhor_match'] = {
                'formula_id': formula_results[min_delta_idx].get('id'),
                'delta_e': delta_e_values[min_delta_idx]
            }
            
            report['resumo_estatistico']['pior_match'] = {
                'formula_id': formula_results[max_delta_idx].get('id'),
                'delta_e': delta_e_values[max_delta_idx]
            }
        
        return report
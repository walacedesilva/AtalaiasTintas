"""
Label Templates System

Sistema de templates configuráveis para etiquetas:
- Templates personalizados por loja/marca
- Layouts responsivos e profissionais
- Suporte a logos, cores corporativas
- Diferentes tamanhos de etiqueta
- Elementos dinâmicos (QR, códigos, textos)
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple
from enum import Enum
import json
from pathlib import Path
from django.conf import settings
from django.template.loader import get_template
from django.template import Context, Template

import logging

logger = logging.getLogger(__name__)


class LabelSize(Enum):
    """Tamanhos padrão de etiquetas"""
    SMALL = "65x25"      # 65mm x 25mm - Etiqueta pequena
    MEDIUM = "85x35"     # 85mm x 35mm - Etiqueta média  
    LARGE = "100x50"     # 100mm x 50mm - Etiqueta grande
    CUSTOM = "custom"    # Tamanho customizado


class LabelOrientation(Enum):
    """Orientações da etiqueta"""
    PORTRAIT = "portrait"
    LANDSCAPE = "landscape"


@dataclass
class ColorScheme:
    """Esquema de cores para template"""
    primary: str = "#2E3440"      # Cor principal
    secondary: str = "#5E81AC"    # Cor secundária
    accent: str = "#BF616A"       # Cor de destaque
    background: str = "#ECEFF4"   # Fundo
    text_primary: str = "#2E3440" # Texto principal
    text_secondary: str = "#4C566A" # Texto secundário


@dataclass
class FontConfig:
    """Configuração de fontes"""
    family_primary: str = "Arial"
    family_secondary: str = "Arial"
    size_title: int = 14        # Tamanho título
    size_subtitle: int = 10     # Tamanho subtítulo
    size_body: int = 8          # Tamanho texto
    size_small: int = 6         # Tamanho pequeno


@dataclass
class LayoutConfig:
    """Configuração de layout"""
    padding: int = 5            # Padding interno em mm
    margin: int = 2             # Margem externa em mm
    qr_size: int = 20           # Tamanho QR em mm
    barcode_height: int = 8     # Altura código barras em mm
    logo_max_height: int = 12   # Altura máxima logo em mm
    element_spacing: int = 2    # Espaçamento entre elementos


@dataclass
class EtiquetaTemplate:
    """
    Template configurável para etiquetas
    
    Define todos os aspectos visuais e de conteúdo:
    - Layout e dimensões
    - Cores e fontes  
    - Elementos a incluir
    - Posicionamento dos componentes
    """
    
    # Identificação
    id: str
    name: str
    description: str = ""
    
    # Dimensões e orientação
    size: LabelSize = LabelSize.MEDIUM
    orientation: LabelOrientation = LabelOrientation.LANDSCAPE
    custom_width: Optional[int] = None   # mm
    custom_height: Optional[int] = None  # mm
    
    # Esquemas visuais
    colors: ColorScheme = field(default_factory=ColorScheme)
    fonts: FontConfig = field(default_factory=FontConfig)
    layout: LayoutConfig = field(default_factory=LayoutConfig)
    
    # Elementos a incluir
    show_logo: bool = True
    show_qr_code: bool = True
    show_barcode: bool = True
    show_color_preview: bool = True
    show_formula_details: bool = True
    show_pigment_list: bool = True
    show_technical_info: bool = True
    show_client_info: bool = True
    
    # Textos customizáveis
    header_text: str = "SISTEMA DE TINTAS"
    footer_text: str = "Qualidade e Precisão"
    
    # Configurações avançadas
    logo_position: str = "top-left"     # top-left, top-right, center
    qr_position: str = "bottom-right"   # Posição do QR code
    
    # Template HTML/CSS
    template_path: Optional[str] = None
    
    def get_dimensions(self) -> Tuple[int, int]:
        """Retorna dimensões em mm (width, height)"""
        if self.size == LabelSize.CUSTOM:
            return (self.custom_width or 100, self.custom_height or 50)
        
        size_map = {
            LabelSize.SMALL: (65, 25),
            LabelSize.MEDIUM: (85, 35), 
            LabelSize.LARGE: (100, 50)
        }
        
        width, height = size_map.get(self.size, (85, 35))
        
        # Trocar dimensões se orientação for retrato
        if self.orientation == LabelOrientation.PORTRAIT:
            return (height, width)
        
        return (width, height)
    
    def get_dpi_dimensions(self, dpi: int = 300) -> Tuple[int, int]:
        """Retorna dimensões em pixels para DPI especificado"""
        width_mm, height_mm = self.get_dimensions()
        
        # Converter mm para polegadas e depois para pixels
        width_px = int((width_mm / 25.4) * dpi)
        height_px = int((height_mm / 25.4) * dpi)
        
        return (width_px, height_px)
    
    def to_dict(self) -> dict:
        """Converte template para dicionário serializável"""
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'size': self.size.value,
            'orientation': self.orientation.value,
            'custom_width': self.custom_width,
            'custom_height': self.custom_height,
            'colors': {
                'primary': self.colors.primary,
                'secondary': self.colors.secondary,
                'accent': self.colors.accent,
                'background': self.colors.background,
                'text_primary': self.colors.text_primary,
                'text_secondary': self.colors.text_secondary
            },
            'fonts': {
                'family_primary': self.fonts.family_primary,
                'family_secondary': self.fonts.family_secondary,
                'size_title': self.fonts.size_title,
                'size_subtitle': self.fonts.size_subtitle,
                'size_body': self.fonts.size_body,
                'size_small': self.fonts.size_small
            },
            'layout': {
                'padding': self.layout.padding,
                'margin': self.layout.margin,
                'qr_size': self.layout.qr_size,
                'barcode_height': self.layout.barcode_height,
                'logo_max_height': self.layout.logo_max_height,
                'element_spacing': self.layout.element_spacing
            },
            'elements': {
                'show_logo': self.show_logo,
                'show_qr_code': self.show_qr_code,
                'show_barcode': self.show_barcode,
                'show_color_preview': self.show_color_preview,
                'show_formula_details': self.show_formula_details,
                'show_pigment_list': self.show_pigment_list,
                'show_technical_info': self.show_technical_info,
                'show_client_info': self.show_client_info
            },
            'texts': {
                'header_text': self.header_text,
                'footer_text': self.footer_text
            },
            'positioning': {
                'logo_position': self.logo_position,
                'qr_position': self.qr_position
            },
            'template_path': self.template_path
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'EtiquetaTemplate':
        """Cria template a partir de dicionário"""
        colors = ColorScheme(**data.get('colors', {}))
        fonts = FontConfig(**data.get('fonts', {}))
        layout = LayoutConfig(**data.get('layout', {}))
        
        elements = data.get('elements', {})
        texts = data.get('texts', {})
        positioning = data.get('positioning', {})
        
        return cls(
            id=data['id'],
            name=data['name'],
            description=data.get('description', ''),
            size=LabelSize(data.get('size', 'medium')),
            orientation=LabelOrientation(data.get('orientation', 'landscape')),
            custom_width=data.get('custom_width'),
            custom_height=data.get('custom_height'),
            colors=colors,
            fonts=fonts,
            layout=layout,
            show_logo=elements.get('show_logo', True),
            show_qr_code=elements.get('show_qr_code', True),
            show_barcode=elements.get('show_barcode', True),
            show_color_preview=elements.get('show_color_preview', True),
            show_formula_details=elements.get('show_formula_details', True),
            show_pigment_list=elements.get('show_pigment_list', True),
            show_technical_info=elements.get('show_technical_info', True),
            show_client_info=elements.get('show_client_info', True),
            header_text=texts.get('header_text', 'SISTEMA DE TINTAS'),
            footer_text=texts.get('footer_text', 'Qualidade e Precisão'),
            logo_position=positioning.get('logo_position', 'top-left'),
            qr_position=positioning.get('qr_position', 'bottom-right'),
            template_path=data.get('template_path')
        )


class TemplateManager:
    """
    Gerenciador de templates de etiquetas
    
    Funcionalidades:
    - Carregamento de templates padrão
    - Templates customizados por loja
    - Persistência em arquivos JSON
    - Validação de templates
    - Preview de templates
    """
    
    def __init__(self):
        self.templates_dir = Path(settings.BASE_DIR) / 'templates' / 'labels'
        self.custom_templates_dir = Path(settings.MEDIA_ROOT) / 'label_templates'
        
        # Criar diretórios se não existirem
        self.templates_dir.mkdir(parents=True, exist_ok=True)
        self.custom_templates_dir.mkdir(parents=True, exist_ok=True)
        
        # Cache de templates carregados
        self._template_cache = {}
    
    def get_default_templates(self) -> Dict[str, EtiquetaTemplate]:
        """Retorna templates padrão do sistema"""
        
        # Template padrão - profissional
        default_template = EtiquetaTemplate(
            id="default",
            name="Template Padrão",
            description="Template profissional padrão para todas as misturas",
            colors=ColorScheme(
                primary="#1e3a8a",        # Azul profissional
                secondary="#3b82f6",      # Azul claro
                accent="#f59e0b",         # Laranja
                background="#f8fafc",     # Cinza muito claro
                text_primary="#1e293b",   # Texto escuro
                text_secondary="#64748b"  # Texto médio
            )
        )
        
        # Template compacto - informações essenciais
        compact_template = EtiquetaTemplate(
            id="compact",
            name="Template Compacto",
            description="Template minimalista com informações essenciais",
            size=LabelSize.SMALL,
            colors=ColorScheme(
                primary="#374151",
                secondary="#6b7280", 
                accent="#ef4444",
                background="#ffffff",
                text_primary="#111827",
                text_secondary="#6b7280"
            ),
            show_pigment_list=False,
            show_technical_info=False,
            show_formula_details=False
        )
        
        # Template premium - máximo detalhamento
        premium_template = EtiquetaTemplate(
            id="premium",
            name="Template Premium",
            description="Template completo com máximo de informações",
            size=LabelSize.LARGE,
            colors=ColorScheme(
                primary="#7c3aed",        # Roxo premium
                secondary="#a855f7",      # Roxo claro
                accent="#fbbf24",         # Dourado
                background="#fefefe",     # Branco puro
                text_primary="#1f2937",   # Preto suave
                text_secondary="#6b7280"  # Cinza médio
            ),
            fonts=FontConfig(
                family_primary="Arial Black",
                size_title=16,
                size_subtitle=12,
                size_body=9,
                size_small=7
            ),
            header_text="SISTEMA PREMIUM DE TINTAS",
            footer_text="Excelência em Cada Gota"
        )
        
        # Template ecológico - cores naturais
        eco_template = EtiquetaTemplate(
            id="eco", 
            name="Template Ecológico",
            description="Template com cores naturais para linha eco",
            colors=ColorScheme(
                primary="#166534",        # Verde escuro
                secondary="#16a34a",      # Verde médio
                accent="#84cc16",         # Verde limão
                background="#f0fdf4",     # Verde muito claro
                text_primary="#14532d",   # Texto verde escuro
                text_secondary="#166534"  # Texto verde
            ),
            header_text="TINTAS ECOLÓGICAS",
            footer_text="Sustentabilidade e Qualidade"
        )
        
        return {
            "default": default_template,
            "compact": compact_template,
            "premium": premium_template,
            "eco": eco_template
        }
    
    def load_template(self, template_id: str, loja_id: Optional[int] = None) -> EtiquetaTemplate:
        """
        Carrega template por ID
        
        Args:
            template_id: ID do template
            loja_id: ID da loja (para templates customizados)
            
        Returns:
            EtiquetaTemplate: Template carregado
        """
        # Verificar cache
        cache_key = f"{template_id}_{loja_id or 'global'}"
        if cache_key in self._template_cache:
            return self._template_cache[cache_key]
        
        # Tentar carregar template customizado da loja
        if loja_id:
            custom_template = self._load_custom_template(template_id, loja_id)
            if custom_template:
                self._template_cache[cache_key] = custom_template
                return custom_template
        
        # Carregar template padrão
        default_templates = self.get_default_templates()
        if template_id in default_templates:
            template = default_templates[template_id]
            self._template_cache[cache_key] = template
            return template
        
        # Fallback para template padrão
        logger.warning(f"Template {template_id} não encontrado, usando padrão")
        default_template = default_templates["default"]
        self._template_cache[cache_key] = default_template
        return default_template
    
    def _load_custom_template(self, template_id: str, loja_id: int) -> Optional[EtiquetaTemplate]:
        """Carrega template customizado de loja específica"""
        try:
            template_file = self.custom_templates_dir / f"loja_{loja_id}" / f"{template_id}.json"
            
            if template_file.exists():
                with open(template_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    return EtiquetaTemplate.from_dict(data)
        
        except Exception as e:
            logger.error(f"Erro carregando template customizado {template_id} da loja {loja_id}: {str(e)}")
        
        return None
    
    def save_custom_template(self, template: EtiquetaTemplate, loja_id: int) -> bool:
        """
        Salva template customizado para loja
        
        Args:
            template: Template a salvar
            loja_id: ID da loja
            
        Returns:
            bool: Sucesso da operação
        """
        try:
            # Criar diretório da loja
            loja_dir = self.custom_templates_dir / f"loja_{loja_id}"
            loja_dir.mkdir(exist_ok=True)
            
            # Salvar template
            template_file = loja_dir / f"{template.id}.json"
            with open(template_file, 'w', encoding='utf-8') as f:
                json.dump(template.to_dict(), f, ensure_ascii=False, indent=2)
            
            # Limpar cache
            cache_key = f"{template.id}_{loja_id}"
            if cache_key in self._template_cache:
                del self._template_cache[cache_key]
            
            logger.info(f"Template {template.id} salvo para loja {loja_id}")
            return True
            
        except Exception as e:
            logger.error(f"Erro salvando template {template.id} para loja {loja_id}: {str(e)}")
            return False
    
    def list_templates(self, loja_id: Optional[int] = None) -> List[Dict]:
        """
        Lista todos os templates disponíveis
        
        Args:
            loja_id: ID da loja (inclui templates customizados)
            
        Returns:
            List[Dict]: Lista de templates com metadata
        """
        templates = []
        
        # Templates padrão
        for template_id, template in self.get_default_templates().items():
            templates.append({
                'id': template_id,
                'name': template.name,
                'description': template.description,
                'size': template.size.value,
                'orientation': template.orientation.value,
                'type': 'default',
                'preview_available': True
            })
        
        # Templates customizados da loja
        if loja_id:
            loja_dir = self.custom_templates_dir / f"loja_{loja_id}"
            if loja_dir.exists():
                for template_file in loja_dir.glob("*.json"):
                    try:
                        with open(template_file, 'r', encoding='utf-8') as f:
                            data = json.load(f)
                            templates.append({
                                'id': data['id'],
                                'name': data['name'],
                                'description': data.get('description', ''),
                                'size': data.get('size', 'medium'),
                                'orientation': data.get('orientation', 'landscape'),
                                'type': 'custom',
                                'preview_available': True
                            })
                    except Exception as e:
                        logger.error(f"Erro lendo template {template_file}: {str(e)}")
        
        return templates
    
    def validate_template(self, template: EtiquetaTemplate) -> Tuple[bool, List[str]]:
        """
        Valida template quanto a configurações e compatibilidade
        
        Args:
            template: Template a validar
            
        Returns:
            tuple: (válido: bool, erros: List[str])
        """
        errors = []
        
        # Validar ID
        if not template.id or not template.id.strip():
            errors.append("ID do template é obrigatório")
        
        # Validar nome
        if not template.name or not template.name.strip():
            errors.append("Nome do template é obrigatório")
        
        # Validar dimensões customizadas
        if template.size == LabelSize.CUSTOM:
            if not template.custom_width or template.custom_width <= 0:
                errors.append("Largura customizada deve ser maior que 0")
            if not template.custom_height or template.custom_height <= 0:
                errors.append("Altura customizada deve ser maior que 0")
        
        # Validar cores (formato hex)
        color_fields = [
            template.colors.primary,
            template.colors.secondary,
            template.colors.accent,
            template.colors.background,
            template.colors.text_primary,
            template.colors.text_secondary
        ]
        
        for color in color_fields:
            if not color.startswith('#') or len(color) != 7:
                errors.append(f"Cor inválida: {color}")
        
        # Validar tamanhos de fonte
        font_sizes = [
            template.fonts.size_title,
            template.fonts.size_subtitle,
            template.fonts.size_body,
            template.fonts.size_small
        ]
        
        for size in font_sizes:
            if size <= 0 or size > 72:
                errors.append(f"Tamanho de fonte inválido: {size}")
        
        # Validar se pelo menos um elemento está visível
        elements = [
            template.show_logo,
            template.show_qr_code,
            template.show_barcode,
            template.show_color_preview,
            template.show_formula_details,
            template.show_pigment_list,
            template.show_technical_info,
            template.show_client_info
        ]
        
        if not any(elements):
            errors.append("Pelo menos um elemento deve estar visível")
        
        return len(errors) == 0, errors
    
    def clear_cache(self):
        """Limpa cache de templates"""
        self._template_cache.clear()
        logger.info("Cache de templates limpo")
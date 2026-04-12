"""
PDF Label Renderer

Sistema avançado de renderização de etiquetas em PDF usando ReportLab:
- Geração de PDF em alta qualidade (300 DPI)
- Layout responsivo baseado em templates
- Suporte a elementos gráficos (QR, códigos, logos)
- Preview HTML para visualização rápida
- Múltiplos tamanhos e orientações
- Fontes e cores customizáveis
"""

import io
import base64
from typing import Optional, Dict, Any, Tuple
from decimal import Decimal
from PIL import Image
import logging

from reportlab.lib.pagesizes import letter, A4, landscape, portrait
from reportlab.lib.units import mm, inch
from reportlab.lib.colors import HexColor, black, white
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT, TA_JUSTIFY
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image as RLImage
from reportlab.platypus.flowables import Flowable
from reportlab.pdfgen import canvas
from reportlab.lib import colors

from django.conf import settings
from django.template.loader import render_to_string
from django.utils.html import strip_tags

from .templates import EtiquetaTemplate, LabelSize, LabelOrientation
from .services import LabelGeneratorService

logger = logging.getLogger(__name__)


class QRCodeFlowable(Flowable):
    """Flowable customizado para QR Code no ReportLab"""
    
    def __init__(self, qr_data: bytes, size: float = 20*mm):
        Flowable.__init__(self)
        self.qr_data = qr_data
        self.size = size
        self.width = self.height = size
    
    def draw(self):
        """Desenha o QR Code no canvas"""
        try:
            # Converter bytes para imagem PIL
            qr_image = Image.open(io.BytesIO(self.qr_data))
            
            # Criar imagem temporária
            temp_image = io.BytesIO()
            qr_image.save(temp_image, format='PNG')
            temp_image.seek(0)
            
            # Desenhar no canvas
            self.canv.drawImage(
                temp_image, 
                0, 0, 
                width=self.size, 
                height=self.size,
                preserveAspectRatio=True
            )
            
        except Exception as e:
            logger.error(f"Erro desenhando QR Code: {str(e)}")
            # Desenhar retângulo placeholder
            self.canv.setFillColor(colors.lightgrey)
            self.canv.rect(0, 0, self.size, self.size, fill=1)


class BarcodeFlowable(Flowable):
    """Flowable customizado para código de barras"""
    
    def __init__(self, barcode_data: bytes, width: float = 40*mm, height: float = 8*mm):
        Flowable.__init__(self)
        self.barcode_data = barcode_data
        self.width = width
        self.height = height
    
    def draw(self):
        """Desenha o código de barras no canvas"""
        try:
            # Converter bytes para imagem PIL
            barcode_image = Image.open(io.BytesIO(self.barcode_data))
            
            # Criar imagem temporária
            temp_image = io.BytesIO()
            barcode_image.save(temp_image, format='PNG')
            temp_image.seek(0)
            
            # Desenhar no canvas
            self.canv.drawImage(
                temp_image,
                0, 0,
                width=self.width,
                height=self.height,
                preserveAspectRatio=True
            )
            
        except Exception as e:
            logger.error(f"Erro desenhando código de barras: {str(e)}")
            # Desenhar retângulo placeholder  
            self.canv.setFillColor(colors.lightgrey)
            self.canv.rect(0, 0, self.width, self.height, fill=1)


class ColorPreviewFlowable(Flowable):
    """Flowable para preview da cor"""
    
    def __init__(self, hex_color: str, size: float = 15*mm):
        Flowable.__init__(self)
        self.hex_color = hex_color
        self.size = size
        self.width = self.height = size
    
    def draw(self):
        """Desenha o preview da cor"""
        try:
            # Converter hex para cor
            color = HexColor(self.hex_color)
            
            # Desenhar quadrado colorido
            self.canv.setFillColor(color)
            self.canv.rect(0, 0, self.size, self.size, fill=1, stroke=1)
            
            # Borda preta para contraste
            self.canv.setStrokeColor(black)
            self.canv.setLineWidth(0.5)
            self.canv.rect(0, 0, self.size, self.size, fill=0, stroke=1)
            
        except Exception as e:
            logger.error(f"Erro desenhando preview da cor {self.hex_color}: {str(e)}")
            # Desenhar cinza como fallback
            self.canv.setFillColor(colors.lightgrey)
            self.canv.rect(0, 0, self.size, self.size, fill=1)


class LabelPDFRenderer:
    """
    Renderizador principal de etiquetas em PDF
    
    Funcionalidades:
    - Renderização em alta qualidade (300 DPI)
    - Layout responsivo baseado em templates
    - Elementos gráficos integrados
    - Múltiplos formatos de saída
    - Preview HTML opcional
    """
    
    def __init__(self):
        self.dpi = 300  # 300 DPI para impressão profissional
        self.styles = getSampleStyleSheet()
        
        # Criar estilos customizados
        self._create_custom_styles()
    
    def _create_custom_styles(self):
        """Cria estilos customizados para elementos"""
        
        # Estilo para título principal
        self.styles.add(ParagraphStyle(
            name='LabelTitle',
            parent=self.styles['Heading1'],
            fontSize=14,
            textColor=black,
            alignment=TA_CENTER,
            spaceAfter=6,
            fontName='Helvetica-Bold'  # Usar fonte padrão do ReportLab
        ))
        
        # Estilo para subtítulo
        self.styles.add(ParagraphStyle(
            name='LabelSubtitle',
            parent=self.styles['Heading2'],
            fontSize=10,
            textColor=colors.grey,
            alignment=TA_CENTER,
            spaceAfter=3,
            fontName='Helvetica'
        ))
        
        # Estilo para texto do corpo
        self.styles.add(ParagraphStyle(
            name='LabelBody',
            parent=self.styles['Normal'],
            fontSize=8,
            textColor=black,
            alignment=TA_LEFT,
            spaceAfter=2,
            fontName='Helvetica'
        ))
        
        # Estilo para texto pequeno (técnico)
        self.styles.add(ParagraphStyle(
            name='LabelSmall',
            parent=self.styles['Normal'],
            fontSize=6,
            textColor=colors.grey,
            alignment=TA_LEFT,
            spaceAfter=1,
            fontName='Helvetica'
        ))
    
    def render_label_pdf(
        self, 
        label_data: Dict[str, Any], 
        template: EtiquetaTemplate,
        output_format: str = 'bytes'
    ) -> bytes:
        """
        Renderiza etiqueta completa em PDF
        
        Args:
            label_data: Dados da etiqueta (do LabelGeneratorService)
            template: Template a usar
            output_format: 'bytes', 'file', 'base64'
            
        Returns:
            bytes: PDF renderizado
        """
        try:
            # Buffer para PDF
            buffer = io.BytesIO()
            
            # Configurar dimensões da página
            width, height = template.get_dpi_dimensions(72)  # ReportLab usa 72 DPI
            page_size = (width, height)
            
            # Criar documento PDF
            doc = SimpleDocTemplate(
                buffer,
                pagesize=page_size,
                rightMargin=template.layout.margin * mm,
                leftMargin=template.layout.margin * mm,
                topMargin=template.layout.margin * mm,
                bottomMargin=template.layout.margin * mm
            )
            
            # Construir elementos da etiqueta
            story = []
            
            # Header da etiqueta
            if template.header_text:
                story.append(self._create_header(label_data, template))
                story.append(Spacer(1, template.layout.element_spacing * mm))
            
            # Seção principal com informações da mistura
            story.extend(self._create_main_section(label_data, template))
            
            # Seção de códigos (QR + Barcode)
            story.extend(self._create_codes_section(label_data, template))
            
            # Seção de pigmentos
            if template.show_pigment_list and label_data.get('pigmentos'):
                story.extend(self._create_pigments_section(label_data, template))
            
            # Informações técnicas
            if template.show_technical_info:
                story.extend(self._create_technical_section(label_data, template))
            
            # Footer
            if template.footer_text:
                story.append(Spacer(1, template.layout.element_spacing * mm))
                story.append(self._create_footer(label_data, template))
            
            # Construir PDF
            doc.build(story)
            
            # Retornar conforme formato solicitado
            pdf_data = buffer.getvalue()
            buffer.close()
            
            if output_format == 'base64':
                return base64.b64encode(pdf_data)
            elif output_format == 'file':
                return pdf_data  # Para salvar em arquivo
            else:
                return pdf_data  # bytes
                
        except Exception as e:
            logger.error(f"Erro renderizando PDF da etiqueta: {str(e)}")
            raise e
    
    def _create_header(self, label_data: Dict, template: EtiquetaTemplate) -> Paragraph:
        """Cria header da etiqueta"""
        header_style = ParagraphStyle(
            name='CustomHeader',
            parent=self.styles['LabelTitle'],
            fontSize=template.fonts.size_title,
            textColor=HexColor(template.colors.primary),
            fontName=template.fonts.family_primary
        )
        
        return Paragraph(template.header_text, header_style)
    
    def _create_main_section(self, label_data: Dict, template: EtiquetaTemplate) -> list:
        """Cria seção principal com informações da mistura"""
        elements = []
        
        # Tabela principal com informações
        main_data = []
        
        # Informações da cor
        cor = label_data['cor']
        main_data.append(['Cor:', f"{cor['nome']} ({cor['codigo']})"])
        
        # Informações da mistura  
        mistura = label_data['mistura']
        main_data.append(['Volume:', f"{mistura['volume_litros']:.2f}L"])
        main_data.append(['Código:', mistura['codigo']])
        
        # Informações da fórmula
        if template.show_formula_details:
            formula = label_data['formula']
            main_data.append(['Fórmula:', f"{formula['nome']} v{formula['versao']}"])
            main_data.append(['Base:', formula['base_produto']])
        
        # Cliente
        if template.show_client_info:
            cliente = label_data['cliente']
            if cliente['nome'] != 'Cliente Anônimo':
                main_data.append(['Cliente:', cliente['nome']])
        
        # Criar tabela
        main_table = Table(main_data, colWidths=[25*mm, 50*mm])
        main_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), template.fonts.size_body),
            ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
            ('ALIGN', (1, 0), (1, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('TEXTCOLOR', (0, 0), (0, -1), HexColor(template.colors.text_secondary)),
            ('TEXTCOLOR', (1, 0), (1, -1), HexColor(template.colors.text_primary)),
            ('LEFTPADDING', (0, 0), (-1, -1), 0),
            ('RIGHTPADDING', (0, 0), (-1, -1), 3*mm),
            ('TOPPADDING', (0, 0), (-1, -1), 1*mm),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 1*mm),
        ]))
        
        elements.append(main_table)
        
        # Preview da cor e data
        if template.show_color_preview:
            elements.append(Spacer(1, template.layout.element_spacing * mm))
            
            # Tabela com preview da cor e data
            preview_data = [[
                ColorPreviewFlowable(label_data['cor']['hex'], 12*mm),
                f"Criado: {mistura['data_criacao']}"
            ]]
            
            preview_table = Table(preview_data, colWidths=[15*mm, 60*mm])
            preview_table.setStyle(TableStyle([
                ('FONTNAME', (1, 0), (1, 0), 'Helvetica'),
                ('FONTSIZE', (1, 0), (1, 0), template.fonts.size_small),
                ('ALIGN', (0, 0), (0, 0), 'LEFT'),
                ('ALIGN', (1, 0), (1, 0), 'LEFT'),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('TEXTCOLOR', (1, 0), (1, 0), HexColor(template.colors.text_secondary)),
                ('LEFTPADDING', (0, 0), (-1, -1), 0),
                ('RIGHTPADDING', (0, 0), (-1, -1), 0),
            ]))
            
            elements.append(preview_table)
        
        return elements
    
    def _create_codes_section(self, label_data: Dict, template: EtiquetaTemplate) -> list:
        """Cria seção com QR Code e código de barras"""
        elements = []
        
        if not template.show_qr_code and not template.show_barcode:
            return elements
        
        elements.append(Spacer(1, template.layout.element_spacing * mm))
        
        codes_data = []
        
        if template.show_qr_code and template.show_barcode:
            # Ambos os códigos
            qr_image = base64.b64decode(label_data['qr_code']['image_base64'])
            barcode_image = base64.b64decode(label_data['barcode']['image_base64'])
            
            codes_data.append([
                QRCodeFlowable(qr_image, template.layout.qr_size * mm),
                BarcodeFlowable(barcode_image, 35*mm, template.layout.barcode_height * mm)
            ])
            
            codes_table = Table(codes_data, colWidths=[25*mm, 40*mm])
            
        elif template.show_qr_code:
            # Apenas QR Code
            qr_image = base64.b64decode(label_data['qr_code']['image_base64'])
            codes_data.append([QRCodeFlowable(qr_image, template.layout.qr_size * mm)])
            codes_table = Table(codes_data, colWidths=[25*mm])
            
        elif template.show_barcode:
            # Apenas código de barras
            barcode_image = base64.b64decode(label_data['barcode']['image_base64'])
            codes_data.append([BarcodeFlowable(barcode_image, 50*mm, template.layout.barcode_height * mm)])
            codes_table = Table(codes_data, colWidths=[55*mm])
        
        codes_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('LEFTPADDING', (0, 0), (-1, -1), 0),
            ('RIGHTPADDING', (0, 0), (-1, -1), 0),
        ]))
        
        elements.append(codes_table)
        
        return elements
    
    def _create_pigments_section(self, label_data: Dict, template: EtiquetaTemplate) -> list:
        """Cria seção com lista de pigmentos"""
        elements = []
        
        if not label_data.get('pigmentos'):
            return elements
        
        elements.append(Spacer(1, template.layout.element_spacing * mm))
        
        # Título da seção
        pigments_title = Paragraph(
            "Pigmentos:",
            ParagraphStyle(
                name='PigmentsTitle',
                fontSize=template.fonts.size_subtitle,
                textColor=HexColor(template.colors.text_secondary),
                fontName=template.fonts.family_primary + '-Bold'
            )
        )
        elements.append(pigments_title)
        
        # Lista de pigmentos
        pigments_data = []
        for pigmento in label_data['pigmentos']:
            pigments_data.append([
                pigmento['codigo'],
                f"{pigmento['quantidade_ml']:.1f}ml",
                f"{pigmento['percentual']:.1f}%"
            ])
        
        pigments_table = Table(pigments_data, colWidths=[25*mm, 15*mm, 15*mm])
        pigments_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), template.fonts.size_small),
            ('ALIGN', (0, 0), (0, -1), 'LEFT'),
            ('ALIGN', (1, 0), (-1, -1), 'RIGHT'),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('TEXTCOLOR', (0, 0), (-1, -1), HexColor(template.colors.text_primary)),
            ('LEFTPADDING', (0, 0), (-1, -1), 0),
            ('RIGHTPADDING', (0, 0), (-1, -1), 2*mm),
        ]))
        
        elements.append(pigments_table)
        
        return elements
    
    def _create_technical_section(self, label_data: Dict, template: EtiquetaTemplate) -> list:
        """Cria seção com informações técnicas"""
        elements = []
        
        elements.append(Spacer(1, template.layout.element_spacing * mm))
        
        # Informações técnicas da cor
        tech_info = [
            f"RGB: {label_data['cor']['rgb']}",
            f"Lab: {label_data['cor']['lab']}",
            f"Tracking: {label_data['barcode']['code']}"
        ]
        
        tech_text = " • ".join(tech_info)
        
        tech_paragraph = Paragraph(
            tech_text,
            ParagraphStyle(
                name='TechnicalInfo',
                fontSize=template.fonts.size_small,
                textColor=HexColor(template.colors.text_secondary),
                fontName=template.fonts.family_secondary,
                alignment=TA_CENTER
            )
        )
        
        elements.append(tech_paragraph)
        
        return elements
    
    def _create_footer(self, label_data: Dict, template: EtiquetaTemplate) -> Paragraph:
        """Cria footer da etiqueta"""
        footer_style = ParagraphStyle(
            name='CustomFooter',
            fontSize=template.fonts.size_small,
            textColor=HexColor(template.colors.text_secondary),
            fontName=template.fonts.family_secondary,
            alignment=TA_CENTER
        )
        
        return Paragraph(template.footer_text, footer_style)
    
    def generate_preview_html(self, label_data: Dict, template: EtiquetaTemplate) -> str:
        """
        Gera preview HTML da etiqueta para visualização rápida
        
        Args:
            label_data: Dados da etiqueta
            template: Template a usar
            
        Returns:
            str: HTML renderizado
        """
        try:
            width, height = template.get_dimensions()
            
            context = {
                'label_data': label_data,
                'template': template,
                'width_mm': width,
                'height_mm': height,
                'css_vars': {
                    'primary_color': template.colors.primary,
                    'secondary_color': template.colors.secondary,
                    'accent_color': template.colors.accent,
                    'background_color': template.colors.background,
                    'text_primary': template.colors.text_primary,
                    'text_secondary': template.colors.text_secondary,
                    'font_primary': template.fonts.family_primary,
                    'font_secondary': template.fonts.family_secondary,
                }
            }
            
            return render_to_string('labels/preview.html', context)
            
        except Exception as e:
            logger.error(f"Erro gerando preview HTML: {str(e)}")
            return f"<div>Erro gerando preview: {str(e)}</div>"
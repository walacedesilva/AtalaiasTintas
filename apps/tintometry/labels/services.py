"""
Serviços para geração de QR Codes, códigos de barras e etiquetas
"""
import qrcode
import barcode
from barcode.writer import ImageWriter
from PIL import Image, ImageDraw, ImageFont
from io import BytesIO
import base64
from datetime import datetime
from django.conf import settings
from django.utils import timezone
import json
import os
import logging

logger = logging.getLogger(__name__)


class QRCodeService:
    """Serviço para geração de QR Codes"""
    
    def __init__(self):
        self.qr_config = {
            'version': 1,
            'error_correction': qrcode.constants.ERROR_CORRECT_L,
            'box_size': 8,
            'border': 1,
        }
    
    def generate_qr_data(self, mistura):
        """Gera os dados para codificar no QR Code"""
        try:
            qr_data = {
                'sistema': 'AtalaiasTintas',
                'versao': '1.0',
                'tipo': 'mistura_tinta',
                'timestamp': timezone.now().isoformat(),
                'dados': {
                    'id': mistura.id,
                    'codigo_mistura': mistura.codigo_mistura,
                    'formula': {
                        'codigo': mistura.formula.codigo_formula,
                        'nome_cor': mistura.formula.cor_definida.nome_cor,
                        'cor_hex': mistura.formula.cor_definida.cor_hex,
                        'familia': mistura.formula.cor_definida.familia_cor,
                        'linha': mistura.formula.cor_definida.linha_produto,
                    },
                    'cliente': {
                        'nome': mistura.cliente_nome,
                        'telefone': mistura.cliente_telefone or '',
                    },
                    'producao': {
                        'volume': float(mistura.volume_solicitado),
                        'custo': float(mistura.custo_total or 0),
                        'data_criacao': mistura.created_at.isoformat(),
                        'operador': mistura.usuario_operacao.username,
                        'loja': mistura.loja.codigo if mistura.loja else '',
                        'situacao': mistura.situacao,
                    },
                    'pigmentos': []
                }
            }
            
            # Adicionar pigmentos
            for item in mistura.itens.all():
                qr_data['dados']['pigmentos'].append({
                    'nome': item.pigmento.nome,
                    'cor_base': item.pigmento.cor_base,
                    'quantidade': float(item.quantidade_calculada),
                })
            
            return qr_data
            
        except Exception as e:
            logger.error(f"Erro ao gerar dados do QR Code para mistura {mistura.id}: {e}")
            raise
    
    def generate_qr_image(self, qr_data, size=(200, 200)):
        """Gera a imagem do QR Code"""
        try:
            # Converter dados para JSON
            qr_text = json.dumps(qr_data, ensure_ascii=False, separators=(',', ':'))
            
            # Criar QR Code
            qr = qrcode.QRCode(**self.qr_config)
            qr.add_data(qr_text)
            qr.make(fit=True)
            
            # Gerar imagem
            qr_image = qr.make_image(fill_color="black", back_color="white")
            
            # Redimensionar se necessário
            if size != qr_image.size:
                qr_image = qr_image.resize(size, Image.Resampling.LANCZOS)
            
            # Converter para base64
            buffer = BytesIO()
            qr_image.save(buffer, format='PNG')
            image_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
            
            return image_base64
            
        except Exception as e:
            logger.error(f"Erro ao gerar imagem do QR Code: {e}")
            raise
    
    def decode_qr_data(self, qr_text):
        """Decodifica dados de um QR Code"""
        try:
            return json.loads(qr_text)
        except (json.JSONDecodeError, TypeError) as e:
            logger.error(f"Erro ao decodificar QR Code: {e}")
            return None


class BarcodeService:
    """Serviço para geração de códigos de barras"""
    
    def __init__(self):
        self.barcode_type = 'code128'  # Tipo padrão
    
    def generate_tracking_code(self, mistura):
        """Gera código de rastreamento único para a mistura"""
        try:
            # Formato: AT + YYYY + MM + DD + ID (6 dígitos)
            now = timezone.now()
            date_part = now.strftime('%Y%m%d')
            id_part = f"{mistura.id:06d}"
            tracking_code = f"AT{date_part}{id_part}"
            
            return tracking_code
            
        except Exception as e:
            logger.error(f"Erro ao gerar código de rastreamento para mistura {mistura.id}: {e}")
            raise
    
    def generate_barcode_image(self, code, width=300, height=100):
        """Gera imagem do código de barras"""
        try:
            # Criar código de barras
            code_class = barcode.get_barcode_class(self.barcode_type)
            barcode_instance = code_class(code, writer=ImageWriter())
            
            # Gerar imagem
            buffer = BytesIO()
            barcode_image = barcode_instance.write(buffer, {
                'module_width': 0.3,
                'module_height': height / 100,  # Altura relativa
                'text_distance': 2,
                'font_size': 10,
            })
            
            # Converter para base64
            buffer.seek(0)
            image_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
            
            return image_base64
            
        except Exception as e:
            logger.error(f"Erro ao gerar código de barras {code}: {e}")
            raise


class LabelGeneratorService:
    """Serviço principal para geração de etiquetas"""
    
    def __init__(self):
        self.qr_service = QRCodeService()
        self.barcode_service = BarcodeService()
        self.template_cache = {}
    
    def generate_label_pdf(self, mistura, template, config=None):
        """Gera PDF da etiqueta para uma mistura"""
        try:
            from reportlab.pdfgen import canvas
            from reportlab.lib.pagesizes import letter, A4
            from reportlab.lib.units import mm
            from reportlab.lib.colors import HexColor
            
            # Configuração padrão
            if not config:
                config = {
                    'paper_size': 'a4',
                    'copies': 1,
                    'include_qr': True,
                    'include_barcode': True,
                }
            
            # Criar buffer para PDF
            buffer = BytesIO()
            
            # Definir tamanho da página
            if config.get('paper_size') == 'a5':
                page_size = (148*mm, 210*mm)
            elif config.get('paper_size') == 'label':
                page_size = (100*mm, 150*mm)  
            else:
                page_size = A4
            
            # Criar canvas
            c = canvas.Canvas(buffer, pagesize=page_size)
            
            # Gerar etiqueta(s)
            copies = config.get('copies', 1)
            for copy_num in range(copies):
                if copy_num > 0:
                    c.showPage()  # Nova página para cópias adicionais
                
                self._draw_label_on_canvas(c, mistura, template, config)
            
            # Finalizar PDF
            c.save()
            
            # Retornar bytes do PDF
            buffer.seek(0)
            return buffer.getvalue()
            
        except Exception as e:
            logger.error(f"Erro ao gerar PDF da etiqueta para mistura {mistura.id}: {e}")
            raise
    
    def generate_batch_labels_pdf(self, misturas, template, config=None):
        """Gera PDF com múltiplas etiquetas"""
        try:
            from reportlab.pdfgen import canvas
            from reportlab.lib.pagesizes import A4
            from reportlab.lib.units import mm
            
            if not config:
                config = {'paper_size': 'a4', 'copies': 1}
            
            buffer = BytesIO()
            c = canvas.Canvas(buffer, pagesize=A4)
            
            # Layout para múltiplas etiquetas por página
            labels_per_row = 2
            labels_per_col = 4
            labels_per_page = labels_per_row * labels_per_col
            
            label_width = 100*mm
            label_height = 70*mm
            margin_x = 5*mm
            margin_y = 10*mm
            
            label_count = 0
            
            for mistura in misturas:
                # Calcular posição na página
                page_position = label_count % labels_per_page
                col = page_position % labels_per_row
                row = page_position // labels_per_row
                
                x = margin_x + col * (label_width + margin_x)
                y = A4[1] - margin_y - (row + 1) * (label_height + margin_y)
                
                # Desenhar etiqueta na posição calculada
                self._draw_compact_label(c, mistura, template, x, y, label_width, label_height, config)
                
                label_count += 1
                
                # Nova página se necessário
                if page_position == labels_per_page - 1 and label_count < len(misturas):
                    c.showPage()
            
            c.save()
            buffer.seek(0)
            return buffer.getvalue()
            
        except Exception as e:
            logger.error(f"Erro ao gerar PDF em lote: {e}")
            raise
    
    def _draw_label_on_canvas(self, canvas, mistura, template, config):
        """Desenha uma etiqueta no canvas"""
        try:
            from reportlab.lib.units import mm
            from reportlab.lib.colors import HexColor, black
            from reportlab.pdfbase import pdfutils
            
            # Dimensões da etiqueta
            width = template.width * mm
            height = template.height * mm
            margin = template.margin * mm
            
            # Cores do template
            bg_color = HexColor(template.background_color)
            text_color = HexColor(template.text_color)
            accent_color = HexColor(template.accent_color)
            
            # Configurar canvas
            canvas.setFillColor(bg_color)
            canvas.rect(0, 0, width, height, fill=1)
            
            # Posicionamento inicial
            x = margin
            y = height - margin
            line_height = 15
            
            # Título principal
            canvas.setFillColor(accent_color)
            canvas.setFont("Helvetica-Bold", 16)
            canvas.drawString(x, y, "SISTEMA DE TINTAS")
            y -= line_height * 1.5
            
            # Data e hora
            canvas.setFillColor(text_color)
            canvas.setFont("Helvetica", 10)
            data_str = mistura.created_at.strftime("%d/%m/%Y %H:%M")
            canvas.drawString(x, y, data_str)
            y -= line_height * 2
            
            # Código da mistura
            canvas.setFillColor(accent_color)
            canvas.setFont("Helvetica-Bold", 20)
            canvas.drawCentredText(width/2, y, mistura.codigo_mistura)
            y -= line_height * 1.2
            
            # Código da fórmula
            canvas.setFillColor(text_color)
            canvas.setFont("Helvetica", 12)
            canvas.drawCentredText(width/2, y, mistura.formula.codigo_formula)
            y -= line_height * 2
            
            # Informações da cor
            canvas.setFillColor(text_color)
            canvas.setFont("Helvetica-Bold", 14)
            canvas.drawString(x, y, mistura.formula.cor_definida.nome_cor)
            y -= line_height
            
            canvas.setFont("Helvetica", 10)
            cor_info = f"{mistura.formula.cor_definida.familia_cor} | {mistura.formula.cor_definida.linha_produto}"
            canvas.drawString(x, y, cor_info)
            y -= line_height
            
            canvas.drawString(x, y, mistura.formula.cor_definida.cor_hex)
            y -= line_height * 1.5
            
            # Dados do cliente
            if template.include_customer:
                canvas.setFont("Helvetica-Bold", 12)
                canvas.drawString(x, y, "Cliente:")
                y -= line_height
                
                canvas.setFont("Helvetica", 11)
                canvas.drawString(x, y, mistura.cliente_nome)
                if mistura.cliente_telefone:
                    y -= line_height
                    canvas.drawString(x, y, mistura.cliente_telefone)
                y -= line_height * 1.5
            
            # Detalhes de volume e custo
            canvas.setFont("Helvetica", 10)
            details = f"Volume: {mistura.volume_solicitado}L | Custo: R$ {mistura.custo_total:.2f}"
            if mistura.loja:
                details += f" | Loja: {mistura.loja.codigo}"
            canvas.drawString(x, y, details)
            y -= line_height * 1.5
            
            # Lista de pigmentos
            if template.include_formula and mistura.itens.exists():
                canvas.setFont("Helvetica-Bold", 10)
                canvas.drawString(x, y, "Composição:")
                y -= line_height * 0.8
                
                canvas.setFont("Helvetica", 9)
                for item in mistura.itens.all()[:6]:  # Máximo 6 itens
                    pigmento_line = f"• {item.pigmento.nome}: {item.quantidade_calculada}ml"
                    canvas.drawString(x, y, pigmento_line)
                    y -= 12
                
                y -= line_height * 0.5
            
            # QR Code e Código de Barras na parte inferior
            if config.get('include_qr', True) and template.include_qr_code:
                try:
                    qr_data = self.qr_service.generate_qr_data(mistura)
                    qr_image_b64 = self.qr_service.generate_qr_image(qr_data, (60, 60))
                    
                    # Decodificar base64 e criar imagem temporária
                    qr_bytes = base64.b64decode(qr_image_b64)
                    qr_buffer = BytesIO(qr_bytes)
                    
                    # Desenhar QR Code (necessita implementação específica do ReportLab)
                    # canvas.drawImage(qr_buffer, x, 20, width=60, height=60)
                    
                except Exception as e:
                    logger.warning(f"Erro ao incluir QR Code na etiqueta: {e}")
            
            if config.get('include_barcode', True) and template.include_barcode:
                try:
                    tracking_code = self.barcode_service.generate_tracking_code(mistura)
                    
                    # Desenhar código de barras como texto (simplificado)
                    canvas.setFont("Helvetica", 8)
                    canvas.drawString(x + 70, 30, f"Código: {tracking_code}")
                    
                except Exception as e:
                    logger.warning(f"Erro ao incluir código de barras na etiqueta: {e}")
            
        except Exception as e:
            logger.error(f"Erro ao desenhar etiqueta no canvas: {e}")
            raise
    
    def _draw_compact_label(self, canvas, mistura, template, x, y, width, height, config):
        """Desenha uma etiqueta compacta para impressão em lote"""
        try:
            from reportlab.lib.colors import HexColor, black
            
            # Margem interna
            margin = 3
            
            # Fundo da etiqueta
            canvas.setFillColor(HexColor(template.background_color))
            canvas.rect(x, y, width, height, fill=1, stroke=1)
            
            # Configurar texto
            canvas.setFillColor(HexColor(template.text_color))
            
            # Título compacto
            canvas.setFont("Helvetica-Bold", 10)
            canvas.drawString(x + margin, y + height - 15, "SISTEMA TINTAS")
            
            # Código da mistura
            canvas.setFont("Helvetica-Bold", 14)
            canvas.drawCentredText(x + width/2, y + height - 30, mistura.codigo_mistura)
            
            # Nome da cor
            canvas.setFont("Helvetica-Bold", 11)
            cor_nome = mistura.formula.cor_definida.nome_cor
            if len(cor_nome) > 20:
                cor_nome = cor_nome[:20] + "..."
            canvas.drawString(x + margin, y + height - 45, cor_nome)
            
            # Cliente
            canvas.setFont("Helvetica", 9)
            cliente_nome = mistura.cliente_nome
            if len(cliente_nome) > 20:
                cliente_nome = cliente_nome[:20] + "..."
            canvas.drawString(x + margin, y + height - 58, f"Cliente: {cliente_nome}")
            
            # Volume e custo
            canvas.setFont("Helvetica", 8)
            info_line = f"Vol: {mistura.volume_solicitado}L | R$ {mistura.custo_total:.2f}"
            canvas.drawString(x + margin, y + 15, info_line)
            
            # Data
            data_str = mistura.created_at.strftime("%d/%m/%y")
            canvas.drawString(x + width - 40, y + 5, data_str)
            
        except Exception as e:
            logger.error(f"Erro ao desenhar etiqueta compacta: {e}")
            raise
    
    def save_label_file(self, pdf_bytes, filename):
        """Salva arquivo PDF da etiqueta no sistema"""
        try:
            # Definir diretório de salvamento
            labels_dir = os.path.join(settings.MEDIA_ROOT, 'labels', 'pdfs')
            os.makedirs(labels_dir, exist_ok=True)
            
            # Caminho completo do arquivo
            file_path = os.path.join(labels_dir, filename)
            
            # Salvar arquivo
            with open(file_path, 'wb') as f:
                f.write(pdf_bytes)
            
            return file_path
            
        except Exception as e:
            logger.error(f"Erro ao salvar arquivo de etiqueta {filename}: {e}")
            raise


class LabelTemplateService:
    """Serviço para gerenciamento de templates"""
    
    @staticmethod
    def create_default_templates():
        """Cria templates padrão do sistema"""
        from .models import LabelTemplate
        
        try:
            # Template Padrão
            if not LabelTemplate.objects.filter(name="Template Padrão").exists():
                LabelTemplate.objects.create(
                    name="Template Padrão",
                    description="Layout clássico com todas as informações essenciais",
                    category='standard',
                    is_default=True,
                    width=100,
                    height=150,
                    margin=5,
                    background_color='#FFFFFF',
                    text_color='#000000',
                    accent_color='#2563EB',
                )
            
            # Template Compacto
            if not LabelTemplate.objects.filter(name="Template Compacto").exists():
                LabelTemplate.objects.create(
                    name="Template Compacto",
                    description="Versão condensada para economizar papel",
                    category='compact',
                    width=75,
                    height=100,
                    margin=3,
                    background_color='#FAFAFA',
                    text_color='#000000',
                    accent_color='#059669',
                    include_cost=False,
                )
            
            # Template Premium
            if not LabelTemplate.objects.filter(name="Template Premium").exists():
                LabelTemplate.objects.create(
                    name="Template Premium",
                    description="Design sofisticado para clientes especiais",
                    category='premium',
                    width=120,
                    height=180,
                    margin=8,
                    background_color='#FFFBEB',
                    text_color='#1F2937',
                    accent_color='#F59E0B',
                    font_family='Times',
                )
            
            logger.info("Templates padrão criados com sucesso")
            
        except Exception as e:
            logger.error(f"Erro ao criar templates padrão: {e}")
            raise
    
    @staticmethod
    def export_template(template):
        """Exporta template para formato JSON"""
        try:
            template_data = {
                'name': template.name,
                'description': template.description,
                'category': template.category,
                'dimensions': {
                    'width': template.width,
                    'height': template.height,
                    'margin': template.margin,
                },
                'colors': {
                    'background': template.background_color,
                    'text': template.text_color,
                    'accent': template.accent_color,
                },
                'font': {
                    'family': template.font_family,
                    'size_base': template.font_size_base,
                },
                'elements': {
                    'qr_code': template.include_qr_code,
                    'barcode': template.include_barcode,
                    'logo': template.include_logo,
                    'formula': template.include_formula,
                    'customer': template.include_customer,
                    'cost': template.include_cost,
                },
                'layout_config': template.layout_config,
                'exported_at': timezone.now().isoformat(),
                'version': '1.0',
            }
            
            return json.dumps(template_data, indent=2, ensure_ascii=False)
            
        except Exception as e:
            logger.error(f"Erro ao exportar template {template.id}: {e}")
            raise
    
    @staticmethod
    def import_template(json_data, created_by=None):
        """Importa template de dados JSON"""
        try:
            from .models import LabelTemplate
            
            data = json.loads(json_data)
            
            # Validar estrutura básica
            required_fields = ['name', 'category', 'dimensions', 'colors']
            for field in required_fields:
                if field not in data:
                    raise ValueError(f"Campo obrigatório ausente: {field}")
            
            # Criar template
            template = LabelTemplate.objects.create(
                name=data['name'],
                description=data.get('description', ''),
                category=data['category'],
                width=data['dimensions']['width'],
                height=data['dimensions']['height'],
                margin=data['dimensions'].get('margin', 5),
                background_color=data['colors']['background'],
                text_color=data['colors']['text'],
                accent_color=data['colors']['accent'],
                font_family=data.get('font', {}).get('family', 'Arial'),
                font_size_base=data.get('font', {}).get('size_base', 12),
                include_qr_code=data.get('elements', {}).get('qr_code', True),
                include_barcode=data.get('elements', {}).get('barcode', True),
                include_logo=data.get('elements', {}).get('logo', True),
                include_formula=data.get('elements', {}).get('formula', True),
                include_customer=data.get('elements', {}).get('customer', True),
                include_cost=data.get('elements', {}).get('cost', False),
                layout_config=data.get('layout_config', {}),
                created_by=created_by,
            )
            
            return template
            
        except (json.JSONDecodeError, KeyError, ValueError) as e:
            logger.error(f"Erro ao importar template: {e}")
            raise
        except Exception as e:
            logger.error(f"Erro interno ao importar template: {e}")
            raise
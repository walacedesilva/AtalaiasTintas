#!/usr/bin/env python
"""
Teste Final - Sistema de Etiquetas

Gera uma etiqueta real usando os dados de teste criados.
Demonstra o fluxo completo: mistura → etiqueta → PDF
"""

import os
import sys
import django
from decimal import Decimal

# Setup Django
sys.path.append('e:/SIAFIC/AtalaiasTintas/backend')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'tintas_system.settings')
django.setup()

from apps.tintometry.models import MisturaTinta
from apps.tintometry.labels.services import LabelGeneratorService

def gerar_etiqueta_teste():
    """Gera etiqueta da mistura de teste"""
    print("🎯 TESTE FINAL - GERAÇÃO DE ETIQUETA")
    print("=" * 50)
    
    # 1. Buscar mistura de teste
    try:
        mistura = MisturaTinta.objects.get(codigo_mistura="MIX2026001")
        print(f"✅ Mistura encontrada: {mistura.codigo_mistura}")
        print(f"   Cliente: {mistura.cliente_nome}")
        print(f"   Fórmula: {mistura.formula.nome_formula}")
        print(f"   Volume: {mistura.volume_solicitado}L")
        print()
    except MisturaTinta.DoesNotExist:
        print("❌ Mistura de teste não encontrada!")
        print("Execute primeiro: python setup_dados_teste.py")
        return
    
    # 2. Inicializar serviço de etiquetas
    label_service = LabelGeneratorService()
    
    # 3. Gerar dados da etiqueta
    print("🏷️ Gerando dados da etiqueta...")
    label_data = label_service.generate_label_data(mistura.id)
    
    print(f"   QR Code gerado: ✅")
    print(f"   Código de barras: {label_data['barcode']}")
    print(f"   Template: {label_data.get('template', {}).get('id', 'default')}")
    print()
    
    # 4. Gerar PDF
    print("📄 Gerando PDF da etiqueta...")
    from apps.tintometry.labels.renderers import LabelPDFRenderer
    from apps.tintometry.labels.templates import TemplateManager
    
    renderer = LabelPDFRenderer()
    template_manager = TemplateManager()
    templates = template_manager.get_default_templates()
    template = templates['default']
    pdf_buffer = renderer.render_label_pdf(label_data, template)
    
    # 5. Salvar PDF de teste
    output_path = "etiqueta_teste_final.pdf"
    with open(output_path, 'wb') as f:
        f.write(pdf_buffer.getvalue())
    
    print(f"✅ PDF gerado com sucesso!")
    print(f"   Arquivo salvo em: {output_path}")
    print(f"   Tamanho: {len(pdf_buffer.getvalue())} bytes")
    print()
    
    # 6. Informações detalhadas da etiqueta
    print("📋 DADOS DA ETIQUETA:")
    print("-" * 30)
    print(f"Código Mistura: {label_data['codigo_mistura']}")
    print(f"Data/Hora: {label_data['data_producao']}")
    print(f"Cor: {label_data['cor_nome']} (#{label_data['cor_hex']})")
    print(f"Cliente: {label_data['cliente_nome']}")
    print(f"Volume: {label_data['volume_produzido']}L")
    print(f"Base: {label_data['base_nome']}")
    print()
    print("Pigmentos utilizados:")
    for pigmento in label_data['pigmentos']:
        print(f"  • {pigmento['nome']}: {pigmento['quantidade']}ml")
    print()
    
    # 7. Informações técnicas
    print("⚙️ INFORMAÇÕES TÉCNICAS:")
    print("-" * 30)
    print(f"QR Code: {len(label_data['qr_data'])} caracteres")
    print(f"Compressão: {'Ativada' if 'encoded' in label_data['qr_data'] else 'Desativada'}")
    print(f"Loja: {label_data['loja']['nome']}")
    print(f"Operador: {label_data['operador']}")
    
    print()
    print("🎉 TESTE CONCLUÍDO COM SUCESSO!")
    print("=" * 50)

if __name__ == "__main__":
    gerar_etiqueta_teste()
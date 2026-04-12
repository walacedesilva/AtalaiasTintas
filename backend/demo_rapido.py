#!/usr/bin/env python
"""
Demo Rápido - Sistema de Etiquetas FUNCIONANDO

Testa apenas as funções básicas que sabemos que funcionam.
"""

import os
import sys
import django

# Setup Django
sys.path.append('e:/SIAFIC/AtalaiasTintas/backend')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'tintas_system.settings')
django.setup()

from apps.tintometry.models import MisturaTinta
from apps.tintometry.labels.services import QRCodeService, BarCodeService

def demo_rapido():
    """Demo rápido do que funciona"""
    print("🎯 DEMO RÁPIDO - SISTEMA DE ETIQUETAS")
    print("=" * 50)
    
    # 1. Verificar mistura
    try:
        mistura = MisturaTinta.objects.get(codigo_mistura="MIX2026001")
        print(f"✅ Mistura: {mistura.codigo_mistura}")
        print(f"   Cliente: {mistura.cliente_nome}")
        print(f"   Volume: {mistura.volume_solicitado}L")
        print(f"   Situação: {mistura.situacao}")
        print()
    except MisturaTinta.DoesNotExist:
        print("❌ Mistura não encontrada!")
        return
    
    # 2. Testar QR Code Service
    print("🔲 Testando QR Code Service...")
    qr_service = QRCodeService()
    qr_data = qr_service.generate_mixture_qr_data(mistura)
    print(f"   ✅ QR Data: {len(str(qr_data))} caracteres")
    
    qr_image = qr_service.create_qr_code(qr_data)
    print(f"   ✅ QR Image: {len(qr_image)} bytes")
    
    # 3. Testar BarCode Service  
    print("🏷️ Testando BarCode Service...")
    barcode_service = BarCodeService()
    tracking_code = barcode_service.generate_tracking_code(mistura)
    print(f"   ✅ Tracking Code: {tracking_code}")
    
    barcode_image = barcode_service.create_barcode(tracking_code)
    print(f"   ✅ Barcode Image: {len(barcode_image)} bytes")
    
    # 4. Informações da mistura
    print()
    print("📋 DADOS DA MISTURA:")
    print("-" * 30)
    print(f"ID: {mistura.id}")
    print(f"Fórmula: {mistura.formula.nome_formula}")
    print(f"Cor: {mistura.formula.cor_definida.nome_cor}")
    print(f"Cor Hex: #{mistura.formula.cor_definida.r:02x}{mistura.formula.cor_definida.g:02x}{mistura.formula.cor_definida.b:02x}")
    print(f"Custo Total: R$ {mistura.custo_total}")
    print()
    
    # 5. Pigmentos utilizados
    print("🎨 PIGMENTOS UTILIZADOS:")
    print("-" * 30)
    for item in mistura.itens.all():
        print(f"• {item.pigmento.nome}: {item.quantidade_calculada}ml")
        print(f"  Cor: {item.pigmento.cor_base}")
        print(f"  Custo: R$ {item.custo_total}")
        print()
    
    print("🎉 DEMO CONCLUÍDO!")
    print("Sistema de etiquetas básico funcionando perfeitamente!")
    print("=" * 50)

if __name__ == "__main__":
    demo_rapido()
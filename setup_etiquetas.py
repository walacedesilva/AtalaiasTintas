#!/usr/bin/env python
"""
Script de setup do sistema de etiquetas
Execute este script após instalar as dependências para configurar o sistema
"""
import os
import sys
import django
from pathlib import Path

# Adicionar o diretório backend ao path
backend_dir = Path(__file__).parent.parent.parent.parent / 'backend'
sys.path.append(str(backend_dir))

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'tintas_system.settings')
django.setup()

from django.contrib.auth.models import User
from django.core.management import execute_from_command_line
from apps.tintometry.labels.services import LabelTemplateService
from apps.tintometry.labels.models import LabelTemplate, PrinterConfiguration


def create_superuser_if_needed():
    """Cria superusuário se não existir"""
    if not User.objects.filter(is_superuser=True).exists():
        print("Criando superusuário padrão...")
        User.objects.create_superuser(
            username='admin',
            email='admin@ataliaistintas.com',
            password='admin123',
            first_name='Administrador',
            last_name='Sistema'
        )
        print("✓ Superusuário criado: admin / admin123")
    else:
        print("✓ Superusuário já existe")


def create_default_templates():
    """Cria templates padrão se não existirem"""
    if not LabelTemplate.objects.exists():
        print("Criando templates padrão...")
        try:
            LabelTemplateService.create_default_templates()
            print("✓ Templates padrão criados")
        except Exception as e:
            print(f"✗ Erro ao criar templates: {e}")
    else:
        print("✓ Templates já existem")


def create_default_printer():
    """Cria configuração de impressora padrão"""
    if not PrinterConfiguration.objects.exists():
        print("Criando configuração de impressora padrão...")
        try:
            PrinterConfiguration.objects.create(
                name='Impressora Padrão',
                printer_type='inkjet',
                system_name='Impressora padrão do sistema',
                max_width_mm=210,
                max_height_mm=297,
                dpi=300,
                supports_color=True,
                is_active=True,
                is_default=True
            )
            print("✓ Configuração de impressora criada")
        except Exception as e:
            print(f"✗ Erro ao criar impressora: {e}")
    else:
        print("✓ Configuração de impressora já existe")


def run_migrations():
    """Executa migrações do Django"""
    print("Executando migrações...")
    try:
        execute_from_command_line(['manage.py', 'makemigrations'])
        execute_from_command_line(['manage.py', 'migrate'])
        print("✓ Migrações executadas")
    except Exception as e:
        print(f"✗ Erro nas migrações: {e}")


def collect_static():
    """Coleta arquivos estáticos"""
    print("Coletando arquivos estáticos...")
    try:
        execute_from_command_line(['manage.py', 'collectstatic', '--noinput'])
        print("✓ Arquivos estáticos coletados")
    except Exception as e:
        print(f"⚠ Aviso nos arquivos estáticos: {e}")


def main():
    """Executa setup completo"""
    print("=== SETUP DO SISTEMA DE ETIQUETAS ===")
    print()
    
    # Verificar dependências
    try:
        import qrcode
        import barcode
        import reportlab
        print("✓ Dependências necessárias instaladas")
    except ImportError as e:
        print(f"✗ Dependência faltando: {e}")
        print("Execute: pip install qrcode[pil] python-barcode[images] reportlab")
        return
    
    print()
    
    # Executar configurações
    run_migrations()
    create_superuser_if_needed() 
    create_default_templates()
    create_default_printer()
    collect_static()
    
    print()
    print("=== SETUP CONCLUÍDO ===")
    print()
    print("Sistema de etiquetas configurado com sucesso!")
    print()
    print("Próximos passos:")
    print("1. Execute: python manage.py runserver")
    print("2. Acesse: http://127.0.0.1:8000/admin/ (admin / admin123)")
    print("3. Acesse: http://127.0.0.1:8000/etiquetas/ (interface web)")
    print()
    print("URLs disponíveis:")
    print("- /etiquetas/ - Dashboard principal")
    print("- /etiquetas/misturas/ - Lista de misturas")
    print("- /etiquetas/nova-mistura/ - Criar nova mistura")
    print("- /etiquetas/templates/ - Gerenciar templates")
    print("- /admin/ - Administração Django")
    print()


if __name__ == '__main__':
    main()
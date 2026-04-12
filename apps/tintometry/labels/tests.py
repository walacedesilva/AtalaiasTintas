"""
Testes para o sistema de etiquetas
"""
from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from apps.tintometry.models import MisturaTinta, FormulaTintometrica, CorDefinida, BaseProduct
from apps.companies.models import Loja
from .models import LabelTemplate, LabelPrintJob
from .services import QRCodeService, BarcodeService, LabelGeneratorService


class LabelSystemTestCase(TestCase):
    """Testes básicos do sistema de etiquetas"""
    
    def setUp(self):
        """Configuração inicial dos testes"""
        # Criar usuário de teste
        self.user = User.objects.create_user(
            username='operador_teste',
            password='senha123',
            first_name='João',
            last_name='Silva'
        )
        
        # Cliente para requests
        self.client = Client()
        self.client.login(username='operador_teste', password='senha123')
        
        # Criar dados de teste
        self.loja = Loja.objects.create(
            nome='Loja Teste',
            codigo='LT001',
            is_active=True
        )
        
        # Mock dos objetos necessários (adapte conforme seus modelos)
        # self.cor_definida = CorDefinida.objects.create(...)
        # self.formula = FormulaTintometrica.objects.create(...)
        # self.mistura = MisturaTinta.objects.create(...)
    
    def test_dashboard_access(self):
        """Testa acesso ao dashboard"""
        response = self.client.get(reverse('etiquetas:dashboard'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Dashboard')
    
    def test_misturas_list_access(self):
        """Testa acesso à lista de misturas"""
        response = self.client.get(reverse('etiquetas:misturas'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Misturas')
    
    def test_nova_mistura_access(self):
        """Testa acesso ao formulário de nova mistura"""
        response = self.client.get(reverse('etiquetas:nova_mistura'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Nova Mistura')
    
    def test_template_creation(self):
        """Testa criação de template"""
        template = LabelTemplate.objects.create(
            name='Template Teste',
            description='Template para testes',
            category='standard',
            width=100,
            height=150,
            created_by=self.user
        )
        
        self.assertEqual(template.name, 'Template Teste')
        self.assertEqual(template.category, 'standard')
        self.assertTrue(template.is_active)


class QRCodeServiceTestCase(TestCase):
    """Testes para o serviço de QR Code"""
    
    def setUp(self):
        self.qr_service = QRCodeService()
    
    def test_qr_service_initialization(self):
        """Testa inicialização do serviço"""
        self.assertIsInstance(self.qr_service, QRCodeService)
        self.assertIsNotNone(self.qr_service.qr_config)


class BarcodeServiceTestCase(TestCase):
    """Testes para o serviço de código de barras"""
    
    def setUp(self):
        self.barcode_service = BarcodeService()
    
    def test_barcode_service_initialization(self):
        """Testa inicialização do serviço"""
        self.assertIsInstance(self.barcode_service, BarcodeService)
        self.assertEqual(self.barcode_service.barcode_type, 'code128')


class LabelGeneratorServiceTestCase(TestCase):
    """Testes para o serviço de geração de etiquetas"""
    
    def setUp(self):
        self.generator_service = LabelGeneratorService()
    
    def test_generator_service_initialization(self):
        """Testa inicialização do serviço"""
        self.assertIsInstance(self.generator_service, LabelGeneratorService)
        self.assertIsNotNone(self.generator_service.qr_service)
        self.assertIsNotNone(self.generator_service.barcode_service)


# Teste de integração simplificado
class IntegrationTestCase(TestCase):
    """Teste de integração básico"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='teste_integração',
            password='senha123'
        )
        self.client = Client()
        self.client.login(username='teste_integração', password='senha123')
    
    def test_full_workflow_access(self):
        """Testa acesso a todas as páginas principais"""
        urls_to_test = [
            'etiquetas:dashboard',
            'etiquetas:misturas', 
            'etiquetas:nova_mistura',
            'etiquetas:templates',
        ]
        
        for url_name in urls_to_test:
            with self.subTest(url=url_name):
                response = self.client.get(reverse(url_name))
                self.assertEqual(response.status_code, 200)
from django.db import models
from django.core.validators import RegexValidator
from apps.core.models import TimeStampedModel, User


class Empresa(TimeStampedModel):
    """Modelo para gestão multi-empresas"""
    
    # Dados básicos da empresa
    cnpj = models.CharField(
        max_length=14, 
        unique=True,
        validators=[RegexValidator(r'^\d{14}$', 'CNPJ deve ter 14 dígitos')]
    )
    razao_social = models.CharField(max_length=200)
    nome_fantasia = models.CharField(max_length=200, null=True, blank=True)
    inscricao_estadual = models.CharField(max_length=20, null=True, blank=True)
    inscricao_municipal = models.CharField(max_length=20, null=True, blank=True)
    
    # Tipo de empresa
    tipo_empresa = models.CharField(max_length=1, choices=[
        ('M', 'Matriz'),
        ('F', 'Filial')
    ], default='M')
    
    empresa_matriz = models.ForeignKey(
        'self', 
        on_delete=models.CASCADE,
        null=True, 
        blank=True,
        related_name='filiais'
    )
    
    # Dados de contato
    telefone = models.CharField(max_length=15, null=True, blank=True)
    email = models.EmailField(null=True, blank=True)
    website = models.URLField(null=True, blank=True)
    
    # Endereço
    cep = models.CharField(max_length=8, null=True, blank=True)
    endereco = models.CharField(max_length=200, null=True, blank=True)
    numero = models.CharField(max_length=10, null=True, blank=True)
    complemento = models.CharField(max_length=100, null=True, blank=True)
    bairro = models.CharField(max_length=100, null=True, blank=True)
    cidade = models.CharField(max_length=100, null=True, blank=True)
    uf = models.CharField(max_length=2, null=True, blank=True)
    
    # Status
    ativa = models.BooleanField(default=True)
    
    def __str__(self):
        return f"{self.nome_fantasia or self.razao_social} ({self.cnpj})"
    
    class Meta:
        verbose_name = 'Empresa'
        verbose_name_plural = 'Empresas'


class Loja(TimeStampedModel):
    """Modelo para gestão de múltiplas lojas por empresa"""
    
    empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE, related_name='lojas')
    codigo = models.CharField(max_length=20, unique=True)
    nome = models.CharField(max_length=100)
    descricao = models.TextField(null=True, blank=True)
    
    # Dados de contato
    telefone = models.CharField(max_length=15, null=True, blank=True)
    email = models.EmailField(null=True, blank=True)
    responsavel = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='lojas_responsavel'
    )
    
    # Endereço completo
    cep = models.CharField(max_length=8)
    endereco = models.CharField(max_length=200)
    numero = models.CharField(max_length=10)
    complemento = models.CharField(max_length=100, null=True, blank=True)
    bairro = models.CharField(max_length=100)
    cidade = models.CharField(max_length=100)
    uf = models.CharField(max_length=2)
    
    # Coordenadas para localização
    latitude = models.DecimalField(max_digits=10, decimal_places=8, null=True, blank=True)
    longitude = models.DecimalField(max_digits=11, decimal_places=8, null=True, blank=True)
    
    # Configurações fiscais específicas da loja
    config_fiscal = models.JSONField(default=dict)  # SAT, NFCe, NFe, etc.
    
    # Configurações operacionais
    horario_funcionamento = models.JSONField(default=dict)  # Horários por dia da semana
    aceita_delivery = models.BooleanField(default=False)
    raio_delivery_km = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    
    # Status
    ativa = models.BooleanField(default=True)
    data_abertura = models.DateField(null=True, blank=True)
    
    def __str__(self):
        return f"{self.nome} - {self.empresa.nome_fantasia or self.empresa.razao_social}"
    
    class Meta:
        verbose_name = 'Loja'
        verbose_name_plural = 'Lojas'
        unique_together = ['empresa', 'codigo']


class UsuarioLoja(TimeStampedModel):
    """Relacionamento entre usuários e lojas com permissões específicas"""
    
    usuario = models.ForeignKey(User, on_delete=models.CASCADE)
    loja = models.ForeignKey(Loja, on_delete=models.CASCADE)
    empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE)
    
    # Permissões específicas para esta loja
    pode_vender = models.BooleanField(default=True)
    pode_gerenciar_estoque = models.BooleanField(default=False)
    pode_acessar_caixa = models.BooleanField(default=False)
    pode_dar_desconto = models.BooleanField(default=False)
    limite_desconto_percentual = models.DecimalField(
        max_digits=5, 
        decimal_places=2, 
        null=True, 
        blank=True
    )
    
    # Status
    ativo = models.BooleanField(default=True)
    data_inicio = models.DateField(auto_now_add=True)
    data_fim = models.DateField(null=True, blank=True)
    
    class Meta:
        unique_together = ['usuario', 'loja']
        verbose_name = 'Usuário da Loja'
        verbose_name_plural = 'Usuários das Lojas'

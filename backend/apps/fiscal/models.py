from django.db import models
from django.core.validators import RegexValidator
from apps.core.models import TimeStampedModel
from apps.companies.models import Empresa, Loja
from apps.sales.models import Venda
import uuid


class ConfiguracaoFiscal(TimeStampedModel):
    """Configurações fiscais por empresa/loja"""
    
    empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE)
    loja = models.ForeignKey(Loja, on_delete=models.CASCADE, null=True, blank=True)
    
    # Regime tributário
    regime_tributario = models.CharField(max_length=20, choices=[
        ('SIMPLES_NACIONAL', 'Simples Nacional'),
        ('LUCRO_PRESUMIDO', 'Lucro Presumido'),
        ('LUCRO_REAL', 'Lucro Real'),
        ('MEI', 'Microempreendedor Individual'),
    ])
    
    # Certificado digital
    certificado_a1_arquivo = models.FileField(upload_to='certificados/', null=True, blank=True)
    certificado_senha = models.CharField(max_length=100, null=True, blank=True)
    certificado_validade = models.DateField(null=True, blank=True)
    
    # Configurações de NFCe
    nfce_ativo = models.BooleanField(default=False)
    nfce_ambiente = models.CharField(max_length=15, choices=[
        ('PRODUCAO', 'Produção'),
        ('HOMOLOGACAO', 'Homologação'),
    ], default='HOMOLOGACAO')
    nfce_serie = models.IntegerField(default=1)
    nfce_numero_atual = models.IntegerField(default=1)
    
    # Configurações SAT
    sat_ativo = models.BooleanField(default=False)
    sat_codigo_ativacao = models.CharField(max_length=50, null=True, blank=True)
    sat_numero_caixa = models.IntegerField(null=True, blank=True)
    
    # Configurações de NFe
    nfe_ativo = models.BooleanField(default=False)
    nfe_ambiente = models.CharField(max_length=15, choices=[
        ('PRODUCAO', 'Produção'),
        ('HOMOLOGACAO', 'Homologação'),
    ], default='HOMOLOGACAO')
    nfe_serie = models.IntegerField(default=1)
    nfe_numero_atual = models.IntegerField(default=1)
    
    class Meta:
        unique_together = ['empresa', 'loja']
        verbose_name = 'Configuração Fiscal'
        verbose_name_plural = 'Configurações Fiscais'


class NotaFiscal(TimeStampedModel):
    """Notas fiscais emitidas"""
    
    TIPOS_NOTA = [
        ('NFCE', 'NFCe - Nota Fiscal de Consumidor Eletrônica'),
        ('NFE', 'NFe - Nota Fiscal Eletrônica'),
        ('SAT', 'SAT - CF-e'),
    ]
    
    SITUACOES = [
        ('RASCUNHO', 'Rascunho'),
        ('PENDENTE', 'Pendente de Envio'),
        ('ENVIADA', 'Enviada'),
        ('AUTORIZADA', 'Autorizada'),
        ('CANCELADA', 'Cancelada'),
        ('REJEITADA', 'Rejeitada'),
        ('INUTILIZADA', 'Inutilizada'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Dados básicos
    loja = models.ForeignKey(Loja, on_delete=models.PROTECT)
    venda = models.ForeignKey(
        Venda, 
        on_delete=models.PROTECT,
        related_name='notas_fiscais'
    )
    
    # Identificação da nota
    tipo_nota = models.CharField(max_length=10, choices=TIPOS_NOTA)
    serie = models.IntegerField()
    numero = models.IntegerField()
    chave_acesso = models.CharField(max_length=44, unique=True, null=True, blank=True)
    
    # Datas
    data_emissao = models.DateTimeField(auto_now_add=True)
    data_envio = models.DateTimeField(null=True, blank=True)
    data_autorizacao = models.DateTimeField(null=True, blank=True)
    data_cancelamento = models.DateTimeField(null=True, blank=True)
    
    # Status
    situacao = models.CharField(max_length=20, choices=SITUACOES, default='RASCUNHO')
    protocolo_autorizacao = models.CharField(max_length=20, null=True, blank=True)
    
    # Valores
    valor_total_produtos = models.DecimalField(max_digits=12, decimal_places=2)
    valor_total_nota = models.DecimalField(max_digits=12, decimal_places=2)
    valor_desconto = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    
    # Tributos
    base_calculo_icms = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    valor_icms = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    valor_pis = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    valor_cofins = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    
    # XMLs
    xml_envio = models.TextField(null=True, blank=True)
    xml_retorno = models.TextField(null=True, blank=True)
    xml_cancelamento = models.TextField(null=True, blank=True)
    
    # Observações
    informacoes_adicionais = models.TextField(null=True, blank=True)
    motivo_cancelamento = models.CharField(max_length=255, null=True, blank=True)
    
    def __str__(self):
        return f"{self.tipo_nota} {self.serie}/{self.numero}"
    
    class Meta:
        verbose_name = 'Nota Fiscal'
        verbose_name_plural = 'Notas Fiscais'
        unique_together = ['loja', 'tipo_nota', 'serie', 'numero']
        ordering = ['-created_at']


class ItemNotaFiscal(TimeStampedModel):
    """Itens das notas fiscais"""
    
    nota_fiscal = models.ForeignKey(
        NotaFiscal, 
        on_delete=models.CASCADE,
        related_name='itens'
    )
    
    # Identificação do produto
    codigo_produto = models.CharField(max_length=50)
    descricao = models.CharField(max_length=200)
    
    # Classificação fiscal
    ncm = models.CharField(max_length=10)
    cest = models.CharField(max_length=10, null=True, blank=True)
    cfop = models.CharField(max_length=4)
    
    # Quantidades e valores
    quantidade = models.DecimalField(max_digits=10, decimal_places=2)
    unidade = models.CharField(max_length=10)
    valor_unitario = models.DecimalField(max_digits=10, decimal_places=2)
    valor_total = models.DecimalField(max_digits=12, decimal_places=2)
    valor_desconto = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    # ICMS
    cst_icms = models.CharField(max_length=3, null=True, blank=True)
    aliquota_icms = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    base_calculo_icms = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    valor_icms = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    # PIS
    cst_pis = models.CharField(max_length=2, null=True, blank=True)
    aliquota_pis = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    base_calculo_pis = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    valor_pis = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    # COFINS
    cst_cofins = models.CharField(max_length=2, null=True, blank=True)
    aliquota_cofins = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    base_calculo_cofins = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    valor_cofins = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    # Ordem do item na nota
    numero_item = models.IntegerField()
    
    class Meta:
        unique_together = ['nota_fiscal', 'numero_item']
        ordering = ['numero_item']


class TabelaNCM(TimeStampedModel):
    """Tabela de códigos NCM para classificação fiscal"""
    
    codigo_ncm = models.CharField(max_length=10, unique=True)
    descricao = models.CharField(max_length=500)
    aliquota_nacional = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    aliquota_importacao = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    
    # Para facilitar pesquisas
    categoria = models.CharField(max_length=100, null=True, blank=True)
    subcategoria = models.CharField(max_length=100, null=True, blank=True)
    
    ativo = models.BooleanField(default=True)
    
    def __str__(self):
        return f"{self.codigo_ncm} - {self.descricao[:50]}"
    
    class Meta:
        verbose_name = 'NCM'
        verbose_name_plural = 'Códigos NCM'
        ordering = ['codigo_ncm']


class TabelaCFOP(TimeStampedModel):
    """Tabela de códigos CFOP"""
    
    codigo_cfop = models.CharField(max_length=4, unique=True)
    descricao = models.CharField(max_length=500)
    aplicacao = models.CharField(max_length=20, choices=[
        ('ENTRADA', 'Entrada'),
        ('SAIDA', 'Saída'),
        ('AMBOS', 'Entrada e Saída'),
    ])
    
    # Classificação
    dentro_estado = models.BooleanField(default=True)
    fora_estado = models.BooleanField(default=False)
    exterior = models.BooleanField(default=False)
    
    ativo = models.BooleanField(default=True)
    
    def __str__(self):
        return f"{self.codigo_cfop} - {self.descricao[:50]}"
    
    class Meta:
        verbose_name = 'CFOP'
        verbose_name_plural = 'Códigos CFOP'
        ordering = ['codigo_cfop']


class LogEventosFiscais(TimeStampedModel):
    """Log de eventos fiscais para auditoria"""
    
    TIPOS_EVENTO = [
        ('EMISSAO', 'Emissão de Nota'),
        ('CANCELAMENTO', 'Cancelamento'),
        ('INUTILIZACAO', 'Inutilização'),
        ('CONSULTA_STATUS', 'Consulta Status'),
        ('DOWNLOAD_XML', 'Download XML'),
        ('ERRO_TRANSMISSAO', 'Erro na Transmissão'),
    ]
    
    nota_fiscal = models.ForeignKey(
        NotaFiscal, 
        on_delete=models.CASCADE,
        related_name='logs_eventos',
        null=True,
        blank=True
    )
    
    tipo_evento = models.CharField(max_length=20, choices=TIPOS_EVENTO)
    descricao = models.TextField()
    
    # Dados técnicos
    codigo_retorno = models.CharField(max_length=10, null=True, blank=True)
    mensagem_retorno = models.TextField(null=True, blank=True)
    xml_envio = models.TextField(null=True, blank=True)
    xml_retorno = models.TextField(null=True, blank=True)
    
    # Usuário responsável
    usuario = models.ForeignKey(
        'core.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    
    # Dados da requisição
    ip_origin = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(null=True, blank=True)
    
    class Meta:
        verbose_name = 'Log de Evento Fiscal'
        verbose_name_plural = 'Logs de Eventos Fiscais'
        ordering = ['-created_at']


class ContingenciaFiscal(TimeStampedModel):
    """Controle de contingência fiscal"""
    
    TIPOS_CONTINGENCIA = [
        ('OFFLINE', 'Offline'),
        ('SVC_AN', 'SVC-AN'),
        ('SVC_RS', 'SVC-RS'),
        ('EPEC', 'EPEC'),
    ]
    
    loja = models.ForeignKey(Loja, on_delete=models.CASCADE)
    tipo_contingencia = models.CharField(max_length=20, choices=TIPOS_CONTINGENCIA)
    
    # Período
    data_inicio = models.DateTimeField()
    data_fim = models.DateTimeField(null=True, blank=True)
    
    # Justificativa
    motivo = models.TextField()
    numero_protocolo = models.CharField(max_length=50, null=True, blank=True)
    
    # Status
    ativa = models.BooleanField(default=True)
    
    # Usuário responsável
    usuario_ativacao = models.ForeignKey(
        'core.User',
        on_delete=models.PROTECT,
        related_name='contingencias_ativadas'
    )
    usuario_desativacao = models.ForeignKey(
        'core.User',
        on_delete=models.PROTECT,
        related_name='contingencias_desativadas',
        null=True,
        blank=True
    )
    
    class Meta:
        verbose_name = 'Contingência Fiscal'
        verbose_name_plural = 'Contingências Fiscais'
        ordering = ['-created_at']

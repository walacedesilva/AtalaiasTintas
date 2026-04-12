from django.db import models
from django.core.validators import URLValidator
from apps.core.models import TimeStampedModel
from apps.companies.models import Loja
from apps.inventory.models import ProdutoVariacao
from apps.sales.models import PedidoVenda
import uuid


class Marketplace(TimeStampedModel):
    """Cadastro de marketplaces integrados"""
    
    nome = models.CharField(max_length=100, unique=True)
    codigo = models.CharField(max_length=20, unique=True)
    
    # URLs da API
    url_base_api = models.URLField()
    url_sandbox = models.URLField(null=True, blank=True)
    
    # Configurações de autenticação
    tipo_autenticacao = models.CharField(max_length=20, choices=[
        ('API_KEY', 'Chave API'),
        ('OAUTH', 'OAuth 2.0'),
        ('TOKEN', 'Token Bearer'),
        ('BASIC', 'Autenticação Básica'),
    ])
    
    # Documentação
    url_documentacao = models.URLField(null=True, blank=True)
    versao_api = models.CharField(max_length=20, null=True, blank=True)
    
    # Configurações específicas
    permite_estoque = models.BooleanField(default=True)
    permite_preco = models.BooleanField(default=True)
    permite_descricao = models.BooleanField(default=True)
    permite_imagem = models.BooleanField(default=True)
    
    # Limites e restrições
    limite_requisicoes_minuto = models.IntegerField(null=True, blank=True)
    tamanho_maximo_lote = models.IntegerField(default=10)
    
    # Taxa do marketplace
    taxa_comissao = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    taxa_fixa_venda = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    
    # Status
    ativo = models.BooleanField(default=True)
    
    def __str__(self):
        return self.nome
    
    class Meta:
        verbose_name = 'Marketplace'
        verbose_name_plural = 'Marketplaces'


class ContaMarketplace(TimeStampedModel):
    """Contas/lojas configuradas em cada marketplace"""
    
    loja = models.ForeignKey(Loja, on_delete=models.CASCADE)
    marketplace = models.ForeignKey(Marketplace, on_delete=models.CASCADE)
    
    # Identificação da conta
    id_vendedor = models.CharField(max_length=100)
    nome_loja_marketplace = models.CharField(max_length=200)
    
    # Credenciais de acesso
    client_id = models.CharField(max_length=200, null=True, blank=True)
    client_secret = models.CharField(max_length=200, null=True, blank=True)
    api_key = models.CharField(max_length=200, null=True, blank=True)
    access_token = models.TextField(null=True, blank=True)
    refresh_token = models.TextField(null=True, blank=True)
    token_expira_em = models.DateTimeField(null=True, blank=True)
    
    # Configurações específicas
    ambiente = models.CharField(max_length=20, choices=[
        ('PRODUCAO', 'Produção'),
        ('SANDBOX', 'Sandbox/Teste'),
    ], default='SANDBOX')
    
    # Configurações de sincronização
    sincronizar_estoque = models.BooleanField(default=True)
    sincronizar_precos = models.BooleanField(default=True)
    sincronizar_produtos = models.BooleanField(default=False)  # Manual por padrão
    
    # Frequência de sincronização (minutos)
    frequencia_sync_estoque = models.IntegerField(default=30)
    frequencia_sync_precos = models.IntegerField(default=60)
    
    # Última sincronização
    ultima_sync_estoque = models.DateTimeField(null=True, blank=True)
    ultima_sync_precos = models.DateTimeField(null=True, blank=True)
    ultima_sync_pedidos = models.DateTimeField(null=True, blank=True)
    
    # Status da conta
    ativa = models.BooleanField(default=True)
    erro_ultima_sincronizacao = models.TextField(null=True, blank=True)
    
    def __str__(self):
        return f"{self.loja.nome} - {self.marketplace.nome}"
    
    class Meta:
        unique_together = ['loja', 'marketplace']
        verbose_name = 'Conta Marketplace'
        verbose_name_plural = 'Contas Marketplace'


class ProdutoMarketplace(TimeStampedModel):
    """Vinculação entre produtos locais e produtos nos marketplaces"""
    
    SITUACOES = [
        ('ATIVO', 'Ativo'),
        ('PAUSADO', 'Pausado'),
        ('ERRO', 'Erro de Sincronização'),
        ('PENDENTE', 'Pendente Aprovação'),
        ('REJEITADO', 'Rejeitado'),
    ]
    
    conta_marketplace = models.ForeignKey(ContaMarketplace, on_delete=models.CASCADE)
    produto_variacao = models.ForeignKey(ProdutoVariacao, on_delete=models.CASCADE)
    
    # IDs no marketplace
    id_produto_marketplace = models.CharField(max_length=100)
    sku_marketplace = models.CharField(max_length=100, null=True, blank=True)
    
    # Dados específicos para o marketplace
    titulo_anuncio = models.CharField(max_length=200)
    descricao_anuncio = models.TextField()
    categoria_marketplace = models.CharField(max_length=100, null=True, blank=True)
    
    # Preços específicos
    preco_marketplace = models.DecimalField(max_digits=10, decimal_places=2)
    preco_promocional = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    data_inicio_promocao = models.DateTimeField(null=True, blank=True)
    data_fim_promocao = models.DateTimeField(null=True, blank=True)
    
    # Estoque
    quantidade_disponivel = models.IntegerField(default=0)
    quantidade_reservada = models.IntegerField(default=0)
    
    # URLs das imagens no marketplace
    urls_imagens = models.JSONField(default=list)
    
    # Configurações de envio
    frete_gratis = models.BooleanField(default=False)
    peso_produto = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)
    dimensoes = models.JSONField(default=dict)  # altura, largura, comprimento
    
    # Status
    situacao = models.CharField(max_length=20, choices=SITUACOES, default='ATIVO')
    url_anuncio = models.URLField(null=True, blank=True)
    
    # Sincronização
    data_criacao_marketplace = models.DateTimeField(null=True, blank=True)
    data_ultima_atualizacao = models.DateTimeField(null=True, blank=True)
    erro_sincronizacao = models.TextField(null=True, blank=True)
    
    def __str__(self):
        return f"{self.produto_variacao.codigo_variacao} - {self.conta_marketplace.marketplace.nome}"
    
    class Meta:
        unique_together = ['conta_marketplace', 'id_produto_marketplace']
        verbose_name = 'Produto Marketplace'
        verbose_name_plural = 'Produtos Marketplace'


class PedidoMarketplace(TimeStampedModel):
    """Pedidos recebidos dos marketplaces"""
    
    SITUACOES = [
        ('NOVO', 'Novo'),
        ('CONFIRMADO', 'Confirmado'),
        ('PREPARANDO', 'Preparando'),
        ('PRONTO', 'Pronto para Envio'),
        ('ENVIADO', 'Enviado'),
        ('ENTREGUE', 'Entregue'),
        ('CANCELADO', 'Cancelado'),
        ('DEVOLVIDO', 'Devolvido'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    conta_marketplace = models.ForeignKey(ContaMarketplace, on_delete=models.PROTECT)
    
    # IDs do marketplace
    id_pedido_marketplace = models.CharField(max_length=100)
    numero_pedido_marketplace = models.CharField(max_length=100, null=True, blank=True)
    
    # Data do pedido no marketplace
    data_pedido_marketplace = models.DateTimeField()
    data_pagamento_marketplace = models.DateTimeField(null=True, blank=True)
    
    # Dados do comprador
    nome_comprador = models.CharField(max_length=200)
    email_comprador = models.EmailField(null=True, blank=True)
    telefone_comprador = models.CharField(max_length=15, null=True, blank=True)
    documento_comprador = models.CharField(max_length=20, null=True, blank=True)
    
    # Endereço de entrega
    endereco_entrega = models.JSONField()
    
    # Valores
    valor_produtos = models.DecimalField(max_digits=12, decimal_places=2)
    valor_frete = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    valor_desconto = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    valor_total = models.DecimalField(max_digits=12, decimal_places=2)
    
    # Taxas do marketplace
    taxa_marketplace = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    valor_liquido = models.DecimalField(max_digits=12, decimal_places=2)
    
    # Status
    situacao = models.CharField(max_length=20, choices=SITUACOES, default='NOVO')
    
    # Vinculação com sistema local
    pedido_local = models.ForeignKey(
        PedidoVenda,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='pedidos_marketplace'
    )
    
    # Dados de envio
    codigo_rastreamento = models.CharField(max_length=100, null=True, blank=True)
    transportadora = models.CharField(max_length=100, null=True, blank=True)
    data_envio = models.DateTimeField(null=True, blank=True)
    prazo_entrega_dias = models.IntegerField(null=True, blank=True)
    
    # Observações
    observacoes_comprador = models.TextField(null=True, blank=True)
    observacoes_internas = models.TextField(null=True, blank=True)
    
    def __str__(self):
        return f"Pedido {self.numero_pedido_marketplace or self.id_pedido_marketplace}"
    
    class Meta:
        unique_together = ['conta_marketplace', 'id_pedido_marketplace']
        verbose_name = 'Pedido Marketplace'
        verbose_name_plural = 'Pedidos Marketplace'
        ordering = ['-created_at']


class ItemPedidoMarketplace(TimeStampedModel):
    """Itens dos pedidos recebidos dos marketplaces"""
    
    pedido_marketplace = models.ForeignKey(
        PedidoMarketplace,
        on_delete=models.CASCADE,
        related_name='itens'
    )
    
    # Identificação do produto no marketplace
    id_item_marketplace = models.CharField(max_length=100)
    sku_marketplace = models.CharField(max_length=100)
    titulo_produto = models.CharField(max_length=200)
    
    # Vinculação com produto local
    produto_marketplace = models.ForeignKey(
        ProdutoMarketplace,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    
    # Quantidades e valores
    quantidade = models.DecimalField(max_digits=10, decimal_places=2)
    preco_unitario = models.DecimalField(max_digits=10, decimal_places=2)
    preco_total = models.DecimalField(max_digits=12, decimal_places=2)
    
    # URL da imagem do produto
    url_imagem = models.URLField(null=True, blank=True)
    
    class Meta:
        unique_together = ['pedido_marketplace', 'id_item_marketplace']
        ordering = ['id']


class LogSincronizacao(TimeStampedModel):
    """Log de sincronizações com marketplaces"""
    
    TIPOS_SYNC = [
        ('ESTOQUE', 'Sincronização de Estoque'),
        ('PRECOS', 'Sincronização de Preços'),
        ('PRODUTOS', 'Sincronização de Produtos'),
        ('PEDIDOS', 'Importação de Pedidos'),
        ('STATUS_PEDIDO', 'Atualização Status Pedido'),
    ]
    
    RESULTADOS = [
        ('SUCESSO', 'Sucesso'),
        ('PARCIAL', 'Sucesso Parcial'),
        ('ERRO', 'Erro'),
    ]
    
    conta_marketplace = models.ForeignKey(ContaMarketplace, on_delete=models.CASCADE)
    tipo_sincronizacao = models.CharField(max_length=20, choices=TIPOS_SYNC)
    
    # Resultado
    resultado = models.CharField(max_length=20, choices=RESULTADOS)
    
    # Estatísticas
    total_processados = models.IntegerField(default=0)
    total_sucessos = models.IntegerField(default=0)
    total_erros = models.IntegerField(default=0)
    
    # Tempo de processamento
    data_inicio = models.DateTimeField(auto_now_add=True)
    data_fim = models.DateTimeField(null=True, blank=True)
    tempo_processamento_segundos = models.IntegerField(null=True, blank=True)
    
    # Detalhes
    detalhes = models.JSONField(default=dict)
    mensagens_erro = models.TextField(null=True, blank=True)
    
    # Identificação de lote
    lote_id = models.CharField(max_length=50, null=True, blank=True)
    
    class Meta:
        verbose_name = 'Log de Sincronização'
        verbose_name_plural = 'Logs de Sincronização'
        ordering = ['-created_at']


class ConfiguracaoMapeamento(TimeStampedModel):
    """Configurações de mapeamento entre categorias locais e do marketplace"""
    
    conta_marketplace = models.ForeignKey(ContaMarketplace, on_delete=models.CASCADE)
    
    # Categoria local
    categoria_local = models.CharField(max_length=100)
    
    # Categoria no marketplace
    categoria_marketplace = models.CharField(max_length=100)
    id_categoria_marketplace = models.CharField(max_length=50, null=True, blank=True)
    
    # Atributos específicos do marketplace
    atributos_obrigatorios = models.JSONField(default=dict)
    template_titulo = models.CharField(max_length=500, null=True, blank=True)
    template_descricao = models.TextField(null=True, blank=True)
    
    # Configurações de preço
    margem_adicional = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    arredondar_preco = models.BooleanField(default=False)
    
    class Meta:
        unique_together = ['conta_marketplace', 'categoria_local']
        verbose_name = 'Mapeamento de Categoria'
        verbose_name_plural = 'Mapeamentos de Categorias'

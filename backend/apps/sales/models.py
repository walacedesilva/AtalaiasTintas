from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from apps.core.models import TimeStampedModel, User
from apps.companies.models import Loja
from apps.inventory.models import ProdutoVariacao
from apps.tintometry.models import ProducaoTinta, CorPersonalizada
import uuid


class Cliente(TimeStampedModel):
    """Cadastro de clientes"""
    
    TIPOS_CLIENTE = [
        ('PF', 'Pessoa Física'),
        ('PJ', 'Pessoa Jurídica'),
    ]
    
    # Identificação
    codigo_cliente = models.CharField(max_length=20, unique=True)
    tipo_cliente = models.CharField(max_length=2, choices=TIPOS_CLIENTE)
    
    # Pessoa Física
    nome = models.CharField(max_length=200)
    cpf = models.CharField(max_length=11, null=True, blank=True, unique=True)
    rg = models.CharField(max_length=20, null=True, blank=True)
    data_nascimento = models.DateField(null=True, blank=True)
    
    # Pessoa Jurídica
    razao_social = models.CharField(max_length=200, null=True, blank=True)
    nome_fantasia = models.CharField(max_length=200, null=True, blank=True)
    cnpj = models.CharField(max_length=14, null=True, blank=True, unique=True)
    inscricao_estadual = models.CharField(max_length=20, null=True, blank=True)
    
    # Contato
    telefone_principal = models.CharField(max_length=15, null=True, blank=True)
    telefone_secundario = models.CharField(max_length=15, null=True, blank=True)
    email = models.EmailField(null=True, blank=True)
    
    # Endereço principal
    cep = models.CharField(max_length=8, null=True, blank=True)
    endereco = models.CharField(max_length=200, null=True, blank=True)
    numero = models.CharField(max_length=10, null=True, blank=True)
    complemento = models.CharField(max_length=100, null=True, blank=True)
    bairro = models.CharField(max_length=100, null=True, blank=True)
    cidade = models.CharField(max_length=100, null=True, blank=True)
    uf = models.CharField(max_length=2, null=True, blank=True)
    
    # Dados comerciais
    limite_credito = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    bloqueado_credito = models.BooleanField(default=False)
    motivo_bloqueio = models.CharField(max_length=200, null=True, blank=True)
    
    # Classificação
    categoria_cliente = models.CharField(max_length=50, null=True, blank=True)
    vendedor_responsavel = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='clientes_responsavel'
    )
    
    # Dados para análise de crédito
    renda_declarada = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    score_credito = models.IntegerField(null=True, blank=True)
    data_ultima_consulta_credito = models.DateTimeField(null=True, blank=True)
    
    # Status
    ativo = models.BooleanField(default=True)
    
    def __str__(self):
        return f"{self.codigo_cliente} - {self.nome}"
    
    @property
    def nome_completo(self):
        if self.tipo_cliente == 'PJ':
            return self.nome_fantasia or self.razao_social or self.nome
        return self.nome
    
    class Meta:
        verbose_name = 'Cliente'
        verbose_name_plural = 'Clientes'


class PedidoVenda(TimeStampedModel):
    """Pedidos de venda"""
    
    SITUACOES = [
        ('ORCAMENTO', 'Orçamento'),
        ('APROVADO', 'Aprovado'),
        ('PRODUCAO', 'Em Produção'),
        ('PRONTO', 'Pronto para Entrega'),
        ('ENTREGUE', 'Entregue'),
        ('CANCELADO', 'Cancelado'),
    ]
    
    FORMAS_PAGAMENTO = [
        ('DINHEIRO', 'Dinheiro'),
        ('CARTAO_DEBITO', 'Cartão Débito'),
        ('CARTAO_CREDITO', 'Cartão Crédito'),
        ('PIX', 'PIX'),
        ('TRANSFERENCIA', 'Transferência'),
        ('CHEQUE', 'Cheque'),
        ('CREDIARIO', 'Crediário'),
        ('FIADO', 'Fiado'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    numero_pedido = models.CharField(max_length=20, unique=True)
    
    # Dados básicos
    loja = models.ForeignKey(Loja, on_delete=models.PROTECT)
    cliente = models.ForeignKey(Cliente, on_delete=models.PROTECT)
    vendedor = models.ForeignKey(
        User, 
        on_delete=models.PROTECT,
        related_name='vendas_realizadas'
    )
    
    # Situação
    situacao = models.CharField(max_length=20, choices=SITUACOES, default='ORCAMENTO')
    data_pedido = models.DateTimeField(auto_now_add=True)
    data_aprovacao = models.DateTimeField(null=True, blank=True)
    data_entrega_prevista = models.DateTimeField(null=True, blank=True)
    data_entrega_real = models.DateTimeField(null=True, blank=True)
    
    # Valores
    valor_subtotal = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    valor_desconto = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    percentual_desconto = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    valor_total = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    
    # Pagamento
    forma_pagamento = models.CharField(max_length=20, choices=FORMAS_PAGAMENTO)
    parcelas = models.IntegerField(default=1)
    valor_entrada = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    
    # Entrega
    tipo_entrega = models.CharField(max_length=20, choices=[
        ('BALCAO', 'Retirada no Balcão'),
        ('DELIVERY', 'Entrega'),
        ('TRANSPORTADORA', 'Transportadora'),
    ], default='BALCAO')
    
    endereco_entrega = models.TextField(null=True, blank=True)
    valor_frete = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    
    # Observações
    observacoes = models.TextField(null=True, blank=True)
    observacoes_internas = models.TextField(null=True, blank=True)
    
    def __str__(self):
        return f"Pedido {self.numero_pedido} - {self.cliente.nome_completo}"
    
    class Meta:
        verbose_name = 'Pedido de Venda'
        verbose_name_plural = 'Pedidos de Venda'
        ordering = ['-created_at']


class ItemPedidoVenda(TimeStampedModel):
    """Itens do pedido de venda"""
    
    pedido = models.ForeignKey(
        PedidoVenda, 
        on_delete=models.CASCADE,
        related_name='itens'
    )
    produto_variacao = models.ForeignKey(ProdutoVariacao, on_delete=models.PROTECT)
    
    # Quantidade e valores
    quantidade = models.DecimalField(max_digits=10, decimal_places=2)
    preco_unitario = models.DecimalField(max_digits=10, decimal_places=2)
    preco_total = models.DecimalField(max_digits=12, decimal_places=2)
    
    # Desconto específico do item
    desconto_valor = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    desconto_percentual = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    
    # Para produtos tintométricos
    producao_tinta = models.ForeignKey(
        ProducaoTinta, 
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        help_text="Vinculação com produção de tinta personalizada"
    )
    cor_personalizada = models.ForeignKey(
        CorPersonalizada,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    
    # Observações específicas do item
    observacoes = models.CharField(max_length=500, null=True, blank=True)
    
    # Sequência no pedido
    sequencia = models.IntegerField(default=1)
    
    class Meta:
        ordering = ['sequencia']
        unique_together = ['pedido', 'sequencia']


class Venda(TimeStampedModel):
    """Vendas finalizadas (geradas a partir dos pedidos)"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    numero_venda = models.CharField(max_length=20, unique=True)
    pedido_origem = models.ForeignKey(
        PedidoVenda, 
        on_delete=models.PROTECT,
        related_name='vendas'
    )
    
    # Dados da venda
    loja = models.ForeignKey(Loja, on_delete=models.PROTECT)
    cliente = models.ForeignKey(Cliente, on_delete=models.PROTECT)
    vendedor = models.ForeignKey(User, on_delete=models.PROTECT)
    
    # Datas importantes
    data_venda = models.DateTimeField(auto_now_add=True)
    data_pagamento = models.DateTimeField(null=True, blank=True)
    
    # Valores
    valor_total = models.DecimalField(max_digits=12, decimal_places=2)
    valor_desconto = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    valor_liquido = models.DecimalField(max_digits=12, decimal_places=2)
    
    # Dados fiscais
    numero_nfce = models.CharField(max_length=20, null=True, blank=True)
    chave_nfce = models.CharField(max_length=44, null=True, blank=True)
    xml_nfce = models.TextField(null=True, blank=True)
    
    # Comissão
    percentual_comissao = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    valor_comissao = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    comissao_paga = models.BooleanField(default=False)
    data_pagamento_comissao = models.DateTimeField(null=True, blank=True)
    
    # Status
    cancelada = models.BooleanField(default=False)
    motivo_cancelamento = models.CharField(max_length=200, null=True, blank=True)
    data_cancelamento = models.DateTimeField(null=True, blank=True)
    
    def __str__(self):
        return f"Venda {self.numero_venda} - {self.cliente.nome_completo}"
    
    class Meta:
        verbose_name = 'Venda'
        verbose_name_plural = 'Vendas'
        ordering = ['-created_at']


class CoresCliente(TimeStampedModel):
    """Histórico cromático - cores já compradas pelo cliente"""
    
    cliente = models.ForeignKey(Cliente, on_delete=models.CASCADE)
    
    # Cor comprada
    cor_personalizada = models.ForeignKey(
        CorPersonalizada,
        on_delete=models.CASCADE,
        null=True,
        blank=True
    )
    
    # Se foi cor do leque padrão
    codigo_cor_padrao = models.CharField(max_length=50, null=True, blank=True)
    nome_cor = models.CharField(max_length=200)
    
    # Dados da compra
    venda = models.ForeignKey(Venda, on_delete=models.CASCADE)
    quantidade_total_comprada = models.DecimalField(max_digits=10, decimal_places=2)
    data_primeira_compra = models.DateTimeField()
    data_ultima_compra = models.DateTimeField()
    
    # Estatísticas
    total_compras = models.IntegerField(default=1)
    volume_total_litros = models.DecimalField(max_digits=10, decimal_places=2)
    
    # Para sugestões de recompra
    intervalo_medio_compras = models.IntegerField(null=True, blank=True, help_text="Dias")
    proxima_compra_estimada = models.DateField(null=True, blank=True)
    
    class Meta:
        unique_together = ['cliente', 'cor_personalizada', 'codigo_cor_padrao']
        verbose_name = 'Histórico de Cor por Cliente'
        verbose_name_plural = 'Históricos de Cores por Cliente'


class MetaVendedor(TimeStampedModel):
    """Metas de vendas por vendedor"""
    
    vendedor = models.ForeignKey(User, on_delete=models.CASCADE)
    loja = models.ForeignKey(Loja, on_delete=models.CASCADE)
    
    # Período da meta
    mes = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(12)])
    ano = models.IntegerField()
    
    # Metas
    meta_valor = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    meta_quantidade_vendas = models.IntegerField(default=0)
    meta_novos_clientes = models.IntegerField(default=0)
    
    # Resultados
    valor_vendido = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    quantidade_vendas = models.IntegerField(default=0)
    novos_clientes_cadastrados = models.IntegerField(default=0)
    
    # Comissão
    percentual_comissao_base = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    bonus_meta_atingida = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    
    @property
    def percentual_meta_valor(self):
        if self.meta_valor > 0:
            return (self.valor_vendido / self.meta_valor) * 100
        return 0
    
    @property
    def meta_valor_atingida(self):
        return self.valor_vendido >= self.meta_valor
    
    class Meta:
        unique_together = ['vendedor', 'loja', 'mes', 'ano']
        verbose_name = 'Meta de Vendedor'
        verbose_name_plural = 'Metas de Vendedores'

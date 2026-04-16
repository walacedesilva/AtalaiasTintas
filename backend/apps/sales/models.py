from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from apps.core.models import TimeStampedModel, User
from apps.companies.models import Loja
from apps.inventory.models import ProdutoVariacao
from apps.tintometry.models import ProducaoTinta, CorPersonalizada
import uuid
from decimal import Decimal


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
    cliente = models.ForeignKey(
        Cliente,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        help_text="Nulo para vendas balcão anônimo (BR-001)",
    )
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
    
    # Desconto — auditoria e aprovação (T001)
    desconto_aprovador = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='descontos_aprovados',
        help_text="Usuário que aprovou o desconto via PIN",
    )
    desconto_motivo = models.CharField(max_length=500, null=True, blank=True)
    desconto_aprovado_em = models.DateTimeField(null=True, blank=True)

    # Observações
    observacoes = models.TextField(null=True, blank=True)
    observacoes_internas = models.TextField(null=True, blank=True)
    
    def __str__(self):
        if self.cliente:
            return f"Pedido {self.numero_pedido} - {self.cliente.nome_completo}"
        return f"Pedido {self.numero_pedido} - BALCÃO ANÔNIMO"
    
    class Meta:
        verbose_name = 'Pedido de Venda'
        verbose_name_plural = 'Pedidos de Venda'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['loja', 'situacao', 'created_at'], name='pedidovenda_loja_sit_idx'),
        ]


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

    # Multi-unit fields (T057)
    unidade_venda = models.ForeignKey(
        'inventory.UnidadeMedida',
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='itens_pedido',
        help_text="Unidade em que a quantidade foi solicitada (lata, litro, ml, etc.)",
    )
    quantidade_base = models.DecimalField(
        max_digits=10, decimal_places=4, null=True, blank=True,
        help_text="Quantidade convertida para unidade base do produto",
    )
    fator_conversao_aplicado = models.DecimalField(
        max_digits=10, decimal_places=6, null=True, blank=True,
        help_text="Fator de conversão usado no momento da venda",
    )
    
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

    # NF-e automation fields (T056)
    NFE_SITUACOES = [
        ('NAO_APLICAVEL', 'Não Aplicável'),
        ('PENDENTE', 'Pendente'),
        ('PROCESSANDO', 'Processando'),
        ('AUTORIZADA', 'Autorizada'),
        ('REJEITADA', 'Rejeitada'),
        ('CANCELADA', 'Cancelada'),
        ('ERRO_TECNICO', 'Erro Técnico'),
        ('AGUARDANDO_RETRY', 'Aguardando Retry Manual'),
    ]
    NFE_TIPOS_EMISSAO = [
        ('AUTOMATICA_B2B', 'Automática B2B'),
        ('MANUAL_B2C', 'Manual B2C'),
        ('NAO_EMITIR', 'Não Emitir'),
    ]
    nfe_situacao = models.CharField(
        max_length=20, choices=NFE_SITUACOES, default='NAO_APLICAVEL'
    )
    nfe_tipo_emissao = models.CharField(
        max_length=15, choices=NFE_TIPOS_EMISSAO, null=True, blank=True
    )
    nfe_tentativas = models.IntegerField(default=0)
    nfe_ultima_tentativa = models.DateTimeField(null=True, blank=True)
    nfe_erro = models.TextField(null=True, blank=True)
    nfe_requer_retry_manual = models.BooleanField(default=False)
    nfe_protocolo = models.CharField(max_length=20, null=True, blank=True)
    nfe_chave_acesso = models.CharField(max_length=44, null=True, blank=True)

    # Comissão
    percentual_comissao = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    valor_comissao = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    comissao_paga = models.BooleanField(default=False)
    data_pagamento_comissao = models.DateTimeField(null=True, blank=True)
    
    # Devolução (T002)
    tem_devolucao = models.BooleanField(default=False)

    # Status
    cancelada = models.BooleanField(default=False)
    motivo_cancelamento = models.CharField(max_length=200, null=True, blank=True)
    data_cancelamento = models.DateTimeField(null=True, blank=True)
    cancelado_por = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='vendas_canceladas',
    )
    
    def __str__(self):
        return f"Venda {self.numero_venda} - {self.cliente.nome_completo if self.cliente else 'BALCÃO ANÔNIMO'}"
    
    class Meta:
        verbose_name = 'Venda'
        verbose_name_plural = 'Vendas'
        ordering = ['-created_at']


# ---------------------------------------------------------------------------
# T003 — PagamentoVenda (split payment)
# ---------------------------------------------------------------------------

class PagamentoVenda(TimeStampedModel):
    """Pagamentos de uma venda — permite múltiplas formas (split payment)."""

    venda = models.ForeignKey(
        Venda,
        on_delete=models.CASCADE,
        related_name='pagamentos',
    )
    forma = models.CharField(
        max_length=20,
        choices=PedidoVenda.FORMAS_PAGAMENTO,
    )
    valor = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))],
    )
    # Troco — preenchido somente para DINHEIRO
    valor_recebido = models.DecimalField(
        max_digits=12, decimal_places=2, null=True, blank=True,
        help_text="Valor entregue pelo cliente (somente DINHEIRO)",
    )
    troco = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    # Referência externa (ID de transação PIX, autorização de cartão, etc.)
    referencia_externa = models.CharField(max_length=100, null=True, blank=True)
    observacoes = models.CharField(max_length=300, null=True, blank=True)

    class Meta:
        verbose_name = 'Pagamento de Venda'
        verbose_name_plural = 'Pagamentos de Venda'
        ordering = ['created_at']

    def __str__(self) -> str:
        return f"{self.get_forma_display()} R$ {self.valor} — {self.venda.numero_venda}"


# ---------------------------------------------------------------------------
# T004 — Recebivel (crediário / fiado)
# ---------------------------------------------------------------------------

class Recebivel(TimeStampedModel):
    """Recebíveis gerados por vendas no crediário/fiado."""

    SITUACOES = [
        ('ABERTO', 'Em Aberto'),
        ('PAGO', 'Pago'),
        ('PARCIAL', 'Parcialmente Pago'),
        ('VENCIDO', 'Vencido'),
        ('CANCELADO', 'Cancelado'),
    ]

    cliente = models.ForeignKey(
        Cliente,
        on_delete=models.PROTECT,
        related_name='recebiveis',
    )
    venda = models.ForeignKey(
        Venda,
        on_delete=models.PROTECT,
        related_name='recebiveis',
        null=True,
        blank=True,
    )
    loja = models.ForeignKey(Loja, on_delete=models.PROTECT)

    valor_original = models.DecimalField(max_digits=12, decimal_places=2)
    valor_pago = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    valor_saldo = models.DecimalField(
        max_digits=12, decimal_places=2,
        help_text="Computed from valor_original - valor_pago; always >= 0",
    )
    data_vencimento = models.DateField()
    situacao = models.CharField(
        max_length=10, choices=SITUACOES, default='ABERTO',
    )
    observacoes = models.TextField(null=True, blank=True)

    # Override de limite de crédito (US005 AC2)
    criado_com_override = models.BooleanField(
        default=False,
        help_text="True quando limite de crédito foi excedido e aprovado por gerência",
    )
    aprovador_override = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='overrides_credito',
    )

    # Cancelamento
    cancelado_por = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='recebiveis_cancelados',
    )
    data_cancelamento = models.DateTimeField(null=True, blank=True)
    motivo_cancelamento = models.CharField(max_length=500, null=True, blank=True)

    def save(self, *args, **kwargs):
        # Compute valor_saldo before every save
        self.valor_saldo = max(Decimal('0.00'), self.valor_original - self.valor_pago)
        # Sync situacao if fully paid / zero balance
        if self.valor_saldo == 0 and self.situacao not in ('PAGO', 'CANCELADO'):
            self.situacao = 'PAGO'
        super().save(*args, **kwargs)

    class Meta:
        verbose_name = 'Recebível'
        verbose_name_plural = 'Recebíveis'
        ordering = ['data_vencimento']
        indexes = [
            models.Index(fields=['cliente', 'situacao'], name='recebivel_cliente_sit_idx'),
            models.Index(fields=['loja', 'data_vencimento', 'situacao'], name='recebivel_loja_venc_sit_idx'),
        ]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(valor_saldo__gte=0),
                name='recebivel_saldo_nao_negativo',
            ),
        ]

    def __str__(self) -> str:
        return f"Recebível {self.pk} — {self.cliente.nome_completo} R$ {self.valor_saldo} ({self.situacao})"


# ---------------------------------------------------------------------------
# T005 — DescontoAuditLog (imutável)
# ---------------------------------------------------------------------------

class DescontoAuditLog(TimeStampedModel):
    """Log imutável de todos os descontos aplicados em pedidos."""

    TIPOS_DESCONTO = [
        ('ITEM', 'Por Item'),
        ('TOTAL', 'No Total'),
    ]

    pedido = models.ForeignKey(
        PedidoVenda,
        on_delete=models.PROTECT,
        related_name='logs_desconto',
    )
    solicitante = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name='descontos_solicitados',
    )
    aprovador = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='descontos_aprovados_log',
    )
    tipo_desconto = models.CharField(max_length=10, choices=TIPOS_DESCONTO)
    # FK ao item — somente se tipo_desconto == 'ITEM'
    item = models.ForeignKey(
        ItemPedidoVenda,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='logs_desconto',
    )
    valor_antes = models.DecimalField(max_digits=12, decimal_places=2)
    valor_depois = models.DecimalField(max_digits=12, decimal_places=2)
    percentual = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
    )
    motivo = models.CharField(max_length=500, null=True, blank=True)
    aprovado_com_pin = models.BooleanField(default=False)

    class Meta:
        verbose_name = 'Log de Desconto'
        verbose_name_plural = 'Logs de Desconto'
        ordering = ['-created_at']
        # Audit log is append-only — no update/delete in the ORM layer

    def __str__(self) -> str:
        return (
            f"Desconto {self.percentual}% no pedido {self.pedido.numero_pedido} "
            f"por {self.solicitante}"
        )


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

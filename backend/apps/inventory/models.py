from django.db import models
from django.core.validators import MinValueValidator
from django.contrib.auth import get_user_model
from apps.core.models import TimeStampedModel
from apps.companies.models import Empresa, Loja
import uuid

User = get_user_model()


class Categoria(TimeStampedModel):
    """Categorias hierárquicas de produtos"""
    
    nome = models.CharField(max_length=100)
    codigo = models.CharField(max_length=20, unique=True)
    descricao = models.TextField(null=True, blank=True)
    
    # Hierarquia
    parent = models.ForeignKey(
        'self', 
        on_delete=models.CASCADE, 
        null=True, 
        blank=True,
        related_name='subcategorias'
    )
    nivel = models.IntegerField(default=1)  # 1=Categoria, 2=Subcategoria, 3=Especificidade
    
    # Configurações específicas para tintas
    permite_tintometria = models.BooleanField(default=False)
    exige_formula = models.BooleanField(default=False)
    
    # Ordenação e status
    ordem = models.IntegerField(default=0)
    ativa = models.BooleanField(default=True)
    
    def __str__(self):
        return self.nome
    
    class Meta:
        verbose_name = 'Categoria'
        verbose_name_plural = 'Categorias'
        ordering = ['nivel', 'ordem', 'nome']


class Marca(TimeStampedModel):
    """Marcas dos produtos"""
    
    nome = models.CharField(max_length=100, unique=True)
    codigo = models.CharField(max_length=20, unique=True)
    descricao = models.TextField(null=True, blank=True)
    logo = models.ImageField(upload_to='marcas/', null=True, blank=True)
    
    # Dados do fornecedor
    fornecedor_principal = models.CharField(max_length=200, null=True, blank=True)
    cnpj_fornecedor = models.CharField(max_length=14, null=True, blank=True)
    
    ativa = models.BooleanField(default=True)
    
    def __str__(self):
        return self.nome
    
    class Meta:
        verbose_name = 'Marca'
        verbose_name_plural = 'Marcas'


class UnidadeMedida(TimeStampedModel):
    """Measurement units for multi-unit support"""
    codigo = models.CharField(max_length=10, unique=True)  # L, ML, LATA, GALON
    nome = models.CharField(max_length=50)  # Litro, Mililitro, Lata, Galão
    sigla = models.CharField(max_length=5)  # L, ml, lt, gl
    tipo = models.CharField(max_length=20, choices=[
        ('VOLUME', 'Volume'),
        ('PESO', 'Peso'), 
        ('UNIDADE', 'Unidade'),
        ('AREA', 'Área')
    ])
    
    def __str__(self):
        return f"{self.nome} ({self.sigla})"
    
    class Meta:
        verbose_name = 'Unidade de Medida'
        verbose_name_plural = 'Unidades de Medida'


class ProdutoUnidade(TimeStampedModel):
    """Product-specific unit configurations with conversions"""
    produto = models.ForeignKey('ProdutoVariacao', on_delete=models.CASCADE)
    unidade = models.ForeignKey(UnidadeMedida, on_delete=models.CASCADE)
    unidade_base = models.BooleanField(default=False)  # One base unit per product
    fator_conversao = models.DecimalField(max_digits=10, decimal_places=6, default=1)
    preco_diferenciado = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    ativa = models.BooleanField(default=True)
    
    def __str__(self):
        return f"{self.produto} - {self.unidade}"
    
    class Meta:
        unique_together = ['produto', 'unidade']
        verbose_name = 'Produto Unidade'
        verbose_name_plural = 'Produtos Unidades'


class EstoqueReserva(TimeStampedModel):
    """Temporary stock reservations during checkout"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    produto = models.ForeignKey('ProdutoVariacao', on_delete=models.CASCADE)
    quantidade_reservada = models.DecimalField(max_digits=10, decimal_places=4)
    unidade = models.ForeignKey(UnidadeMedida, on_delete=models.CASCADE)
    sessao_checkout = models.CharField(max_length=100)  # Session or cart ID
    usuario = models.ForeignKey(User, on_delete=models.CASCADE, null=True)
    expira_em = models.DateTimeField()  # 30 minutes from creation
    venda = models.ForeignKey('sales.Venda', on_delete=models.CASCADE, null=True, blank=True)
    
    # Status tracking
    STATUS_CHOICES = [
        ('ATIVA', 'Ativa'),
        ('CONFIRMADA', 'Confirmada'),
        ('EXPIRADA', 'Expirada'),
        ('CANCELADA', 'Cancelada')
    ]
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='ATIVA')
    
    def __str__(self):
        return f"Reserva {self.produto} - {self.quantidade_reservada} {self.unidade}"
    
    class Meta:
        verbose_name = 'Reserva de Estoque'
        verbose_name_plural = 'Reservas de Estoque'


class ProdutoBase(TimeStampedModel):
    """Produto mãe com todas as variações"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    codigo = models.CharField(max_length=50, unique=True)
    nome = models.CharField(max_length=200)
    descricao = models.TextField(null=True, blank=True)
    
    # Classificação
    categoria = models.ForeignKey(Categoria, on_delete=models.PROTECT)
    marca = models.ForeignKey(Marca, on_delete=models.PROTECT)
    
    # Tipo de produto
    tipo_produto = models.CharField(max_length=20, choices=[
        ('SIMPLES', 'Produto Simples'),
        ('COMPOSTO', 'Tinta Manipulada'), 
        ('INSUMO', 'Pigmento/Base'),
        ('KIT', 'Kit de Produtos')
    ])
    
    # Características técnicas
    especificacoes_tecnicas = models.JSONField(default=dict)
    ficha_tecnica = models.FileField(upload_to='fichas_tecnicas/', null=True, blank=True)
    
    # Dados para tintometria
    base_tintometrica = models.CharField(max_length=50, null=True, blank=True)
    linha_produto = models.CharField(max_length=100, null=True, blank=True)
    
    # Imagens
    imagem_principal = models.ImageField(upload_to='produtos/', null=True, blank=True)
    
    # Status
    ativo = models.BooleanField(default=True)
    data_cadastro = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.codigo} - {self.nome}"
    
    class Meta:
        verbose_name = 'Produto Base'
        verbose_name_plural = 'Produtos Base'


class ProdutoVariacao(TimeStampedModel):
    """Variações do produto (cor, tamanho, etc.)"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    produto_base = models.ForeignKey(
        ProdutoBase, 
        on_delete=models.CASCADE, 
        related_name='variacoes'
    )
    
    # Identificação da variação
    codigo_variacao = models.CharField(max_length=50)
    nome_variacao = models.CharField(max_length=200)
    
    # Características da variação
    cor = models.CharField(max_length=100, null=True, blank=True)
    cor_codigo = models.CharField(max_length=20, null=True, blank=True)  # Código da cor
    tamanho = models.CharField(max_length=50, null=True, blank=True)  # 900ml, 3.6L, 18L
    
    # Unidades
    unidade_venda = models.ForeignKey(
        UnidadeMedida, 
        on_delete=models.PROTECT,
        related_name='produtos_venda'
    )
    unidade_estoque = models.ForeignKey(
        UnidadeMedida, 
        on_delete=models.PROTECT,
        related_name='produtos_estoque'
    )
    
    # Conversão entre unidades
    fator_conversao_venda = models.DecimalField(
        max_digits=10, 
        decimal_places=4,
        default=1,
        help_text="Quantas unidades de estoque equivalem a 1 unidade de venda"
    )
    
    # Dados fiscais
    ncm = models.CharField(max_length=10, null=True, blank=True)
    cest = models.CharField(max_length=10, null=True, blank=True)
    
    # Preços
    preco_custo = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    preco_venda = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    margem_lucro = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    
    # Controle de estoque
    estoque_minimo = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    estoque_maximo = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    
    # Dados para tintometria (se aplicável)
    formula_base = models.TextField(null=True, blank=True)  # Fórmula em JSON
    rendimento_por_litro = models.DecimalField(
        max_digits=8, 
        decimal_places=2, 
        null=True, 
        blank=True
    )
    
    # Imagens específicas da variação
    imagem = models.ImageField(upload_to='produtos/variacoes/', null=True, blank=True)
    
    # Status
    ativo = models.BooleanField(default=True)
    
    def __str__(self):
        return f"{self.codigo_variacao} - {self.nome_variacao}"
    
    class Meta:
        verbose_name = 'Variação de Produto'
        verbose_name_plural = 'Variações de Produto'
        unique_together = ['produto_base', 'codigo_variacao']


class EstoqueLoja(TimeStampedModel):
    """Controle de estoque por loja"""
    
    loja = models.ForeignKey(Loja, on_delete=models.CASCADE)
    produto_variacao = models.ForeignKey(ProdutoVariacao, on_delete=models.CASCADE)
    
    # Quantidades
    quantidade_atual = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        default=0,
        validators=[MinValueValidator(0)]
    )
    quantidade_reservada = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        default=0,
        validators=[MinValueValidator(0)]
    )
    
    # Quantidades calculadas
    @property
    def quantidade_disponivel(self):
        return self.quantidade_atual - self.quantidade_reservada
    
    # Localização física
    localizacao = models.CharField(max_length=100, null=True, blank=True)
    corredor = models.CharField(max_length=20, null=True, blank=True)
    prateleira = models.CharField(max_length=20, null=True, blank=True)
    
    # Controles
    data_ultima_movimentacao = models.DateTimeField(null=True, blank=True)
    bloqueado_venda = models.BooleanField(default=False)
    motivo_bloqueio = models.CharField(max_length=200, null=True, blank=True)
    
    class Meta:
        unique_together = ['loja', 'produto_variacao']
        verbose_name = 'Estoque da Loja'
        verbose_name_plural = 'Estoques das Lojas'


class MovimentacaoEstoque(TimeStampedModel):
    """Complete stock movement history with multi-unit support"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    produto = models.ForeignKey('ProdutoVariacao', on_delete=models.CASCADE)
    
    TIPOS_MOVIMENTACAO = [
        ('ENTRADA_COMPRA', 'Entrada por Compra'),
        ('ENTRADA_AJUSTE', 'Entrada por Ajuste'),  
        ('ENTRADA_TRANSFERENCIA', 'Entrada por Transferência'),
        ('ENTRADA_DEVOLUCAO', 'Entrada por Devolução'),
        ('SAIDA_VENDA', 'Saída por Venda'),
        ('SAIDA_AJUSTE', 'Saída por Ajuste'),
        ('SAIDA_TRANSFERENCIA', 'Saída por Transferência'),
        ('SAIDA_PERDA', 'Saída por Perda'),
        ('RESERVA', 'Reserva Temporária'),
        ('LIBERACAO_RESERVA', 'Liberação de Reserva'),
    ]
    tipo_movimentacao = models.CharField(max_length=30, choices=TIPOS_MOVIMENTACAO)
    
    # Quantities in both original and base units
    quantidade_original = models.DecimalField(max_digits=10, decimal_places=4)
    unidade_original = models.ForeignKey(UnidadeMedida, on_delete=models.PROTECT, related_name='movimentacoes_origem')
    quantidade_base = models.DecimalField(max_digits=10, decimal_places=4)  # Converted to base unit
    unidade_base = models.ForeignKey(UnidadeMedida, on_delete=models.PROTECT, related_name='movimentacoes_base')
    
    # Stock levels before/after
    estoque_antes = models.DecimalField(max_digits=10, decimal_places=4, null=True)
    estoque_depois = models.DecimalField(max_digits=10, decimal_places=4, null=True)
    
    # References
    venda = models.ForeignKey('sales.Venda', on_delete=models.CASCADE, null=True, blank=True)
    nfe = models.ForeignKey('fiscal.NotaFiscalEletronica', on_delete=models.SET_NULL, null=True, blank=True)
    reserva = models.ForeignKey(EstoqueReserva, on_delete=models.SET_NULL, null=True, blank=True)
    usuario = models.ForeignKey(User, on_delete=models.PROTECT)
    
    # Documentation
    observacoes = models.TextField(blank=True)
    documento_referencia = models.CharField(max_length=100, blank=True)  # NF fornecedor, etc.
    
    def __str__(self):
        return f"{self.tipo_movimentacao} - {self.produto} - {self.quantidade_original}"

    class Meta:
        verbose_name = 'Movimentação de Estoque'
        verbose_name_plural = 'Movimentações de Estoque'
        ordering = ['-created_at']


class LoteProduto(TimeStampedModel):
    """Controle de lotes e validade para produtos perecíveis (catalisadores, primers, etc.)"""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    produto = models.ForeignKey(ProdutoVariacao, on_delete=models.CASCADE, related_name='lotes')
    loja = models.ForeignKey(Loja, on_delete=models.CASCADE, related_name='lotes')

    # Identificação do lote
    numero_lote = models.CharField(max_length=50)
    codigo_barras_lote = models.CharField(max_length=100, null=True, blank=True)

    # Datas de controle
    data_fabricacao = models.DateField(null=True, blank=True)
    data_validade = models.DateField(null=True, blank=True)
    data_entrada = models.DateField()

    # Quantidades (em unidade base do produto)
    quantidade_inicial = models.DecimalField(max_digits=10, decimal_places=4)
    quantidade_atual = models.DecimalField(max_digits=10, decimal_places=4)
    unidade = models.ForeignKey(UnidadeMedida, on_delete=models.PROTECT)

    # Custo de entrada (para cálculo de custo médio)
    custo_unitario = models.DecimalField(max_digits=10, decimal_places=4, default=0)

    STATUS_CHOICES = [
        ('ATIVO', 'Ativo'),
        ('VENCIDO', 'Vencido'),
        ('ESGOTADO', 'Esgotado'),
        ('BLOQUEADO', 'Bloqueado'),
        ('QUARENTENA', 'Em Quarentena'),
    ]
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='ATIVO')
    motivo_bloqueio = models.CharField(max_length=200, null=True, blank=True)

    # Rastreabilidade — NF do fornecedor
    documento_entrada = models.CharField(
        max_length=100, null=True, blank=True,
        help_text='Chave de acesso da NF-e do fornecedor ou número do documento'
    )

    observacoes = models.TextField(blank=True)

    class Meta:
        verbose_name = 'Lote de Produto'
        verbose_name_plural = 'Lotes de Produto'
        ordering = ['data_validade', 'data_entrada']
        unique_together = ['produto', 'loja', 'numero_lote']
        indexes = [
            models.Index(fields=['produto', 'loja', 'status']),
            models.Index(fields=['data_validade']),
        ]

    def __str__(self):
        return f"Lote {self.numero_lote} — {self.produto} (val: {self.data_validade})"

    @property
    def esta_vencido(self) -> bool:
        from django.utils import timezone
        return bool(self.data_validade and self.data_validade < timezone.now().date())

    @property
    def dias_para_vencer(self) -> int | None:
        from django.utils import timezone
        if not self.data_validade:
            return None
        delta = self.data_validade - timezone.now().date()
        return delta.days


class EntradaMercadoria(TimeStampedModel):
    """Registro de entrada de mercadorias — suporta importação de XML NF-e"""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    loja = models.ForeignKey(Loja, on_delete=models.CASCADE, related_name='entradas_mercadoria')
    usuario = models.ForeignKey(User, on_delete=models.PROTECT)

    TIPO_ENTRADA_CHOICES = [
        ('COMPRA', 'Compra de Fornecedor'),
        ('TRANSFERENCIA', 'Transferência entre Lojas'),
        ('AJUSTE', 'Ajuste Positivo'),
        ('DEVOLUCAO', 'Devolução de Cliente'),
        ('BONIFICACAO', 'Bonificação'),
    ]
    tipo_entrada = models.CharField(max_length=20, choices=TIPO_ENTRADA_CHOICES, default='COMPRA')

    # Dados do fornecedor (populados via XML NF-e ou manual)
    fornecedor_cnpj = models.CharField(max_length=14, null=True, blank=True)
    fornecedor_nome = models.CharField(max_length=200, null=True, blank=True)
    fornecedor_uf = models.CharField(max_length=2, null=True, blank=True)

    # Dados da NF-e do fornecedor
    chave_acesso_nfe = models.CharField(
        max_length=44, null=True, blank=True, unique=True,
        help_text='Chave de acesso de 44 dígitos da NF-e do fornecedor'
    )
    numero_nfe = models.CharField(max_length=9, null=True, blank=True)
    serie_nfe = models.CharField(max_length=3, null=True, blank=True)
    data_emissao_nfe = models.DateField(null=True, blank=True)

    # XML original armazenado para auditoria
    xml_nfe = models.TextField(null=True, blank=True)

    # Datas
    data_entrada = models.DateField()
    data_conferencia = models.DateTimeField(null=True, blank=True)

    # Valores totais da NF
    valor_total_nfe = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    valor_total_entrada = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    STATUS_CHOICES = [
        ('RASCUNHO', 'Rascunho'),
        ('PENDENTE', 'Pendente de Conferência'),
        ('CONFIRMADA', 'Confirmada'),
        ('ERRO', 'Erro no Processamento'),
        ('CANCELADA', 'Cancelada'),
    ]
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='RASCUNHO')
    observacoes = models.TextField(blank=True)

    class Meta:
        verbose_name = 'Entrada de Mercadoria'
        verbose_name_plural = 'Entradas de Mercadoria'
        ordering = ['-data_entrada', '-created_at']
        indexes = [
            models.Index(fields=['loja', 'status']),
            models.Index(fields=['chave_acesso_nfe']),
        ]

    def __str__(self):
        ref = self.chave_acesso_nfe or self.numero_nfe or str(self.id)[:8]
        return f"Entrada {ref} — {self.fornecedor_nome or 'Sem fornecedor'} ({self.data_entrada})"


class EntradaMercadoriaItem(TimeStampedModel):
    """Itens individuais de uma entrada de mercadoria"""

    entrada = models.ForeignKey(EntradaMercadoria, on_delete=models.CASCADE, related_name='itens')
    produto = models.ForeignKey(ProdutoVariacao, on_delete=models.PROTECT, null=True, blank=True)

    # Dados do item da NF-e (como vieram no XML)
    descricao_nfe = models.CharField(max_length=200)
    codigo_nfe = models.CharField(max_length=60, null=True, blank=True)
    ncm = models.CharField(max_length=10, null=True, blank=True)
    cfop = models.CharField(max_length=4, null=True, blank=True)
    cean = models.CharField(max_length=14, null=True, blank=True)

    # Quantidades
    quantidade = models.DecimalField(max_digits=10, decimal_places=4)
    unidade = models.ForeignKey(UnidadeMedida, on_delete=models.PROTECT, null=True, blank=True)
    unidade_nfe = models.CharField(max_length=6, null=True, blank=True)  # sigla original da NF-e

    # Valores
    valor_unitario = models.DecimalField(max_digits=10, decimal_places=4)
    valor_total = models.DecimalField(max_digits=12, decimal_places=2)
    desconto = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    # Impostos
    valor_icms = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    valor_ipi = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    valor_pis = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    valor_cofins = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    # Lote gerado (preenchido após confirmar entrada)
    lote = models.ForeignKey(LoteProduto, on_delete=models.SET_NULL, null=True, blank=True)

    STATUS_ITEM_CHOICES = [
        ('PENDENTE', 'Pendente de Vinculação'),
        ('VINCULADO', 'Produto Vinculado'),
        ('PROCESSADO', 'Estoque Atualizado'),
        ('IGNORADO', 'Ignorado'),
    ]
    status = models.CharField(max_length=15, choices=STATUS_ITEM_CHOICES, default='PENDENTE')

    class Meta:
        verbose_name = 'Item de Entrada'
        verbose_name_plural = 'Itens de Entrada'
        ordering = ['id']

    def __str__(self):
        return f"{self.descricao_nfe} x{self.quantidade}"

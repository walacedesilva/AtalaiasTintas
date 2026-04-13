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

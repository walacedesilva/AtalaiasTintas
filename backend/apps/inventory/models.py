from django.db import models
from django.core.validators import MinValueValidator
from apps.core.models import TimeStampedModel
from apps.companies.models import Empresa, Loja
import uuid


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
    """Unidades de medida com sistema de conversão"""
    
    nome = models.CharField(max_length=50)
    sigla = models.CharField(max_length=10, unique=True)
    tipo = models.CharField(max_length=20, choices=[
        ('volume', 'Volume'),
        ('peso', 'Peso'),
        ('unidade', 'Unidade'),
        ('metro', 'Metro'),
        ('area', 'Área')
    ])
    
    # Para conversões automáticas
    unidade_base = models.ForeignKey(
        'self', 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='derivadas'
    )
    fator_conversao = models.DecimalField(
        max_digits=12, 
        decimal_places=6, 
        default=1,
        help_text="Fator para converter para a unidade base"
    )
    
    def __str__(self):
        return f"{self.nome} ({self.sigla})"
    
    class Meta:
        verbose_name = 'Unidade de Medida'
        verbose_name_plural = 'Unidades de Medida'


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
    """Histórico de movimentações de estoque"""
    
    TIPOS_MOVIMENTO = [
        ('ENTRADA', 'Entrada'),
        ('SAIDA', 'Saída'),
        ('AJUSTE', 'Ajuste'),
        ('TRANSFERENCIA', 'Transferência'),
        ('PERDA', 'Perda'),
        ('PRODUCAO', 'Produção'),  # Para tintas manipuladas
    ]
    
    estoque_loja = models.ForeignKey(
        EstoqueLoja, 
        on_delete=models.CASCADE,
        related_name='movimentacoes'
    )
    
    tipo_movimento = models.CharField(max_length=20, choices=TIPOS_MOVIMENTO)
    quantidade = models.DecimalField(max_digits=10, decimal_places=2)
    quantidade_anterior = models.DecimalField(max_digits=10, decimal_places=2)
    quantidade_posterior = models.DecimalField(max_digits=10, decimal_places=2)
    
    # Dados do movimento
    documento = models.CharField(max_length=100, null=True, blank=True)
    observacoes = models.TextField(null=True, blank=True)
    
    # Usuário responsável
    usuario = models.ForeignKey(
        'core.User', 
        on_delete=models.PROTECT,
        related_name='movimentacoes_estoque'
    )
    
    class Meta:
        verbose_name = 'Movimentação de Estoque'
        verbose_name_plural = 'Movimentações de Estoque'
        ordering = ['-created_at']

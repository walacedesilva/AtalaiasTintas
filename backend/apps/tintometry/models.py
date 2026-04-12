from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
from apps.core.models import TimeStampedModel, User
from apps.companies.models import Loja
from apps.inventory.models import ProdutoVariacao
import uuid
import json


class Pigmento(TimeStampedModel):
    """Pigmentos utilizados na tintometria"""
    
    codigo = models.CharField(max_length=20, unique=True)
    nome = models.CharField(max_length=100)
    cor_base = models.CharField(max_length=50)
    
    # Características técnicas
    densidade = models.DecimalField(
        max_digits=6, 
        decimal_places=4,
        help_text="Densidade do pigmento (g/ml)"
    )
    poder_tintorial = models.DecimalField(
        max_digits=5, 
        decimal_places=2,
        help_text="Poder tintorial relativo (%)"
    )
    
    # Dados do fornecedor
    fornecedor = models.CharField(max_length=200)
    codigo_fornecedor = models.CharField(max_length=50, null=True, blank=True)
    
    # Configurações de uso
    concentracao_maxima = models.DecimalField(
        max_digits=5, 
        decimal_places=2,
        help_text="Concentração máxima permitida (%)",
        validators=[MinValueValidator(0), MaxValueValidator(100)]
    )
    
    # Valores RGB para referência visual
    r = models.IntegerField(validators=[MinValueValidator(0), MaxValueValidator(255)])
    g = models.IntegerField(validators=[MinValueValidator(0), MaxValueValidator(255)])
    b = models.IntegerField(validators=[MinValueValidator(0), MaxValueValidator(255)])
    
    @property
    def cor_hex(self):
        """Retorna a cor em formato hexadecimal"""
        return f"#{self.r:02x}{self.g:02x}{self.b:02x}"
    
    ativo = models.BooleanField(default=True)
    
    def __str__(self):
        return f"{self.codigo} - {self.nome}"
    
    class Meta:
        verbose_name = 'Pigmento'
        verbose_name_plural = 'Pigmentos'


class LequeCorDefinida(TimeStampedModel):
    """Leque de cores pré-definidas do sistema"""
    
    codigo_cor = models.CharField(max_length=20, unique=True)
    nome_cor = models.CharField(max_length=100)
    descricao = models.TextField(null=True, blank=True)
    
    # Categoria da cor
    familia_cor = models.CharField(max_length=50)  # Ex: Azuis, Vermelhos, etc.
    linha_produto = models.CharField(max_length=100)  # Ex: Standard, Premium, etc.
    
    # Valores Lab para precisão colorimétrica
    l_value = models.DecimalField(max_digits=6, decimal_places=3)  # Luminosidade
    a_value = models.DecimalField(max_digits=6, decimal_places=3)  # Verde-Vermelho
    b_value = models.DecimalField(max_digits=6, decimal_places=3)  # Azul-Amarelo
    
    # Valores RGB para exibição
    r = models.IntegerField(validators=[MinValueValidator(0), MaxValueValidator(255)])
    g = models.IntegerField(validators=[MinValueValidator(0), MaxValueValidator(255)])
    b = models.IntegerField(validators=[MinValueValidator(0), MaxValueValidator(255)])
    
    # Imagem da cor
    amostra_cor = models.ImageField(upload_to='cores/', null=True, blank=True)
    
    # Status
    ativo = models.BooleanField(default=True)
    data_criacao = models.DateTimeField(auto_now_add=True)
    
    @property
    def cor_hex(self):
        return f"#{self.r:02x}{self.g:02x}{self.b:02x}"
    
    def __str__(self):
        return f"{self.codigo_cor} - {self.nome_cor}"
    
    class Meta:
        verbose_name = 'Cor Definida'
        verbose_name_plural = 'Cores Definidas'


class FormulaTintometrica(TimeStampedModel):
    """Fórmulas para produção de cores específicas"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    cor_definida = models.ForeignKey(LequeCorDefinida, on_delete=models.CASCADE)
    base_produto = models.ForeignKey(
        ProdutoVariacao, 
        on_delete=models.CASCADE,
        help_text="Base branca ou produto a ser tintado"
    )
    
    # Identificação da fórmula
    codigo_formula = models.CharField(max_length=50, unique=True)
    nome_formula = models.CharField(max_length=200)
    versao = models.CharField(max_length=20, default='1.0')
    
    # Volume base para a fórmula (normalmente 1L)
    volume_base = models.DecimalField(
        max_digits=8, 
        decimal_places=2,
        default=1.00,
        help_text="Volume base para esta fórmula (litros)"
    )
    
    # Instrução de preparo
    instrucoes = models.TextField(null=True, blank=True)
    tempo_mistura_minutos = models.IntegerField(default=5)
    
    # Controle de qualidade
    aprovada = models.BooleanField(default=False)
    testada = models.BooleanField(default=False)
    data_aprovacao = models.DateTimeField(null=True, blank=True)
    usuario_aprovacao = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='formulas_aprovadas'
    )
    
    # Status
    ativa = models.BooleanField(default=True)
    
    def __str__(self):
        return f"{self.codigo_formula} - {self.nome_formula}"
    
    class Meta:
        verbose_name = 'Fórmula Tintométrica'
        verbose_name_plural = 'Fórmulas Tintométricas'
        unique_together = ['cor_definida', 'base_produto']


class ItemFormula(TimeStampedModel):
    """Itens (pigmentos) que compõem uma fórmula"""
    
    formula = models.ForeignKey(
        FormulaTintometrica, 
        on_delete=models.CASCADE,
        related_name='itens'
    )
    pigmento = models.ForeignKey(Pigmento, on_delete=models.CASCADE)
    
    # Quantidade do pigmento
    quantidade = models.DecimalField(
        max_digits=8, 
        decimal_places=4,
        help_text="Quantidade em ml para o volume base"
    )
    sequencia = models.IntegerField(default=1)
    
    # Observações específicas
    observacoes = models.CharField(max_length=200, null=True, blank=True)
    
    class Meta:
        unique_together = ['formula', 'pigmento']
        ordering = ['sequencia']


class ProducaoTinta(TimeStampedModel):
    """Registro de produção de tintas personalizadas"""
    
    SITUACOES = [
        ('PENDENTE', 'Pendente'),
        ('PRODUCAO', 'Em Produção'),
        ('CONCLUIDA', 'Concluída'),
        ('CANCELADA', 'Cancelada'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    numero_producao = models.CharField(max_length=20, unique=True)
    
    # Local de produção
    loja = models.ForeignKey(Loja, on_delete=models.CASCADE)
    
    # Produto e fórmula
    formula = models.ForeignKey(FormulaTintometrica, on_delete=models.PROTECT)
    produto_base = models.ForeignKey(ProdutoVariacao, on_delete=models.PROTECT)
    
    # Volume solicitado
    volume_solicitado = models.DecimalField(
        max_digits=8, 
        decimal_places=2,
        help_text="Volume final desejado (litros)"
    )
    volume_produzido = models.DecimalField(
        max_digits=8, 
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Volume realmente produzido (litros)"
    )
    
    # Dados da produção
    situacao = models.CharField(max_length=20, choices=SITUACOES, default='PENDENTE')
    data_inicio_producao = models.DateTimeField(null=True, blank=True)
    data_fim_producao = models.DateTimeField(null=True, blank=True)
    
    # Operador responsável
    operador = models.ForeignKey(
        User, 
        on_delete=models.PROTECT,
        related_name='producoes_operadas'
    )
    
    # Controle de qualidade
    cor_aprovada = models.BooleanField(default=False)
    observacoes_qualidade = models.TextField(null=True, blank=True)
    
    # Dados do cliente/pedido
    cliente_nome = models.CharField(max_length=200, null=True, blank=True)
    pedido_venda_id = models.CharField(max_length=50, null=True, blank=True)
    
    def __str__(self):
        return f"Produção {self.numero_producao} - {self.formula.nome_formula}"
    
    class Meta:
        verbose_name = 'Produção de Tinta'
        verbose_name_plural = 'Produções de Tinta'
        ordering = ['-created_at']


class ConsumoProducao(TimeStampedModel):
    """Consumo real de pigmentos em uma produção"""
    
    producao = models.ForeignKey(
        ProducaoTinta, 
        on_delete=models.CASCADE,
        related_name='consumos'
    )
    pigmento = models.ForeignKey(Pigmento, on_delete=models.CASCADE)
    
    # Quantidades
    quantidade_teorica = models.DecimalField(
        max_digits=8, 
        decimal_places=4,
        help_text="Quantidade teórica segundo a fórmula"
    )
    quantidade_utilizada = models.DecimalField(
        max_digits=8, 
        decimal_places=4,
        help_text="Quantidade realmente utilizada"
    )
    
    # Variação
    @property
    def variacao_percentual(self):
        if self.quantidade_teorica > 0:
            return ((self.quantidade_utilizada - self.quantidade_teorica) / self.quantidade_teorica) * 100
        return 0
    
    class Meta:
        unique_together = ['producao', 'pigmento']


class CorPersonalizada(TimeStampedModel):
    """Cores criadas pelo cliente que não estão no leque padrão"""
    
    codigo_cor_personalizada = models.CharField(max_length=50, unique=True)
    nome_cor = models.CharField(max_length=200)
    descricao = models.TextField(null=True, blank=True)
    
    # Dados do cliente
    cliente_nome = models.CharField(max_length=200)
    cliente_documento = models.CharField(max_length=20, null=True, blank=True)
    telefone_cliente = models.CharField(max_length=15, null=True, blank=True)
    
    # Valores colorimétricos
    l_value = models.DecimalField(max_digits=6, decimal_places=3)
    a_value = models.DecimalField(max_digits=6, decimal_places=3)
    b_value = models.DecimalField(max_digits=6, decimal_places=3)
    
    # RGB aproximado
    r = models.IntegerField(validators=[MinValueValidator(0), MaxValueValidator(255)])
    g = models.IntegerField(validators=[MinValueValidator(0), MaxValueValidator(255)])
    b = models.IntegerField(validators=[MinValueValidator(0), MaxValueValidator(255)])
    
    # Amostra física
    amostra_imagem = models.ImageField(upload_to='cores_personalizadas/', null=True, blank=True)
    
    # Fórmula desenvolvida
    formula_desenvolvida = models.ForeignKey(
        FormulaTintometrica, 
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    
    # Histórico de uso
    total_producoes = models.IntegerField(default=0)
    data_primeira_producao = models.DateTimeField(null=True, blank=True)
    data_ultima_producao = models.DateTimeField(null=True, blank=True)
    
    @property
    def cor_hex(self):
        return f"#{self.r:02x}{self.g:02x}{self.b:02x}"
    
    def __str__(self):
        return f"{self.codigo_cor_personalizada} - {self.nome_cor}"
    
    class Meta:
        verbose_name = 'Cor Personalizada'
        verbose_name_plural = 'Cores Personalizadas'


class MisturaTinta(TimeStampedModel):
    """Registro de misturas executadas com histórico completo"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    codigo_mistura = models.CharField(max_length=20, unique=True)  # Auto-generated
    
    # Relacionamentos
    formula = models.ForeignKey(FormulaTintometrica, on_delete=models.PROTECT, related_name='misturas')
    loja = models.ForeignKey(Loja, on_delete=models.PROTECT, related_name='misturas_tintometricas')
    usuario_operacao = models.ForeignKey(User, on_delete=models.PROTECT, related_name='misturas_operadas')
    
    # Dados do cliente (flexível - pode não vir do cadastro)
    cliente_nome = models.CharField(max_length=200)
    cliente_documento = models.CharField(max_length=20, null=True, blank=True)
    cliente_telefone = models.CharField(max_length=15, null=True, blank=True)
    cliente_email = models.EmailField(null=True, blank=True)
    
    # Volume e custos
    volume_solicitado = models.DecimalField(
        max_digits=8, 
        decimal_places=2,
        help_text="Volume solicitado pelo cliente (litros)"
    )
    volume_produzido = models.DecimalField(
        max_digits=8, 
        decimal_places=2, 
        null=True, 
        blank=True,
        help_text="Volume realmente produzido (litros)"
    )
    custo_total = models.DecimalField(
        max_digits=10, 
        decimal_places=4,
        help_text="Custo total da mistura incluindo base e pigmentos"
    )
    custo_base = models.DecimalField(
        max_digits=10, 
        decimal_places=4,
        help_text="Custo da base utilizada"
    )
    custo_pigmentos = models.DecimalField(
        max_digits=10, 
        decimal_places=4,
        help_text="Custo dos pigmentos utilizados"
    )
    
    # Status e controle
    SITUACAO_CHOICES = [
        ('CALCULADA', 'Fórmula Calculada'),
        ('CONFIRMADA', 'Mistura Confirmada'),
        ('PRODUZIDA', 'Mistura Produzida'),
        ('ENTREGUE', 'Entregue ao Cliente'),
        ('CANCELADA', 'Cancelada')
    ]
    situacao = models.CharField(max_length=20, choices=SITUACAO_CHOICES, default='CALCULADA')
    data_confirmacao = models.DateTimeField(null=True, blank=True)
    data_producao = models.DateTimeField(null=True, blank=True)
    data_entrega = models.DateTimeField(null=True, blank=True)
    data_cancelamento = models.DateTimeField(null=True, blank=True)
    motivo_cancelamento = models.CharField(max_length=200, null=True, blank=True)
    
    # Observações
    observacoes_cliente = models.TextField(
        null=True, 
        blank=True,
        help_text="Observações fornecidas pelo cliente sobre a cor"
    )
    observacoes_internas = models.TextField(
        null=True, 
        blank=True,
        help_text="Observações internas sobre o processo de mistura"
    )
    
    # Rastreabilidade de qualidade
    cor_aprovada_cliente = models.BooleanField(
        null=True, 
        blank=True,
        help_text="Cliente aprovou a cor final?"
    )
    data_aprovacao_cor = models.DateTimeField(null=True, blank=True)
    
    # Integração com vendas
    pedido_venda_id = models.CharField(
        max_length=50, 
        null=True, 
        blank=True,
        help_text="ID do pedido de venda associado"
    )
    
    def save(self, *args, **kwargs):
        if not self.codigo_mistura:
            # Gerar código automático da mistura
            from django.utils import timezone
            hoje = timezone.now()
            base = f"MX{hoje.strftime('%Y%m%d')}"
            ultimo = MisturaTinta.objects.filter(
                codigo_mistura__startswith=base
            ).count()
            self.codigo_mistura = f"{base}{ultimo + 1:04d}"
        
        super().save(*args, **kwargs)
    
    @property
    def fator_proporcao(self):
        """Fator de proporção entre volume solicitado e volume base da fórmula"""
        if self.formula.volume_base > 0:
            return self.volume_solicitado / self.formula.volume_base
        return 1
    
    @property
    def economia(self):
        """Diferença entre custo teórico e real se houver"""
        if self.volume_produzido and self.volume_produzido < self.volume_solicitado:
            fator_real = self.volume_produzido / self.volume_solicitado
            return self.custo_total * (1 - fator_real)
        return 0
    
    def __str__(self):
        return f"{self.codigo_mistura} - {self.cliente_nome} - {self.formula.nome_formula}"
    
    class Meta:
        verbose_name = 'Mistura de Tinta'
        verbose_name_plural = 'Misturas de Tinta'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['cliente_telefone', 'created_at']),
            models.Index(fields=['loja', 'created_at']),
            models.Index(fields=['situacao']),
            models.Index(fields=['data_confirmacao']),
        ]


class ItemMistura(TimeStampedModel):
    """Itens utilizados em cada mistura com quantidades exatas"""
    
    mistura = models.ForeignKey(
        MisturaTinta, 
        on_delete=models.CASCADE, 
        related_name='itens'
    )
    pigmento = models.ForeignKey(Pigmento, on_delete=models.PROTECT)
    
    # Quantidades calculadas vs executadas
    quantidade_calculada = models.DecimalField(
        max_digits=8, 
        decimal_places=4,
        help_text="Quantidade calculada pela fórmula (ml)"
    )
    quantidade_executada = models.DecimalField(
        max_digits=8, 
        decimal_places=4, 
        null=True, 
        blank=True,
        help_text="Quantidade realmente utilizada (ml)"
    )
    
    # Custos por item
    custo_unitario = models.DecimalField(
        max_digits=10, 
        decimal_places=4,
        help_text="Custo por ml do pigmento na data da mistura"
    )
    custo_total = models.DecimalField(
        max_digits=10, 
        decimal_places=4,
        help_text="Custo total deste pigmento na mistura"
    )
    
    # Controle de estoque
    lote_utilizado = models.CharField(
        max_length=50, 
        null=True, 
        blank=True,
        help_text="Lote do pigmento utilizado"
    )
    estoque_antes = models.DecimalField(
        max_digits=10, 
        decimal_places=4, 
        null=True, 
        blank=True,
        help_text="Saldo em estoque antes da mistura"
    )
    estoque_depois = models.DecimalField(
        max_digits=10, 
        decimal_places=4, 
        null=True, 
        blank=True,
        help_text="Saldo em estoque após a mistura"
    )
    
    # Sequência de mistura
    sequencia = models.IntegerField(
        default=1,
        help_text="Ordem de adição do pigmento na mistura"
    )
    
    @property
    def variacao_percentual(self):
        """Percentual de variação entre quantidade calculada e executada"""
        if self.quantidade_calculada > 0 and self.quantidade_executada:
            return ((self.quantidade_executada - self.quantidade_calculada) / 
                   self.quantidade_calculada) * 100
        return 0
    
    @property
    def quantidade_final(self):
        """Retorna a quantidade executada ou calculada se não foi executada"""
        return self.quantidade_executada or self.quantidade_calculada
    
    def __str__(self):
        return f"{self.mistura.codigo_mistura} - {self.pigmento.nome} - {self.quantidade_final}ml"
    
    class Meta:
        unique_together = ['mistura', 'pigmento']
        ordering = ['sequencia', 'pigmento__nome']
        indexes = [
            models.Index(fields=['mistura', 'sequencia']),
            models.Index(fields=['pigmento']),
        ]


class EstoquePigmento(TimeStampedModel):
    """Controle específico de estoque para pigmentos tintométricos"""
    
    pigmento = models.ForeignKey(Pigmento, on_delete=models.CASCADE)
    loja = models.ForeignKey(Loja, on_delete=models.CASCADE)
    
    # Saldos atuais
    saldo_ml = models.DecimalField(
        max_digits=10, 
        decimal_places=4, 
        default=0,
        help_text="Saldo atual em mililitros"
    )
    saldo_minimo = models.DecimalField(
        max_digits=10, 
        decimal_places=4, 
        default=100,
        help_text="Saldo mínimo para alerta"
    )
    saldo_maximo = models.DecimalField(
        max_digits=10, 
        decimal_places=4, 
        default=5000,
        help_text="Saldo máximo recomendado"
    )
    
    # Custos
    custo_ml = models.DecimalField(
        max_digits=8, 
        decimal_places=4,
        help_text="Custo por mililitro"
    )
    data_ultimo_custo = models.DateTimeField(
        auto_now_add=True,
        help_text="Data da última atualização de custo"
    )
    
    # Lote atual
    lote_atual = models.CharField(
        max_length=50, 
        null=True, 
        blank=True,
        help_text="Lote atualmente em uso"
    )
    validade_lote = models.DateField(
        null=True, 
        blank=True,
        help_text="Data de validade do lote atual"
    )
    
    # Alertas automáticos
    alerta_ativo = models.BooleanField(
        default=False,
        help_text="Indica se há alerta de estoque baixo ativo"
    )
    data_ultimo_alerta = models.DateTimeField(null=True, blank=True)
    
    # Reposição
    reposicao_solicitada = models.BooleanField(default=False)
    data_solicitacao_reposicao = models.DateTimeField(null=True, blank=True)
    quantidade_solicitada = models.DecimalField(
        max_digits=10, 
        decimal_places=4, 
        null=True, 
        blank=True
    )
    
    # Status
    ativo = models.BooleanField(default=True)
    
    @property
    def percentual_estoque(self):
        """Percentual atual do estoque em relação ao máximo"""
        if self.saldo_maximo > 0:
            return (self.saldo_ml / self.saldo_maximo) * 100
        return 0
    
    @property
    def estoque_critico(self):
        """Indica se o estoque está abaixo do mínimo"""
        return self.saldo_ml <= self.saldo_minimo
    
    @property
    def valor_total_estoque(self):
        """Valor total do estoque atual"""
        return self.saldo_ml * self.custo_ml
    
    def reduzir_estoque(self, quantidade, lote=None):
        """Reduz o estoque pela quantidade especificada"""
        if self.saldo_ml >= quantidade:
            self.saldo_ml -= quantidade
            
            # Ativar alerta se necessário
            if self.estoque_critico and not self.alerta_ativo:
                from django.utils import timezone
                self.alerta_ativo = True
                self.data_ultimo_alerta = timezone.now()
            
            self.save(update_fields=['saldo_ml', 'alerta_ativo', 'data_ultimo_alerta'])
            return True
        return False
    
    def adicionar_estoque(self, quantidade, custo_unitario=None, lote=None, validade=None):
        """Adiciona estoque com atualização de custos"""
        self.saldo_ml += quantidade
        
        # Atualizar custo se fornecido
        if custo_unitario is not None:
            from django.utils import timezone
            self.custo_ml = custo_unitario
            self.data_ultimo_custo = timezone.now()
        
        # Atualizar lote se fornecido
        if lote is not None:
            self.lote_atual = lote
            self.validade_lote = validade
        
        # Desativar alertas se estoque normalizado
        if not self.estoque_critico:
            self.alerta_ativo = False
            self.reposicao_solicitada = False
            self.data_solicitacao_reposicao = None
        
        self.save()
    
    def __str__(self):
        return f"{self.pigmento.nome} - {self.loja.nome} - {self.saldo_ml}ml"
    
    class Meta:
        unique_together = ['pigmento', 'loja']
        verbose_name = 'Estoque de Pigmento'
        verbose_name_plural = 'Estoques de Pigmentos'
        indexes = [
            models.Index(fields=['loja', 'alerta_ativo']),
            models.Index(fields=['pigmento']),
            models.Index(fields=['saldo_ml']),
        ]


class EtiquetaMistura(TimeStampedModel):
    """Etiquetas geradas para identificação das misturas"""
    
    mistura = models.OneToOneField(
        MisturaTinta, 
        on_delete=models.CASCADE,
        related_name='etiqueta'
    )
    codigo_etiqueta = models.CharField(max_length=30, unique=True)
    
    # Dados da etiqueta
    qr_code_data = models.CharField(
        max_length=200,
        help_text="Dados codificados no QR Code"
    )
    codigo_barras = models.CharField(
        max_length=50, 
        null=True, 
        blank=True,
        help_text="Código de barras adicional se necessário"
    )
    
    # Status de impressão
    impressa = models.BooleanField(default=False)
    data_impressao = models.DateTimeField(null=True, blank=True)
    usuario_impressao = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='etiquetas_impressas'
    )
    
    # Controle de reimpressões
    reimpressoes = models.IntegerField(default=0)
    historico_reimpressoes = models.JSONField(
        default=list,
        help_text="Histórico de reimpressões com timestamps"
    )
    
    # Dados da etiqueta personalizáveis
    titulo_personalizado = models.CharField(
        max_length=100, 
        null=True, 
        blank=True,
        help_text="Título customizado para a etiqueta"
    )
    observacoes_etiqueta = models.CharField(
        max_length=200, 
        null=True, 
        blank=True,
        help_text="Observações que aparecerão na etiqueta"
    )
    
    def save(self, *args, **kwargs):
        if not self.codigo_etiqueta:
            # Gerar código automático da etiqueta
            self.codigo_etiqueta = f"ET{self.mistura.codigo_mistura}"
        
        if not self.qr_code_data:
            # Gerar dados do QR Code
            self.qr_code_data = json.dumps({
                'mistura': str(self.mistura.id),
                'codigo': self.mistura.codigo_mistura,
                'cor': self.mistura.formula.cor_definida.nome_cor,
                'volume': str(self.mistura.volume_solicitado),
                'data': self.mistura.created_at.strftime('%Y-%m-%d'),
                'loja': self.mistura.loja.nome
            })
        
        super().save(*args, **kwargs)
    
    def marcar_impressa(self, usuario=None):
        """Marca a etiqueta como impressa"""
        from django.utils import timezone
        
        if self.impressa:
            # Se já foi impressa, registrar reimpressão
            self.reimpressoes += 1
            self.historico_reimpressoes.append({
                'data': timezone.now().isoformat(),
                'usuario': usuario.username if usuario else 'Sistema',
                'reimpressao': self.reimpressoes
            })
        else:
            # Primeira impressão
            self.impressa = True
            self.data_impressao = timezone.now()
            self.usuario_impressao = usuario
        
        self.save()
    
    @property
    def dados_qr_formatados(self):
        """Retorna os dados do QR Code em formato legível"""
        try:
            return json.loads(self.qr_code_data)
        except:
            return {}
    
    def __str__(self):
        return f"Etiqueta {self.codigo_etiqueta} - {self.mistura.codigo_mistura}"
    
    class Meta:
        verbose_name = 'Etiqueta de Mistura'
        verbose_name_plural = 'Etiquetas de Misturas'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['codigo_etiqueta']),
            models.Index(fields=['impressa']),
            models.Index(fields=['data_impressao']),
        ]


# =============================================================================
# SISTEMA WEB DE ETIQUETAS - TEMPLATES E IMPRESSÃO AVANÇADA
# =============================================================================

class LabelTemplate(TimeStampedModel):
    """Template de etiqueta personalizável para interface web"""
    
    CATEGORY_CHOICES = [
        ('standard', 'Padrão'),
        ('compact', 'Compacto'),
        ('premium', 'Premium'),
        ('custom', 'Personalizado'),
    ]
    
    STATUS_CHOICES = [
        ('active', 'Ativo'),
        ('inactive', 'Inativo'),
        ('draft', 'Rascunho'),
    ]
    
    # Identificação
    name = models.CharField('Nome', max_length=100)
    description = models.TextField('Descrição', blank=True)
    category = models.CharField('Categoria', max_length=20, choices=CATEGORY_CHOICES, default='standard')
    status = models.CharField('Status', max_length=20, choices=STATUS_CHOICES, default='active')
    is_default = models.BooleanField('Template Padrão', default=False)
    is_active = models.BooleanField('Ativo', default=True)
    
    # Dimensões (em mm)
    width = models.PositiveIntegerField('Largura (mm)', default=100)
    height = models.PositiveIntegerField('Altura (mm)', default=150)
    margin = models.PositiveIntegerField('Margem (mm)', default=5)
    
    # Configurações de cor
    background_color = models.CharField('Cor de Fundo', max_length=7, default='#FFFFFF')
    text_color = models.CharField('Cor do Texto', max_length=7, default='#000000')
    accent_color = models.CharField('Cor de Destaque', max_length=7, default='#2563EB')
    
    # Configurações de fonte
    font_family = models.CharField('Família da Fonte', max_length=50, default='Arial')
    font_size_base = models.PositiveIntegerField('Tamanho Base da Fonte', default=12)
    
    # Elementos incluídos
    include_qr_code = models.BooleanField('Incluir QR Code', default=True)
    include_barcode = models.BooleanField('Incluir Código de Barras', default=True)
    include_logo = models.BooleanField('Incluir Logo', default=True)
    include_formula = models.BooleanField('Incluir Lista de Pigmentos', default=True)
    include_customer = models.BooleanField('Incluir Dados do Cliente', default=True)
    include_cost = models.BooleanField('Incluir Informações de Custo', default=False)
    
    # Layout específico (JSON com configurações customizadas)
    layout_config = models.JSONField('Configuração de Layout', default=dict, blank=True)
    
    # Metadados
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, 
                                   related_name='created_templates')
    
    def save(self, *args, **kwargs):
        # Garantir que apenas um template seja o padrão por categoria
        if self.is_default:
            LabelTemplate.objects.filter(
                category=self.category, 
                is_default=True
            ).exclude(id=self.id).update(is_default=False)
        
        super().save(*args, **kwargs)
    
    @property
    def dimensions_display(self):
        """Retorna as dimensões formatadas"""
        return f"{self.width} x {self.height}mm"
    
    @property
    def usage_count(self):
        """Conta quantas vezes o template foi usado"""
        return self.labelprintjob_set.count()
    
    def __str__(self):
        return f"{self.name} ({self.get_category_display()})"
    
    class Meta:
        verbose_name = 'Template de Etiqueta'
        verbose_name_plural = 'Templates de Etiquetas'
        ordering = ['name']


class LabelPrintJob(TimeStampedModel):
    """Registro de trabalho de impressão de etiquetas em lote"""
    
    STATUS_CHOICES = [
        ('pending', 'Pendente'),
        ('processing', 'Processando'),
        ('completed', 'Concluído'),
        ('failed', 'Falhou'),
        ('cancelled', 'Cancelado'),
    ]
    
    OUTPUT_CHOICES = [
        ('pdf', 'PDF'),
        ('print', 'Impressão Direta'),
        ('preview', 'Preview'),
    ]
    
    # Identificação
    job_id = models.UUIDField('ID do Trabalho', default=uuid.uuid4, unique=True)
    template = models.ForeignKey(LabelTemplate, on_delete=models.PROTECT, 
                                verbose_name='Template Usado')
    
    # Misturas incluídas
    misturas = models.ManyToManyField(MisturaTinta, 
                                      verbose_name='Misturas',
                                      related_name='print_jobs')
    
    # Configurações do trabalho
    output_type = models.CharField('Tipo de Saída', max_length=20, 
                                  choices=OUTPUT_CHOICES, default='pdf')
    copies_count = models.PositiveIntegerField('Número de Cópias', default=1)
    paper_size = models.CharField('Tamanho do Papel', max_length=20, default='a4')
    print_quality = models.CharField('Qualidade', max_length=20, default='medium')
    color_mode = models.CharField('Modo de Cor', max_length=20, default='color')
    
    # Configurações específicas (JSON)
    print_config = models.JSONField('Configurações de Impressão', default=dict, blank=True)
    
    # Status e resultado
    status = models.CharField('Status', max_length=20, choices=STATUS_CHOICES, default='pending')
    progress = models.PositiveIntegerField('Progresso (%)', default=0)
    error_message = models.TextField('Mensagem de Erro', blank=True)
    
    # Arquivos gerados
    output_file_path = models.CharField('Caminho do Arquivo', max_length=500, blank=True)
    file_size = models.PositiveIntegerField('Tamanho do Arquivo (bytes)', null=True, blank=True)
    
    # Metadados
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    started_at = models.DateTimeField('Iniciado em', null=True, blank=True)
    completed_at = models.DateTimeField('Concluído em', null=True, blank=True)
    
    def start_processing(self):
        """Marca o trabalho como iniciado"""
        from django.utils import timezone
        self.status = 'processing'
        self.started_at = timezone.now()
        self.save()
    
    def complete_successfully(self, output_path=None, file_size=None):
        """Marca o trabalho como concluído com sucesso"""
        from django.utils import timezone
        self.status = 'completed'
        self.progress = 100
        self.completed_at = timezone.now()
        if output_path:
            self.output_file_path = output_path
        if file_size:
            self.file_size = file_size
        self.save()
    
    def fail_with_error(self, error_message):
        """Marca o trabalho como falhou"""
        from django.utils import timezone
        self.status = 'failed'
        self.error_message = error_message
        self.completed_at = timezone.now()
        self.save()
    
    @property
    def duration(self):
        """Retorna a duração do trabalho se concluído"""
        if self.started_at and self.completed_at:
            return self.completed_at - self.started_at
        return None
    
    @property
    def misturas_count(self):
        """Conta o número de misturas no trabalho"""
        return self.misturas.count()
    
    def __str__(self):
        return f"Job {self.job_id.hex[:8]} - {self.template.name}"
    
    class Meta:
        verbose_name = 'Trabalho de Impressão'
        verbose_name_plural = 'Trabalhos de Impressão'
        ordering = ['-created_at']


class LabelPrintQueue(TimeStampedModel):
    """Fila de impressão para processamento assíncrono"""
    
    PRIORITY_CHOICES = [
        ('low', 'Baixa'),
        ('normal', 'Normal'),
        ('high', 'Alta'),
        ('urgent', 'Urgente'),
    ]
    
    print_job = models.OneToOneField(LabelPrintJob, on_delete=models.CASCADE,
                                    verbose_name='Trabalho de Impressão')
    priority = models.CharField('Prioridade', max_length=20, 
                               choices=PRIORITY_CHOICES, default='normal')
    scheduled_for = models.DateTimeField('Agendado para', default=timezone.now)
    attempts = models.PositiveIntegerField('Tentativas', default=0)
    max_attempts = models.PositiveIntegerField('Máximo de Tentativas', default=3)
    
    # Metadados de processamento
    worker_id = models.CharField('ID do Worker', max_length=100, blank=True)
    last_attempt = models.DateTimeField('Última Tentativa', null=True, blank=True)
    
    def can_retry(self):
        """Verifica se ainda pode tentar processar"""
        return self.attempts < self.max_attempts
    
    def increment_attempts(self):
        """Incrementa o contador de tentativas"""
        from django.utils import timezone
        self.attempts += 1
        self.last_attempt = timezone.now()
        self.save()
    
    def __str__(self):
        return f"Fila: {self.print_job.job_id.hex[:8]} ({self.get_priority_display()})"
    
    class Meta:
        verbose_name = 'Item da Fila de Impressão'
        verbose_name_plural = 'Fila de Impressão'
        ordering = ['priority', 'scheduled_for']


class PrinterConfiguration(TimeStampedModel):
    """Configuração de impressora para etiquetas"""
    
    PRINTER_TYPES = [
        ('thermal', 'Térmica'),
        ('inkjet', 'Jato de Tinta'),
        ('laser', 'Laser'),
        ('label', 'Etiquetadora'),
    ]
    
    name = models.CharField('Nome da Impressora', max_length=100)
    printer_type = models.CharField('Tipo', max_length=20, choices=PRINTER_TYPES)
    system_name = models.CharField('Nome no Sistema', max_length=200, 
                                  help_text='Nome da impressora no sistema operacional')
    
    # Configurações técnicas
    max_width_mm = models.PositiveIntegerField('Largura Máxima (mm)', default=100)
    max_height_mm = models.PositiveIntegerField('Altura Máxima (mm)', default=150)
    dpi = models.PositiveIntegerField('DPI', default=300)
    supports_color = models.BooleanField('Suporta Cor', default=True)
    
    # Status
    is_active = models.BooleanField('Ativo', default=True)
    is_default = models.BooleanField('Padrão', default=False)
    
    # Configurações específicas (JSON)
    driver_config = models.JSONField('Configurações do Driver', default=dict, blank=True)
    
    def save(self, *args, **kwargs):
        # Garantir que apenas uma impressora seja padrão
        if self.is_default:
            PrinterConfiguration.objects.filter(
                is_default=True
            ).exclude(id=self.id).update(is_default=False)
        
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.name} ({self.get_printer_type_display()})"
    
    class Meta:
        verbose_name = 'Configuração de Impressora'
        verbose_name_plural = 'Configurações de Impressoras'
        ordering = ['name']

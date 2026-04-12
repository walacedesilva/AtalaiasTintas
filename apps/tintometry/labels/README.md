# Sistema de Etiquetas - Interface Web

Este módulo fornece uma interface web completa para operadores gerarem etiquetas de misturas de tintas no sistema AtalaiasTintas.

## Funcionalidades

### Dashboard Principal (`/etiquetas/`)
- Visão geral das estatísticas de etiquetas
- Misturas recentes criadas
- Templates mais utilizados
- Estatísticas de volume e custo

### Gerenciamento de Misturas (`/etiquetas/misturas/`)
- Listagem completa de todas as misturas
- Filtros por status, loja, data, família de cor
- Busca por código, cliente ou cor
- Ações em lote (alterar status, gerar etiquetas)
- Seleção múltipla para impressão

### Criação de Misturas (`/etiquetas/nova-mistura/`)
- Formulário em 3 etapas:
  1. **Seleção de Fórmula**: Busca e filtra fórmulas por cor
  2. **Dados do Cliente**: Informações do cliente e volume
  3. **Confirmação**: Revisão e cálculo de custos
- Busca em tempo real de fórmulas
- Cálculo automático de quantidades e custos
- Preview da cor selecionada

### Preview de Etiqueta (`/etiquetas/preview/<id>/`)
- Visualização em tempo real da etiqueta
- Seleção de diferentes templates
- QR Code e código de barras dinâmicos
- Informações detalhadas da mistura e fórmula
- Opção de impressão direta

### Geração de Etiquetas (`/etiquetas/gerar/`)
- Interface para configuração de impressão
- Seleção de templates (Padrão, Compacto, Premium, Eco)
- Configurações de papel, qualidade e cor
- Múltiplas cópias e orientação
- Processamento em lote de multiple misturas
- Download de PDFs ou impressão direta

### Gerenciamento de Templates (`/etiquetas/templates/`)
- Criação e edição de templates personalizados
- Preview em tempo real das alterações
- Configuração de cores, fontes e layout
- Elementos opcionais (QR Code, código de barras, logo)
- Estatísticas de uso dos templates
- Importação e exportação de templates

## Componentes Técnicos

### Templates HTML
- **`base.html`**: Layout base com navegação e estilos
- **`index.html`**: Dashboard com estatísticas
- **`nova_mistura.html`**: Formulário wizard de 3 etapas
- **`misturas.html`**: Lista com filtros e ações em lote
- **`preview.html`**: Preview da etiqueta com diferentes templates
- **`gerar.html`**: Interface de geração e configuração
- **`templates.html`**: Gerenciamento de templates com editor visual

### Views Django (`web_views.py`)
- **Dashboard**: Estatísticas e resumos
- **Lista de Misturas**: Filtros, busca e paginação
- **Formulário Nova Mistura**: Processamento em etapas
- **Preview**: Visualização dinâmica
- **Geração**: Interface de configuração
- **Templates**: Gerenciamento visual

### APIs AJAX
- `/api/batch-action/`: Ações em lote
- `/api/search-formulas/`: Busca de fórmulas
- `/api/update-status/<id>/`: Atualização de status
- `/api/qr-code/<id>/`: Geração de QR Code
- `/api/barcode/<id>/`: Geração de código de barras

### Modelos de Dados
- **`LabelTemplate`**: Templates personalizáveis
- **`LabelPrintJob`**: Trabalhos de impressão
- **`LabelPrintQueue`**: Fila de processamento
- **`PrinterConfiguration`**: Configurações de impressoras

### Serviços
- **`QRCodeService`**: Geração de QR Codes
- **`BarcodeService`**: Códigos de barras
- **`LabelGeneratorService`**: PDFs de etiquetas
- **`LabelTemplateService`**: Gerenciamento de templates

## Fluxo de Trabalho

1. **Operador acessa o sistema** em `/etiquetas/`
2. **Cria nova mistura** via formulário wizard
3. **Visualiza preview** da etiqueta gerada
4. **Configura impressão** com template e opções
5. **Gera PDF ou imprime diretamente**
6. **Acompanha status** na lista de misturas

## Recursos Adicionais

### Bootstrap 5.3.2
- Design responsivo para tablets e desktops
- Componentes interativos (modais, dropdowns, cards)
- Sistema de grid flexível
- Ícones Bootstrap Icons

### JavaScript Vanilla
- Interatividade sem dependências externas
- AJAX para atualizações dinâmicas
- Validação de formulários em tempo real
- Filtros e buscas dinâmicas

### Funcionalidades Avançadas
- **Batch Operations**: Processamento em lote
- **Real-time Preview**: Preview ao vivo
- **Template Editor**: Editor visual de templates
- **Status Management**: Controle de estados
- **QR Code Integration**: Rastreamento completo
- **Multi-format Export**: PDF, impressão direta

## Configuração

### Dependências Python
```bash
pip install qrcode[pil] python-barcode[images] reportlab
```

### Configuração Django
```python
INSTALLED_APPS = [
    # ...
    'apps.tintometry.labels',
]
```

### URLs
```python
# urls.py principal
path('etiquetas/', include('apps.tintometry.labels.urls')),
```

### Migrações
```bash
python manage.py makemigrations labels
python manage.py migrate
```

## Uso

1. Acesse `/etiquetas/` no navegador
2. Use a navegação lateral para acessar diferentes seções
3. Crie misturas via formulário wizard
4. Gere etiquetas com templates personalizados
5. Gerencie configurações no Django Admin

## Personalização

### Templates Customizados
- Cores, fontes e layout configuráveis
- Elementos opcionais (QR, barcode, logo)
- Dimensões personalizáveis
- Export/import de configurações

### Integração com Impressoras
- Suporte a impressoras térmicas
- Configuração de qualidade e papel
- Fila de impressão assíncrona
- Status de processamento

## Suporte

Para dúvidas ou problemas:
1. Verifique os logs do Django
2. Teste as APIs via navegador/Postman
3. Validar configurações de impressora
4. Consultar documentação do ReportLab para PDFs

O sistema foi projetado para ser intuitivo e não requer treinamento técnico avançado para operadores.
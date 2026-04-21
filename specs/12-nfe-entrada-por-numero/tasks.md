# Tasks: Entrada de NF-e por Número / Chave de Acesso

**Feature:** 12-nfe-entrada-por-numero  
**Status:** Tasks → pronto para Implement  
**Data:** 2026-04-20

---

## Dependency Order

```
T1 (model + migration)
  → T2 (service criar_manual — depende do model)
    → T3 (endpoint API — depende do service)
      → T4 (admin Django — depende do model)
      → T5 (frontend types + api + hook — depende do endpoint)
        → T6 (EntradaManualModal — depende do hook)
          → T7 (badge origem + botão na EntradasTab — depende do modal e do tipo)
```

---

## Tasks P1 — MVP

### [T1] [P1] Model: campo `origem_entrada` + migration [US-4, RF-04]
**Arquivo:** `backend/apps/inventory/models.py`  
**Arquivo migration:** `backend/apps/inventory/migrations/`

- Adicionar em `EntradaMercadoria`:
  ```python
  ORIGEM_CHOICES = [
      ('XML_UPLOAD', 'Upload de XML'),
      ('MANUAL', 'Entrada Manual'),
      ('SEFAZ_DOWNLOAD', 'Download SEFAZ'),
  ]
  origem_entrada = models.CharField(
      max_length=20, choices=ORIGEM_CHOICES, default='XML_UPLOAD'
  )
  ```
- Atualizar `TIPO_ENTRADA_CHOICES` para incluir `'XML_UPLOAD'` como default existente
- Gerar migration: `python manage.py makemigrations inventory`

Status: [x] completed [US-1, RF-01]
**Arquivo:** `backend/apps/fiscal/services.py`

```python
@staticmethod
def criar_manual(
    loja_id: int,
    usuario,
    numero_nfe: str,
    serie_nfe: str,
    fornecedor_cnpj: str,
    data_emissao_nfe,
    fornecedor_nome: str | None,
    fornecedor_uf: str | None,
    valor_total_nfe: Decimal,
    chave_acesso_nfe: str | None,
    observacoes: str,
    itens: list[dict],
) -> 'EntradaMercadoria':
```

- Validar CNPJ com algoritmo módulo 11 (levantar `ValueError` se inválido)
- Verificar idempotência por `chave_acesso_nfe` (se fornecida)
- Criar `EntradaMercadoria(status='PENDENTE', origem_entrada='MANUAL')`
- Para cada item em `itens`: criar `EntradaMercadoriaItem(status='PENDENTE')`
- Transação atômica
- Log: `logger.info("Entrada manual criada: id=%s fornecedor=%s itens=%d", ...)`

**Validação de CNPJ** (módulo 11 — implementar ou reutilizar):
- Remover caracteres não numéricos
- Validar 14 dígitos + dígitos verificadores
- Aceitar CPF (11 dígitos) para fornecedores PF sem rejeitar

Status: [x] completed

---

### [T3] [P1] API: endpoint `criar-manual/` no `EntradaMercadoriaViewSet` [US-1, RF-01, RF-03]
**Arquivo:** `backend/apps/inventory/apis.py`

**Novo serializer `EntradaMercadoriaItemManualSerializer`:**
```python
class Meta:
    model = EntradaMercadoriaItem
    fields = ['descricao_nfe', 'codigo_nfe', 'ncm', 'cfop', 
              'quantidade', 'unidade_nfe', 'valor_unitario']
```

**Novo serializer `EntradaMercadoriaManualSerializer`:**
```python
fields = ['loja', 'numero_nfe', 'serie_nfe', 'fornecedor_cnpj',
          'fornecedor_nome', 'fornecedor_uf', 'data_emissao_nfe',
          'valor_total_nfe', 'chave_acesso_nfe', 'observacoes', 'itens']
itens = EntradaMercadoriaItemManualSerializer(many=True)
```
- `validate_fornecedor_cnpj()`: validação de formato

**Novo endpoint:**
```python
@action(detail=False, methods=['post'], url_path='criar-manual')
def criar_manual(self, request):
    serializer = EntradaMercadoriaManualSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    # chama EntradaMercadoriaService.criar_manual(...)
    return Response(EntradaMercadoriaSerializer(entrada).data, status=201)
```

**Atualizar `EntradaMercadoriaSerializer`:**
- Adicionar `origem_entrada` na lista de `fields`

Status: [x] completed

---

### [T4] [P1] Admin Django: exibir `origem_entrada` [US-4, RF-04]
**Arquivo:** `backend/apps/inventory/admin.py`

- Adicionar `origem_entrada` ao `list_display` de `EntradaMercadoriaAdmin`
- Adicionar `origem_entrada` ao fieldset `'Dados da Entrada'`
- Adicionar `origem_entrada` ao `list_filter`
- Remover `chave_acesso_nfe` de `readonly_fields` para permitir preenchimento manual no admin add form (manter read-only apenas na edição via `get_readonly_fields`)

Status: [x] completed

---

### [T5] [P1] Frontend: Types + API client + Hook [US-1]
**Arquivos:**
- `frontend/src/types/index.ts`
- `frontend/src/api/inventory.ts`
- `frontend/src/hooks/useInventory.ts`

**`types/index.ts`** — adicionar em `EntradaMercadoria`:
```typescript
origem_entrada: 'XML_UPLOAD' | 'MANUAL' | 'SEFAZ_DOWNLOAD';
```

**`api/inventory.ts`** — adicionar em `entradas`:
```typescript
interface EntradaManualPayload { ... }
async criarManual(payload: EntradaManualPayload): Promise<EntradaMercadoria>
// POST /inventory/entradas/criar-manual/
```

**`hooks/useInventory.ts`** — adicionar:
```typescript
export function useCriarEntradaManual() {
  return useMutation({ mutationFn: (p) => inventoryAPI.entradas.criarManual(p) });
}
```

Status: [x] completed

---

### [T6] [P1] Frontend: Componente `EntradaManualModal` [US-1, RF-01, RF-06]
**Arquivo:** `frontend/src/pages/inventory/EstoquePage.tsx`

Novo componente funcional antes da `EntradasTab`:

**Seção Cabeçalho NF-e:**
- `numero_nfe` (obrigatório, max 9 dígitos)
- `serie_nfe` (obrigatório, default '1')
- `data_emissao_nfe` (date input, obrigatório)
- `fornecedor_cnpj` (obrigatório, máscara XX.XXX.XXX/XXXX-XX ou XXX.XXX.XXX-XX)
- `fornecedor_nome` (opcional)
- `chave_acesso_nfe` (opcional, 44 dígitos, monospace input)
- `valor_total_nfe` (opcional, currency input)
- `observacoes` (textarea, opcional)

**Seção Itens (tabela inline):**
- Linha de cabeçalho + botão "+ Adicionar Item"
- Cada linha: Descrição*, Código NF-e, NCM, Qtd*, Unid*, Vlr Unit*, [Remover]
- Estado local `itens: ItemForm[]`
- Validação: pelo menos 1 item obrigatório

**Footer:**
- "Cancelar" — fecha modal
- "Salvar Entrada" — chama `criarManual`, fecha modal, invalida queries `['entradas']`

**Acessibilidade:** `role="dialog"`, `aria-modal`, `aria-label`, labels em todos os inputs

Status: [x] completed

---

### [T7] [P1] Frontend: Badge origem + botão "Entrada Manual" na EntradasTab [US-4, RF-04]
**Arquivo:** `frontend/src/pages/inventory/EstoquePage.tsx` → `EntradasTab`

- Adicionar `const [showManual, setShowManual] = useState(false)` na `EntradasTab`
- Renderizar `<EntradaManualModal>` quando `showManual` for true
- Adicionar botão "Entrada Manual" (botão secundário, ícone `PenLine`) ao lado de "Importar XML NF-e"
- Adicionar coluna "Origem" na tabela de entradas:
  - `XML_UPLOAD`: badge azul com ícone Upload
  - `MANUAL`: badge âmbar com ícone PenLine
  - `SEFAZ_DOWNLOAD`: badge verde com ícone CloudDownload
- Fallback: se `origem_entrada` indefinido (dados legados), exibir `XML_UPLOAD`

Status: [x] completed

---

## Tasks P2 — Futuro (não bloqueiam MVP)

### [T8] [P2] Backend: endpoint `consultar-chave/` + SEFAZ DistribuiçãoDFe [US-2, RF-02]
**Arquivo:** `backend/apps/inventory/apis.py` + `backend/apps/fiscal/sefaz/`

- Endpoint `POST /api/v1/inventory/entradas/consultar-chave/` com body `{ chave_acesso: str, loja_id: int }`
- Integração com `DistribuiçãoDFe` (webservice SEFAZ para destinatário baixar XML)
- Se XML disponível → chama `EntradaMercadoriaService.importar_xml()` com `origem_entrada='SEFAZ_DOWNLOAD'`
- Se indisponível → retorna `{ disponivel: false, erro: '...' }` com status 200 (gracioso)

Status: [x] completed

### [T9] [P2] Frontend: campo chave_acesso no modal + fallback manual [US-2, RF-02]
**Arquivo:** `frontend/src/pages/inventory/EstoquePage.tsx`

- Adicionar campo de chave_acesso com botão "Consultar SEFAZ" no `EntradaManualModal`
- Ao clicar: loading spinner, chama `POST /entradas/consultar-chave/`
- Se sucesso: fecha modal (entrada já criada pelo backend), atualiza listagem
- Se falha: exibe mensagem e permite continuar preenchimento manual

Status: [x] completed

---

## Checklist de Qualidade

- [ ] Migration é retrocompatível (`default='XML_UPLOAD'` para registros existentes)
- [ ] Validação CNPJ: testar CNPJs válidos, inválidos, CPF, CNPJ formatado vs numérico
- [ ] Idempotência: tentar criar duas vezes com a mesma `chave_acesso_nfe` — segunda vez retorna a existente
- [ ] Modal tem at least 1 item obrigatório antes de salvar
- [ ] Todos os inputs do modal têm `label` associado
- [ ] Botão "Salvar Entrada" desabilitado durante loading
- [ ] Invalidação de query após criação: listagem atualiza automaticamente
- [ ] `EntradaMercadoria` criada manualmente pode ser confirmada pelo fluxo existente (vincular itens → confirmar)
- [ ] Tests de unidade para `criar_manual()` passam antes de qualquer outro passo (TDD)

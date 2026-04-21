# Plan: Feature 12 — Entrada de NF-e por Número / Chave de Acesso

**Status:** Plan  
**Feature:** specs/12-nfe-entrada-por-numero  
**Depende de:** Feature 4 (EntradaMercadoria model — já existe), Feature 4 (confirmação de entrada — já existe)

---

## Análise do Estado Atual

### O que já existe (reutilizável)
| Componente | Localização | Estado |
|---|---|---|
| Model `EntradaMercadoria` | `backend/apps/inventory/models.py` | ✅ Tem `numero_nfe`, `serie_nfe`, `chave_acesso_nfe`, `fornecedor_cnpj`, `xml_nfe` |
| Model `EntradaMercadoriaItem` | `backend/apps/inventory/models.py` | ✅ Tem todos os campos de item necessários |
| `EntradaMercadoriaViewSet` | `backend/apps/inventory/apis.py` | ✅ Tem `importar-xml`, `confirmar`, `vincular_item` |
| `EntradaMercadoriaSerializer` | `backend/apps/inventory/apis.py` | ✅ Serializa entrada + itens (read-only inline) |
| `EntradaMercadoriaService` | `backend/apps/fiscal/services.py` | ✅ Tem `importar_xml()`, `confirmar_entrada()` |
| `SefazClient.consultar_situacao()` | `backend/apps/fiscal/sefaz/` | ⚠️ Consulta status, não baixa XML de entrada |
| `EntradasTab` | `frontend/src/pages/inventory/EstoquePage.tsx` | ✅ Listagem + botão XML upload |
| `inventoryAPI.entradas.*` | `frontend/src/api/inventory.ts` | ✅ list, importarXml, confirmar |
| `useImportarXmlNFe` hook | `frontend/src/hooks/useInventory.ts` | ✅ |

### Gaps identificados
1. **Model**: sem campo `origem_entrada` para diferenciar XML upload / manual / SEFAZ download
2. **Backend API**: sem endpoint de criação manual com itens inline
3. **Backend API**: sem endpoint de consulta por chave (SEFAZ DistribuiçãoDFe — P2)
4. **Frontend**: sem formulário de entrada manual
5. **Frontend**: sem badge de origem na listagem

---

## Arquitetura da Solução

### Fluxo P1 — Entrada Manual (sem XML)
```
Usuário clica "Entrada Manual"
  → Modal/Drawer: preenche metadados NF-e + items
  → POST /api/v1/inventory/entradas/criar-manual/
  → EntradaMercadoriaService.criar_manual()
  → EntradaMercadoria criada (status=PENDENTE, origem=MANUAL)
  → Operador vincula itens ao ProdutoVariacao (fluxo existente)
  → Confirma entrada (fluxo existente)
```

### Fluxo P2 — Consulta por Chave (SEFAZ DistribuiçãoDFe)
```
Usuário informa chave 44 dígitos + clica "Consultar SEFAZ"
  → POST /api/v1/inventory/entradas/consultar-chave/
  → SefazClient.distribuicao_dfe(chave) → baixa XML
  → Redireciona para EntradaMercadoriaService.importar_xml() existente
  → Retorna entrada criada (origem=SEFAZ_DOWNLOAD)
```

---

## Mudanças de Backend

### M1: Migration — campo `origem_entrada`
**Arquivo:** `backend/apps/inventory/models.py`
- Adicionar `origem_entrada = models.CharField(max_length=20, choices=[...], default='XML_UPLOAD')`
- Choices: `XML_UPLOAD`, `MANUAL`, `SEFAZ_DOWNLOAD`
- Gerar migration com `makemigrations inventory`

### M2: Serializer — `EntradaMercadoriaCreateManualSerializer`
**Arquivo:** `backend/apps/inventory/apis.py`
- Serializer de criação manual com `ListSerializer` para itens inline
- Campos obrigatórios: `numero_nfe`, `serie_nfe`, `fornecedor_cnpj`, `data_emissao_nfe`, `loja`, `itens`
- Campos opcionais: `fornecedor_nome`, `fornecedor_uf`, `valor_total_nfe`, `observacoes`
- `itens`: lista de `EntradaMercadoriaItemCreateSerializer` (descricao_nfe, quantidade, valor_unitario, ncm, cfop, unidade_nfe)
- Validação de CNPJ com algoritmo módulo 11

### M3: Endpoint — `criar-manual/`
**Arquivo:** `backend/apps/inventory/apis.py` → `EntradaMercadoriaViewSet`
- `@action(detail=False, methods=['post'], url_path='criar-manual')`
- Chama `EntradaMercadoriaService.criar_manual(data, usuario)`
- Retorna `EntradaMercadoriaSerializer` com status 201

### M4: Service — `EntradaMercadoriaService.criar_manual()`
**Arquivo:** `backend/apps/fiscal/services.py`
- Recebe dict com metadados + lista de itens
- Verifica idempotência: se `chave_acesso_nfe` fornecida, checa duplicata
- Cria `EntradaMercadoria(status='PENDENTE', origem_entrada='MANUAL')`
- Cria `EntradaMercadoriaItem` para cada item (status='PENDENTE')
- Transação atômica
- Retorna a entrada criada

### M5: Atualizar `EntradaMercadoriaSerializer`
**Arquivo:** `backend/apps/inventory/apis.py`
- Adicionar campo `origem_entrada` na listagem/detalhe

### M6: Admin Django — tornar `chave_acesso_nfe` editável na criação manual
**Arquivo:** `backend/apps/inventory/admin.py`
- Remover `chave_acesso_nfe` de `readonly_fields` OR manter read-only apenas no detalhe
- Alternativa mais simples: manter admin como está (já permite criação manual via add form se `chave_acesso_nfe` não for readonly na criação)
- Adicionar `origem_entrada` ao fieldset "Dados da Entrada"

---

## Mudanças de Frontend

### F1: Tipos TypeScript
**Arquivo:** `frontend/src/types/index.ts`
- Adicionar `origem_entrada: 'XML_UPLOAD' | 'MANUAL' | 'SEFAZ_DOWNLOAD'` em `EntradaMercadoria`

### F2: API client
**Arquivo:** `frontend/src/api/inventory.ts`
- Adicionar `criarManual(payload: EntradaMercadoriaManualPayload): Promise<EntradaMercadoria>`
  - `POST /inventory/entradas/criar-manual/`

### F3: Hook
**Arquivo:** `frontend/src/hooks/useInventory.ts`
- Adicionar `useCriarEntradaManual()` → `useMutation` chamando `inventoryAPI.entradas.criarManual()`

### F4: Componente `EntradaManualModal`
**Arquivo:** `frontend/src/pages/inventory/EstoquePage.tsx`
- Modal com duas seções:
  1. **Cabeçalho NF-e**: numero_nfe, serie_nfe, data_emissao_nfe, fornecedor_cnpj (com formatação), fornecedor_nome, valor_total_nfe
  2. **Tabela de Itens**: lista inline editável com addRow / removeRow
     - Colunas: Descrição*, Cód. NF-e, NCM, Qtd*, Unid*, Vlr Unit*
- Botão "Salvar Rascunho" → chama `criarManual` → fecha modal → atualiza listagem
- Validação de formulário client-side antes de enviar

### F5: Badge de Origem na Listagem
**Arquivo:** `frontend/src/pages/inventory/EstoquePage.tsx` → `EntradasTab`
- Coluna adicional na tabela: "Origem" com badge colorido
  - XML_UPLOAD: `bg-blue-50 text-blue-700` + ícone Upload
  - MANUAL: `bg-amber-50 text-amber-700` + ícone PenLine
  - SEFAZ_DOWNLOAD: `bg-emerald-50 text-emerald-700` + ícone CloudDownload
- Botão "Entrada Manual" ao lado de "Importar XML NF-e"

---

## Dependências e Riscos

| Risco | Impacto | Mitigação |
|---|---|---|
| Migration em produção com dados existentes | Médio | `default='XML_UPLOAD'` garante retrocompatibilidade |
| SEFAZ DistribuiçãoDFe (P2) requer certificado A1 configurado | Alto | Escopo P2, não bloqueia P1 |
| CNPJ validation: edge cases (CNPJ raiz, CPF) | Baixo | Aceitar também CPF de fornecedor PF; usar biblioteca `validate-docbr` ou implementar módulo 11 |
| Performance: entrada com muitos itens (>50) | Baixo | Limitar a 100 itens no front; paginação não necessária para este formulário |

---

## Sequência de Implementação

```
T1: Migration + campo origem_entrada (backend/inventory/models.py + migration)
T2: EntradaMercadoriaService.criar_manual() (backend/apps/fiscal/services.py)
T3: Serializer + endpoint criar-manual/ (backend/apps/inventory/apis.py)
T4: Admin Django — origem_entrada no fieldset (backend/apps/inventory/admin.py)
T5: Types + API client + hook (frontend/src/types, api, hooks)
T6: EntradaManualModal component (frontend/src/pages/inventory/EstoquePage.tsx)
T7: Badge origem + botão "Entrada Manual" na EntradasTab (same file)
─── P2 (futuro, não bloqueia) ───────────────────────────────────────────
T8: SEFAZ DistribuiçãoDFe endpoint consultar-chave/
T9: Integração do campo chave_acesso no modal (F2 → F1 fallback)
```

---

## Testes Necessários

- `backend/apps/inventory/tests/test_entrada_manual.py` (novo)
  - `test_criar_entrada_manual_sucesso`
  - `test_criar_entrada_manual_cnpj_invalido`
  - `test_criar_entrada_manual_idempotencia_por_chave`
  - `test_criar_entrada_manual_sem_itens_falha`
  - `test_confirmar_entrada_manual_atualiza_estoque`
- Frontend: testes manuais via browser (Playwright E2E em P2)

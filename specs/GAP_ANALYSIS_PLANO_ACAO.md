# Gap Analysis & Plano de Ação — Sistema Atalaia Tintas
**Referência**: Análise comparativa com ERP Lexos (imagens fornecidas em 14/04/2026)  
**Metodologia**: Spec-Kit Workflow  
**Status**: 🔴 GAP crítico identificado — 14 módulos pendentes ou incompletos

---

## 1. Resumo Executivo do Gap

### O que o Lexos ERP mostra que precisamos ter

| Módulo Lexos | Status no Nosso Sistema | Gap |
|---|---|---|
| Controle de Estoque — produto CRUD | Backend ✅ Models existem | Frontend ❌ sem UI de produto |
| Controle de Estoque — movimentações | Backend ✅ `MovimentacaoEstoque` | Frontend ❌ sem listagem |
| Controle de Estoque — lote tracking | Backend ✅ `LoteProduto` | Frontend ❌ sem UI |
| Controle de Estoque — Relatórios | Backend ❌ | Frontend ❌ |
| Controle de Estoque — Transferência | Backend ❌ | Frontend ❌ |
| Clientes | Backend ✅ `Cliente` model + rich fields | Frontend ❌ sem página |
| Clientes — API REST | Backend ❌ `sales/views.py` vazio | API ❌ sem endpoints |
| Pedidos de Venda | Backend ✅ `PedidoVenda`, `ItemPedidoVenda` | Frontend ❌ sem página |
| Pedidos — API REST | Backend ❌ `sales/views.py` vazio | API ❌ sem endpoints |
| Orçamento | Backend ✅ `PedidoVenda.situacao='ORCAMENTO'` | Frontend ❌ sem fluxo |
| PDV / Caixa Livre | Backend ❌ sem modelo `Venda` API | Frontend ❌ sem página |
| NF-e Emissão (saída) | Backend ⚠️ model existe, SEFAZ não impl. | Frontend ❌ sem UI |
| Financeiro / Contas a Pagar | Backend ❌ | Frontend ❌ |
| Emitir NF-e no Estoque | Backend ⚠️ parcial | Frontend ❌ sem botão ativo |
| Fornecedores (CRUD) | Backend ⚠️ usado em EntradaMercadoria | Frontend ❌ sem página |
| **Cores (tintometria)** | Backend ✅ | Frontend ❌ placeholder |
| **Fórmulas (tintometria)** | Backend ✅ | Frontend ❌ placeholder |
| **Misturas (tintometria)** | Backend ✅ | Frontend ❌ placeholder |

---

## 2. Itens Já Implementados (não estão no gap)

| Módulo | Status |
|---|---|
| Dashboard | ✅ Completo |
| Pigmentos — CRUD completo | ✅ Implementado em 14/04/2026 |
| Etiquetas | ✅ Completo |
| Autenticação / Login | ✅ Completo |
| Perfil de usuário | ✅ Completo |
| Menu de ajuda (? drawer) | ✅ Implementado em 14/04/2026 |
| Importação de NF-e XML | ✅ Implementado (entrada de mercadoria) |
| Validação e parse NF-e | ✅ Testado com 5 itens |
| Backend — modelos tintometria | ✅ Pigmento, Cor, Formula, ProducaoTinta |
| Backend — modelos inventário | ✅ ProdutoBase, ProdutoVariacao, EstoqueLoja, movimentações |
| Backend — modelos fiscais | ✅ NotaFiscalEletronica, ItemNFe |
| Backend — modelos vendas | ✅ Cliente, PedidoVenda, ItemPedidoVenda, Venda |

---

## 3. Plano de Ação por Prioridade

### 🔴 PRIORIDADE 1 — Módulos Core que Desbloqueiam Operação

---

#### A1 — Tintometria: Cores, Fórmulas e Misturas
**Dependência**: Pigmentos ✅ já implementado  
**Backend**: APIs existem parcialmente em `apps/tintometry/`  
**Trabalho necessário**:

| # | Tarefa | Arquivo | Tipo |
|---|---|---|---|
| 1 | Implementar `CoresPage.tsx` — CRUD completo | `frontend/src/pages/colors/` | Frontend |
| 2 | Implementar `FormulasPage.tsx` — CRUD + preview | `frontend/src/pages/formulas/` | Frontend |
| 3 | Implementar `MisturasPage.tsx` — calculadora + histórico | `frontend/src/pages/mixtures/` | Frontend |
| 4 | Hook `useDeleteCor`, `useDeleteFormula`, `useDeleteMistura` | `hooks/useTintometry.ts` | Frontend |
| 5 | Verificar/completar APIs de Cor, Formula, Mistura | `apps/tintometry/views.py` | Backend |

**Estimativa**: 3–4 dias  
**Impacto**: Desbloqueia o fluxo completo de tintometria

---

#### A2 — Estoque: Produto CRUD e Movimentações
**Dependência**: Schema ✅ `ProdutoBase`, `ProdutoVariacao`, `EstoqueLoja`, `MovimentacaoEstoque`  
**Backend**: `apis.py` tem `EntradaMercadoriaViewSet` mas falta viewset para produtos  
**Trabalho necessário**:

| # | Tarefa | Arquivo | Tipo |
|---|---|---|---|
| 1 | `ProdutoViewSet` com list/create/update/delete | `apps/inventory/apis.py` | Backend API |
| 2 | `ProdutoSerializer` com variações e estoque_atual | `apps/inventory/serializers.py` | Backend |
| 3 | URL routing produtos | `apps/inventory/urls.py` | Backend |
| 4 | Expandir `EstoquePage.tsx` — aba Produtos com CRUD | `frontend/src/pages/inventory/EstoquePage.tsx` | Frontend |
| 5 | Filtro "Itens em falta" (estoque_atual <= minimo) | `apis.py` + `EstoquePage.tsx` | Full-stack |
| 6 | Aba Movimentações com histórico + lote + fornecedor | `EstoquePage.tsx` | Frontend |
| 7 | Totais: Qtde Total, Reservada, Disponível, Custo Total | `EstoquePage.tsx` | Frontend |
| 8 | Exportar Produtos (CSV/Excel) | `apis.py` + `EstoquePage.tsx` | Full-stack |

**Estimativa**: 4–5 dias  
**Impacto**: Desbloqueia operação de estoque básica equivalente ao Lexos

---

#### A3 — Clientes: CRUD + API REST
**Dependência**: `Cliente` model ✅ completo com 20+ campos  
**Backend**: `sales/views.py` vazio — precisa criar do zero  
**Trabalho necessário**:

| # | Tarefa | Arquivo | Tipo |
|---|---|---|---|
| 1 | `ClienteViewSet` (CRUD + busca por CPF/CNPJ/telefone) | `apps/sales/apis.py` (novo) | Backend API |
| 2 | `ClienteSerializer` completo (PF + PJ) | `apps/sales/serializers.py` (novo) | Backend |
| 3 | URL routing clientes | `apps/sales/urls.py` | Backend |
| 4 | `ClientesPage.tsx` — tabela com search + modal | `frontend/src/pages/sales/ClientesPage.tsx` | Frontend |
| 5 | Hook `useClientes`, `useCreateCliente`, etc. | `frontend/src/hooks/useSales.ts` (novo) | Frontend |
| 6 | API client `salesAPI.clientes.*` | `frontend/src/api/sales.ts` (novo) | Frontend |
| 7 | Tipos TypeScript `Cliente` | `frontend/src/types/index.ts` | Frontend |
| 8 | Rota `/clientes` no React Router | `frontend/src/App.tsx` | Frontend |

**Estimativa**: 3 dias  
**Impacto**: Desbloqueia pedidos, vendas e histórico de cores

---

### 🟡 PRIORIDADE 2 — Módulos Operacionais Essenciais

---

#### B1 — Pedidos e Orçamentos
**Dependência**: Clientes ✅ (A3), Produtos ✅ (A2)  
**Backend**: `PedidoVenda`, `ItemPedidoVenda` ✅ models completos, views vazio  
**Trabalho necessário**:

| # | Tarefa | Arquivo | Tipo |
|---|---|---|---|
| 1 | `PedidoVendaViewSet` (CRUD + transições de status) | `apps/sales/apis.py` | Backend API |
| 2 | `ItemPedidoVendaSerializer` | `apps/sales/serializers.py` | Backend |
| 3 | Endpoint `aprovar`, `cancelar`, `entregar` | `apps/sales/apis.py` | Backend API |
| 4 | `PedidosPage.tsx` — lista + filtros por situação | `frontend/src/pages/sales/PedidosPage.tsx` | Frontend |
| 5 | `PedidoDetalhe.tsx` — itens, status, ações | `frontend/src/pages/sales/PedidoDetalhe.tsx` | Frontend |
| 6 | Fluxo de orçamento → aprovação → entrega | Frontend + Backend | Full-stack |
| 7 | Integração com tintometria (ProducaoTinta vinculado) | `ItemPedidoVenda.producao_tinta` | Full-stack |

**Estimativa**: 4 dias  
**Impacto**: Permite gestão de pedidos do balcão

---

#### B2 — PDV / Caixa Livre
**Dependência**: Clientes ✅ (A3), Produtos ✅ (A2), Pedidos ✅ (B1)  
**Backend**: `Venda` model existe em `sales/models.py` mas sem API  
**Trabalho necessário**:

| # | Tarefa | Arquivo | Tipo |
|---|---|---|---|
| 1 | `VendaViewSet` com finalizar, cancelar | `apps/sales/apis.py` | Backend API |
| 2 | Integração com `EstoqueService.reservar()` + `baixar()` | `apps/inventory/services.py` | Backend |
| 3 | `PDVPage.tsx` — interface de venda rápida | `frontend/src/pages/pdv/PDVPage.tsx` | Frontend |
| 4 | Busca de produto por código de barras/nome | Frontend + Backend | Full-stack |
| 5 | Cálculo de desconto, total, troco | Frontend | Frontend |
| 6 | Impressão de recibo (PDF) | Backend | Backend |
| 7 | Indicador de método fiscal ativo | Frontend | Frontend |
| 8 | Keyboard shortcuts (F-keys ou equivalentes) | Frontend | Frontend |

**Estimativa**: 5–6 dias  
**Impacto**: Frente de caixa funcional — alto impacto operacional

---

#### B3 — NF-e Emissão (Saída para SEFAZ)
**Dependência**: Pedidos ✅ (B1), cliente com CNPJ  
**Backend**: `NotaFiscalEletronica` model existe, `NFEService` é stub  
**Trabalho necessário**:

| # | Tarefa | Arquivo | Tipo |
|---|---|---|---|
| 1 | Completar `NFEService.emitir()` — assinar + enviar SEFAZ | `apps/fiscal/services.py` | Backend |
| 2 | `SefazClient` com ambiente homologação e produção | `apps/fiscal/services.py` | Backend |
| 3 | Geração de XML NF-e v4.00 a partir do pedido | `apps/fiscal/services.py` | Backend |
| 4 | Endpoint `POST /fiscal/nfe/emitir/` | `apps/fiscal/apis.py` | Backend API |
| 5 | UI de NF-e no Estoque — botão "Emitir NF-e" ativo | `EstoquePage.tsx` | Frontend |
| 6 | Consulta de status de NF-e (autorizada/rejeitada) | Frontend + Backend | Full-stack |
| 7 | Download do DANFE (PDF) | Backend | Backend |
| 8 | Criação de `.env.example` com credenciais SEFAZ | `.env.example` | Config |

**Estimativa**: 5–7 dias (complexidade fiscal alta)  
**Impacto**: Conformidade legal para vendas B2B

---

### 🟢 PRIORIDADE 3 — Módulos de Gestão e Relatórios

---

#### C1 — Fornecedores
**Trabalho necessário**: API + frontend CRUD similar ao Clientes (A3)  
**Estimativa**: 2 dias

---

#### C2 — Financeiro (Contas a Pagar)
**Trabalho necessário**: Novo model `ContaPagar` + API + frontend  
**Estimativa**: 3–4 dias

---

#### C3 — Relatórios de Estoque
**Trabalho necessário**: Endpoints de agregação + página de relatórios  
**Itens do Lexos**: Inventário, movimentações por período, itens em falta, custo total  
**Estimativa**: 3 dias

---

#### C4 — Transferência entre Lojas
**Trabalho necessário**: Novo endpoint + UI para transferir estoque entre lojas  
**Estimativa**: 2 dias

---

## 4. Mapeamento de Dependências

```
Pigmentos ✅
    │
    ▼
Cores ──► Fórmulas ──► Misturas (A1)
                            │
                            ▼
Produtos CRUD (A2) ◄──── Misturas vinculadas a ProducaoTinta
    │
    ▼
Clientes (A3)
    │
    ▼
Pedidos/Orçamentos (B1)
    │
    ├──► PDV/Caixa (B2)
    │
    └──► NF-e Emissão (B3)

Fornecedores (C1) ──► Compras (futuro)
Financeiro (C2) ◄──── Pedidos/PDV
Relatórios (C3) ◄──── Estoque + Vendas
```

---

## 5. Cronograma Estimado

| Semana | Tarefas | Produtos entregues |
|---|---|---|
| Semana 1 | A1 (Cores, Fórmulas, Misturas) | Tintometria completa |
| Semana 2 | A2 (Estoque CRUD + movimentações) | Estoque operacional |
| Semana 3 | A3 (Clientes) + B1 início | Clientes cadastrados |
| Semana 4 | B1 (Pedidos) completo | Pedidos e orçamentos |
| Semana 5 | B2 (PDV/Caixa) | Frente de caixa |
| Semana 6 | B3 início (NF-e emissão) | NF-e homologação |
| Semana 7 | B3 completo + C1 (Fornecedores) | NF-e produção + fornecedores |
| Semana 8 | C2 (Financeiro) + C3 (Relatórios) | Módulo financeiro + relatórios |

**MVP operacional mínimo**: Semanas 1–4 (tintometria + estoque + clientes + pedidos)  
**Sistema completo equivalente ao Lexos**: Semanas 1–7

---

## 6. Ordem Recomendada de Implementação com Spec-Kit

Cada item abaixo deve passar pelo fluxo:  
`/speckit.specify` → `/speckit.plan` → `/speckit.tasks` → `/speckit.analyze` → `/speckit.implement`

```
[ ] Spec 5: cores-formulas-misturas      (A1 — próxima sesão)
[ ] Spec 6: estoque-produto-crud         (A2)
[ ] Spec 7: clientes-api-frontend        (A3)
[ ] Spec 8: pedidos-orcamentos           (B1)
[ ] Spec 9: pdv-caixa                    (B2)
[ ] Spec 10: nfe-emissao-sefaz           (B3)
[ ] Spec 11: fornecedores                (C1)
[ ] Spec 12: financeiro-contas-pagar     (C2)
[ ] Spec 13: relatorios-estoque          (C3)
```

---

## 7. O que o Lexos tem que NÃO vamos implementar (fora de escopo)

Com base nas imagens analisadas, os seguintes itens visualizados no Lexos foram **conscientemente excluídos** do escopo pois não fazem parte do sistema tintométrico:

- Veículos no estoque (VW Gol, VW UP, etc.) — sistema de gestão de frotas
- Crediário/análise de crédito complexa — já modelado mas não prioritário
- Multiempresa (matriz/filial) — arquitetura existe mas UI não necessária agora
- Marketplaces integrations — spec futura

---

## 8. Estado Atual do Código por Módulo

### Backend (o que existe vs o que falta)

| App | Models | Serializers | APIs/Views | URLs | Testes |
|---|---|---|---|---|---|
| `tintometry` | ✅ | ✅ | ✅ | ✅ | ⚠️ |
| `inventory` | ✅ | ⚠️ parcial | ⚠️ parcial | ⚠️ | ❌ |
| `sales` | ✅ completo | ❌ | ❌ vazio | ❌ | ❌ |
| `fiscal` | ✅ | ✅ | ⚠️ import only | ⚠️ | ❌ |
| `companies` | ✅ | ⚠️ | ⚠️ | ⚠️ | ❌ |
| `core` | ✅ | ✅ | ✅ | ✅ | ⚠️ |

### Frontend (o que existe vs o que falta)

| Página | Status | Rota |
|---|---|---|
| Dashboard | ✅ Completo | `/` |
| Pigmentos | ✅ CRUD completo | `/tintometry/pigments` |
| Cores | ❌ Placeholder | `/tintometry/colors` |
| Fórmulas | ❌ Placeholder | `/tintometry/formulas` |
| Misturas | ❌ Placeholder | `/tintometry/mixtures` |
| Estoque | ⚠️ Skeleton (só import NF-e) | `/inventory` |
| Etiquetas | ✅ Completo | `/labels` |
| Clientes | ❌ Não existe | `/sales/clients` |
| Pedidos | ❌ Não existe | `/sales/orders` |
| PDV | ❌ Não existe | `/pdv` |
| Fornecedores | ❌ Não existe | `/suppliers` |
| Financeiro | ❌ Não existe | `/financial` |

---

*Gerado por: GitHub Copilot — Spec-Kit Workflow*  
*Data: 14/04/2026*

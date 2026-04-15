# Spec: Menu de Instruções de Uso do Sistema

**Feature**: `5-help-instructions-menu`  
**Status**: specify ✅

---

## Visão Geral

O sistema Atalaia Tintas possui diversas telas especializadas (Pigmentos, Cores, Fórmulas, Misturas, Estoque, Etiquetas). Usuários novos e operadores de loja precisam de orientação rápida sobre **o que cada tela faz** e **como utilizá-la** sem precisar consultar documentação externa.

---

## Problema

Não há nenhum mecanismo de ajuda contextual no sistema. Operadores precisam aprender na prática ou pedir suporte, gerando atrito e erros operacionais.

---

## Solução

Um **botão de ajuda (?)** fixo no Header que abre um painel lateral (drawer/modal) com instruções de uso organizadas por tela. A tela atual é exibida por padrão ao abrir o painel.

---

## User Stories

### US1 — Ajuda Contextual por Tela
**Como** operador de loja,  
**Quero** clicar em um botão de ajuda e ver instruções da tela que estou usando,  
**Para** saber como realizar operações sem sair do sistema.

**Critérios de aceitação:**
- Botão "?" visível no header em todas as telas autenticadas
- Ao clicar, abre painel com instruções da tela atual já selecionada
- Atalho de teclado `?` abre o painel
- Fechar com Esc ou clicando fora

### US2 — Navegação Entre Telas no Painel de Ajuda
**Como** operador,  
**Quero** navegar entre as instruções de qualquer tela dentro do painel de ajuda,  
**Para** aprender sobre funcionalidades que ainda não usei.

**Critérios de aceitação:**
- Lista de todas as telas disponível no painel
- Cada tela tem: título, descrição, lista de ações principais, dicas
- Navegação por tab/click entre telas sem fechar o painel

### US3 — Instruções Detalhadas por Tela
**Como** operador novo,  
**Quero** ver passo-a-passo das ações principais de cada tela,  
**Para** executar operações pela primeira vez sem erros.

**Critérios de aceitação:**
- Cada tela tem ao menos 3 ações documentadas com passos numerados
- Telas "em desenvolvimento" são marcadas claramente
- Instrução de atalhos de teclado disponíveis

---

## Telas Cobertas

| Tela | Rota | Descrição |
|------|------|-----------|
| Painel | `/dashboard` | Visão geral de métricas e acesso rápido |
| Pigmentos | `/pigments` | Cadastro e gestão de pigmentos |
| Cores Definidas | `/colors` | Catálogo de cores do leque |
| Fórmulas | `/formulas` | Fórmulas de mistura tintométrica |
| Misturas | `/mixtures` | Execução e acompanhamento de misturas |
| Controle de Estoque | `/inventory` | Estoque de pigmentos por loja |
| Etiquetas | `/labels` | Geração e impressão de etiquetas |

---

## Restrições (fora do escopo)

- Não é um sistema de tour guiado passo-a-passo
- Não envolve backend ou persistência
- Não inclui busca textual nas instruções (v1)

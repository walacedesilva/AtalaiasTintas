# Feature 12: Entrada de NF-e por Número / Chave de Acesso

**Status:** Specify  
**Priority:** P1 (MVP)  
**Estimated Complexity:** Medium  
**Business Impact:** High — operadores bloqueados quando não possuem o arquivo XML

---

## Contexto & Necessidade de Negócio

A loja atualmente só consegue registrar entrada de mercadorias importando um arquivo XML da NF-e do fornecedor. Na prática, existem situações frequentes onde o XML não está disponível no momento do recebimento:

- Fornecedor entrega mercadoria com NF-e impressa (DANFE) sem enviar o XML por e-mail
- XML ainda não foi transmitido pelo fornecedor à SEFAZ
- Arquivo XML foi perdido ou está corrompido
- Loja precisa registrar uma entrada retroativa a partir do número que está no sistema do fornecedor

Nesses casos, o operador não tem como registrar a entrada no sistema, causando:
- Divergência entre estoque físico e sistema
- Impossibilidade de rastrear custo de compra
- Necessidade de workaround manual (planilhas, anotações)

---

## User Stories

### US-1: Entrada manual por número de NF-e
**Como** operador de estoque  
**Eu quero** registrar uma entrada de mercadoria informando o número da NF-e, a série e o CNPJ do fornecedor, sem precisar do arquivo XML  
**Para que** eu possa manter o estoque atualizado mesmo quando o XML não está disponível

**Critérios de Aceitação:**
- Posso informar: número da NF-e, série, data de emissão, CNPJ/nome do fornecedor, valor total
- Posso adicionar itens manualmente (código, descrição, quantidade, unidade, valor unitário)
- O sistema valida campos obrigatórios antes de salvar
- A entrada fica com status "PENDENTE" aguardando confirmação
- A entrada pode ser confirmada para dar baixa no estoque (mesmo sem XML)

### US-2: Busca de NF-e por chave de acesso (44 dígitos)
**Como** operador de estoque  
**Eu quero** informar a chave de acesso de 44 dígitos da NF-e que consta no DANFE  
**Para que** o sistema tente baixar automaticamente o XML da SEFAZ e pré-preencha todos os campos da entrada

**Critérios de Aceitação:**
- Campo de chave de acesso com máscara/validação de 44 dígitos numéricos
- Sistema tenta consultar e baixar o XML via SEFAZ (DistribuiçãoDFe)
- Se SEFAZ retornar o XML: campos pré-preenchidos automaticamente (igual ao fluxo de upload XML)
- Se SEFAZ indisponível ou chave não encontrada: sistema informa o erro e permite entrada manual (US-1)
- Idempotência: se a chave já foi importada anteriormente, sistema exibe a entrada existente

### US-3: Localização de entrada por número no administrativo
**Como** gerente de estoque  
**Eu quero** buscar entradas já registradas pelo número da NF-e ou chave de acesso  
**Para que** eu possa auditar e confirmar entradas específicas rapidamente

**Critérios de Aceitação:**
- Filtro por número NF-e, chave de acesso e CNPJ do fornecedor na listagem de entradas
- Resultado exibe status, fornecedor, data e valor da entrada
- Posso acessar o detalhe e confirmar a entrada a partir do resultado da busca

### US-4: Indicação de origem da entrada
**Como** contador  
**Eu quero** saber se uma entrada foi registrada via XML importado ou via número manual  
**Para que** eu saiba quais entradas possuem documento fiscal completo e quais precisam de regularização posterior

**Critérios de Aceitação:**
- Listagem exibe badge diferenciando "XML Importado" vs "Entrada Manual"
- Relatório/exportação inclui a coluna de origem da entrada

---

## Requisitos Funcionais

### RF-01: Formulário de Entrada Manual
- Campo obrigatório: número NF-e (até 9 dígitos), série (até 3 dígitos), CNPJ emitente (14 dígitos, validado)
- Campo obrigatório: data de emissão
- Campo opcional: nome do fornecedor (se não informado, exibir CNPJ)
- Campo opcional: valor total da NF-e
- Tabela de itens: adicionar/editar/remover itens inline
  - Cada item: código, descrição (obrigatório), NCM (opcional), CFOP (opcional), quantidade, unidade, valor unitário

### RF-02: Consulta por Chave de Acesso (44 dígitos)
- Campo de entrada: 44 dígitos numéricos com validação de formato
- Botão "Consultar SEFAZ" — chama `DistribuiçãoDFe` ou endpoint de consulta equivalente
- Fallback gracioso: se SEFAZ indisponível, exibe mensagem e permite continuar com entrada manual

### RF-03: Idempotência
- Sistema verifica `chave_acesso_nfe` antes de criar nova entrada
- Se já existe: exibe entrada existente e não cria duplicata

### RF-04: Rastreabilidade de Origem
- Campo `origem_entrada` no model: `'XML_UPLOAD'` | `'MANUAL'` | `'SEFAZ_DOWNLOAD'`
- Listagem exibe badge de origem
- Filtragem por origem na listagem administrativa

### RF-05: Confirmação e Baixa de Estoque
- Entrada manual pode ser confirmada pelo mesmo fluxo de vinculação de itens e confirmação já existente
- Operador vincula cada item ao `ProdutoVariacao` correspondente antes de confirmar
- Confirmação atualiza estoque (idêntico ao fluxo de entrada via XML)

### RF-06: Validação de CNPJ
- CNPJ do fornecedor deve ser validado com algoritmo módulo 11
- Campo deve formatar automaticamente (00.000.000/0000-00)

---

## Requisitos Não-Funcionais

- Interface consistente com o padrão visual existente da `EntradasTab` em `EstoquePage.tsx`
- Formulário de entrada manual deve ser acessível (labels, keyboard navigation, ARIA)
- Consulta SEFAZ deve ter timeout de 10 segundos com feedback visual de loading
- Entrada manual com até 100 itens deve renderizar sem degradação perceptível
- Auditoria: toda entrada deve registrar o usuário responsável

---

## Fora do Escopo

- Manifestação de NF-e destinatária (confirmação junto à SEFAZ de que recebeu a mercadoria) — escopo futuro
- Integração automática com e-mail do fornecedor para captura de XML — escopo futuro
- Devolução/Retorno de NF-e — escopo futuro
- Entrada de NF-e de serviço (NFS-e) — fora do escopo do sistema de estoque de tintas

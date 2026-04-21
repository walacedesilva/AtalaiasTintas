# Spec: Página de Ajuda e Onboarding para Novos Usuários

**Feature ID**: 13  
**Status**: specified

---

## Visão Geral

Novos usuários do sistema Atalaia Tintas não sabem por onde começar nem como usar os módulos principais. O botão "Ajuda" existe mas não oferece um guia prático e visual do sistema como um todo.

## Problema

- Novos funcionários precisam de treinamento manual
- O HelpDrawer atual só ajuda por tela, sem visão geral do sistema
- Não há um ponto de entrada único que explique o fluxo completo de trabalho

## Solução

Uma página dedicada de onboarding acessível pelo botão "Ajuda" no header, que guia o usuário por todas as áreas do sistema de forma visual, passo a passo e prática.

## User Stories

**US1** — Como novo usuário, quero ver uma visão geral do sistema para entender onde cada função está.  
**US2** — Como novo usuário, quero ver o passo a passo de cada módulo para aprender rapidamente.  
**US3** — Como usuário, quero navegar entre os módulos no guia e ir direto para a tela correspondente.  
**US4** — Como gestor, quero um guia que possa ser acessado a qualquer momento para consulta.

## Requisitos Funcionais

1. Página acessível via rota `/help`
2. Apresentar todos os módulos do sistema: Dashboard, Estoque, Tintometria, Etiquetas, Fiscal, Relatórios, Configurações
3. Cada módulo deve ter: título, descrição, lista de ações práticas e dicas
4. Navegação linear (anterior / próximo) e por índice lateral
5. Botão "Ir para [tela]" em cada módulo para navegação direta
6. Botão "Ajuda" no header navega para `/help`
7. Design visual com ícones, numeração de passos e progresso

## Requisitos Não-Funcionais

- Responsivo (desktop e mobile)
- Acessível (aria-labels, navegação por teclado)
- Carregamento instantâneo (sem dependência de API)

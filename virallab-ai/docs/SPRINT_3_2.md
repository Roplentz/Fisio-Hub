# Sprint 3.2 — Estado, caminhos e navegação

Esta entrega extrai do runtime monolítico três responsabilidades estáveis:

- caminhos e criação dos diretórios do workspace;
- inicialização e reinicialização do estado da sessão;
- catálogo, sincronização e progresso da navegação.

O runtime permanece responsável pelas telas, mas usa adaptadores finos sobre os módulos em `src/virallab/studio`.

Critérios de aprovação:

- nenhuma duplicação das regras extraídas no runtime;
- navegação programática sem escrita tardia na chave do widget;
- testes unitários sem inicialização do Streamlit;
- CI, Guardian e Delivery Safety verdes;
- PR em rascunho, sem alteração da `main`.

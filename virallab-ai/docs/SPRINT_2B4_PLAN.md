# Sprint 2B.4 — Bootstrap explícito

Objetivo: consolidar o Studio em uma função `main()` explícita, remover o módulo obsoleto `studio_source_patch` e eliminar testes que ainda validam a antiga injeção de código-fonte.

Critérios de segurança:

- nenhuma alteração na branch `main`;
- PR em rascunho;
- `app.py` chama `app_v3.main()` explicitamente;
- importar `app_v3` não deve renderizar a interface automaticamente;
- CI, Guardian e Delivery Safety obrigatoriamente verdes;
- validação em staging antes de promoção.

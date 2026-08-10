# FisioHub Automation Lab

Este diretório contém as automações experimentais do FisioHub.

## Primeira automação

`FH-AUTO-001 - Auditoria Inteligente do Google Drive`

Arquivos:

```text
automation/
├── README.md
├── FH-AUTO-001-drive-audit-blueprint.md
└── workflows/
    └── FH-AUTO-001-drive-audit-demo.json
```

## Como importar no n8n

1. Inicie o ambiente com `scripts/start-n8n.ps1`.
2. Abra `http://localhost:5678`.
3. Conclua a criação do usuário local do n8n.
4. No menu de workflows, escolha a opção de importar arquivo.
5. Selecione `FH-AUTO-001-drive-audit-demo.json`.
6. Abra o workflow.
7. Clique em `Executar workflow`.
8. Abra o resultado do nó `Classificador CKO`.

## Resultado esperado

O fluxo usa um documento fictício chamado `Redação` cujo conteúdo indica ser a Constituição do FisioHub.

A saída deverá sinalizar:

- domínio `00_CONSTITUTION`;
- tipo `Constitution`;
- título genérico;
- risco de duplicidade médio;
- necessidade de aprovação humana;
- execução em `dry_run`.

## Segurança

Esta demonstração:

- não usa credenciais;
- não acessa seu Google Drive;
- não envia dados para modelos externos;
- não altera arquivos;
- não exclui nada;
- não escreve em banco.

## Próxima fase

Após o teste local:

1. criar credencial Google OAuth no n8n;
2. restringir a uma pasta piloto;
3. começar com leitura de metadados;
4. registrar resultados em uma planilha de auditoria;
5. adicionar o CKO com IA;
6. manter aprovação humana para mudanças.

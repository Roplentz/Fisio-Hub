# FH-AUTO-001 — Auditoria Inteligente do Google Drive

**Versão:** 0.1  
**Status:** Draft técnico  
**Owner:** Chief Knowledge Officer (CKO)  
**Modo inicial:** Leitura e recomendação  
**Escrita automática no Drive:** Desabilitada

## 1. Objetivo

Criar a primeira automação do FisioHub para identificar novos arquivos, documentos sem identificação, títulos genéricos, possíveis duplicidades e ativos que precisam ser vinculados ao Documentation OS.

## 2. Princípio de segurança

A primeira versão não move, renomeia, exclui, arquiva ou declara documentos como oficiais.

Ela apenas:

1. recebe dados de um arquivo;
2. normaliza metadados;
3. classifica o ativo;
4. identifica sinais de duplicidade;
5. gera recomendação do CKO;
6. registra uma saída de auditoria.

## 3. Fluxo

```text
Manual Trigger
    ↓
Configuração de auditoria
    ↓
Entrada de arquivo de demonstração
    ↓
Normalização
    ↓
Classificação CKO
    ↓
Relatório estruturado
```

Na fase seguinte:

```text
Google Drive Trigger
    ↓
Google Drive Metadata
    ↓
Extração de texto
    ↓
Busca no Índice Mestre
    ↓
CKO / modelo de IA
    ↓
Google Sheets ou Supabase
    ↓
Aprovação humana
```

## 4. Dados mínimos de entrada

```json
{
  "file_id": "drive-file-id",
  "name": "Redação",
  "mime_type": "application/vnd.google-apps.document",
  "modified_time": "2026-07-10T12:00:00Z",
  "content_preview": "CONSTITUIÇÃO DO FISIOHUB..."
}
```

## 5. Saída esperada

```json
{
  "suggested_id": "FH-CONST-001",
  "domain": "00_CONSTITUTION",
  "document_type": "Constitution",
  "status_recommendation": "Under Review",
  "generic_name": true,
  "duplicate_risk": "medium",
  "requires_human_approval": true,
  "recommended_action": "Renomear e comparar com a Constituição vigente antes de promover a oficial"
}
```

## 6. Regras iniciais do classificador

- Título `Redação`, `Documento`, `Sem título` ou semelhante: sinalizar como nome genérico.
- Conteúdo com `CONSTITUIÇÃO`, `MISSÃO`, `VALORES`: classificar em `00_CONSTITUTION`.
- Conteúdo com `MASTER PLAN`, `ROADMAP`, `OKR`, `KPI`: classificar em `01_MASTER_PLAN`.
- Conteúdo com `GOVERNANÇA`, `EXECUTIVE OS`, `CONSELHO`: classificar em `02_GOVERNANCE`.
- Conteúdo com `ARQUITETURA`, `API`, `BACKEND`, `FRONTEND`, `LANGGRAPH`: classificar em `03_ARCHITECTURE`.
- Conteúdo com `CLINICAL AI KERNEL`, `DECISION ENGINE`, `DIGITAL TWIN`: classificar em `04_CLINICAL_AI_KERNEL`.
- Conteúdo com `ONTOLOGY`, `KNOWLEDGE GRAPH`, `KNOWLEDGE GENOME`: classificar em `05_KNOWLEDGE_GRAPH`.
- Conteúdo com `PILATESVISION`, `ORTHOVISION`, `NEUROVISION`: classificar em `06_PRODUCTS`.

## 7. Decisões humanas obrigatórias

Exigem aprovação do CEO/CKO humano:

- declarar documento como oficial;
- substituir versão vigente;
- mover para arquivo;
- renomear em massa;
- excluir duplicatas;
- modificar documentos constitucionais;
- publicar conteúdo clínico como norma.

## 8. Critérios de aceite da fase 0.1

- o workflow importa no n8n;
- roda manualmente;
- produz JSON válido;
- identifica título genérico;
- classifica um documento de demonstração;
- não solicita credenciais;
- não escreve em serviços externos.

## 9. Próxima evolução

1. Conectar credencial Google Drive somente leitura.
2. Escolher uma pasta piloto.
3. Ler os arquivos modificados nos últimos sete dias.
4. Registrar resultados em uma planilha de auditoria.
5. Adicionar modelo de IA para análise semântica.
6. Criar gate de aprovação humana.

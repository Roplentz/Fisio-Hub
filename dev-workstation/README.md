# FisioHub Developer Workstation

Ambiente gratuito e isolado para desenvolvimento do FisioHub, PilatesVision, automações e n8n.

## Objetivo

Padronizar uma estação Windows com:

- Git
- GitHub Desktop ou Git CLI
- VS Code
- Python 3.11+
- Node.js LTS
- Docker Desktop
- n8n Community Edition em container
- ambiente preparado para Supabase CLI e FastAPI

## Princípios

1. Não instalar o n8n globalmente.
2. Rodar o n8n em Docker para evitar conflitos.
3. Persistir dados do n8n em volume local.
4. Não versionar senhas ou chaves.
5. Usar `.env` local baseado em `.env.example`.
6. Manter o ambiente de automação separado dos produtos clínicos.

## Estrutura

```text
dev-workstation/
├── README.md
├── .env.example
├── docker-compose.yml
└── scripts/
    ├── check-workstation.ps1
    ├── start-n8n.ps1
    └── stop-n8n.ps1
```

## Etapa 1 — instalar pré-requisitos

No computador Windows, instalar:

1. Git
2. VS Code
3. Python 3.11 ou superior
4. Node.js LTS
5. Docker Desktop

Depois reiniciar o computador e abrir o Docker Desktop.

## Etapa 2 — verificar o computador

Abra o PowerShell na raiz do repositório e execute:

```powershell
Set-ExecutionPolicy -Scope Process Bypass
.\dev-workstation\scripts\check-workstation.ps1
```

O script mostra o que já está instalado e o que falta.

## Etapa 3 — preparar variáveis

Copie:

```text
dev-workstation/.env.example
```

para:

```text
dev-workstation/.env
```

Troque a senha inicial do n8n antes de iniciar.

## Etapa 4 — iniciar o n8n

```powershell
.\dev-workstation\scripts\start-n8n.ps1
```

Depois abra:

```text
http://localhost:5678
```

## Etapa 5 — parar o n8n

```powershell
.\dev-workstation\scripts\stop-n8n.ps1
```

## Segurança

- O serviço fica disponível apenas em `localhost`.
- Não exponha a porta 5678 na internet.
- Não coloque credenciais reais no GitHub.
- Faça backup periódico da pasta/volume do n8n.
- A primeira automação deve apenas auditar e recomendar; não deve mover ou apagar arquivos automaticamente.

## Primeiro laboratório

Workflow inicial:

```text
Google Drive
→ detectar arquivo novo
→ extrair metadados
→ consultar CKO
→ classificar
→ registrar em índice provisório
→ solicitar aprovação humana
```

Nenhuma ação destrutiva será automatizada na primeira fase.

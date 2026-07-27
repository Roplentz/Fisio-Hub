# ViralLab — Auditoria Técnica Sprint 1

Data: 2026-07-26
Escopo: arquitetura, Python, Streamlit, IA/TTS, renderização, testes e deploy.
Status da produção durante a auditoria: rollback para `main` no commit `0cfbcb92dd6ccc606e8e12f99579904a43e9ddb4`.

## Resumo executivo

O ViralLab possui um núcleo funcional e vários módulos úteis, mas ainda não está pronto para evolução segura em produção. O principal risco não é uma função isolada: é o acoplamento entre inicialização do Streamlit, patches em runtime, estado de sessão, filesystem compartilhado e uma esteira de CI que não valida a aplicação como servidor web.

### Nota por domínio

| Domínio | Nota | Diagnóstico |
|---|---:|---|
| Arquitetura | 2/5 | Bons módulos de domínio, porém entrypoint e UI continuam acoplados por execução dinâmica e patches. |
| Código Python | 3/5 | Código legível em diversos módulos, mas há arquivos monolíticos, exceções genéricas e efeitos colaterais na importação. |
| Streamlit/UX técnica | 2/5 | Fluxo visual claro, porém estado lógico e estado de widget estão misturados; inicialização é frágil. |
| IA e providers | 3/5 | Estratégia multi-provider é promissora, mas dependências e falhas dos modelos não estão isoladas suficientemente. |
| Voz/TTS | 2/5 | Kokoro funciona em algumas combinações, mas o ambiente real revelou incompatibilidade de dispositivo e ausência de teste integrado. |
| Render/FFmpeg | 3/5 | Existe render smoke e estrutura de plano, porém segurança de caminhos e escaping precisam de endurecimento incremental. |
| Testes | 2/5 | Há boa quantidade de testes unitários, mas falta teste do servidor Streamlit, browser smoke e matriz de dependências. |
| CI/CD | 1/5 | Dois workflows parcialmente redundantes; nenhum bloqueia publicação por teste HTTP/E2E; rollback não é automatizado. |
| Segurança/isolamento | 2/5 | Workspace global e arquivos persistidos no diretório do app podem misturar sessões e dados. |
| Operabilidade | 1/5 | Logs não estruturados, sem healthcheck, sem versão visível, sem release gate e sem staging formal. |

**Avaliação geral: 2,1/5 — protótipo funcional com dívida estrutural elevada.**

## Achados críticos — P0

### P0-1 — Entry point executa código dinamicamente

`app.py` lê `app_v3.py`, altera seu código-fonte e executa o resultado com `exec(compile(...))`. Antes disso instala patches de qualidade, navegação e voz. Isso impede análise confiável do ciclo de inicialização, dificulta traceback e permite divergência entre o arquivo testado e o arquivo efetivamente executado.

Impacto: indisponibilidade total do app, regressões difíceis de reproduzir e elevada complexidade de manutenção.

Recomendação: não remover tudo de uma vez em produção. Criar primeiro um `app_staging.py` estável, com importação normal, e migrar uma preocupação por PR.

### P0-2 — CI não testa o Streamlit como aplicação web

O CI compila apenas `app.py`, executa pytest e renderiza um vídeo via CLI. O Guardian compila arquivos e faz import smoke de módulos internos. Nenhum workflow inicia `streamlit run`, aguarda healthcheck, acessa a página via HTTP ou valida que a sessão abre sem exceção.

Impacto: todos os checks podem ficar verdes enquanto a aplicação pública entrega tela preta ou falha durante bootstrap.

Recomendação: criar teste de servidor com processo isolado, timeout, `/_stcore/health` e coleta de logs. Depois adicionar Playwright para validar título e um elemento essencial.

### P0-3 — Não há ambiente de staging real

Mudanças estruturais foram validadas em branch e mescladas diretamente para a branch usada pelo Streamlit público.

Impacto: produção tornou-se o primeiro ambiente de integração real.

Recomendação: criar app separado no Streamlit Cloud apontando para branch `staging`, com secrets próprios e dados descartáveis.

### P0-4 — Workspace compartilhado entre sessões

`app_v3.py` cria `workspace/analysis`, `workspace/projects` e `workspace/learning` sob o diretório do aplicativo e usa esses caminhos globalmente. O identificador do projeto reduz colisões, mas ativos globais, aprendizado e referências de avatar continuam compartilhados pelo processo.

Impacto: vazamento ou mistura de dados entre usuários/sessões, corrida de escrita e perda de arquivos em reinícios do Streamlit Cloud.

Recomendação: introduzir `WorkspaceService`, escopo por usuário/sessão e backend persistente explícito. Não tratar filesystem efêmero do Streamlit como banco de dados.

## Achados altos — P1

### P1-1 — Estado lógico e chave de widget misturados

`studio_step` é simultaneamente rota lógica e chave do `selectbox`. Botões modificam diretamente esse valor. O projeto criou um patch específico para contornar o comportamento do Streamlit.

Recomendação: manter duas chaves (`current_step` e `step_selector`) e uma função de transição testável. Fazer a troca primeiro em staging.

### P1-2 — `app_v3.py` é um módulo monolítico com efeitos na importação

O arquivo configura página, injeta CSS, cria diretórios, lê dados, cria widgets e executa roteamento no nível do módulo. UI, estado, persistência e orquestração estão no mesmo arquivo.

Recomendação: extrair gradualmente `ui/state.py`, `ui/navigation.py`, `services/project_service.py` e páginas/steps. O entrypoint deve apenas configurar e chamar `main()`.

### P1-3 — Dependências contraditórias

`pyproject.toml` declara `dependencies = []`, enquanto `requirements.txt` instala todo o conjunto pesado. Assim, `pip install -e .` não instala nem Streamlit, e os ambientes podem receber conjuntos diferentes.

Recomendação: definir dependências mínimas de runtime no projeto; manter extras por capacidade; gerar lock/constraints para produção; remover duplicidade manual entre requirements e pyproject.

### P1-4 — Instalação indiscriminada de dependências pesadas

O CI principal instala `.[all]`, incluindo Whisper, OpenCV, Kokoro, Google APIs e outras integrações para testar alterações que muitas vezes não usam esses componentes.

Impacto: CI lento, instável e com maior superfície de incompatibilidade.

Recomendação: matriz `core`, `voice`, `visual` e `full-integration`, com o job core obrigatório e os demais programados ou condicionais.

### P1-5 — TTS não possui teste integrado do provider real

Os testes do VoiceEngine usam providers falsos. O erro real do Kokoro relacionado ao dispositivo não foi detectado.

Recomendação: teste unitário com dublê da API exata do Kokoro, teste de compatibilidade de versão e teste integrado agendado com modelo/cache controlado. Exibir fallback para upload/gravação quando TTS estiver indisponível.

### P1-6 — Exceções amplas escondem bugs

A geração de estratégia captura `Exception` e transforma qualquer falha em mensagem genérica. Isso mistura erro de usuário, indisponibilidade do provider e bug de programação.

Recomendação: taxonomia de erros (`ConfigurationError`, `ProviderError`, `ValidationError`, `InfrastructureError`) e logging do traceback apenas no servidor.

## Achados médios — P2

- CSS amplo e dependente de seletores internos do Streamlit pode quebrar após atualização.
- Não há versão/commit visível na interface para confirmar qual build está publicado.
- Não há healthcheck de dependências externas: FFmpeg, FFprobe, Tesseract, modelos e secrets.
- O upload é gravado diretamente sem política central de tamanho, quota e limpeza.
- O diretório contém artefatos `__pycache__` versionados, aumentando ruído e commits automáticos.
- Os workflows `ViralLab CI` e `ViralLab Guardian` duplicam instalação, compilação e pytest.
- O Guardian executa apenas permissões de leitura, mas o histórico mostra commits automáticos de formatação fora do fluxo normal; essa automação precisa ser auditada e separada de checks obrigatórios.
- Não existe política explícita de retenção/remoção de projetos e mídias.
- Não há observabilidade estruturada por `project_id`, provider, etapa, duração e resultado.

## Arquitetura atual — síntese

Fluxo principal:

`Streamlit Cloud -> app.py -> patches runtime -> leitura/alteração de app_v3.py -> exec -> UI monolítica -> services/providers -> filesystem local -> FFmpeg/modelos externos`

Pontos positivos:

- domínio possui módulos separados para assets, geração, aprendizagem, providers, voz e renderização;
- existe CLI funcional e render smoke;
- modelos e pacotes exportáveis já oferecem base para futura API;
- há testes unitários em várias áreas.

Gargalo central:

A arquitetura modular do domínio é anulada no topo por um bootstrap dinâmico e uma UI com efeitos colaterais globais.

## Arquitetura alvo recomendada

```text
virallab/
  domain/
  application/
  infrastructure/
    ai/
    tts/
    media/
    persistence/
  interfaces/
    cli/
    streamlit/
  observability/
```

O Streamlit deve depender de casos de uso; casos de uso não devem importar Streamlit.

## Estratégia de testes alvo

1. Unitários: domínio e validação sem rede/modelos.
2. Contract tests: providers Gemini, Ollama, Kokoro e FFmpeg usando dublês fiéis.
3. Integração: filesystem temporário, FFmpeg e planos reais.
4. Server smoke: iniciar Streamlit, verificar health endpoint e página.
5. E2E staging: Playwright executa um fluxo curto sem provider pago.
6. Canary manual: aprovação explícita antes de promover staging para produção.

## Backlog priorizado

### Sprint 2A — Segurança de entrega

1. Criar branch e app `staging`.
2. Adicionar smoke real do Streamlit ao CI.
3. Exibir commit/version na UI.
4. Documentar rollback e release checklist.
5. Bloquear merge sem checks obrigatórios.

### Sprint 2B — Bootstrap estável

1. Criar entrypoint alternativo sem `exec`, inicialmente apenas em staging.
2. Separar navegação lógica do widget.
3. Criar `main()` explícito.
4. Manter feature flag para retorno imediato ao bootstrap legado.

### Sprint 2C — Dependências e voz

1. Consolidar `pyproject.toml` e requirements.
2. Fixar constraints de produção.
3. Encapsular Kokoro e implementar fallback controlado.
4. Adicionar matriz de testes por extra.

### Sprint 2D — Isolamento e persistência

1. Implementar `WorkspaceService`.
2. Diretórios temporários por sessão/projeto.
3. Quotas e limpeza.
4. Persistência explícita para projetos e aprendizado.

## Critérios para considerar produção segura

- Staging publicado e validado.
- `streamlit run` testado no CI com healthcheck.
- E2E mínimo aprovado.
- Nenhum `exec` ou alteração de source code no entrypoint novo.
- Rollback documentado e testado.
- Workspace isolado.
- Dependências reproduzíveis.
- Erros externos não derrubam a aplicação inteira.
- Commit/version visível na interface.

## Decisão recomendada

Não iniciar uma grande refatoração. A próxima entrega deve ser exclusivamente a **Sprint 2A — Segurança de entrega**. Somente depois de staging, healthcheck e rollback comprovados devemos retomar mudanças de arquitetura.

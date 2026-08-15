# FisioHub Venture Copilot v1.0

## Visão

O FisioHub Venture Copilot é o agente de inovação do FisioHub. Sua função é conduzir estudantes, profissionais e equipes pela construção estruturada de projetos de inovação, desde a identificação do problema até a validação de uma solução e preparação para implementação ou lançamento.

Princípio: **PENSAR → INVESTIGAR → DECIDIR → CONSTRUIR → TESTAR → APRENDER**.

## Proposta de valor

> Um copiloto de inovação que acompanha o projeto do problema à validação, questionando hipóteses, avaliando evidências e indicando o próximo melhor passo.

## Arquitetura multiagente

### Venture Orchestrator
Responsável por interpretar o estado do projeto, escolher o agente especialista, verificar gates, atualizar o Project State e definir a próxima ação.

### Agentes
- Discovery Agent — problema, JTBD, hipóteses, evidências e experimentos.
- Opportunity Agent — alternativas, valor percebido × simplicidade e seleção da solução.
- Product Architect — jornada, funcionalidades, MVP e PRD.
- Build Strategist — arquitetura técnica e implementação.
- Product Experience Agent — UX, UI, acessibilidade e percepção de valor.
- Validation & Launch Agent — QA, monetização, métricas e lançamento.
- Critic Agent — agente transversal que procura fragilidades, contradições e premissas perigosas.

## Project State

```json
{
  "project_id": "",
  "project_name": "",
  "user_id": "",
  "current_phase": 0,
  "status": "active",
  "problem": {
    "statement": "",
    "context": "",
    "consequences": "",
    "frequency": "",
    "severity": ""
  },
  "audience": {
    "primary": "",
    "segments": []
  },
  "jtbd": "",
  "evidence": [],
  "assumptions": [],
  "unknowns": [],
  "risks": [],
  "opportunity_score": 0,
  "value_proposition": "",
  "solutions": [],
  "selected_solution": "",
  "mvp": {},
  "business_model": {},
  "experiments": [],
  "metrics": [],
  "decisions": [],
  "current_gate": "",
  "next_action": "",
  "updated_at": ""
}
```

## Rótulos de conhecimento
Toda informação importante deve ser classificada como FATO, EVIDÊNCIA, HIPÓTESE, INFERÊNCIA ou DESCONHECIDO.

## Jornada principal
1. Criar projeto.
2. Explicar ideia/problema em linguagem livre.
3. Discovery Agent extrai problema, público, contexto, hipóteses e riscos.
4. Gate 0: AVANÇAR / INVESTIGAR / PIVOTAR.
5. Registrar evidências e hipóteses.
6. Opportunity Agent gera até cinco alternativas.
7. Selecionar solução.
8. Product Architect define MVP e PRD.
9. Critic Agent audita o projeto.
10. Exportar projeto/PRD/PDF.

## Gates
- Gate 0 — Problem Gate
- Gate 1 — Opportunity Gate
- Gate 2 — Solution Gate
- Gate 3 — MVP Gate
- Gate 4 — Validation Gate

O usuário poderá avançar com gate incompleto, mas o sistema deverá registrar **AVANÇO COM RISCO**.

## Innovation Score
Score 0–100, com cinco dimensões de 20 pontos:
- Problema
- Evidência
- Valor
- Viabilidade
- Validação

O score é diagnóstico, não uma medida científica validada.

## Evidence Engine
Cada evidência deverá registrar tipo, fonte, data, descrição, hipótese relacionada e força da evidência (fraca/moderada/forte).

## Hypothesis Board
Cada hipótese terá impacto se estiver errada × incerteza, produzindo prioridade Critical/High/Medium/Low.

## Experiment Builder
Transforma hipótese em experimento com público, método, métrica, sinal positivo e decisão GO/PIVOT/STOP.

## Solution Lab
Gerar alternativas tecnológicas e não tecnológicas. Evitar viés de aplicativo como solução automática.

## MVP Builder
Classificar funcionalidades em MUST / SHOULD / LATER.
Pergunta obrigatória: “Se retirarmos isso, o usuário ainda recebe o valor principal?” Se sim, remover do MVP.

## Critic Mode
Botão: **DESAFIAR MEU PROJETO**.
Saída: maior fragilidade, hipótese mais perigosa, contradições, complexidade desnecessária e o que testar amanhã.

## Professor Mode
Professor visualiza evolução, decisões, evidências, gates, scores e intervenções da IA. Registrar a origem das decisões: aluno, IA sugeriu/aluno aceitou, IA sugeriu/aluno rejeitou ou professor.

## Stack sugerida
- Front-end: manter o stack atual do FisioHub.
- Backend: Supabase.
- Banco: PostgreSQL via Supabase.
- Auth: Supabase Auth.
- IA: camada AIProvider desacoplada de um único modelo.

## Saída estruturada dos agentes

```json
{
  "analysis": "...",
  "facts": [],
  "evidence": [],
  "assumptions": [],
  "risks": [],
  "recommendation": "INVESTIGATE",
  "next_action": "...",
  "project_updates": {}
}
```

Regra: a IA não altera o Project State diretamente. Fluxo: **IA → resposta estruturada → validação → banco**.

## Banco mínimo
- users
- projects
- project_states
- project_versions
- hypotheses
- evidence
- experiments
- decisions
- agent_runs
- scores
- feedback
- exports

## MVP v1 — MUST
- login
- criar projeto
- Project State
- jornada visual
- Discovery Agent
- Opportunity Agent
- Product Architect
- Critic Agent
- hipóteses
- evidências
- gates
- Innovation Score
- histórico de decisões
- geração de projeto
- exportação PDF

## SHOULD
- dashboard professor
- experiment builder
- feedback professor
- versionamento
- pitch
- PRD automático

## LATER
- construção automática do app
- GitHub/Lovable/Claude Code/Figma
- marketplace
- editais
- aceleradoras

## Plano de sprints

### Sprint 1 — Venture Core
Project State, workspace, timeline, painel Copilot, Orchestrator, Discovery Agent, saída JSON e persistência Supabase.

### Sprint 2 — Discovery Agent
Conversa, extração estruturada, fatos, hipóteses, JTBD, riscos e Problem Gate.

### Sprint 3 — Evidence Engine
Adicionar evidência, relacionar hipótese, força da evidência e Innovation Score.

### Sprint 4 — Opportunity Agent
Alternativas, matriz, ranking, seleção e Opportunity Gate.

### Sprint 5 — Product Architect
Proposta de valor, jornada, MUST/SHOULD/LATER, MVP e PRD.

### Sprint 6 — Critic Agent
Auditoria, contradições, riscos e hipótese crítica.

### Sprint 7 — Exportação
Project PDF, PRD e One Page.

### Sprint 8 — Professor Mode
Visão da turma, scores, riscos, progresso, feedback e analytics pedagógico.

## North Star Metric
**Projetos que chegam a um experimento de validação com hipótese explicitamente definida.**

## Diferencial estratégico
O FisioHub não deve ser apenas “IA que cria projeto”. O diferencial é **IA que ensina e registra como um projeto de inovação é pensado, testado e construído**.

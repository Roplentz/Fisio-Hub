# Sprint 0 — Fundação e Validação Manual

## Objetivo
Transformar a ideia do EXECUTA AI em uma especificação testável antes de programar o MVP.

## Duração
3–5 dias.

## Entregáveis
1. Identidade e promessa.
2. System Prompt v0.1.
3. Máquina de estados.
4. Modelo de memória.
5. Taxonomia inicial de barreiras.
6. Teste com 30 cenários simulados e, em seguida, 30 casos reais com usuários.
7. Métricas de baseline.
8. Lista de melhorias para Sprint 1.

## 0.1 Identidade
**Nome:** EXECUTA AI

**Tagline:** Pare de planejar começar. Comece.

**Promessa:** O agente que transforma tarefas adiadas em ações executáveis.

## 0.2 Máquina de estados
`NEW_TASK → DIAGNOSIS → MICRO_ACTION → READY → EXECUTING → CHECK_IN`

Sucesso: `CONTINUE / COMPLETE`

Falha: `RECOVERY → MICRO_ACTION`

## 0.3 Modelo de dados
Campos mínimos por tarefa:
- task
- task_type
- created_at
- resistance_before
- barrier
- micro_action
- estimated_minutes
- trigger
- started
- completed
- resistance_after
- result
- recovery_needed

Perfil mínimo:
- preferred_work_time
- average_resistance
- average_start_delay
- successful_triggers
- common_barriers
- best_session_duration

## 0.4 Taxonomia inicial
- falta de clareza
- tarefa grande demais
- medo de errar
- medo de julgamento
- tédio
- baixa energia
- excesso de opções
- perfeccionismo
- ansiedade antecipatória
- falta de prioridade
- ambiente inadequado
- interrupções
- ausência de prazo

## 0.5 Protocolo de teste
Para cada caso registrar:
- tarefa;
- resistência inicial 0–10;
- barreira inferida;
- número de mensagens até microação;
- microação proposta;
- duração;
- iniciou ou não;
- resistência final;
- concluiu ou não;
- necessidade de recovery;
- percepção de utilidade 0–10.

## 0.6 Critério de saída do Sprint 0
Avançar para Sprint 1 se:
- ≥70% dos casos chegarem a uma microação clara;
- ≥50% iniciarem a tarefa em teste real;
- resistência cair em média ≥2 pontos após início;
- não houver padrão recorrente de conversas longas sem ação.

## Nota metodológica
Os 30 cenários deste repositório são **simulados para QA**. Eles não substituem 30 usuários reais. O Sprint 0 só é validado comercial e comportamentalmente após teste humano.

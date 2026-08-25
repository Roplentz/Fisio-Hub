# EXECUTA AI — Protocolo Humano v0.2

## Objetivo
Testar se o agente consegue transformar uma tarefa realmente evitada em uma ação observável, segura e mensurável.

## Amostra inicial
10 participantes × 3 tarefas reais = 30 execuções.

## Inclusão
- adulto;
- possui ao menos uma tarefa real evitada;
- aceita registrar resistência 0–10;
- aceita fazer uma microação curta durante o teste.

## Exclusão operacional
Situações de crise, emergência médica, autoagressão, violência ou tarefas perigosas saem do fluxo experimental e seguem safety routing.

## Procedimento por tarefa
1. Registrar task_created_at.
2. Coletar descrição da tarefa.
3. Coletar resistência inicial 0–10.
4. Fazer safety check.
5. Coletar 1–2 falas diagnósticas.
6. Registrar fatos observados e hipótese de barreira.
7. Gerar microação.
8. Definir gatilho e duração.
9. Criar Attempt.
10. Registrar started_at quando o usuário iniciar.
11. Fazer check-in ao fim.
12. Coletar resistência pós.
13. Registrar outcome.
14. Se houver falha/interrupção, criar Recovery Attempt e registrar reentrada.

## Métricas primárias
- taxa de início;
- mediana de tempo até início;
- delta de resistência;
- taxa de conclusão da microação;
- taxa de reentrada após falha.

## Métricas secundárias
- mensagens até ação;
- score da interação;
- percepção de utilidade 0–10;
- vontade de usar novamente;
- preferência de duração de sprint.

## Critérios GO preliminares
- >= 70% chegam a uma microação válida;
- >= 50% iniciam a ação durante a sessão;
- delta mediano de resistência >= 2 pontos entre quem inicia;
- >= 70% das interações com score >= 80/100;
- zero falha crítica de safety;
- >= 60% dizem que usariam novamente.

## Critérios AJUSTAR
- boa taxa de microação, mas baixa taxa de início;
- início alto com pouca redução de resistência;
- recuperação fraca;
- excesso de mensagens antes da ação.

## Critérios PIVOT
- usuários valorizam diagnóstico, mas não execução;
- gatilhos/microações não geram comportamento observável mesmo após iterações;
- benefício percebido insuficiente para recorrência.

## Registro mínimo por caso
participant_id, task_id, task_text, resistance_before, evidence_utterance, barrier_hypothesis, confidence, micro_action, trigger, attempt_type, created_at, started_at, ended_at, outcome, resistance_after, reentry_needed, reentry_started_at, score, usefulness, notes.

## Regra ética operacional
Não atribuir diagnóstico psicológico. O teste avalia comportamento de execução e usabilidade do agente, não saúde mental.
# EXECUTA AI — Execution Engine v0.1

## Objetivo
Especificar o motor mínimo que transforma uma tarefa evitada em uma sequência mensurável de diagnóstico, início, execução e retomada.

## Entidades
### Task
- id
- user_id
- title
- created_at
- current_state
- status: open | completed | archived
- barrier_hypothesis
- barrier_confidence

### Attempt
- id
- task_id
- attempt_type: initial | continuation | recovery
- created_at
- started_at
- ended_at
- resistance_before
- resistance_after
- micro_action
- trigger
- target_minutes
- outcome: started | completed | abandoned | interrupted
- notes

### Reentry
- id
- task_id
- interruption_at
- reentry_started_at
- days_to_reentry
- reentry_action
- outcome

## Máquina de estados
NEW_TASK
→ SAFETY_CHECK

SAFE
→ DIAGNOSIS
→ MICRO_ACTION
→ READY
→ EXECUTING
→ CHECK_IN

CHECK_IN + sucesso
→ CONTINUE ou COMPLETE

CHECK_IN + falha/interrupção
→ RECOVERY_DIAGNOSIS
→ REENTRY_ACTION
→ READY

ROUTE_OUT
→ SAFE_RESPONSE
→ END

## Regras
1. Nunca ir para MICRO_ACTION sem SAFETY_CHECK.
2. Nunca afirmar barreira sem evidência do usuário.
3. Toda tentativa deve gerar um registro Attempt.
4. Toda retomada deve preservar a tentativa anterior.
5. Toda sessão deve permitir calcular resistência antes/depois.
6. Toda ação deve ter critério de sucesso observável.
7. Se a primeira ação falhar, a próxima deve ser menor ou mais específica.

## Pseudofluxo
```text
receive_task()
  -> safety_check()
     if route_out: safe_response(); end
  -> collect_resistance()
  -> diagnose_from_user_evidence()
  -> generate_micro_action()
  -> define_trigger()
  -> create_attempt()
  -> user_executes()
  -> check_in()
     if completed: close_task()
     if started_not_completed: continue_or_schedule_next()
     if failed: create_reentry_action()
```

## Métricas derivadas
- start_rate = attempts_started / attempts_created
- completion_rate = tasks_completed / tasks_created
- median_time_to_start = median(started_at - attempt.created_at)
- resistance_delta = resistance_before - resistance_after
- recovery_rate = successful_reentries / interrupted_tasks
- median_days_to_reentry
- average_attempts_per_task

## Eventos recomendados
- task_created
- safety_check_completed
- diagnosis_completed
- micro_action_created
- attempt_created
- attempt_started
- attempt_completed
- attempt_interrupted
- checkin_completed
- reentry_created
- reentry_started
- task_completed

## Critério mínimo de engine válido
Um fluxo é válido se for possível reconstruir a cronologia completa da tarefa sem sobrescrever tentativas anteriores.
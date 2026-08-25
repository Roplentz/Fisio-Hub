# EXECUTA AI — Sprint 0.5

## Objetivo
Transformar a fundação conceitual do Sprint 0 em um motor experimental testável, seguro e mensurável antes do MVP completo.

## Escopo
1. Corrigir os 4 achados P1 do review.
2. Evoluir o modelo de dados para múltiplas tentativas e retomadas com timestamps.
3. Criar System Prompt v0.2 com safety routing.
4. Criar Execution Engine v0.1 como especificação funcional.
5. Tornar os casos de QA reproduzíveis com evidência de diálogo.
6. Definir score de qualidade da interação.
7. Preparar protocolo para 10 pessoas × 3 tarefas reais.
8. Fazer auditoria open-source-first antes do Sprint 1.

## P1-1 — Registro temporal de tentativas
Novo modelo conceitual:

Task
- id
- user_id
- title
- created_at
- status
- barrier_hypothesis

Attempt[]
- attempt_id
- task_id
- attempt_type: initial | continuation | recovery
- started_at
- ended_at
- resistance_before
- resistance_after
- micro_action
- trigger
- outcome: started | completed | abandoned | interrupted
- notes

Reentry[]
- reentry_id
- task_id
- interruption_at
- reentry_started_at
- days_to_reentry
- reentry_action
- outcome

Com isso podemos medir:
- tempo entre intenção e início;
- duração da tentativa;
- taxa de início;
- taxa de conclusão;
- queda de resistência;
- tempo até reentrada;
- número de tentativas por tarefa.

## P1-2 — QA baseado em evidências
Nenhum caso de QA deve inferir barreira apenas a partir do título da tarefa. Cada caso deve conter:
- tarefa;
- resistência inicial;
- fala do usuário com sinais observáveis;
- barreira esperada ou conjunto aceitável;
- microação esperada;
- condição de sucesso;
- resposta proibida.

## P1-3 — Safety routing
Antes de qualquer execução, o agente deve classificar se a tarefa envolve:
- autoagressão ou suicídio;
- violência contra terceiros;
- atividade ilegal perigosa;
- emergência médica;
- outra tarefa incompatível com assistência de execução.

Nesses casos, o fluxo normal deve ser interrompido. O agente não cria microação para executar o comportamento perigoso. Deve responder com suporte seguro e, quando aplicável, orientar busca de ajuda apropriada.

## P1-4 — Open Source First
Antes do Sprint 1, auditar soluções e bibliotecas relevantes para:
- máquinas de estado;
- agentes conversacionais;
- memória;
- analytics/event tracking;
- scheduling;
- habit/task systems;
- safety/evaluation.

Avaliar para cada candidato:
- licença;
- maturidade;
- privacidade;
- comunidade;
- facilidade de integração;
- possibilidade de reutilização;
- risco de lock-in.

## Execution Engine v0.1
Fluxo:
NEW_TASK -> SAFETY_CHECK -> DIAGNOSIS -> MICRO_ACTION -> READY -> EXECUTING -> CHECK_IN

Se sucesso:
CHECK_IN -> CONTINUE | COMPLETE

Se falha:
CHECK_IN -> RECOVERY_DIAGNOSIS -> REENTRY_ACTION -> READY

## Score da interação
0-100 pontos:
- 20 pts: diagnóstico baseado em evidência;
- 20 pts: microação realmente pequena e observável;
- 15 pts: gatilho claro;
- 15 pts: tempo definido;
- 10 pts: mensuração antes/depois;
- 10 pts: segurança adequada;
- 10 pts: retomada correta quando necessária.

Gate de qualidade sugerido: >= 80/100.

## Critérios de saída do Sprint 0.5
GO se:
- todos os P1 corrigidos;
- prompt v0.2 aprovado;
- 30 casos simulados reproduzíveis;
- engine documentado;
- score aplicável;
- protocolo humano pronto;
- auditoria open-source-first concluída;
- primeiros testes internos sem falhas críticas de segurança.

Caso contrário: AJUSTAR antes do Sprint 1.
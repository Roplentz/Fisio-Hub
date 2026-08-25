# EXECUTA AI — Open Source First Audit

## Objetivo
Reduzir retrabalho no Sprint 1 avaliando o que pode ser reutilizado em vez de construído do zero.

## Categorias a auditar
1. State machines / workflow orchestration
2. Agent runtimes
3. Memory / persistence
4. Analytics / event tracking
5. Scheduling / reminders
6. Habit / task systems
7. Evaluation / safety

## Critérios por candidato
- licença permissiva?
- projeto ativo?
- comunidade saudável?
- documentação suficiente?
- integração simples com stack web moderna?
- permite self-hosting?
- privacidade adequada?
- baixo lock-in?
- encaixa no MVP ou é complexidade prematura?

## Shortlist inicial para investigação no Sprint 0.5
### State machine
- XState
Motivo: máquina de estados explícita, madura e útil para o fluxo NEW_TASK -> SAFETY_CHECK -> ...

### Agent runtime
- OpenAI Agents SDK
- LangGraph
Motivo: comparar simplicidade, estado, tool use, observabilidade e lock-in.

### Persistência
- Supabase/Postgres
Motivo: dados relacionais, auth, eventos, JSON e facilidade de MVP.

### Analytics
- PostHog
Motivo: eventos, funis, self-hosting/opções de privacidade.

### Scheduling
- cron/queue simples no MVP; evitar plataforma complexa antes de validar recorrência.

### Evaluation
- testes determinísticos de estado + suíte própria de QA antes de introduzir framework adicional.

## Decisão provisória
Para o Sprint 1, priorizar arquitetura simples:
- frontend web;
- backend leve;
- Postgres/Supabase;
- máquina de estados explícita;
- LLM apenas para interpretação e geração da microação;
- regras críticas de safety e transição fora do LLM quando possível.

## Pendência
Antes de selecionar bibliotecas finais, validar licença atual, manutenção e adequação técnica de cada candidato. Este documento registra shortlist e critérios; a decisão tecnológica final pertence ao gate do Sprint 1.
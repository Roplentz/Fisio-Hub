# EXECUTA AI — Sprint 1

## Objetivo
Entregar um MVP funcional e testável que transforme uma tarefa evitada em uma microação, conduza uma sessão curta, registre tentativa/resultado e aplique recuperação quando o usuário não inicia.

## Escopo entregue
- Intake de tarefa e resistência 0–10.
- Seleção de barreira inicial.
- Geração determinística de microação.
- Redução adicional quando a ação ainda parece grande.
- Timer de 2–5 minutos.
- Check-in de início.
- Resistência antes/depois.
- Registro de resultado.
- Histórico local com múltiplas tentativas e timestamps.
- Recovery loop.
- Safety routing básico para tarefas perigosas/crise.

## Fora do escopo
- LLM em produção.
- Login e banco remoto.
- Notificações.
- Integração com calendário.
- Dashboard longitudinal multiusuário.
- Gamificação.

## Critérios de aceite
1. Usuário consegue registrar uma tarefa em <30s.
2. Sistema sempre produz uma ação observável e curta.
3. Uma tentativa não sobrescreve tentativas anteriores.
4. Resistência pré/pós é registrada.
5. Falha de início leva a uma ação menor.
6. Dados persistem localmente no navegador.
7. Conteúdo claramente perigoso sai do fluxo normal.

## Métricas do piloto
- Task-to-action rate.
- Action-to-start rate.
- Tempo entre criação e tentativa.
- Variação de resistência.
- Reentry rate após falha.
- Número médio de tentativas até início.

## Gate Sprint 1 → Sprint 2
GO se, em 30 execuções reais:
- ≥70% chegam a uma microação considerada clara.
- ≥50% iniciam durante a sessão.
- queda mediana de resistência ≥2 pontos entre quem inicia.
- ≥50% dos que falham aceitam uma ação de reentrada.

Caso contrário: ajustar prompt, taxonomia e algoritmo antes de adicionar complexidade.
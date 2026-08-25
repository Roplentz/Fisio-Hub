# EXECUTA AI — Sprint 1.1

## Objetivo
Adicionar inteligência conversacional sem remover o motor determinístico que garante execução e recuperação.

## Arquitetura
Frontend híbrido → Edge Function → OpenAI Responses API.

- Motor local continua como fallback.
- LLM pode fazer no máximo uma pergunta de diagnóstico quando faltam evidências.
- Saída esperada: safety_route, barreira, confiança, evidência, pergunta opcional, microação, duração e justificativa.
- Safety routing ocorre no frontend e novamente no backend.
- A chave OpenAI nunca vai para o navegador.

## Modelo inicial
`gpt-5.6-luna`, priorizando custo/latência para o piloto. O modelo pode ser alterado pela variável `EXECUTA_AI_MODEL`.

## Backend
Código em `projects/executa-ai/supabase/functions/executa-ai/index.ts`.

Variáveis necessárias no ambiente do backend:
- `OPENAI_API_KEY`
- `EXECUTA_AI_MODEL` (opcional)

## Frontend
`public/executa-ai/config.js` recebe a URL pública do backend. Enquanto `apiUrl` estiver vazio, o aplicativo opera em modo local e não quebra.

## Gate
Antes do Sprint 2:
1. 30 execuções reais.
2. >= 50% iniciam a microação.
3. queda mediana de resistência >= 2 pontos.
4. comparar LLM vs motor local.
5. nenhum caso crítico encaminhado indevidamente para execução.

## Estado de implantação
O projeto Supabase `FISIOIA Academy` foi encontrado, porém está inativo e a restauração foi bloqueada pelo limite de projetos gratuitos ativos. A integração fica pronta em código, mas o endpoint só pode ser ativado após disponibilizar um backend seguro (restaurar/usar um projeto autorizado ou outro serviço server-side) e configurar `OPENAI_API_KEY` no ambiente.

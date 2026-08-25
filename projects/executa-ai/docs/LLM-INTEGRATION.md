# LLM Integration Contract — EXECUTA AI

O MVP do Sprint 1 usa um motor determinístico para validar comportamento antes de adicionar custo e variabilidade de modelo.

## Contrato futuro
Entrada:
- task
- user_utterance
- resistance_before
- prior_attempts[]
- recent_patterns[]

Saída estruturada:
```json
{
  "safety_route": "normal|crisis|harmful|medical_emergency",
  "barrier": "clarity|size|judgment|boredom|energy|options|other",
  "barrier_confidence": 0.0,
  "evidence": ["trechos relatados pelo usuário"],
  "micro_action": "ação observável",
  "minutes": 5,
  "trigger": "quando X, fazer Y",
  "success_criterion": "critério observável",
  "question": null
}
```

## Regras
- Nunca inferir barreira sem evidência suficiente.
- Se confiança <0,6, retornar uma única pergunta diagnóstica.
- Safety routing precede planejamento.
- Microação deve ser específica, observável e preferencialmente ≤20 min.
- Se tentativa falhar, reduzir escopo antes de ampliar explicação.
- Não emitir diagnóstico psicológico.

## Estratégia
1. Validar fluxo determinístico.
2. Rodar 30 casos humanos.
3. Comparar motor determinístico vs. LLM em conjunto fixo de casos.
4. Só migrar decisão principal ao LLM se houver ganho mensurável em clareza e taxa de início.
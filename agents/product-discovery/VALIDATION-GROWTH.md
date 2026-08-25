# FisioHub Product Discovery — Validation & Growth Engine v1.0

## Missão
Transformar descoberta de oportunidades em decisões comerciais testáveis, evitando escala baseada apenas em opinião.

## Pipeline
RADAR → DISCOVERY → OPPORTUNITY SCORE → VALIDATION → UNIT ECONOMICS → OFFER → EXPERIMENT 7–14D → GO / ITERATE / KILL → LAUNCH → SCALE → LEARNING LOOP

## 1. Opportunity Score (0–100)
Pontuar cada dimensão de 0 a 10 e aplicar os pesos:

- Demanda observável — 15%
- Tendência / crescimento — 10%
- Intensidade do problema — 10%
- Margem potencial — 15%
- Facilidade de aquisição — 10%
- Diferenciação possível — 10%
- Velocidade para MVP — 10%
- Competição favorável — 5%
- Recorrência / recompra — 5%
- Potencial de escala — 10%

`score = Σ(nota_0_10 × peso) × 10`

Faixas:
- 80–100: PRIORIDADE
- 65–79: VALIDAR
- 50–64: OBSERVAR / REFORMULAR
- <50: DESCARTAR por padrão

Sempre registrar também `confidence_score` (0–100), refletindo qualidade, quantidade, atualidade e independência das evidências.

## 2. Evidência mínima
Nunca inventar dados, demanda, depoimentos, faturamento ou escassez. Separar explicitamente:
- FATO: evidência observada e fonte
- ESTIMATIVA: cálculo com premissas declaradas
- HIPÓTESE: ainda precisa de teste

Não recomendar escala sem evidência mínima de demanda.

## 3. Rotas por tipo de produto

### Produto digital / infoproduto
Avaliar problema, público, disposição a pagar, autoridade/distribuição, promessa responsável, ticket, CAC provável, conversão, margem e velocidade de produção.

### Produto físico / importação
Adicionar landed cost, MOQ, frete, impostos, câmbio, prazo, risco regulatório, certificações, devolução, defeito, logística, comissão de marketplace, capital de giro e risco de fornecedor.

Produtos de saúde devem receber `regulatory_gate` antes de compra em escala.

## 4. Geração e comparação de ofertas
Para cada oportunidade aprovada, gerar até 5 formatos/ofertas e comparar:
- demanda
- margem
- risco
- velocidade
- facilidade de venda
- capital necessário
- capacidade de diferenciação

Recomendar uma opção e explicar por quê.

## 5. Matemática reversa
Nunca tratar meta de faturamento como garantia.

Calcular:
- Receita = ticket × vendas
- Vendas necessárias = meta / ticket
- Leads necessários = vendas / taxa_de_conversão
- CAC máximo preliminar = margem de contribuição por venda × percentual aceitável destinado à aquisição
- Lucro estimado = receita - CMV/COGS - taxas - impostos - logística - mídia - devoluções - custos operacionais atribuíveis

Exibir cenários conservador, base e agressivo quando houver incerteza relevante.

## 6. Experimento mínimo 7–14 dias
Antes de produção/estoque em escala, definir o teste mais barato capaz de invalidar a hipótese.

Possíveis testes:
- landing page + lista de espera
- anúncio de intenção / criativo
- pré-venda quando legal e operacionalmente apropriada
- lote piloto
- entrevistas estruturadas
- marketplace test
- oferta para audiência existente

Cada experimento deve ter:
- hipótese
- público
- canal
- orçamento máximo
- duração
- métrica primária
- threshold GO
- threshold ITERATE
- threshold KILL
- riscos

## 7. Decision Gate
### GO
Evidência suficiente + unit economics plausível + riscos controláveis.

### ITERATE
Sinal de demanda existe, mas oferta, preço, canal ou economics precisam mudar.

### KILL
Demanda insuficiente, economics estruturalmente ruins, risco regulatório desproporcional ou teste falhou sem hipótese plausível de correção.

Sunk cost nunca é argumento para GO.

## 8. Plano de lançamento
Para oportunidades GO:
1. proposta de valor
2. ICP/persona operacional
3. oferta e preço
4. ativos mínimos
5. funil
6. conteúdo de 30 dias
7. canais de aquisição
8. plano de 90 dias
9. métricas e alertas
10. próximos experimentos

## 9. Learning Loop
Todo experimento retorna ao Radar. Registrar:
- oportunidade_id
- data
- hipótese
- score inicial
- confidence inicial
- investimento
- canal
- impressões/visitas/leads/vendas quando aplicável
- CAC/CPL/CVR
- receita
- margem
- resultado GO/ITERATE/KILL
- motivo
- aprendizado

O agente deve usar resultados anteriores para recalibrar pesos e premissas, sem transformar correlação em causalidade.

## 10. Contrato de saída
```json
{
  "opportunity_id": "string",
  "name": "string",
  "type": "digital|physical|imported|service|saas|other",
  "opportunity_score": 0,
  "confidence_score": 0,
  "evidence": [],
  "assumptions": [],
  "estimated_initial_investment_brl": null,
  "estimated_margin_pct": null,
  "time_to_test_days": null,
  "regulatory_gate": "not_applicable|pending|pass|fail",
  "recommended_experiment": {},
  "decision": "GO|ITERATE|KILL|RESEARCH",
  "next_action": "string"
}
```

## Regra final
O objetivo não é encontrar ideias interessantes. É encontrar oportunidades que sobrevivam a evidência, matemática e teste real com o menor capital e tempo possíveis.

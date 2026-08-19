# Sprint 4 — Fundação comercial

## Objetivo

Medir consumo, aplicar limites e oferecer visão administrativa antes de
conectar pagamentos reais. O sistema não armazena prontuários ou conteúdo
clínico no razão comercial.

## Entregas

- catálogo inicial de planos;
- créditos mensais e limites de projetos;
- preços de referência em reais;
- tabela de custo por operação;
- reserva atômica de créditos;
- conclusão, falha e reembolso;
- histórico de uso por conta;
- estimativa de custo por evento;
- métricas administrativas agregadas;
- gate transacional para renderização;
- testes de saldo, concorrência lógica, reembolso e métricas.

## Planos iniciais para validação

| Plano | Créditos | Preço | Uso comercial |
|---|---:|---:|---|
| Explorar | 20 | R$ 0 | Não |
| Creator | 300 | R$ 97 | Sim |
| Creator Pro | 1.200 | R$ 297 | Sim |

Os valores são hipóteses de produto e devem ser validados com usuários antes
de serem apresentados como oferta definitiva.

## Limites do Sprint 4

Não foram implementados:

- cobrança real;
- checkout;
- cartão de crédito;
- renovação automática;
- emissão fiscal;
- Supabase em produção;
- Stripe ou outro gateway;
- alteração autônoma de planos.

A próxima etapa comercial deve substituir o ledger SQLite por persistência
centralizada, mantendo os mesmos contratos de reserva, conclusão e reembolso.

## Privacidade

O ledger recebe somente identificadores técnicos de conta/projeto, tipo de
operação, quantidade, créditos e custo. Conteúdo clínico, roteiro, mídia e
dados de pacientes não entram nesta camada.

# EXECUTA AI — Sprint 2: SaaS Comercial

## Objetivo
Transformar o MVP conversacional em um SaaS vendável com autenticação, plano Pro, memória de execução e onboarding.

## Escopo
1. Login/cadastro via Supabase Auth.
2. Área privada `/executa-ai/app/`.
3. Plano Founder Pro de R$59/mês.
4. Integração comercial preparada para Kiwify.
5. Controle de acesso por assinatura.
6. Execution Memory persistida em Supabase.
7. Onboarding inicial em menos de 2 minutos.
8. Dashboard mínimo: tarefas iniciadas, taxa de início, resistência média e barreiras recorrentes.
9. Página `/executa-ai/assinar/` para conversão.
10. Página `/executa-ai/bem-vindo/` para ativação pós-compra.

## Arquitetura
Landing/Vercel → Kiwify → Supabase Auth + subscriptions → EXECUTA AI Pro → OpenAI Edge Function → sessões/memória.

## Regra comercial
Plano: `founder_59`
Preço: R$59/mês
Moeda: BRL
Posicionamento: preço fundador enquanto a assinatura permanecer ativa.

## Gate do Sprint
GO quando:
- cadastro/login funcionar;
- usuário Pro for identificado no backend;
- sessão puder ser persistida por usuário;
- onboarding terminar em <=2 min;
- checkout Kiwify estiver conectado;
- compra teste liberar acesso corretamente.

## Fora do Sprint
App mobile, gamificação avançada, Teams, integrações externas, comunidade e marketplace.

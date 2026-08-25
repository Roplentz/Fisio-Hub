# 30 Cenários Simulados de QA — EXECUTA AI

> Estes casos são simulados para testar consistência do agente. Não são evidência de eficácia com usuários reais.

| # | Tarefa evitada | Resistência | Barreira esperada | Microação esperada |
|---:|---|---:|---|---|
| 1 | Começar TCC | 9 | CLARITY/SIZE | abrir arquivo e escrever 3 subtítulos |
| 2 | Responder e-mail difícil | 8 | JUDGMENT | escrever resposta em rascunho, sem enviar |
| 3 | Fazer declaração de imposto | 9 | SIZE | abrir pasta e separar 5 documentos |
| 4 | Preparar aula | 7 | CLARITY | escrever objetivo da aula em 1 frase |
| 5 | Estudar para prova | 8 | SIZE | abrir material e estudar 1 página por 10 min |
| 6 | Ligar para potencial cliente | 8 | JUDGMENT | escrever 2 frases de abertura |
| 7 | Iniciar treino | 6 | ENERGY | colocar roupa e fazer 5 min de aquecimento |
| 8 | Organizar finanças | 9 | SIZE | abrir extrato e registrar 3 despesas |
| 9 | Publicar post | 8 | PERFECTION | criar rascunho de 5 linhas sem publicar |
| 10 | Escrever artigo | 9 | ERROR | escrever 150 palavras ruins de propósito |
| 11 | Limpar escritório | 6 | SIZE | limpar somente a mesa por 10 min |
| 12 | Atualizar currículo | 7 | CLARITY | abrir arquivo e atualizar último cargo |
| 13 | Criar landing page | 8 | OPTIONS | escrever headline e CTA apenas |
| 14 | Aprender ferramenta nova | 7 | OPTIONS | assistir 1 tutorial de 10 min e testar 1 função |
| 15 | Fazer relatório mensal | 8 | BOREDOM | preencher somente os 3 indicadores principais |
| 16 | Marcar consulta | 5 | ANTICIPATION | abrir contato e digitar mensagem, sem enviar |
| 17 | Gravar vídeo | 9 | JUDGMENT | gravar teste de 30 s sem publicar |
| 18 | Fazer orçamento | 7 | ERROR | criar versão 1 com preço provisório |
| 19 | Revisar manuscrito | 8 | PERFECTION | revisar só o primeiro parágrafo por 10 min |
| 20 | Estudar inglês | 5 | BOREDOM | fazer 5 minutos de leitura em voz alta |
| 21 | Planejar semana | 6 | PRIORITY | escolher apenas 1 resultado obrigatório |
| 22 | Organizar fotos | 4 | BOREDOM | apagar 20 fotos e parar |
| 23 | Fazer backup | 6 | CLARITY | conectar dispositivo e copiar 1 pasta |
| 24 | Enviar proposta | 9 | ERROR/JUDGMENT | revisar somente preço, escopo e CTA |
| 25 | Criar apresentação | 8 | CLARITY | escrever títulos de 5 slides |
| 26 | Começar projeto de software | 9 | SIZE | criar README com problema e objetivo |
| 27 | Ler paper científico | 7 | SIZE | ler resumo e anotar 3 pontos |
| 28 | Fazer follow-up de vendas | 7 | JUDGMENT | enviar 1 follow-up curto para 1 lead |
| 29 | Retomar tarefa após 4 dias | 8 | INTERRUPT | abrir material e trabalhar 5 min |
| 30 | Tarefa sem prazo | 6 | DEADLINE | definir bloco específico de 10 min hoje |

## Check de qualidade para cada execução
- O agente pediu no máximo 1–2 perguntas antes de propor ação?
- A microação cabe em 2–20 minutos?
- A ação é observável?
- Existe critério de sucesso?
- Resistência foi medida antes?
- O agente evitou discurso motivacional longo?
- Em caso de falha, reduziu ainda mais a ação?

## Próximo teste obrigatório
Executar o mesmo protocolo com **30 tarefas reais trazidas por pessoas reais** e comparar taxa de início, queda de resistência e tempo até ação.

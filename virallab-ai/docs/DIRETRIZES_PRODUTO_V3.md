# ViralLab Studio 3.0 — Diretrizes de Produto

**Status:** decisão de produto aprovada  
**Responsável:** Prof. Dr. Rodrigo Plentz  
**Objetivo:** orientar UX, arquitetura, implementação, testes e publicação do ViralLab sem perder decisões entre sprints.

## 1. Visão do produto

O ViralLab é um estúdio de conteúdo com IA para especialistas. Ele deve transformar uma referência ou uma ideia em estratégia, roteiro, identidade visual consistente, narração, criativos e vídeo final.

A experiência deve parecer um produto SaaS profissional, não uma coleção de formulários. A complexidade pertence ao sistema; a simplicidade pertence ao usuário.

## 2. Fluxo oficial

O fluxo principal da versão 3.0 é:

1. **Analisar vídeo** *(opcional)*
2. **Estratégia**
3. **Roteiro**
4. **Avatar IA — Imagem Mestre**
5. **Voz**
6. **Criativos**
7. **Render**
8. **Publicação**
9. **Aprendizado**

A página inicial deve oferecer duas entradas:

- **Analisar um vídeo:** usa o vídeo como referência para extrair estrutura, hook, ritmo, cenas e CTA.
- **Criar do zero:** começa diretamente em Estratégia.

A análise de vídeo é a etapa 1 do produto, mas nunca deve bloquear quem deseja criar do zero.

## 3. Dashboard e navegação

O dashboard deve mostrar:

- projeto atual e percentual concluído;
- última etapa salva;
- ação “Continuar de onde parou”;
- atalhos para Analisar vídeo, Criar do zero, Avatar IA, Criativos e Render;
- estado de cada etapa: não iniciada, em andamento, pronta ou requer atenção.

### Regras de navegação

- Uma etapa por tela no celular.
- Navegação lateral no desktop e seletor compacto no celular.
- Progresso sempre visível.
- Salvamento automático sempre que for seguro.
- O usuário pode voltar sem perder dados.
- Cada etapa deve indicar claramente a próxima ação.

## 4. Análise de vídeo

### Entradas

- upload pelo celular ou computador;
- URL pública compatível;
- opção visível “Criar sem vídeo de referência”.

### Saídas mínimas

- hook;
- tese central;
- estrutura narrativa;
- duração e ritmo;
- divisão aproximada de cenas;
- textos na tela;
- CTA;
- padrões visuais e de edição;
- recomendações para criar conteúdo original inspirado na estrutura, sem copiar literalmente.

### Critérios de aceite

- O restante da análise continua quando a transcrição falhar.
- Vídeos sem áudio não quebram o fluxo.
- Erros parciais são explicados por etapa.
- O resultado pode alimentar Estratégia e Roteiro com um toque.

## 5. Estratégia

A etapa deve definir tema, público, problema, objetivo, canal, duração, formato, tom, nível de evidência e CTA.

A IA pode sugerir opções, mas o usuário mantém controle editorial. Escolhas anteriores devem ser reaproveitadas quando forem pertinentes.

## 6. Roteiro

O roteiro deve ser editável e organizado por cenas. Cada cena deve conter:

- narração;
- texto na tela;
- direção visual;
- tipo de cena;
- duração planejada;
- personagem ou ativo principal.

Alterações no roteiro devem atualizar, de modo controlado, o plano de voz e de criativos. Criativos já aprovados nunca devem ser descartados silenciosamente.

## 7. Avatar IA — Imagem Mestre

“Perfil Visual” passa a ser apresentado ao usuário como **Avatar IA — Imagem Mestre**.

### Entrada obrigatória

O usuário fornece apenas três fotos:

1. **Frente** — olhando para a câmera.
2. **Lado esquerdo** — perfil visível.
3. **Lado direito** — perfil visível.

### Orientação de captura

- boa iluminação frontal;
- fundo neutro;
- rosto inteiro e sem obstrução;
- sem boné ou óculos escuros;
- expressão neutra;
- fotos recentes e nítidas.

### Fluxo

1. Enviar as três fotos em campos separados.
2. Validar presença, orientação e qualidade mínima.
3. Confirmar autorização de uso da própria imagem.
4. Gerar uma Imagem Mestre.
5. Exibir a imagem para **Aprovar**, **Gerar outra** ou **Substituir fotos**.
6. Salvar somente a versão aprovada como referência ativa.

### O que deve ser persistido

- três fotos de referência;
- Imagem Mestre aprovada;
- nome e papel do avatar;
- diretrizes visuais;
- estilos de roupa permitidos;
- preferências de fundo, luz e enquadramento;
- data e versão do perfil;
- registro de consentimento e opção de exclusão.

### Regra de consistência

Toda cena marcada com o avatar do autor deve usar automaticamente a Imagem Mestre e as fotos autorizadas como referência. O sistema deve priorizar a preservação da identidade facial, idade aparente, cabelo, tom de pele e características individuais.

### Limite técnico e ético

Na versão inicial, “Imagem Mestre” significa geração orientada por referências. Não deve ser anunciada como treinamento biométrico ou clonagem perfeita se nenhum modelo individual tiver sido realmente treinado. Fotos e derivados devem poder ser removidos pelo usuário.

### Critérios de aceite

- O botão “Criar Imagem Mestre” só ativa com as três fotos.
- Os três ângulos ficam identificados e podem ser substituídos individualmente.
- A Imagem Mestre exige aprovação explícita.
- A referência aprovada é reutilizada entre projetos.
- Cenas sem o autor não recebem a referência por engano.
- A exclusão remove referências e derivados associados conforme a política de retenção.

## 8. Voz

### Formas de entrada

- gravação do roteiro completo pelo navegador;
- gravação por cena;
- upload de MP3, WAV, M4A, AAC, OGG ou WebM.

### Recursos

- teleprompter;
- reprodução e regravação;
- duração total;
- alinhamento entre áudio e cenas;
- alertas de gravação longa ou curta;
- volume da voz e da trilha;
- possibilidade de corrigir apenas uma cena.

O alinhamento inicial pode ser proporcional ao texto. A evolução recomendada é usar transcrição com marcas temporais e pausas reais.

**Clonagem de voz não faz parte do MVP 3.0.** Se for adicionada futuramente, exigirá consentimento explícito, segurança reforçada, identificação do conteúdo sintético e controle de revogação.

## 9. Criativos

A área de Criativos deve funcionar como uma galeria visual, não como formulário técnico.

### Recursos mínimos

- DNA Visual do projeto;
- escolha do personagem por cena;
- Avatar IA selecionado automaticamente quando o autor aparece;
- geração de variações;
- upload de imagem ou vídeo próprio;
- Aprovar, Rejeitar, Gerar outra e Editar direção;
- histórico de versões;
- enquadramento com área segura para legendas;
- consistência de estilo entre cenas.

Criativos devem nascer do roteiro e respeitar o tempo real da voz quando ela já estiver disponível.

## 10. Render

O Render deve combinar:

- criativos aprovados;
- voz gravada;
- legendas;
- trilha;
- duração e transições;
- formato vertical 1080 × 1920 por padrão.

Nenhum render final deve iniciar com cenas obrigatórias sem criativo aprovado, salvo confirmação explícita do usuário.

## 11. Publicação e Aprendizado

### Publicação

Preparar título, legenda, CTA, hashtags, capa, formato e checklist. Publicação automática em redes sociais é uma evolução posterior e deve exigir confirmação explícita.

### Aprendizado

Registrar feedback editorial, preferências visuais, hooks aprovados e desempenho informado. O aprendizado deve ser auditável, reversível e nunca alterar silenciosamente decisões do usuário.

## 12. Diretrizes de frontend

- mobile-first;
- visual de SaaS profissional;
- cards, galeria e timeline onde agregarem clareza;
- textos curtos e ações evidentes;
- estados vazios úteis;
- feedback de carregamento e progresso;
- componentes responsivos;
- acessibilidade de contraste e toque;
- identidade RP consistente;
- evitar seis ou mais abas horizontais no celular;
- evitar expor nomes de arquivos, caminhos internos ou detalhes técnicos ao usuário final.

## 13. Fonte única de verdade

O `video-package.json` continua sendo a fonte única de verdade do projeto. A evolução do esquema deve incluir, com versionamento e migração:

- estado das nove etapas;
- análise de referência;
- estratégia;
- roteiro e cenas;
- `avatar_profile_id` e versão da Imagem Mestre;
- plano e arquivos de voz;
- criativos e seus estados de aprovação;
- configuração de render;
- metadados de publicação;
- feedback de aprendizado.

Arquivos binários devem ser referenciados no manifesto, não incorporados diretamente ao JSON.

## 14. Segurança, privacidade e uso responsável

- Não enviar dados clínicos identificáveis a serviços públicos de IA.
- Informar quando imagens ou vozes são geradas por IA.
- Obter autorização explícita para rosto e voz.
- Permitir exclusão e substituição de referências.
- Não reutilizar o avatar fora do contexto autorizado.
- Manter revisão humana antes da publicação.
- Guardar segredos apenas em ambiente seguro; nunca no repositório.

## 15. Qualidade e publicação do software

Toda mudança deve passar pelo **ViralLab Guardian**:

- compilação;
- Ruff;
- testes unitários;
- testes de importação;
- testes dos fluxos principais;
- teste de inicialização do Streamlit;
- validação do esquema do projeto;
- testes específicos do Avatar IA e da Voz.

Fluxo recomendado:

`branch de trabalho → Pull Request → Guardian verde → merge em main → Release Gate → production`

A branch `production` deve receber apenas versões validadas. O Streamlit de produção deve acompanhar essa branch.

## 16. Roadmap de implementação

### P0 — Base segura

- atualizar navegação e ordem oficial;
- dashboard responsivo;
- preservar Análise de vídeo;
- schema versionado e migração de projetos existentes;
- testes dos fluxos atuais;
- corrigir divergência entre `main` e `production`.

### P1 — Diferencial central

- Avatar IA com três fotos;
- validação de ângulos;
- criação e aprovação da Imagem Mestre;
- persistência e exclusão;
- integração automática com Criativos;
- testes de consistência e não aplicação indevida.

### P2 — Produção audiovisual

- voz completa e por cena;
- alinhamento temporal melhorado;
- galeria de criativos;
- timeline de render;
- capa e pacote de publicação.

### P3 — Escala

- biblioteca de personagens;
- múltiplos avatares autorizados;
- publicação assistida;
- analytics;
- aprendizado por desempenho;
- clonagem de voz somente com governança específica.

## 17. Definição de pronto da versão 3.0

A versão 3.0 estará pronta quando um usuário, no celular, conseguir:

1. iniciar por vídeo ou do zero;
2. gerar e editar estratégia e roteiro;
3. enviar exatamente três fotos e aprovar a Imagem Mestre;
4. gravar ou enviar a voz;
5. gerar criativos consistentes com o avatar;
6. aprovar os materiais;
7. renderizar um vídeo sincronizado;
8. preparar o pacote de publicação;
9. reabrir o projeto sem perda de dados;
10. excluir suas referências pessoais;
11. concluir o fluxo sem erro nos testes automatizados.

## 18. Fora do escopo imediato

- promessa de clone facial perfeito;
- treinamento biométrico individual sem infraestrutura comprovada;
- clonagem de voz;
- postagem automática sem confirmação;
- correções autônomas de banco, autenticação, pagamentos ou dados pessoais;
- publicação direta de código não validado em produção.

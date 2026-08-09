# Memória de Construção e Roadmap — FisioHub Innovation Lab

> Documento vivo de produto, tecnologia e estratégia. Registra o que foi construído, por que foi construído, o estado atual e a sequência de evolução do ecossistema.

**Responsável:** Prof. Dr. Rodrigo Della Méa Plentz  
**Ecossistema:** FisioHub · Fisio IA OS · FisioConnect  
**Última atualização:** 9 de agosto de 2026  
**Status:** MVP funcional em evolução para produto comercial

---

## 1. Visão do produto

O **FisioHub Innovation Lab** está sendo construído como um sistema operacional de inovação em saúde. A proposta vai além de um site ou gerador de documentos: acompanhar uma ideia desde a identificação do problema até sua validação, conexão científica, captação de recursos, elaboração de proposta e comunicação por pitch.

A tese central é simples:

> **HIPÓTESE → ARTEFATO → EVIDÊNCIA → DECISÃO**

O sistema deve reduzir a complexidade para o usuário sem esconder critérios, fontes, riscos ou decisões. A IA atua como copiloto e equipe especializada; a autoria e a aprovação continuam humanas.

## 2. Princípios que orientam a construção

1. **A complexidade pertence ao sistema; a simplicidade pertence ao usuário.**
2. **Evidência antes de afirmação:** dados, referências e currículos precisam ser rastreáveis.
3. **IA sem licença para inventar:** fatos ausentes devem ser marcados como pendentes.
4. **Aprovação humana:** nenhuma contribuição de agente entra silenciosamente na versão oficial.
5. **Memória e versionamento:** toda alteração relevante precisa preservar a versão anterior e sua justificativa.
6. **Open Source First:** pesquisar, auditar e aproveitar soluções abertas maduras antes de desenvolver do zero.
7. **Acessibilidade real:** tipografia legível, contraste, hierarquia clara e funcionamento responsivo.
8. **Uma única jornada:** módulos especializados não podem parecer produtos desconectados.

## 3. Arquitetura conceitual do ecossistema

O desenho de longo prazo organiza a plataforma em quatro camadas:

| Camada | Função |
|---|---|
| **Experience** | Interface integrada, navegação, design system, acessibilidade e experiência personalizada. |
| **Services** | Projetos, formação, rede científica, editais, propostas, pitch, marketplace e operações. |
| **Cognitive — Fisio IA OS** | Mentor, agentes especializados, orquestração, memória, avaliação e recomendação. |
| **Data** | Identidade, projetos, versões, evidências, currículos, instituições, editais, métricas e auditoria. |

Identidade, login, contexto do usuário, memória do projeto e indicadores devem ser compartilhados por todos os módulos.

## 4. Sites publicados

### 4.1 Laboratório de Landing Page — versão acadêmica

**URL:** https://laboratorio-landing-page.rodrigoplentz.chatgpt.site

Nasceu como ferramenta prática para a disciplina de Conhecimento e Inovação. O aluno registra uma ideia, estrutura a hipótese e transforma o projeto em uma landing page funcional.

Evoluções realizadas:

- roteiro didático para preenchimento dos campos;
- três direções mínimas de design;
- modelos visuais mais modernos e elementos gráficos;
- aumento das fontes e melhoria da legibilidade;
- fluxo de ideia de inovação antes da geração da página;
- canvas vivo e visualização da proposta;
- salvar projeto e exportar em PDF;
- login por e-mail e senha;
- registro dos projetos para acompanhamento docente;
- Mentor de Inovação por IA;
- correções de operação do chatbot e da atualização da landing page;
- preservação da versão acadêmica após a separação do produto comercial.

Jornada pedagógica consolidada:

1. observar o contexto;
2. definir problema e público;
3. formular solução e hipótese;
4. construir o conteúdo antes do design;
5. escolher a direção visual;
6. gerar e publicar o artefato;
7. testar botões, formulário e versão móvel;
8. registrar falhas e correções;
9. apresentar um pitch de três minutos;
10. decidir o próximo experimento.

### 4.2 FisioHub Innovation Lab — versão comercial

**URL:** https://fisiohub-innovation-lab.rodrigoplentz.chatgpt.site

Foi criado a partir da clonagem conceitual do laboratório acadêmico, mas reposicionado como produto comercial do FisioHub. O foco passou da criação isolada de landing pages para uma jornada completa de inovação, ciência, financiamento, proposta e comunicação.

Direção visual escolhida: experiência premium, clara, fluida e integrada, com linguagem de aplicativo e referência de qualidade inspirada em produtos Apple — sem copiar identidade ou componentes proprietários.

## 5. Módulos atuais do FisioHub Innovation Lab

| Módulo | Rota | Propósito |
|---|---|---|
| **FisioConnect** | `/fisioconnect` | Conectar projetos a pesquisadores, instituições, aceleradoras e potenciais parceiros. |
| **Rede de pesquisadores** | `/pesquisadores` | Buscar especialistas e produção científica verificável, com integração conceitual a OpenAlex e ORCID. |
| **Inteligência de editais** | `/editais` | Localizar e analisar editais por busca ativa, URL ou upload. |
| **Equipe de agentes** | `/equipe-ia` | Orquestrar especialistas de IA para construir e revisar propostas. |
| **Inteligência científica** | `/inteligencia-cientifica` | Reunir evidências, referências e rastreabilidade científica. |
| **Pesquisador Sênior** | `/pesquisador-senior` | Alinhar proposta, instituição, investigador principal e critérios do edital. |
| **Propostas** | `/propostas` | Manter a proposta completa, suas seções e versões editáveis. |
| **FisioPitch IA** | `/pitch` | Gerar narrativa e estrutura de pitch com base no projeto. |
| **Quality Lab** | `/qualidade` | Avaliar coerência, completude, riscos, aderência e qualidade final. |
| **Simulação completa** | `/simulacao` | Demonstrar a jornada ponta a ponta. |
| **Caso PROFIX-CB** | `/simulacao-profix` | Simulação aplicada ao Edital FAPERGS/CNPq/CAPES 06/2026. |

## 6. Memória cronológica da construção

### Fase 1 — Laboratório educacional

- criação da aula prática e do roteiro preenchível;
- transformação do roteiro em ferramenta web;
- inclusão de escolhas de design;
- publicação do primeiro laboratório;
- evolução para um laboratório de ideias de inovação;
- login, salvamento, PDF e acompanhamento dos alunos;
- incorporação do primeiro Mentor de Inovação IA;
- correção de falhas do chatbot e da sincronização entre formulário e landing page.

### Fase 2 — Separação acadêmica e comercial

- preservação do laboratório para os alunos;
- criação da versão comercial integrada ao FisioHub;
- evolução da experiência visual para padrão premium;
- reorganização da home como sistema operacional de inovação;
- conexão entre FisioHub e FisioConnect.

### Fase 3 — Rede científica e oportunidades

- criação do FisioConnect;
- busca de pesquisadores e instituições;
- aproximação conceitual com OpenAlex, ORCID, Google Acadêmico e Plataforma Lattes;
- inclusão de fontes financiadoras, aceleradoras, universidades, academias e pesquisadores;
- criação da busca de editais por URL, upload e busca ativa;
- tratamento de falhas quando fontes externas não retornam resultados.

### Fase 4 — Propostas e comunicação

- estruturação do fluxo de propostas adequadas a cada edital;
- criação do módulo de pitch baseado no conteúdo do projeto;
- simulação completa da jornada;
- aplicação ao Edital FAPERGS/CNPq/CAPES 06/2026 — PROFIX-CB;
- aumento das fontes e ajustes de legibilidade em telas densas.

### Sprints 13–15 — Equipe de Proposta

- orquestrador central;
- agentes de elegibilidade, mérito científico, metodologia, orçamento e cronograma;
- revisor crítico e banca simulada;
- acionamento manual dos especialistas;
- comparação da contribuição antes de incorporá-la;
- Scientific Writer para escrita científica avançada;
- aprovação humana e exportação após validação.

### Sprints 16–18 — Inteligência científica e supervisão

- **Evidence Engine** para localizar e organizar evidências;
- referências com OpenAlex e DOI;
- matriz de aderência entre edital, instituição, investigador e proposta;
- arquitetura completa da proposta;
- **Scientific Intelligence Supervisor**, o “agente pensante” do sistema;
- checagens de coerência, rastreabilidade e regressão;
- versionamento, rollback e aprovação humana;
- preservação obrigatória da proposta completa quando os agentes são acionados.

## 7. Estrutura canônica de uma proposta

Toda versão do projeto deve manter, mesmo quando um agente trabalhar em apenas uma seção:

1. título;
2. autores e papéis;
3. instituição proponente e parceiros;
4. resumo;
5. problema e justificativa;
6. introdução e estado da arte;
7. hipótese ou pergunta de pesquisa;
8. objetivo geral;
9. objetivos específicos;
10. metodologia;
11. ética, riscos e proteção de dados;
12. resultados e impactos esperados;
13. indicadores e plano de avaliação;
14. cronograma;
15. orçamento e justificativa orçamentária;
16. referências bibliográficas;
17. anexos e documentos obrigatórios;
18. pendências, alertas e fontes de cada afirmação.

Cada execução de agente deve produzir uma nova versão identificável, com seção alterada, justificativa, fontes, alertas e possibilidade de aceitar, rejeitar ou restaurar.

## 8. Equipe de agentes de IA

| Agente | Responsabilidade |
|---|---|
| **Orquestrador** | Entender a etapa, distribuir tarefas e impedir contradições entre agentes. |
| **Elegibilidade** | Auditar requisitos, impedimentos, documentos e critérios eliminatórios. |
| **Pesquisador Sênior** | Alinhar edital, instituição, programa, investigador principal e equipe. |
| **Scientific Writer** | Reescrever com rigor, clareza, densidade científica e encadeamento lógico. |
| **Mérito Científico** | Fortalecer lacuna, hipótese, inovação, relevância e impacto. |
| **Metodologia** | Revisar desenho, amostra, variáveis, análise, ética e exequibilidade. |
| **Orçamento e Cronograma** | Verificar rubricas, limites, marcos, dependências e coerência financeira. |
| **Revisor Crítico** | Procurar inconsistências, exageros, lacunas e fragilidades. |
| **Banca Simulada** | Pontuar a proposta segundo os critérios e priorizar correções decisivas. |
| **Evidence Engine** | Localizar evidências e devolver referências verificáveis. |
| **Scientific Intelligence Supervisor** | Observar o sistema, detectar redundâncias, medir qualidade e sugerir melhorias contínuas. |

Regra de operação: o sistema pode elaborar uma proposta mesmo quando requisitos não são atendidos, mas deve apresentar o status de inelegibilidade ou risco de forma explícita. A ferramenta ajuda a pensar; não falsifica elegibilidade.

## 9. Problemas identificados e lições incorporadas

| Problema | Aprendizado incorporado |
|---|---|
| Fontes pequenas e leitura difícil | Adotar escala tipográfica mínima e testar telas densas em desktop e mobile. |
| Chatbot indisponível | Exibir estado real, mensagem acionável e mecanismo seguro de nova tentativa. |
| Landing page sem atualizar | Manter fonte única de dados e sincronização explícita entre edição e visualização. |
| Busca científica sem retorno | Tratar indisponibilidade da fonte, oferecer nova tentativa e fontes alternativas. |
| Fluxos redundantes | Reorganizar o produto por jornada, não por tecnologia ou agente. |
| Agentes alterando partes isoladas | Preservar documento mestre, versionamento e comparação de alterações. |
| Risco de informação inventada | Exigir fonte, marcar ausência e separar fato, inferência e sugestão. |
| Requisitos não atendidos | Permitir rascunho com alerta, sem transformar risco em conformidade fictícia. |

## 10. Sprint 19 — Coerência e jornada única

**Objetivo:** transformar o conjunto de módulos em uma experiência contínua, eliminando redundâncias e etapas fora de ordem.

Nova organização principal:

1. **Projeto** — problema, público, solução, hipótese, equipe e versão atual;
2. **Ciência** — pesquisadores, currículo, evidências, lacuna e mérito;
3. **Financiamento** — oportunidades, editais, elegibilidade e aderência;
4. **Proposta** — documento mestre, agentes, versões, orçamento e qualidade;
5. **Comunicação** — landing page, resumo executivo, pitch e materiais finais.

Entregas previstas:

- mapa único de navegação;
- painel “onde estou, o que falta e qual é o próximo passo”;
- remoção de telas e ações duplicadas;
- projeto mestre compartilhado por todos os módulos;
- estados claros: não iniciado, em andamento, pendente, crítico e aprovado;
- revisão tipográfica e de acessibilidade;
- protótipo no Figma antes da implementação final;
- teste completo com o caso PROFIX-CB.

## 11. Roadmap proposto após o Sprint 19

### Sprint 20 — Modelo de dados e memória operacional

- identidade única de usuário, instituição, pesquisador e projeto;
- banco de dados central, permissões e histórico de versões;
- autosave, recuperação e trilha de auditoria;
- contratos de dados entre módulos e agentes.

### Sprint 21 — Integrações de produção

- upload e leitura estruturada de editais;
- ingestão por URL com validação de origem;
- conectores para OpenAlex, ORCID e Crossref;
- apoio à busca em Lattes e Google Acadêmico, respeitando disponibilidade e termos das fontes;
- exportação editável em DOCX e PDF.

### Sprint 22 — Segurança, governança e IA responsável

- autenticação robusta e controle por perfil;
- proteção de dados e adequação à LGPD;
- registro de prompts, fontes, alterações e aprovações;
- avaliação de alucinação, viés, segurança e qualidade;
- limites de autonomia para cada agente.

### Sprint 23 — Produto comercial e métricas

- onboarding por perfil e objetivo;
- planos de assinatura e limites de uso;
- painel administrativo e métricas de ativação, conclusão e qualidade;
- custos por projeto e por execução de agente;
- instrumentos de feedback e suporte.

### Sprint 24 — Pilotos e escala

- piloto com Universidade La Salle e instituições parceiras;
- validação com pesquisadores, programas de pós-graduação e profissionais;
- comparação entre proposta sem agentes e proposta assistida;
- casos de sucesso, playbook de implantação e preparação para escala.

## 12. Critérios para sair de MVP e virar produto

- jornada completa sem perda de dados;
- proposta mestre sempre íntegra e recuperável;
- fontes e citações verificáveis;
- nenhum alerta crítico ocultado;
- exportação DOCX/PDF consistente;
- acessibilidade e responsividade aprovadas;
- autenticação, permissões, privacidade e auditoria operacionais;
- custos de IA conhecidos e controlados;
- evidência de ganho de tempo e qualidade em pilotos reais;
- modelo comercial validado com usuários pagantes.

## 13. Indicadores principais

| Dimensão | Indicadores |
|---|---|
| **Ativação** | Percentual que cria projeto e conclui briefing. |
| **Progresso** | Percentual que chega a ciência, edital, proposta e pitch. |
| **Qualidade** | Completude, aderência ao edital, coerência e rastreabilidade. |
| **Eficiência** | Tempo até primeira versão e número de retrabalhos. |
| **Confiança** | Alertas resolvidos, fontes verificadas e alterações aprovadas. |
| **Resultado** | Propostas submetidas, aprovadas, financiadas e parcerias geradas. |
| **Negócio** | Conversão, retenção, receita recorrente e custo por projeto. |

## 14. Decisões em aberto

- tecnologia definitiva de autenticação, banco e armazenamento;
- política comercial e limites de cada plano;
- fontes externas com acesso oficial e sustentável;
- governança institucional e responsabilidade pelas submissões;
- escopo do marketplace de especialistas e serviços;
- critérios objetivos de qualidade para cada tipo de edital;
- estratégia de propriedade intelectual e licenciamento.

## 15. Registro de decisões futuras

Toda decisão relevante deve acrescentar uma entrada contendo:

- data;
- contexto e problema;
- opções consideradas;
- decisão tomada;
- justificativa;
- responsável;
- módulos afetados;
- riscos e dependências;
- indicador de sucesso;
- resultado observado;
- lições aprendidas.

## 16. Links oficiais

- **Repositório:** https://github.com/Roplentz/Fisio-Hub
- **Laboratório acadêmico:** https://laboratorio-landing-page.rodrigoplentz.chatgpt.site
- **FisioHub Innovation Lab:** https://fisiohub-innovation-lab.rodrigoplentz.chatgpt.site

---

### Regra de manutenção deste documento

Atualizar esta memória ao fim de cada sprint, publicação, integração ou decisão estratégica. O documento deve separar claramente **construído**, **em validação**, **planejado** e **hipótese**. Roadmap não é profecia; é direção com evidência e direito de mudar.

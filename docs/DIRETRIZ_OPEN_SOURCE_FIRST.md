# Diretriz Open Source First

## Status

Diretriz permanente de arquitetura, produto e desenvolvimento do FisioHub e de seus módulos, incluindo o ViralLab.

## Princípio central

> Antes de desenvolver uma funcionalidade do zero, o projeto deve pesquisar, auditar e aproveitar conhecimento, modelos, bibliotecas, padrões e implementações abertas já existentes.

O objetivo é acelerar o desenvolvimento, reduzir custos, evitar retrabalho e construir sobre soluções já testadas pela comunidade.

## Regra de decisão

Toda nova funcionalidade relevante deve começar com uma auditoria do ecossistema aberto, especialmente em:

- GitHub;
- Hugging Face;
- documentação oficial dos projetos;
- artigos científicos e repositórios dos autores;
- comunidades técnicas reconhecidas.

Somente desenvolver do zero quando:

1. não existir solução adequada;
2. as soluções existentes tiverem licença incompatível;
3. houver risco relevante de segurança, privacidade ou manutenção;
4. a integração for mais complexa do que uma implementação própria;
5. a solução não atender aos requisitos de qualidade do produto.

## Critérios obrigatórios de auditoria

Antes de adotar um projeto, modelo ou biblioteca, avaliar:

### 1. Licença

Priorizar licenças permissivas e compatíveis com uso comercial, como:

- Apache 2.0;
- MIT;
- BSD.

Licenças, pesos de modelos e datasets devem ser avaliados separadamente. Um repositório pode ter código aberto e pesos com regras diferentes.

### 2. Maturidade

Verificar:

- frequência de atualizações;
- número e qualidade dos contribuidores;
- issues abertas e resolvidas;
- releases recentes;
- documentação;
- testes automatizados;
- uso real por outros projetos.

Número de estrelas é apenas um sinal auxiliar, não um critério suficiente.

### 3. Qualidade técnica

Avaliar:

- qualidade do resultado;
- velocidade;
- estabilidade;
- consumo de CPU, GPU e memória;
- suporte ao português brasileiro quando necessário;
- facilidade de instalação e operação;
- capacidade de rodar localmente ou em infraestrutura de baixo custo.

### 4. Segurança e privacidade

Verificar:

- envio de dados a terceiros;
- execução de código remoto;
- dependências vulneráveis;
- tratamento de imagens, voz, vídeos e dados pessoais;
- necessidade de consentimento explícito;
- compatibilidade com a LGPD.

### 5. Sustentabilidade

Avaliar:

- risco de abandono;
- dependência excessiva de um único mantenedor;
- possibilidade de manter um fork;
- existência de alternativas substitutas;
- custo futuro de hospedagem e processamento.

## Arquitetura obrigatória

Modelos e provedores externos não devem ser acoplados diretamente ao fluxo principal do produto.

Cada domínio deve possuir uma camada de abstração própria, por exemplo:

```text
Voice Engine
├── Kokoro
├── Chatterbox
├── OpenAI
├── ElevenLabs
└── futuros provedores

Image Engine
├── Gemini
├── FLUX
├── SDXL
├── ComfyUI
└── futuros provedores
```

Todos os provedores de um mesmo domínio devem seguir uma interface comum. Isso permite substituir ou adicionar modelos sem redesenhar o aplicativo.

## Política de implementação

Ao integrar conhecimento aberto:

1. reutilizar padrões consolidados;
2. encapsular dependências externas;
3. registrar versão, licença e origem;
4. criar fallback quando a função for crítica;
5. incluir testes mínimos;
6. medir qualidade e desempenho no ambiente real;
7. evitar copiar código sem compreender sua função e sua licença;
8. manter o fluxo principal independente do fornecedor.

## Política de evolução contínua

O ecossistema open source deve ser reavaliado sempre que:

- uma nova funcionalidade for planejada;
- o modelo atual apresentar limitações;
- surgir uma alternativa relevante;
- houver mudança de licença;
- o projeto adotado deixar de ser mantido;
- custos ou requisitos de infraestrutura mudarem.

Uma substituição deve ocorrer somente quando houver ganho demonstrável em qualidade, custo, velocidade, privacidade ou manutenção.

## Registro mínimo para cada adoção

Toda integração relevante deve documentar:

- nome e endereço do projeto original;
- função exercida no FisioHub;
- versão ou commit utilizado;
- licença do código;
- licença dos pesos e datasets;
- requisitos de hardware;
- riscos conhecidos;
- alternativa de fallback;
- data da última auditoria.

## Aplicação ao ViralLab

No ViralLab, esta diretriz orienta especialmente:

- síntese e clonagem de voz;
- transcrição e alinhamento temporal;
- geração de imagens;
- geração e edição de vídeo;
- avatares;
- legendas inteligentes;
- detecção de rosto e zonas seguras;
- renderização;
- análise de desempenho de conteúdo.

A prioridade é integrar soluções abertas maduras, mantendo uma arquitetura modular que permita testar modelos mais robustos no futuro.

## Princípio de experiência

> A complexidade pertence ao sistema. A simplicidade pertence ao usuário.

O usuário não deve precisar conhecer modelos, provedores ou detalhes técnicos. O sistema deve selecionar, testar e substituir componentes internamente, preservando uma experiência simples, segura e consistente.

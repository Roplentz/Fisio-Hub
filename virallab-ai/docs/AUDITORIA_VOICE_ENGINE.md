# Auditoria do Voice Engine

## Decisão inicial

O ViralLab adota **Kokoro** como primeiro motor local de síntese de voz e mantém uma interface própria para permitir Chatterbox, OpenAI, ElevenLabs e outros provedores no futuro.

## Padrão de experiência adotado

A interface segue conceitos consolidados em plataformas de referência de TTS:

- seleção de voz;
- idioma;
- velocidade;
- estabilidade;
- semelhança;
- expressividade/estilo;
- reforço de presença da voz;
- preview e download;
- cache por roteiro e configuração.

Nem todo provedor implementa todos os parâmetros. O Voice Engine preserva a mesma interface e cada adaptador traduz somente os controles suportados.

## Projetos auditados

### Kokoro

- Função: TTS local padrão.
- Repositório: `hexgrad/kokoro`.
- Licença informada pelo projeto: Apache 2.0 para os pesos.
- Tamanho: 82 milhões de parâmetros.
- Português brasileiro: `lang_code="p"`.
- Pontos fortes: leve, rápido, baixo custo e integração Python simples.
- Limitação atual: os controles avançados são menores que os de serviços comerciais.

### Chatterbox

- Função futura: voz expressiva e clonagem autorizada.
- Repositório: `resemble-ai/chatterbox`.
- Licença do código: MIT.
- Possui modelo específico para português brasileiro.
- Requer mais recursos que Kokoro e deve entrar somente após benchmark no ambiente real.

### Piper

- O repositório original `rhasspy/piper` foi arquivado.
- O desenvolvimento foi movido para outro projeto com licença GPL.
- Não será a base principal do produto sem nova análise jurídica e técnica.

## Arquitetura implementada

```text
Studio
  └── Voice UI
       └── Voice Engine
            ├── KokoroProvider
            ├── cache por hash
            ├── voice-generation.json
            ├── voice-plan.json
            └── futuros provedores
```

## Cache

O cache considera:

- texto integral;
- provedor;
- voz;
- idioma;
- velocidade;
- estabilidade;
- semelhança;
- estilo;
- speaker boost.

Se nada mudar, o áudio é reutilizado.

## Segurança e privacidade

- O Kokoro roda localmente.
- O roteiro não precisa ser enviado a terceiros.
- Clonagem de voz exigirá consentimento explícito e mecanismo de exclusão.
- Vozes de terceiros não devem ser clonadas sem autorização verificável.

## Próximos benchmarks

1. naturalidade em português brasileiro;
2. pronúncia de termos clínicos e siglas;
3. tempo de geração em CPU e GPU;
4. memória utilizada;
5. estabilidade em roteiros de 15, 30, 60 e 90 segundos;
6. comparação cega com Chatterbox e um serviço comercial de referência.

Última auditoria: 26 de julho de 2026.

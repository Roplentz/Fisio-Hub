# ViralLab AI

Sistema de engenharia reversa e geração assistida de conteúdo curto para especialistas em saúde.

## Objetivo

Transformar vídeos de referência, ideias e conhecimento técnico em roteiros, storyboards e planos de edição reproduzíveis, mantendo a identidade e a credibilidade do criador.

## Pipeline do MVP

1. Entrada de vídeo, áudio, transcrição ou tema.
2. Transcrição local com Whisper.
3. Análise de hook, estrutura, ritmo, cortes, elementos visuais e CTA.
4. Geração de roteiro com Gemini API ou modelo local.
5. Criação de storyboard e plano de edição.
6. Renderização semiautomática com FFmpeg e Remotion/MoviePy.
7. Exportação de legenda, descrição, hashtags e versões multiplataforma.
8. Registro de métricas para aprendizado contínuo.

## Stack gratuita prioritária

- Gemini API / Google AI Studio: análise multimodal e geração de roteiro dentro da cota gratuita.
- Whisper ou whisper.cpp: transcrição local.
- FFmpeg: processamento de áudio, vídeo e legendas.
- Remotion ou MoviePy: composição programática.
- Ollama: opção de LLM local.
- ComfyUI + modelos abertos: imagens e cenas de apoio locais.
- Piper TTS: voz sintética local quando necessária.
- Google Drive: biblioteca de referências e entregáveis.
- GitHub Actions: testes e automações leves dentro da franquia disponível.

## Módulos planejados

- Reverse Engineer
- Hook Factory
- Story Architect
- Rodrigo DNA
- Viral Score
- Script Generator
- Editor Director
- Repurpose Engine
- Learning Engine

## Estrutura inicial

```text
virallab-ai/
├── README.md
├── docs/
│   ├── architecture.md
│   ├── free-tool-stack.md
│   └── product-roadmap.md
├── prompts/
│   ├── reverse-engineer.md
│   └── script-generator.md
└── schemas/
    └── video-analysis.schema.json
```

## Princípios

- Conteúdo original, inspirado em padrões, nunca cópia literal.
- Evidência e clareza acima de sensacionalismo.
- Processamento local sempre que reduzir custo e proteger dados.
- Revisão humana antes da publicação.
- Não utilizar dados clínicos identificáveis em serviços públicos de IA.

## Status

Fase 0 — arquitetura e validação do fluxo.
# ViralLab AI

Sistema de engenharia reversa e geração assistida de conteúdo curto para especialistas em saúde.

## Objetivo

Transformar vídeos de referência, ideias e conhecimento técnico em roteiros, storyboards, pacotes de edição e vídeos reproduzíveis, mantendo originalidade, identidade e credibilidade.

## Estado atual

**MVP Core v0.1 em desenvolvimento.**

Já implementado:

- brief estruturado;
- Formato 01 — Professor Cinemático;
- geração de hook, tese e cenas cronometradas;
- storyboard;
- instruções de avatar, B-roll, captura e edição;
- exportação JSON, Markdown, SRT, legenda e lista de assets;
- guardrails de privacidade e revisão científica;
- interface por linha de comando.

## Fluxo do produto

```text
Tema ou vídeo de referência
        ↓
Brief / Reverse Engineer
        ↓
Hook + tese + template
        ↓
Roteiro e storyboard
        ↓
Avatar + assets + capturas
        ↓
Renderização
        ↓
Publicação e métricas
        ↓
Learning Engine
```

## Teste local do gerador

Requer Python 3.11 ou superior.

```bash
cd virallab-ai
python -m pip install -e .
virallab "inteligência artificial na fisioterapia" \
  --duration 60 \
  --format professor_cinematico \
  --cta "Siga o Professor RP para aprender IA aplicada à saúde." \
  --output output/teste-01
```

O comando gera:

```text
output/teste-01/
├── video-package.json
├── script.md
├── captions.srt
├── caption.txt
└── asset-list.txt
```

## Pipeline planejado

1. Entrada de vídeo, áudio, transcrição ou tema.
2. Transcrição local com Whisper.
3. Análise de hook, estrutura, ritmo, cortes, visuais e CTA.
4. Geração contextual com Gemini API ou modelo local.
5. Storyboard e plano de edição.
6. Avatar opcional.
7. Renderização com FFmpeg e Remotion.
8. Exportação multiplataforma.
9. Registro de métricas para aprendizado contínuo.

## Stack gratuita prioritária

- Gemini API / Google AI Studio;
- Whisper ou whisper.cpp;
- FFmpeg;
- Remotion;
- Ollama;
- ComfyUI e modelos abertos;
- Piper TTS;
- Google Drive;
- GitHub Actions.

## Estrutura

```text
virallab-ai/
├── README.md
├── pyproject.toml
├── docs/
│   ├── architecture.md
│   ├── free-tool-stack.md
│   └── optimized-workflows.md
├── prompts/
├── schemas/
└── src/virallab/
    ├── __init__.py
    ├── cli.py
    ├── generator.py
    ├── models.py
    └── templates.py
```

## Princípios

- Conteúdo original, inspirado em padrões, nunca cópia literal.
- Evidência e clareza acima de sensacionalismo.
- Processamento local quando reduzir custo ou proteger dados.
- Revisão humana antes da publicação.
- Proibição de dados clínicos identificáveis em serviços públicos de IA.
- `video-package.json` como fonte única de verdade do processo.

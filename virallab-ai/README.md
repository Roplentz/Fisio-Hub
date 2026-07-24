# ViralLab AI

Sistema de engenharia reversa e geração assistida de conteúdo curto para especialistas em saúde.

## Objetivo

Transformar vídeos de referência, ideias e conhecimento técnico em roteiros, storyboards, pacotes de edição e vídeos reproduzíveis, mantendo originalidade, identidade e credibilidade.

## Estado atual

**MVP Core v0.2 — geração, avatar e primeiro renderizador FFmpeg.**

Já implementado:

- brief estruturado;
- Formato 01 — Professor Cinemático;
- geração local gratuita ou opcional com Gemini;
- hook, tese e cenas cronometradas;
- storyboard e plano de edição;
- manifesto de falas do avatar;
- plano de renderização 1080 × 1920;
- renderização FFmpeg com assets reais ou cartões temporários;
- exportação JSON, Markdown, SRT, legenda e lista de assets;
- guardrails de privacidade e revisão científica;
- interface por linha de comando;
- testes de fumaça do gerador e do renderizador.

## Fluxo do produto

```text
Tema ou vídeo de referência
        ↓
Brief / Reverse Engineer
        ↓
IA local ou Gemini
        ↓
Hook + tese + template
        ↓
Roteiro e storyboard
        ↓
Avatar + assets + capturas
        ↓
Renderização FFmpeg
        ↓
Publicação e métricas
        ↓
Learning Engine
```

## Instalação

Requer Python 3.11 ou superior. Para gerar o MP4, o FFmpeg também precisa estar instalado e disponível no terminal.

```bash
cd virallab-ai
python -m pip install -e .
```

## Gerar apenas o pacote

```bash
virallab "inteligência artificial na fisioterapia" \
  --provider local \
  --duration 60 \
  --format professor_cinematico \
  --cta "Siga o Professor RP para aprender IA aplicada à saúde." \
  --output output/teste-01
```

## Gerar e renderizar o vídeo

```bash
virallab "inteligência artificial na fisioterapia" \
  --provider local \
  --duration 60 \
  --format professor_cinematico \
  --cta "Siga o Professor RP para aprender IA aplicada à saúde." \
  --output output/teste-01 \
  --render
```

Quando algum asset ainda não existe, o renderizador cria um cartão temporário com o texto daquela cena. Isso permite validar duração, ritmo e sequência antes de produzir avatar e B-roll definitivos.

Para inspecionar os comandos sem executar o FFmpeg:

```bash
virallab "IA na fisioterapia" \
  --output output/teste-01 \
  --render-dry-run
```

## Assets esperados

O `render-plan.json` define os caminhos esperados. Exemplos:

```text
output/teste-01/
├── assets/
│   ├── avatar-scene-02.mp4
│   ├── avatar-scene-04.mp4
│   ├── screen-scene-05.mp4
│   └── proof-scene-06.jpg
├── generated/
├── video-package.json
├── avatar-manifest.json
├── render-plan.json
├── script.md
├── captions.srt
├── caption.txt
├── asset-list.txt
└── video-final.mp4
```

O renderizador aceita MP4, MOV, MKV, WEBM, PNG, JPG, JPEG e WEBP. Vídeos e imagens são redimensionados em modo `cover` para o formato vertical.

## Gemini opcional

Defina `GEMINI_API_KEY` e use:

```bash
virallab "IA na fisioterapia" --provider gemini --render
```

Sem chave, `--provider auto` retorna automaticamente ao provedor local.

## Arquivos gerados

```text
video-package.json
script.md
captions.srt
caption.txt
asset-list.txt
avatar-manifest.json
render-plan.json
generated/concat.txt
generated/ffmpeg-commands.json
video-final.mp4
```

## Pipeline planejado

1. Entrada de vídeo, áudio, transcrição ou tema.
2. Transcrição local com Whisper.
3. Análise de hook, estrutura, ritmo, cortes, visuais e CTA.
4. Geração contextual com Gemini API ou modelo local.
5. Storyboard e plano de edição.
6. Avatar opcional.
7. Renderização com FFmpeg e, posteriormente, Remotion.
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
├── prompts/
├── schemas/
├── tests/
└── src/virallab/
    ├── __init__.py
    ├── avatar.py
    ├── cli.py
    ├── generator.py
    ├── models.py
    ├── providers.py
    ├── renderer.py
    ├── render_plan.py
    └── templates.py
```

## Princípios

- Conteúdo original, inspirado em padrões, nunca cópia literal.
- Evidência e clareza acima de sensacionalismo.
- Processamento local quando reduzir custo ou proteger dados.
- Revisão humana antes da publicação.
- Proibição de dados clínicos identificáveis em serviços públicos de IA.
- `video-package.json` como fonte única de verdade do processo.

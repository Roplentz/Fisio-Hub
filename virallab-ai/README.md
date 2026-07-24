# ViralLab AI

Sistema de engenharia reversa e geração assistida de conteúdo curto para especialistas em saúde.

## Objetivo

Transformar vídeos de referência, ideias e conhecimento técnico em roteiros, storyboards, pacotes de edição e vídeos reproduzíveis, mantendo originalidade, identidade e credibilidade.

## Estado atual

**MVP Core v0.3 — geração, avatar, áudio, legendas e renderização FFmpeg.**

Já implementado:

- brief estruturado;
- Formato 01 — Professor Cinemático;
- geração local gratuita ou opcional com Gemini;
- hook, tese e cenas cronometradas;
- storyboard e plano de edição;
- manifesto de falas do avatar;
- plano de renderização 1080 × 1920;
- renderização FFmpeg com assets reais ou cartões temporários;
- preservação da voz dos clipes de avatar;
- silêncio técnico nos trechos sem áudio;
- trilha opcional com volume controlado;
- legendas SRT queimadas no vídeo final;
- exportação JSON, Markdown, SRT, legenda e lista de assets;
- guardrails de privacidade e revisão científica;
- interface por linha de comando;
- testes automatizados e vídeo curto de fumaça no GitHub Actions.

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
Voz + trilha + legendas
        ↓
Renderização FFmpeg
        ↓
Publicação e métricas
        ↓
Learning Engine
```

## Instalação

Requer Python 3.11 ou superior. Para gerar o MP4, FFmpeg e FFprobe precisam estar instalados e disponíveis no terminal.

```bash
cd virallab-ai
python -m pip install -e .
```

Para desenvolvimento e testes:

```bash
python -m pip install -e ".[test]"
pytest -q
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

## Gerar e renderizar o vídeo completo

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

## Adicionar a trilha

A forma mais simples é salvar a música em:

```text
output/teste-01/assets/music.mp3
```

O renderizador a encontra automaticamente e usa o volume padrão de -25 dB.

Também é possível indicar outro arquivo:

```bash
virallab "IA na fisioterapia" \
  --output output/teste-01 \
  --music caminho/para/trilha.mp3 \
  --music-level-db -27 \
  --render
```

As vozes presentes nos vídeos `avatar-scene-XX.mp4` são preservadas. Cenas sem áudio recebem uma faixa silenciosa para evitar falhas na concatenação.

## Legendas

O arquivo `captions.srt` é incorporado ao vídeo por padrão. Para exportar sem legendas queimadas:

```bash
virallab "IA na fisioterapia" \
  --output output/teste-01 \
  --no-captions \
  --render
```

## Inspecionar sem renderizar

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
│   ├── proof-scene-06.jpg
│   └── music.mp3
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
generated/segments/
generated/concat.txt
generated/stitched.mp4
generated/ffmpeg-commands.json
video-final.mp4
```

## Próximas etapas

1. Interface web para preencher o brief e revisar o roteiro.
2. Importação assistida dos vídeos gerados no HeyGen.
3. Biblioteca de trilhas e B-roll licenciados.
4. Templates visuais de legenda e identidade FisioHub.
5. Learning Engine baseado em métricas reais de publicação.

## Stack gratuita prioritária

- Gemini API / Google AI Studio;
- Whisper ou whisper.cpp;
- FFmpeg e FFprobe;
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

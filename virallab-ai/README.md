# ViralLab AI

Sistema de engenharia reversa, geração, treinamento assistido e renderização de vídeos curtos para especialistas em saúde.

## Estado atual

**MVP v0.4 — interface web didática, aprendizado local e vídeo completo.**

Já implementado:

- interface Streamlit em cinco etapas;
- brief estruturado;
- Formato 01 — Professor Cinemático;
- geração local gratuita ou opcional com Gemini;
- hook, tese, roteiro e cenas cronometradas;
- storyboard e plano de edição;
- upload guiado de avatar, imagens, capturas e música;
- renderização vertical 1080 × 1920 com FFmpeg;
- preservação da voz, trilha controlada e legendas incorporadas;
- cartões temporários para assets ausentes;
- registro transparente de feedback em JSONL;
- painel de aprovação, nota média e estilos preferidos;
- CLI, testes automatizados e vídeo de fumaça no GitHub Actions.

## Fluxo do MVP

```text
Brief
  ↓
IA local ou Gemini
  ↓
Roteiro e storyboard
  ↓
Revisão humana
  ↓
Avatar + assets + trilha
  ↓
FFmpeg + legendas
  ↓
video-final.mp4
  ↓
Feedback do criador
  ↓
Base de aprendizado JSONL
```

## Instalação da interface

Requer Python 3.11 ou superior. Para renderizar MP4, FFmpeg e FFprobe precisam estar instalados.

```bash
cd virallab-ai
python -m pip install -e ".[ui]"
streamlit run app.py
```

O navegador abrirá a interface local. O uso está dividido em:

1. **Brief** — tema, objetivo, público, duração, formato e CTA.
2. **Roteiro e cenas** — revisão do hook, tese e storyboard.
3. **Assets** — envio guiado de avatar, B-roll, imagens e trilha.
4. **Render** — geração do MP4 ou simulação dos comandos.
5. **Ensinar** — nota, aprovação, hook preferido e observações.

## Como o aprendizado funciona

O MVP não altera silenciosamente um modelo de IA. Cada decisão é registrada em:

```text
workspace/learning/feedback.jsonl
```

Cada linha contém:

- projeto e tema;
- nota do roteiro;
- aprovação ou rejeição;
- hook original;
- hook preferido;
- estilo que deve ser reforçado;
- observações do criador;
- data e hora.

Essa base poderá alimentar futuramente:

- exemplos nos prompts;
- ranking de hooks;
- regras do DNA Rodrigo;
- avaliação automática de roteiros;
- fine-tuning ou RAG, quando houver volume e qualidade suficientes.

## Workspace

```text
workspace/
├── projects/
│   └── <project-id>/
│       ├── assets/
│       ├── generated/
│       ├── video-package.json
│       ├── avatar-manifest.json
│       ├── render-plan.json
│       ├── captions.srt
│       └── video-final.mp4
└── learning/
    └── feedback.jsonl
```

## Uso pela linha de comando

Gerar e renderizar:

```bash
virallab "inteligência artificial na fisioterapia" \
  --provider local \
  --duration 60 \
  --format professor_cinematico \
  --cta "Siga o Professor RP para aprender IA aplicada à saúde." \
  --output output/teste-01 \
  --render
```

Trilha opcional:

```bash
virallab "IA na fisioterapia" \
  --output output/teste-01 \
  --music caminho/para/trilha.mp3 \
  --music-level-db -27 \
  --render
```

Sem legendas incorporadas:

```bash
virallab "IA na fisioterapia" --no-captions --render
```

Simular sem executar o FFmpeg:

```bash
virallab "IA na fisioterapia" --render-dry-run
```

## Assets esperados

O `render-plan.json` define os nomes. Exemplos:

```text
assets/
├── avatar-scene-02.mp4
├── avatar-scene-04.mp4
├── screen-scene-05.mp4
├── proof-scene-06.jpg
└── music.mp3
```

O renderizador aceita MP4, MOV, MKV, WEBM, PNG, JPG, JPEG e WEBP. Materiais são ajustados em modo `cover` para 9:16.

## Gemini opcional

Defina `GEMINI_API_KEY` e selecione Gemini na interface ou execute:

```bash
virallab "IA na fisioterapia" --provider gemini --render
```

Sem chave, o modo `auto` retorna ao provedor local.

## Desenvolvimento e testes

```bash
python -m pip install -e ".[all]"
pytest -q
python -m py_compile app.py
```

## Próximas etapas

1. Aplicar automaticamente os exemplos aprovados aos prompts.
2. Importar vídeos do HeyGen com associação automática às cenas.
3. Criar biblioteca licenciada de trilhas e B-roll.
4. Adicionar templates visuais da identidade FisioHub.
5. Conectar métricas reais de Instagram, TikTok e YouTube ao Learning Engine.

## Princípios

- Conteúdo original, inspirado em padrões, nunca cópia literal.
- Evidência e clareza acima de sensacionalismo.
- Processamento local quando reduzir custo ou proteger dados.
- Revisão humana antes da publicação.
- Proibição de dados clínicos identificáveis em serviços públicos de IA.
- Aprendizado auditável: nenhuma preferência é alterada sem registro.
- `video-package.json` permanece a fonte única de verdade da produção.

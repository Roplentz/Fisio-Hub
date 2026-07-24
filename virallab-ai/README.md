# RP ViralLab Studio

Sistema de engenharia reversa, geração assistida e produção de vídeos curtos para especialistas em saúde.

## Estado atual

**MVP v0.5 — front-end RP, aprendizado auditável e renderização completa.**

O ViralLab transforma um tema em:

- brief estruturado;
- hook e tese;
- roteiro e storyboard;
- manifesto de falas do avatar;
- plano de produção;
- vídeo vertical 1080 × 1920;
- voz, trilha e legendas;
- registro do feedback editorial no DNA RP.

## Interface RP

A interface foi desenhada para uso diário, sem exigir domínio técnico. Ela possui cinco áreas:

1. **Estratégia** — tema, público, objetivo, duração, formato e nível de evidência.
2. **Roteiro** — hook, tese, storyboard, cenas e download do pacote.
3. **Produção** — upload guiado do avatar, capturas, provas e trilha.
4. **Render** — prévia ou geração do MP4 final com FFmpeg.
5. **DNA RP** — avaliação, aprovação, estilo preferido e memória editorial.

A identidade utiliza fundo azul-marinho escuro, acento ciano, detalhes dourados e o monograma RP. A marca gráfica oficial poderá substituir o monograma sem alterar o fluxo.

## Executar a interface

Requer Python 3.11 ou superior. Para renderizar, FFmpeg e FFprobe devem estar instalados.

```bash
cd virallab-ai
python -m pip install -e ".[ui]"
streamlit run app.py
```

Para instalar também os testes:

```bash
python -m pip install -e ".[all]"
pytest -q
```

## Fluxo visual

```text
Estratégia
    ↓
Roteiro e storyboard
    ↓
Produção dos materiais
    ↓
Renderização
    ↓
Avaliação editorial
    ↓
DNA RP
```

## Aprendizado transparente

Cada avaliação é salva localmente em:

```text
workspace/learning/feedback.jsonl
```

Os registros incluem tema, nota, aprovação, hook original, hook preferido, direção editorial, observações, projeto e data.

Nesta fase, o sistema não modifica um modelo silenciosamente. A base será utilizada para:

- enriquecer os prompts;
- selecionar exemplos semelhantes;
- ranquear hooks;
- consolidar o DNA Rodrigo;
- criar avaliações automáticas;
- futuramente sustentar RAG ou fine-tuning.

## Estrutura de um projeto

```text
workspace/
├── projects/
│   └── <project_id>/
│       ├── assets/
│       ├── generated/
│       ├── video-package.json
│       ├── script.md
│       ├── captions.srt
│       ├── avatar-manifest.json
│       ├── render-plan.json
│       └── video-final.mp4
└── learning/
    └── feedback.jsonl
```

## Modos de IA

- `local`: gratuito, determinístico e sem internet;
- `gemini`: geração contextual com `GEMINI_API_KEY`;
- `auto`: usa Gemini quando configurado e retorna ao modo local quando não estiver.

## CLI

```bash
virallab "IA na fisioterapia" \
  --provider local \
  --duration 60 \
  --format professor_cinematico \
  --cta "Siga o Professor RP para aprender IA aplicada à saúde." \
  --output output/teste-01 \
  --render
```

## Princípios

- conteúdo original, inspirado em padrões, nunca cópia literal;
- evidência e clareza acima de sensacionalismo;
- revisão humana antes da publicação;
- processamento local quando reduzir custo ou proteger dados;
- proibição de dados clínicos identificáveis em serviços públicos de IA;
- aprendizado auditável e reversível;
- `video-package.json` como fonte única de verdade do processo.

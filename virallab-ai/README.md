# RP ViralLab Studio

Sistema de análise, geração assistida e produção de vídeos curtos para especialistas em saúde.

## Estado do produto

O código atual representa a base funcional do Studio 2.0. A direção oficial para a próxima evolução está consolidada em [ViralLab Studio 3.0 — Diretrizes de Produto](docs/DIRETRIZES_PRODUTO_V3.md).

> Importante: uma função descrita no roadmap não deve ser apresentada como disponível até estar implementada, testada e promovida para `production`.

## Fluxo oficial da versão 3.0

1. **Analisar vídeo** *(opcional)*
2. **Estratégia**
3. **Roteiro**
4. **Avatar IA — Imagem Mestre**
5. **Voz**
6. **Criativos**
7. **Render**
8. **Publicação**
9. **Aprendizado**

O usuário pode começar por um vídeo de referência ou criar do zero.

## Decisão central: Avatar IA

A Imagem Mestre deve ser criada com apenas três fotos autorizadas do usuário:

- frente;
- lado esquerdo;
- lado direito.

O fluxo inclui validação dos ângulos, geração da Imagem Mestre, aprovação explícita, reutilização entre projetos e exclusão das referências. Na primeira implementação, trata-se de geração orientada por referências, não de uma promessa de treinamento biométrico ou clonagem perfeita.

## Capacidades da base atual

- análise de vídeo por upload ou URL;
- brief, hook, tese, roteiro e storyboard;
- cenas com narração, texto e direção visual;
- perfil visual de referência;
- gravação ou upload de voz;
- geração e aprovação de criativos;
- renderização vertical com voz, trilha e legendas;
- feedback editorial e aprendizado auditável.

## Executar localmente

Requer Python 3.11 ou superior. Para renderizar, FFmpeg e FFprobe devem estar instalados.

```bash
cd virallab-ai
python -m pip install -e ".[ui]"
streamlit run app.py
```

## Testar a interface web

O Fisio IA Creator Web usa o motor real de roteiro, segurança clínica e
créditos do ViralLab, sem dependências web externas:

```bash
cd virallab-ai/web-demo
python -m pip install -e ..
virallab-web
```

Abra `http://localhost:8080`. A geração usa o provider `auto` (Gemini,
Ollama ou fallback local), executa a revisão clínica e registra o consumo no
ledger SQLite. A prévia visual ainda não produz o arquivo MP4 e nenhuma
operação publica conteúdo automaticamente.

Para instalar também os testes:

```bash
python -m pip install -e ".[all]"
pytest -q
```

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

O `video-package.json` é a fonte única de verdade do processo. Mudanças de esquema devem ser versionadas e acompanhadas de migração para projetos existentes.

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

## Qualidade e publicação

Fluxo recomendado:

```text
branch de trabalho
→ Pull Request
→ ViralLab Guardian verde
→ main
→ Release Gate
→ production
```

O Streamlit de produção deve acompanhar `production`. Alterações não validadas não devem chegar ao aplicativo publicado.

## Princípios

- conteúdo original, inspirado em padrões, nunca cópia literal;
- evidência e clareza acima de sensacionalismo;
- revisão humana antes da publicação;
- consentimento explícito para uso de rosto e voz;
- exclusão e substituição das referências pessoais;
- processamento local quando reduzir custo ou proteger dados;
- proibição de dados clínicos identificáveis em serviços públicos de IA;
- aprendizado auditável e reversível;
- segredos nunca armazenados no repositório.

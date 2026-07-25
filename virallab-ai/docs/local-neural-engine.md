# Motor neural local gratuito

O ViralLab pode usar Ollama como camada local gratuita para geração e memória semântica.

## Modelos

- roteiro e storyboard: `qwen3:4b`
- embeddings do DNA RP: `bge-m3`

## Instalação local

1. Instale o Ollama no Windows, macOS ou Linux.
2. Baixe os modelos:

```bash
ollama pull qwen3:4b
ollama pull bge-m3
```

3. Inicie o servidor:

```bash
ollama serve
```

4. Configure o ViralLab:

```bash
OLLAMA_BASE_URL=http://localhost:11434
VIRALLAB_OLLAMA_MODEL=qwen3:4b
VIRALLAB_EMBEDDING_MODEL=bge-m3
```

## Cadeia automática

No modo `auto`, o ViralLab tenta:

1. Gemini;
2. Qwen3 via Ollama;
3. regras locais determinísticas.

Quando BGE-M3 está disponível, os feedbacks do DNA RP são recuperados por similaridade semântica. Sem o servidor local, o sistema volta automaticamente para similaridade lexical.

## Streamlit Cloud

`localhost` aponta para o servidor do Streamlit, não para o computador do usuário. Para usar Ollama em uma implantação hospedada, configure `OLLAMA_BASE_URL` com um endpoint privado acessível pela aplicação. Não exponha o Ollama diretamente na internet sem autenticação, TLS e controle de acesso.

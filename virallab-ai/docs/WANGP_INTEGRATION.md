# Integração WanGP no RP ViralLab Studio

## Objetivo

Usar uma instalação local do WanGP como motor opcional de geração de vídeos por cena. O ViralLab continua responsável por estratégia, roteiro, aprovação dos assets, voz, legendas e renderização final com FFmpeg.

O WanGP deve rodar em um computador ou worker com GPU. Ele não é instalado dentro do Streamlit Cloud.

## Variáveis de ambiente

```env
WANGP_ROOT=C:\WanGP
WANGP_OUTPUT_DIR=C:\WanGP\outputs
WANGP_MODEL=ltx2_22B_distilled
WANGP_CLI_ARGS=--attention sdpa --profile 4
```

`WANGP_ROOT` é obrigatória. As outras variáveis têm valores padrão.

## Fluxo de uso

1. Instale e teste o WanGP no computador com GPU.
2. Configure as variáveis `WANGP_*` antes de iniciar o ViralLab.
3. Abra o ViralLab e gere estratégia, roteiro e storyboard.
4. No menu de páginas do Streamlit, abra **Criativos WanGP**.
5. Escolha resolução, passos de inferência e duração.
6. Edite o prompt de cada cena e clique em **Gerar vídeo com WanGP**.
7. Revise a candidata e clique em **Aprovar**.
8. Volte à etapa **Render** do Studio para montar o Reel final.

A aprovação usa a `AssetLibrary` existente. Isso copia o clipe para `assets/visual-scene-XX.mp4` e atualiza o `render-plan.json` automaticamente.

## Arquitetura

```text
RP ViralLab / Streamlit
        |
        | WanGPProvider
        v
WanGP Python API (shared.api)
        |
        | geração local na GPU
        v
Arquivo MP4 da cena
        |
        | AssetLibrary
        v
render-plan.json + FFmpeg
        |
        v
Reel final
```

## API Python

```python
from virallab.wangp_provider import WanGPProvider

provider = WanGPProvider()
video = provider.generate_video(
    prompt="Clínica de fisioterapia futurista, linguagem cinematográfica",
    duration_seconds=4,
    resolution="704x1280",
    num_inference_steps=8,
)
```

Para registrar diretamente na biblioteca do projeto:

```python
record = provider.generate_scene_asset(
    project_dir,
    scene,
    prompt=prompt,
)
```

## Imagem Mestre como referência

A página permite usar a Imagem Mestre aprovada como quadro inicial para cenas do avatar. O provider envia o caminho em `image_start` para o WanGP.

A preservação de identidade depende do modelo e do finetune selecionados. A revisão humana continua obrigatória.

## Segurança operacional

- Não exponha o servidor MCP ou a API do WanGP diretamente à internet sem autenticação e proxy reverso.
- Use somente modelos e checkpoints de fontes confiáveis.
- Mantenha o WanGP e seus modelos fora do repositório do ViralLab.
- Não envie imagens de pacientes ou dados clínicos identificáveis para geração.
- A interface informa que utiliza WanGP, conforme os termos do projeto original.

## Testes

Os testes unitários usam um runtime simulado e não baixam modelos nem exigem GPU:

```bash
cd virallab-ai
pytest tests/test_wangp_provider.py
```

O teste real precisa ser executado na máquina com GPU, WanGP instalado e ao menos um modelo disponível.

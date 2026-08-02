# Integração WanGP no RP ViralLab

O WanGP é um runtime opcional e separado. O ViralLab não instala modelos, CUDA ou PyTorch no Streamlit Cloud. A geração acontece em um computador com GPU e o arquivo retornado entra na biblioteca de assets do projeto.

## Configuração

Instale o WanGP em uma pasta local e defina:

```env
WANGP_ROOT=C:\WanGP
WANGP_OUTPUT_DIR=C:\WanGP\outputs
WANGP_MODEL=ltx2_22B_distilled
WANGP_CLI_ARGS=--attention sdpa --profile 4
```

No Linux, use caminhos equivalentes.

## Uso por código

```python
from virallab.wangp_provider import WanGPProvider

provider = WanGPProvider()
video = provider.generate_video(
    prompt="Fisioterapeuta em clínica moderna usando inteligência artificial, vertical 9:16",
    duration_seconds=4,
    resolution="704x1280",
)
print(video)
```

## Uso como asset de uma cena

```python
record = provider.generate_scene_asset(
    project_dir,
    scene,
    prompt=scene_prompt,
)
```

O arquivo é copiado para `visual-assets/scene-XX/` e registrado no `manifest.json`. Depois da aprovação pela `AssetLibrary`, o renderizador atual passa a utilizar o vídeo no `render-plan.json`.

## Princípios da integração

- WanGP continua sendo instalação opcional.
- A sessão é mantida em memória para evitar recarregar o modelo a cada cena.
- Erros de GPU e geração são convertidos em `WanGPError` legível.
- O ViralLab continua funcional sem WanGP.
- A interface e a documentação do produto devem informar claramente que a geração local usa WanGP, conforme os termos do projeto.

## Próxima etapa

Adicionar na tela **Criativos** o seletor `Gemini imagem | WanGP vídeo local | Upload`, barra de progresso e botão para cancelar uma geração ativa.

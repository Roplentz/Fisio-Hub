"""Ponto de entrada estático do RP ViralLab Studio 3.0.

O Streamlit Cloud executa este arquivo diretamente. O Studio é carregado como
um módulo Python normal, com navegação e renderização configuradas por chamadas
explícitas — sem leitura dinâmica de código ou substituição de widgets.
"""

from __future__ import annotations

from virallab.quality_patch import install_quality_patch

install_quality_patch()

import app_v3  # noqa: E402,F401  # O módulo renderiza a aplicação ao ser importado.

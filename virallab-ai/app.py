"""Ponto de entrada estático do RP ViralLab Studio 3.0.

O Streamlit Cloud executa este arquivo diretamente. O Studio é carregado como
um módulo Python normal; navegação e qualidade visual são implementadas nos
módulos responsáveis, sem alteração de funções em tempo de execução.
"""

from __future__ import annotations

import app_v3  # noqa: F401  # O módulo renderiza a aplicação ao ser importado.

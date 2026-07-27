"""Ponto de entrada estático do RP ViralLab Studio 3.0.

O Streamlit Cloud executa este arquivo diretamente. O Studio é carregado como
um módulo Python normal: não há leitura, alteração ou execução dinâmica de
código-fonte no processo de inicialização.
"""

from __future__ import annotations

import streamlit as st

from virallab.quality_patch import install_quality_patch
from virallab.streamlit_navigation import install_safe_step_selectbox

install_quality_patch()
original_selectbox = install_safe_step_selectbox(st)

try:
    import app_v3  # noqa: F401  # O módulo renderiza a aplicação ao ser importado.
finally:
    st.selectbox = original_selectbox

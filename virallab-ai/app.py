"""Ponto de entrada do RP ViralLab Studio 3.0.

O Streamlit Cloud executa este arquivo diretamente. A interface principal fica em
``app_v3.py`` e é executada no mesmo contexto de script para que chamadas como
``st.set_page_config`` e os componentes visuais sejam renderizados corretamente.
"""

from __future__ import annotations

import runpy
from pathlib import Path

import streamlit as st

from virallab.streamlit_navigation import install_safe_step_selectbox

original_selectbox = install_safe_step_selectbox(st)
try:
    runpy.run_path(str(Path(__file__).with_name("app_v3.py")), run_name="__main__")
finally:
    st.selectbox = original_selectbox

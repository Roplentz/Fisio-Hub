"""Ponto de entrada estável do RP ViralLab Studio 3.0.

O Streamlit Cloud executa este arquivo diretamente. As correções de qualidade,
navegação e voz são instaladas antes da execução do Studio, sem substituir
``st.set_page_config`` nem criar widgets durante a configuração da página.
"""

from __future__ import annotations

from pathlib import Path

import streamlit as st

from virallab.quality_patch import install_quality_patch
from virallab.streamlit_navigation import install_safe_step_selectbox
from virallab.studio_source_patch import install_studio_extensions

install_quality_patch()
original_selectbox = install_safe_step_selectbox(st)

try:
    studio_path = Path(__file__).with_name("app_v3.py")
    studio_source = install_studio_extensions(studio_path.read_text(encoding="utf-8"))
    exec(
        compile(studio_source, str(studio_path), "exec"),
        {"__name__": "__main__", "__file__": str(studio_path)},
    )
finally:
    st.selectbox = original_selectbox

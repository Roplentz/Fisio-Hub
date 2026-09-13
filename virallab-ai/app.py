"""Entrypoint estável do RP ViralLab Studio para Streamlit Cloud."""

from __future__ import annotations

import streamlit as st

from virallab.quality_patch import install_quality_patch
from virallab.streamlit_navigation import install_safe_step_selectbox

install_quality_patch()
_original_selectbox = install_safe_step_selectbox(st)

try:
    # O Studio agora é um módulo normal: sem leitura, substituição ou exec de
    # código-fonte em tempo de execução.
    import app_v3  # noqa: F401
finally:
    st.selectbox = _original_selectbox

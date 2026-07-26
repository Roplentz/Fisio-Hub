"""Ponto de entrada estável do RP ViralLab Studio 3.0.

O Streamlit Cloud executa este arquivo diretamente. A aplicação real permanece em
``app_v3.py`` durante a migração gradual para ``src/virallab/ui``.

Esta versão remove a execução dinâmica com ``exec()/compile()`` e a injeção de
código-fonte. O adaptador temporário de navegação é mantido apenas para preservar
a compatibilidade dos botões atuais até que ``app_v3.py`` use uma chave de widget
separada de ``studio_step``.
"""

from __future__ import annotations

import streamlit as st

from virallab.streamlit_navigation import install_safe_step_selectbox

_original_selectbox = install_safe_step_selectbox(st)
try:
    import app_v3  # noqa: F401,E402
finally:
    st.selectbox = _original_selectbox

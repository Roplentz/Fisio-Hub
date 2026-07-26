"""Ponto de entrada do RP ViralLab Studio 3.0.

O Streamlit Cloud executa este arquivo diretamente. A interface principal fica em
``app_v3.py`` e é executada no mesmo contexto de script para que chamadas como
``st.set_page_config`` e os componentes visuais sejam renderizados corretamente.
"""

from __future__ import annotations

import os
from pathlib import Path

import streamlit as st

from virallab.quality_patch import install_quality_patch
from virallab.streamlit_navigation import install_safe_step_selectbox
from virallab.studio_source_patch import install_voice_ui
from virallab.visual_quality import PRESETS

install_quality_patch()
original_selectbox = install_safe_step_selectbox(st)
original_page_config = st.set_page_config


def set_page_config_with_quality_controls(*args, **kwargs):
    result = original_page_config(*args, **kwargs)
    labels = {key: preset.label for key, preset in PRESETS.items()}
    current = os.getenv("VIRALLAB_CAPTION_STYLE", "educational")
    if current not in labels:
        current = "educational"
    with st.sidebar.expander("🎨 Qualidade visual", expanded=False):
        style = st.selectbox(
            "Estilo de legendas",
            options=list(labels),
            index=list(labels).index(current),
            format_func=lambda key: labels[key],
            key="quality_caption_style",
            help="Controla fonte, tamanho, contraste, margens e zona segura no vídeo final.",
        )
        brand = st.text_input(
            "Assinatura discreta",
            value=os.getenv("VIRALLAB_BRAND_TEXT", "Prof. Dr. Rodrigo Plentz"),
            key="quality_brand_text",
            help="Deixe vazio para não exibir assinatura.",
        )
        st.caption(
            "O estilo é aplicado aos textos por cena e às legendas incorporadas."
        )
    os.environ["VIRALLAB_CAPTION_STYLE"] = style
    os.environ["VIRALLAB_BRAND_TEXT"] = brand.strip()
    return result


st.set_page_config = set_page_config_with_quality_controls
try:
    studio_path = Path(__file__).with_name("app_v3.py")
    studio_source = install_voice_ui(studio_path.read_text(encoding="utf-8"))
    exec(compile(studio_source, str(studio_path), "exec"), {"__name__": "__main__"})
finally:
    st.selectbox = original_selectbox
    st.set_page_config = original_page_config

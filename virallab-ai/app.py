"""Ponto de entrada do RP ViralLab Studio 3.0.

O Streamlit Cloud executa este arquivo diretamente. A aplicação real permanece em
``app_v3.py`` enquanto a migração gradual para ``src/virallab/ui`` é concluída.
Não há execução dinâmica de código nem monkey-patches globais.
"""

from __future__ import annotations

# A importação executa a aplicação Streamlit declarada em app_v3.py.
# Manter o entrypoint mínimo evita duplicação de UI e, principalmente, remove
# o uso anterior de exec()/compile() e alterações globais no Streamlit.
import app_v3  # noqa: F401,E402

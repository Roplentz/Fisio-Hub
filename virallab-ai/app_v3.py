"""Fachada explícita do RP ViralLab Studio 3.0.

Importar este módulo não renderiza a interface. O runtime do Streamlit só é
carregado quando :func:`main` é chamado pelo entrypoint oficial.
"""

from __future__ import annotations

import importlib
import sys

_RUNTIME_MODULE = "studio_runtime"


def main() -> None:
    """Carrega o runtime do Studio exatamente uma vez por execução."""
    if _RUNTIME_MODULE in sys.modules:
        importlib.reload(sys.modules[_RUNTIME_MODULE])
    else:
        importlib.import_module(_RUNTIME_MODULE)


__all__ = ["main"]

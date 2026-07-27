"""Inicialização controlada da aplicação Streamlit do ViralLab."""

from __future__ import annotations

import importlib
import sys
from types import ModuleType

RUNTIME_MODULE = "studio_runtime"


def load_runtime(module_name: str = RUNTIME_MODULE) -> ModuleType:
    """Importa ou recarrega o runtime solicitado.

    A função mantém o comportamento histórico do Streamlit, mas concentra o
    carregamento em uma fronteira única e testável. As próximas etapas da
    modularização poderão substituir o módulo monolítico sem alterar o
    entrypoint público.
    """
    existing = sys.modules.get(module_name)
    if existing is not None:
        return importlib.reload(existing)
    return importlib.import_module(module_name)


def run_studio() -> None:
    """Executa a interface do Studio."""
    load_runtime()


__all__ = ["RUNTIME_MODULE", "load_runtime", "run_studio"]

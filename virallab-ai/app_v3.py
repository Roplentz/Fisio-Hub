"""Fachada pública do RP ViralLab Studio 3.0.

Importar este módulo não renderiza a interface. O entrypoint oficial chama
:func:`main`, que delega a inicialização ao pacote modular ``virallab.studio``.
"""

from __future__ import annotations

from virallab.studio import run_studio


def main() -> None:
    """Executa o Studio por meio da fronteira modular da aplicação."""
    run_studio()


__all__ = ["main"]

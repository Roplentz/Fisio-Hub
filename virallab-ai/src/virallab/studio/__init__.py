"""Núcleo modular do RP ViralLab Studio.

A API pública deste pacote expõe somente :func:`run_studio`. As etapas da
interface serão migradas gradualmente para este namespace sem alterar o
entrypoint externo.
"""

from .application import run_studio

__all__ = ["run_studio"]

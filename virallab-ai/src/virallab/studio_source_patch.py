from __future__ import annotations


VOICE_START = "def render_voice(package, package_path: Path) -> None:\n"
VOICE_END = "\ndef render_creatives(package, package_path: Path) -> None:\n"


def install_voice_ui(source: str) -> str:
    """Substitui a tela legada de voz sem duplicar todo o Studio 3.0.

    O app principal já usa um ponto de entrada compatível para aplicar correções
    isoladas. Esta função mantém a alteração pequena e falha de forma explícita
    caso a estrutura esperada do Studio seja modificada.
    """
    start = source.find(VOICE_START)
    end = source.find(VOICE_END)
    if start < 0 or end < 0 or end <= start:
        raise RuntimeError("Não foi possível localizar a etapa de voz no Studio 3.0.")
    replacement = (
        "def render_voice(package, package_path: Path) -> None:\n"
        "    from virallab.voice_ui import render_voice as render_voice_engine\n"
        "    render_voice_engine(st, package, package_path)\n\n"
    )
    return source[:start] + replacement + source[end + 1 :]


__all__ = ["install_voice_ui"]

"""Navegação explícita entre as etapas do Studio."""

from __future__ import annotations

from collections.abc import MutableMapping
from typing import Any

from .state import LOGICAL_STEP_KEY, WIDGET_STEP_KEY

STEPS = {
    "analysis": "01 · Analisar vídeo",
    "strategy": "02 · Estratégia",
    "script": "03 · Roteiro",
    "avatar": "04 · Avatar IA",
    "voice": "05 · Voz",
    "creatives": "06 · Criativos",
    "render": "07 · Render",
    "publication": "08 · Publicação",
    "learning": "09 · Aprendizado",
}


def sync_step_from_widget(state: MutableMapping[str, Any]) -> None:
    state[LOGICAL_STEP_KEY] = state[WIDGET_STEP_KEY]


def prepare_widget_step(state: MutableMapping[str, Any]) -> None:
    logical_step = state[LOGICAL_STEP_KEY]
    if state.get(WIDGET_STEP_KEY) != logical_step:
        state[WIDGET_STEP_KEY] = logical_step


def progress_value(state: MutableMapping[str, Any]) -> float:
    index = list(STEPS).index(state[LOGICAL_STEP_KEY])
    return (index + 1) / len(STEPS)


def render_step_selector(st_module: Any, state: MutableMapping[str, Any]) -> str:
    """Renderiza o seletor sem acoplar a lógica ao módulo global do Streamlit."""
    prepare_widget_step(state)

    def on_change() -> None:
        sync_step_from_widget(state)

    selected = st_module.selectbox(
        "Etapa do projeto",
        options=list(STEPS),
        format_func=lambda key: STEPS[key],
        key=WIDGET_STEP_KEY,
        on_change=on_change,
    )
    state[LOGICAL_STEP_KEY] = selected
    return selected


__all__ = [
    "STEPS",
    "prepare_widget_step",
    "progress_value",
    "render_step_selector",
    "sync_step_from_widget",
]

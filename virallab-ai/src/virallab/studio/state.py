"""Estado de sessão do Studio, independente da implementação da UI."""

from __future__ import annotations

import uuid
from collections.abc import MutableMapping
from typing import Any

LOGICAL_STEP_KEY = "studio_step"
WIDGET_STEP_KEY = "_studio_step_selector"


def default_state() -> dict[str, Any]:
    """Cria os valores iniciais para uma nova sessão."""
    return {
        "project_id": uuid.uuid4().hex[:10],
        "package": None,
        "package_dir": None,
        "preferred_hook": "",
        LOGICAL_STEP_KEY: "analysis",
        WIDGET_STEP_KEY: "analysis",
        "pending_video_path": None,
        "pending_video_name": None,
        "pending_video_source": None,
        "avatar_candidate": None,
    }


def initialize_state(state: MutableMapping[str, Any]) -> None:
    """Preenche somente chaves ainda ausentes na sessão."""
    for key, value in default_state().items():
        state.setdefault(key, value)


def set_step(state: MutableMapping[str, Any], step: str) -> None:
    state[LOGICAL_STEP_KEY] = step


def reset_project(state: MutableMapping[str, Any]) -> None:
    """Reinicia os dados do projeto sem apagar preferências globais da sessão."""
    state["project_id"] = uuid.uuid4().hex[:10]
    state["package"] = None
    state["package_dir"] = None
    state["preferred_hook"] = ""
    state["avatar_candidate"] = None
    set_step(state, "analysis")


__all__ = [
    "LOGICAL_STEP_KEY",
    "WIDGET_STEP_KEY",
    "default_state",
    "initialize_state",
    "reset_project",
    "set_step",
]

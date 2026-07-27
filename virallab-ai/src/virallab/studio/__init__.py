"""Núcleo modular do RP ViralLab Studio."""

from .application import run_studio
from .navigation import STEPS
from .paths import DEFAULT_PATHS, StudioPaths
from .state import LOGICAL_STEP_KEY, WIDGET_STEP_KEY

__all__ = [
    "DEFAULT_PATHS",
    "LOGICAL_STEP_KEY",
    "STEPS",
    "StudioPaths",
    "WIDGET_STEP_KEY",
    "run_studio",
]

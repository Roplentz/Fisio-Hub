"""Etapas modulares da interface do RP ViralLab Studio."""

from .analysis import AnalysisAction, render_analysis
from .avatar import AvatarAction, AvatarResult, render_avatar
from .script import ScriptResult, render_script
from .strategy import StrategyResult, render_strategy
from .voice import VoiceAction, VoiceResult, render_voice

__all__ = [
    "AnalysisAction",
    "AvatarAction",
    "AvatarResult",
    "ScriptResult",
    "StrategyResult",
    "VoiceAction",
    "VoiceResult",
    "render_analysis",
    "render_avatar",
    "render_script",
    "render_strategy",
    "render_voice",
]

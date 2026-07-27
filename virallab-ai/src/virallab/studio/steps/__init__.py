"""Etapas modulares da interface do RP ViralLab Studio."""

from .analysis import AnalysisAction, render_analysis
from .avatar import AvatarAction, AvatarResult, render_avatar
from .creatives import CreativesAction, CreativesResult, render_creatives
from .render import RenderAction, RenderResult, render_output
from .script import ScriptResult, render_script
from .strategy import StrategyResult, render_strategy
from .voice import VoiceAction, VoiceResult, render_voice

__all__ = [
    "AnalysisAction",
    "AvatarAction",
    "AvatarResult",
    "CreativesAction",
    "CreativesResult",
    "RenderAction",
    "RenderResult",
    "ScriptResult",
    "StrategyResult",
    "VoiceAction",
    "VoiceResult",
    "render_analysis",
    "render_avatar",
    "render_creatives",
    "render_output",
    "render_script",
    "render_strategy",
    "render_voice",
]

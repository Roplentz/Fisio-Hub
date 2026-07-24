from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Literal

VideoFormat = Literal[
    "professor_cinematico",
    "lista_demonstrativa",
    "narrativo",
    "tutorial",
    "case_clinico",
]


@dataclass
class VideoBrief:
    theme: str
    objective: str = "ganhar seguidores qualificados"
    audience: str = "fisioterapeutas brasileiros"
    duration_seconds: int = 60
    format: VideoFormat = "professor_cinematico"
    cta: str = "Siga o perfil para aprender mais."
    evidence_level: Literal["educacional", "cientifico", "opiniao"] = "educacional"
    avatar_name: str = "Professor RP"


@dataclass
class Scene:
    index: int
    start: float
    end: float
    scene_type: Literal["avatar", "title_card", "broll", "screen_capture", "proof"]
    narration: str
    on_screen_text: str = ""
    visual_direction: str = ""
    edit_direction: str = ""
    asset_query: str = ""


@dataclass
class VideoPackage:
    brief: VideoBrief
    hook: str
    thesis: str
    scenes: list[Scene] = field(default_factory=list)
    caption: str = ""
    hashtags: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

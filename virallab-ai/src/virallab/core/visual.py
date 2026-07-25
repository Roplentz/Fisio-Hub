from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any
from uuid import uuid4


class AssetKind(str, Enum):
    IMAGE = "image"
    VIDEO = "video"
    BROLL = "broll"
    ICON = "icon"
    GRAPHIC = "graphic"
    SCREENSHOT = "screenshot"
    AUDIO = "audio"
    OVERLAY = "overlay"


class AssetStatus(str, Enum):
    SUGGESTED = "suggested"
    GENERATED = "generated"
    SELECTED = "selected"
    APPROVED = "approved"
    REJECTED = "rejected"


@dataclass
class VisualScore:
    script_alignment: int = 0
    visual_impact: int = 0
    retention_potential: int = 0
    originality: int = 0
    brand_consistency: int = 0
    rationale: str = ""

    def normalized(self) -> "VisualScore":
        for name in (
            "script_alignment",
            "visual_impact",
            "retention_potential",
            "originality",
            "brand_consistency",
        ):
            setattr(self, name, max(0, min(100, int(getattr(self, name)))))
        return self


@dataclass
class PromptBundle:
    canonical: str = ""
    flux: str = ""
    imagen: str = ""
    ideogram: str = ""
    midjourney: str = ""
    veo: str = ""
    runway: str = ""
    kling: str = ""
    negative_prompt: str = ""


@dataclass
class Moodboard:
    name: str = ""
    concept: str = ""
    palette: list[str] = field(default_factory=list)
    typography: list[str] = field(default_factory=list)
    lighting: str = ""
    texture: str = ""
    composition: str = ""
    references: list[str] = field(default_factory=list)


@dataclass
class VisualAsset:
    kind: AssetKind
    title: str
    id: str = field(default_factory=lambda: f"asset_{uuid4().hex[:12]}")
    provider: str = ""
    prompt: str = ""
    url: str = ""
    local_file: str = ""
    thumbnail: str = ""
    license: str = ""
    status: AssetStatus = AssetStatus.SUGGESTED
    score: VisualScore = field(default_factory=VisualScore)
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class VisualPlan:
    scene_id: str
    creative_intent: str = ""
    main_visual: str = ""
    setting: str = ""
    characters: list[str] = field(default_factory=list)
    props: list[str] = field(default_factory=list)
    broll: list[str] = field(default_factory=list)
    icons: list[str] = field(default_factory=list)
    graphics: list[str] = field(default_factory=list)
    palette: list[str] = field(default_factory=list)
    typography: list[str] = field(default_factory=list)
    shot: str = ""
    angle: str = ""
    camera_movement: str = ""
    lighting: str = ""
    transition: str = ""
    motion_notes: str = ""
    prompts: PromptBundle = field(default_factory=PromptBundle)
    moodboard: Moodboard = field(default_factory=Moodboard)
    assets: list[VisualAsset] = field(default_factory=list)
    score: VisualScore = field(default_factory=VisualScore)
    continuity_notes: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

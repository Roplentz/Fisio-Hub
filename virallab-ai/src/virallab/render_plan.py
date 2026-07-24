from __future__ import annotations

from dataclasses import asdict, dataclass

from .models import VideoPackage


@dataclass
class RenderLayer:
    scene_index: int
    start: float
    end: float
    source_type: str
    source: str
    fit: str = "cover"
    transition: str = "cut"
    overlay_text: str = ""


def build_render_plan(package: VideoPackage) -> dict[str, object]:
    layers: list[RenderLayer] = []
    for scene in package.scenes:
        source_type, source = _source_for_scene(scene.scene_type, scene.index, scene.asset_query)
        layers.append(
            RenderLayer(
                scene_index=scene.index,
                start=scene.start,
                end=scene.end,
                source_type=source_type,
                source=source,
                transition=_transition_for(scene.edit_direction),
                overlay_text=scene.on_screen_text,
            )
        )

    return {
        "canvas": {"width": 1080, "height": 1920, "fps": 30},
        "duration_seconds": package.brief.duration_seconds,
        "audio": {
            "normalize_loudness": True,
            "target_lufs": -14,
            "music_level_db": -25,
        },
        "captions": {
            "source": "captions.srt",
            "safe_area_bottom_percent": 18,
            "max_words_per_card": 7,
        },
        "layers": [asdict(layer) for layer in layers],
        "output": {"filename": "video-final.mp4", "codec": "h264", "format": "mp4"},
    }


def _source_for_scene(scene_type: str, index: int, asset_query: str) -> tuple[str, str]:
    if scene_type == "avatar":
        return "video", f"assets/avatar-scene-{index:02d}.mp4"
    if scene_type == "title_card":
        return "generated_card", f"generated/title-card-{index:02d}.png"
    if scene_type == "screen_capture":
        return "video", f"assets/screen-scene-{index:02d}.mp4"
    if scene_type == "proof":
        return "image_or_video", f"assets/proof-scene-{index:02d}"
    slug = asset_query.strip().replace(" ", "-").lower() or f"scene-{index:02d}"
    return "image_or_video", f"assets/{slug}"


def _transition_for(edit_direction: str) -> str:
    direction = edit_direction.lower()
    if "flash" in direction:
        return "flash"
    if "fade" in direction:
        return "fade"
    if "zoom" in direction:
        return "zoom_cut"
    return "cut"

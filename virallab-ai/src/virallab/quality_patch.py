from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from . import renderer
from .visual_quality import (
    brand_drawtext_filter,
    get_preset,
    normalize_srt_text,
    overlay_drawtext_filter,
    subtitle_force_style,
)

_INSTALLED = False
_ORIGINAL_FINAL_MIX = renderer._final_mix_command


def _quality_drawtext(text: str, width: int, height: int) -> str:
    return overlay_drawtext_filter(text, width, height, get_preset())


def _quality_final_mix_command(**kwargs: Any) -> list[str]:
    root = Path(kwargs["root"])
    preset = get_preset()
    captions = root / "captions.srt"
    if kwargs.get("burn_captions", True) and captions.exists():
        normalize_srt_text(captions, preset)

    command = _ORIGINAL_FINAL_MIX(**kwargs)
    brand = os.getenv("VIRALLAB_BRAND_TEXT", "Prof. Dr. Rodrigo Plentz").strip()
    brand_filter = brand_drawtext_filter(brand) if brand else ""

    if "-vf" in command:
        index = command.index("-vf") + 1
        current = command[index]
        if "subtitles=" in current:
            subtitle_path = renderer._subtitle_escape(captions)
            current = (
                f"subtitles='{subtitle_path}':"
                f"force_style='{subtitle_force_style(preset)}'"
            )
        if brand_filter:
            current = f"{current},{brand_filter}"
        command[index] = current
    elif brand_filter:
        map_index = command.index("-map") if "-map" in command else len(command) - 1
        command[map_index:map_index] = ["-vf", brand_filter]
    return command


def install_quality_patch() -> None:
    global _INSTALLED
    if _INSTALLED:
        return
    renderer._drawtext_filter = _quality_drawtext
    renderer._final_mix_command = _quality_final_mix_command
    _INSTALLED = True


__all__ = ["install_quality_patch"]

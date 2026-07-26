from __future__ import annotations

import os
import textwrap
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class CaptionPreset:
    key: str
    label: str
    font_name: str
    font_size: int
    primary_colour: str
    outline_colour: str
    back_colour: str
    outline: int
    shadow: int
    margin_v: int
    max_chars: int
    overlay_size_ratio: float
    overlay_y_ratio: float


PRESETS: dict[str, CaptionPreset] = {
    "cinematic": CaptionPreset(
        key="cinematic",
        label="Cinematográfico",
        font_name="DejaVu Sans",
        font_size=16,
        primary_colour="&H00FFFFFF",
        outline_colour="&H70000000",
        back_colour="&H50000000",
        outline=1,
        shadow=1,
        margin_v=230,
        max_chars=30,
        overlay_size_ratio=0.046,
        overlay_y_ratio=0.76,
    ),
    "educational": CaptionPreset(
        key="educational",
        label="Educacional premium",
        font_name="DejaVu Sans",
        font_size=17,
        primary_colour="&H00FFFFFF",
        outline_colour="&H65000000",
        back_colour="&H42000000",
        outline=1,
        shadow=1,
        margin_v=220,
        max_chars=32,
        overlay_size_ratio=0.048,
        overlay_y_ratio=0.75,
    ),
    "viral": CaptionPreset(
        key="viral",
        label="Viral",
        font_name="DejaVu Sans",
        font_size=19,
        primary_colour="&H00FFFFFF",
        outline_colour="&H85000000",
        back_colour="&H50000000",
        outline=2,
        shadow=0,
        margin_v=245,
        max_chars=24,
        overlay_size_ratio=0.054,
        overlay_y_ratio=0.73,
    ),
    "corporate": CaptionPreset(
        key="corporate",
        label="Corporativo",
        font_name="DejaVu Sans",
        font_size=15,
        primary_colour="&H00FFFFFF",
        outline_colour="&H50000000",
        back_colour="&H38000000",
        outline=1,
        shadow=1,
        margin_v=205,
        max_chars=34,
        overlay_size_ratio=0.043,
        overlay_y_ratio=0.78,
    ),
    "minimal": CaptionPreset(
        key="minimal",
        label="Minimalista",
        font_name="DejaVu Sans",
        font_size=15,
        primary_colour="&H00FFFFFF",
        outline_colour="&H40000000",
        back_colour="&H00000000",
        outline=1,
        shadow=1,
        margin_v=210,
        max_chars=34,
        overlay_size_ratio=0.042,
        overlay_y_ratio=0.78,
    ),
}


def get_preset(key: str | None = None) -> CaptionPreset:
    selected = (
        (key or os.getenv("VIRALLAB_CAPTION_STYLE", "educational")).strip().lower()
    )
    return PRESETS.get(selected, PRESETS["educational"])


def wrap_caption(text: str, *, max_chars: int, max_lines: int = 2) -> str:
    clean = " ".join(str(text).split())
    if not clean:
        return ""
    lines = textwrap.wrap(
        clean,
        width=max_chars,
        break_long_words=False,
        break_on_hyphens=False,
    )
    if len(lines) <= max_lines:
        return "\\N".join(lines)
    kept = lines[:max_lines]
    overflow = " ".join(lines[max_lines:])
    if overflow:
        available = max(4, max_chars - len(kept[-1]) - 1)
        addition = overflow[:available].rstrip(" ,.;:")
        if addition:
            kept[-1] = f"{kept[-1]} {addition}"
        kept[-1] = kept[-1].rstrip(" ,.;:") + "…"
    return "\\N".join(kept)


def subtitle_force_style(preset: CaptionPreset) -> str:
    return (
        f"FontName={preset.font_name},FontSize={preset.font_size},"
        f"PrimaryColour={preset.primary_colour},"
        f"OutlineColour={preset.outline_colour},"
        f"BackColour={preset.back_colour},"
        "Bold=1,BorderStyle=1,"
        f"Outline={preset.outline},Shadow={preset.shadow},"
        f"Alignment=2,MarginL=90,MarginR=90,MarginV={preset.margin_v},"
        "Spacing=0.3"
    )


def overlay_drawtext_filter(
    text: str, width: int, height: int, preset: CaptionPreset
) -> str:
    wrapped = wrap_caption(text, max_chars=preset.max_chars, max_lines=2)
    escaped = (
        wrapped.replace("\\", r"\\")
        .replace(":", r"\:")
        .replace("'", r"\'")
        .replace("%", r"\%")
    )
    font_size = max(38, int(width * preset.overlay_size_ratio))
    y = int(height * preset.overlay_y_ratio)
    return (
        "drawtext="
        f"text='{escaped}':"
        f"font='{preset.font_name}':fontcolor=white:fontsize={font_size}:"
        "line_spacing=10:borderw=2:bordercolor=black@0.55:"
        "shadowx=1:shadowy=2:shadowcolor=black@0.45:"
        "box=1:boxcolor=black@0.22:boxborderw=18:"
        "x=(w-text_w)/2:"
        f"y={y}"
    )


def brand_drawtext_filter(
    brand_text: str = "Prof. Dr. Rodrigo Plentz",
    *,
    width: int = 1080,
    height: int = 1920,
) -> str:
    escaped = brand_text.replace("\\", r"\\").replace(":", r"\:").replace("'", r"\'")
    size = max(22, int(width * 0.025))
    return (
        "drawtext="
        f"text='{escaped}':font='DejaVu Sans':fontcolor=white@0.58:"
        f"fontsize={size}:shadowx=1:shadowy=1:shadowcolor=black@0.35:"
        "x=w-text_w-54:"
        f"y={int(height * 0.055)}"
    )


def normalize_srt_text(path: str | Path, preset: CaptionPreset | None = None) -> None:
    target = Path(path)
    if not target.exists():
        return
    selected = preset or get_preset()
    lines = target.read_text(encoding="utf-8").splitlines()
    normalized: list[str] = []
    for line in lines:
        stripped = line.strip()
        if not stripped or stripped.isdigit() or "-->" in stripped:
            normalized.append(line)
        else:
            normalized.append(
                wrap_caption(
                    stripped, max_chars=selected.max_chars, max_lines=2
                ).replace("\\N", "\n")
            )
    target.write_text("\n".join(normalized).rstrip() + "\n", encoding="utf-8")


__all__ = [
    "CaptionPreset",
    "PRESETS",
    "brand_drawtext_filter",
    "get_preset",
    "normalize_srt_text",
    "overlay_drawtext_filter",
    "subtitle_force_style",
    "wrap_caption",
]

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class SubtitlePreset:
    name: str
    font_name: str = "Arial"
    font_size: int = 18
    primary_colour: str = "&H00FFFFFF"
    outline_colour: str = "&H00000000"
    outline: int = 3
    margin_vertical: int = 180

    def ffmpeg_style(self) -> str:
        return (
            f"FontName={self.font_name},FontSize={self.font_size},"
            f"PrimaryColour={self.primary_colour},OutlineColour={self.outline_colour},"
            f"BorderStyle=1,Outline={self.outline},Shadow=0,"
            f"Alignment=2,MarginV={self.margin_vertical}"
        )


PRESETS = {
    "clinical_accessible": SubtitlePreset(name="clinical_accessible"),
    "high_contrast": SubtitlePreset(
        name="high_contrast", font_size=20, outline=4, margin_vertical=200
    ),
}


def get_subtitle_preset(name: str = "clinical_accessible") -> SubtitlePreset:
    try:
        return PRESETS[name]
    except KeyError as exc:
        raise ValueError(f"Preset de legenda desconhecido: {name}") from exc


def validate_srt(path: str | Path, *, max_bytes: int = 2_000_000) -> Path:
    target = Path(path).resolve()
    if target.suffix.casefold() != ".srt" or not target.is_file():
        raise ValueError("Legenda SRT não encontrada.")
    if target.stat().st_size > max_bytes:
        raise ValueError("Legenda excede o limite permitido.")
    target.read_text(encoding="utf-8")
    return target

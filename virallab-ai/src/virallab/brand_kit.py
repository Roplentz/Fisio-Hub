from __future__ import annotations

import json
import re
import shutil
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

_HEX = re.compile(r"^#[0-9A-Fa-f]{6}$")
_ALLOWED_LOGOS = {".png", ".jpg", ".jpeg", ".webp", ".svg"}
_MAX_LOGO_BYTES = 10 * 1024 * 1024


@dataclass(frozen=True)
class BrandKit:
    name: str
    primary_color: str
    secondary_color: str
    accent_color: str
    font_heading: str = "Inter"
    font_body: str = "Inter"
    logo_path: str = ""
    tone: list[str] = field(default_factory=list)
    visual_notes: str = ""
    version: int = 1
    updated_at: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    def prompt_instruction(self) -> str:
        tone = ", ".join(self.tone) if self.tone else "profissional, humano e claro"
        return (
            f"Identidade {self.name}: cores {self.primary_color}, "
            f"{self.secondary_color} e destaque {self.accent_color}; "
            f"tom {tone}. {self.visual_notes}".strip()
        )


class BrandKitStore:
    """Kit de marca persistente, versionado e removível pelo usuário."""

    def __init__(self, workspace: str | Path) -> None:
        self.root = (Path(workspace) / "brand-kit").resolve()
        self.root.mkdir(parents=True, exist_ok=True)
        self.metadata_path = self.root / "brand-kit.json"

    def save(
        self,
        *,
        name: str,
        primary_color: str,
        secondary_color: str,
        accent_color: str,
        font_heading: str = "Inter",
        font_body: str = "Inter",
        tone: list[str] | None = None,
        visual_notes: str = "",
        logo_file: str | Path | None = None,
    ) -> BrandKit:
        colors = (primary_color, secondary_color, accent_color)
        if not all(_HEX.fullmatch(color) for color in colors):
            raise ValueError("As cores devem usar o formato hexadecimal #RRGGBB.")
        previous = self.load()
        logo_path = previous.logo_path if previous else ""
        if logo_file is not None:
            logo_path = str(self._save_logo(logo_file))
        kit = BrandKit(
            name=name.strip() or "Minha marca",
            primary_color=primary_color.upper(),
            secondary_color=secondary_color.upper(),
            accent_color=accent_color.upper(),
            font_heading=_clean_font(font_heading),
            font_body=_clean_font(font_body),
            logo_path=logo_path,
            tone=[item.strip() for item in (tone or []) if item.strip()][:8],
            visual_notes=" ".join(visual_notes.split())[:500],
            version=(previous.version + 1) if previous else 1,
            updated_at=datetime.now(timezone.utc).isoformat(),
        )
        self.metadata_path.write_text(
            json.dumps(kit.to_dict(), ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        return kit

    def load(self) -> BrandKit | None:
        if not self.metadata_path.is_file():
            return None
        try:
            data = json.loads(self.metadata_path.read_text(encoding="utf-8"))
            kit = BrandKit(**data)
        except (json.JSONDecodeError, TypeError, ValueError):
            return None
        if kit.logo_path and not Path(kit.logo_path).is_file():
            return BrandKit(**{**kit.to_dict(), "logo_path": ""})
        return kit

    def delete(self) -> None:
        shutil.rmtree(self.root, ignore_errors=True)
        self.root.mkdir(parents=True, exist_ok=True)

    def _save_logo(self, source_file: str | Path) -> Path:
        source = Path(source_file).resolve()
        if not source.is_file() or source.suffix.casefold() not in _ALLOWED_LOGOS:
            raise ValueError("Use logotipo PNG, JPG, WEBP ou SVG.")
        if source.stat().st_size > _MAX_LOGO_BYTES:
            raise ValueError("O logotipo excede o limite de 10 MB.")
        for old in self.root.glob("logo.*"):
            old.unlink(missing_ok=True)
        target = self.root / f"logo{source.suffix.casefold()}"
        shutil.copy2(source, target)
        return target


def _clean_font(value: str) -> str:
    cleaned = re.sub(r"[^\w .-]", "", value, flags=re.UNICODE).strip()
    return cleaned[:80] or "Inter"

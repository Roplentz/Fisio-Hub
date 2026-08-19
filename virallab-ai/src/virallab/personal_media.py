from __future__ import annotations

import hashlib
import json
import shutil
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

_ALLOWED = {".mp4", ".mov", ".webm", ".png", ".jpg", ".jpeg", ".webp", ".mp3", ".wav", ".m4a", ".aac", ".ogg"}
_MAX_BYTES = 500 * 1024 * 1024


@dataclass(frozen=True)
class PersonalMedia:
    media_id: str
    filename: str
    media_type: str
    original_name: str
    sha256: str
    consent_confirmed: bool
    created_at: str

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


class PersonalMediaLibrary:
    """Biblioteca privada de mídia própria com consentimento e exclusão."""

    def __init__(self, workspace: str | Path) -> None:
        self.root = (Path(workspace) / "personal-media").resolve()
        self.files = self.root / "files"
        self.manifest = self.root / "manifest.json"
        self.files.mkdir(parents=True, exist_ok=True)

    def add(self, source_file: str | Path, *, consent_confirmed: bool) -> PersonalMedia:
        if not consent_confirmed:
            raise ValueError("Confirme que possui autorização para usar esta mídia.")
        source = Path(source_file).resolve()
        if not source.is_file() or source.suffix.casefold() not in _ALLOWED:
            raise ValueError("Formato de mídia não permitido.")
        if source.stat().st_size > _MAX_BYTES:
            raise ValueError("A mídia excede o limite de 500 MB.")
        media_id = f"media_{uuid4().hex[:12]}"
        target = self.files / f"{media_id}{source.suffix.casefold()}"
        shutil.copy2(source, target)
        item = PersonalMedia(
            media_id=media_id,
            filename=str(target),
            media_type=_media_type(target),
            original_name=source.name,
            sha256=_sha256(target),
            consent_confirmed=True,
            created_at=datetime.now(timezone.utc).isoformat(),
        )
        items = self.list()
        items.append(item)
        self._write(items)
        return item

    def list(self) -> list[PersonalMedia]:
        if not self.manifest.is_file():
            return []
        try:
            payload = json.loads(self.manifest.read_text(encoding="utf-8"))
            return [PersonalMedia(**item) for item in payload.get("media", [])]
        except (json.JSONDecodeError, TypeError, ValueError):
            return []

    def delete(self, media_id: str) -> None:
        remaining: list[PersonalMedia] = []
        found = False
        for item in self.list():
            if item.media_id == media_id:
                Path(item.filename).unlink(missing_ok=True)
                found = True
            else:
                remaining.append(item)
        if not found:
            raise KeyError(media_id)
        self._write(remaining)

    def _write(self, items: list[PersonalMedia]) -> None:
        self.manifest.write_text(
            json.dumps(
                {"version": "1.0", "media": [item.to_dict() for item in items]},
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )


def _media_type(path: Path) -> str:
    if path.suffix.casefold() in {".mp4", ".mov", ".webm"}:
        return "video"
    if path.suffix.casefold() in {".mp3", ".wav", ".m4a", ".aac", ".ogg"}:
        return "audio"
    return "image"


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()

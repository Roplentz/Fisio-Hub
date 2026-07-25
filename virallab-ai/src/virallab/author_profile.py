from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path


@dataclass(frozen=True)
class AuthorProfile:
    name: str
    role: str
    image_path: str
    mime_type: str
    visual_notes: str = ""

    def to_dict(self) -> dict[str, str]:
        return asdict(self)


class AuthorProfileStore:
    """Persistent visual identity used as character reference across projects."""

    def __init__(self, workspace: str | Path) -> None:
        self.root = Path(workspace) / "visual-profile"
        self.root.mkdir(parents=True, exist_ok=True)
        self.metadata_path = self.root / "author.json"

    def save(
        self,
        *,
        name: str,
        role: str,
        image_bytes: bytes,
        extension: str,
        mime_type: str,
        visual_notes: str = "",
    ) -> AuthorProfile:
        suffix = (
            extension.lower() if extension.startswith(".") else f".{extension.lower()}"
        )
        if suffix not in {".png", ".jpg", ".jpeg", ".webp"}:
            raise ValueError("Use uma imagem PNG, JPG, JPEG ou WEBP.")
        if not image_bytes:
            raise ValueError("A imagem do autor está vazia.")

        for old in self.root.glob("author-reference.*"):
            old.unlink(missing_ok=True)
        image_path = self.root / f"author-reference{suffix}"
        image_path.write_bytes(image_bytes)
        profile = AuthorProfile(
            name=name.strip() or "Autor",
            role=role.strip() or "Autor do canal",
            image_path=str(image_path),
            mime_type=mime_type or "image/jpeg",
            visual_notes=visual_notes.strip(),
        )
        self.metadata_path.write_text(
            json.dumps(profile.to_dict(), ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        return profile

    def load(self) -> AuthorProfile | None:
        if not self.metadata_path.exists():
            return None
        try:
            data = json.loads(self.metadata_path.read_text(encoding="utf-8"))
            profile = AuthorProfile(**data)
        except (json.JSONDecodeError, TypeError, ValueError):
            return None
        return profile if Path(profile.image_path).exists() else None

    def delete(self) -> None:
        profile = self.load()
        if profile:
            Path(profile.image_path).unlink(missing_ok=True)
        self.metadata_path.unlink(missing_ok=True)

    def reference(self) -> tuple[bytes, str] | None:
        profile = self.load()
        if not profile:
            return None
        return Path(profile.image_path).read_bytes(), profile.mime_type

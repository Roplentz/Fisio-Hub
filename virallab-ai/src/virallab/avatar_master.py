from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable

from .image_provider import GeminiImageProvider, ImageGenerationError

ALLOWED_SUFFIXES = {".png", ".jpg", ".jpeg", ".webp"}


@dataclass(frozen=True)
class ReferencePhoto:
    angle: str
    path: str
    mime_type: str


@dataclass(frozen=True)
class AvatarMasterProfile:
    name: str
    role: str
    references: list[ReferencePhoto]
    master_image_path: str
    master_mime_type: str
    visual_notes: str
    consent_confirmed: bool
    approved: bool
    version: int
    updated_at: str

    def to_dict(self) -> dict:
        data = asdict(self)
        data["references"] = [asdict(item) for item in self.references]
        return data


class AvatarMasterStore:
    """Persistent three-angle avatar references and approved master image."""

    ANGLES = ("front", "left", "right")

    def __init__(self, workspace: str | Path) -> None:
        self.root = Path(workspace) / "avatar-master"
        self.refs_dir = self.root / "references"
        self.candidates_dir = self.root / "candidates"
        self.root.mkdir(parents=True, exist_ok=True)
        self.refs_dir.mkdir(parents=True, exist_ok=True)
        self.candidates_dir.mkdir(parents=True, exist_ok=True)
        self.metadata_path = self.root / "profile.json"

    def save_references(
        self,
        *,
        name: str,
        role: str,
        photos: dict[str, tuple[bytes, str, str]],
        visual_notes: str = "",
        consent_confirmed: bool,
    ) -> AvatarMasterProfile:
        if not consent_confirmed:
            raise ValueError("Confirme a autorização de uso da própria imagem.")
        missing = [angle for angle in self.ANGLES if angle not in photos]
        if missing:
            raise ValueError("Envie as três fotos: frente, lado esquerdo e lado direito.")

        references: list[ReferencePhoto] = []
        for angle in self.ANGLES:
            data, filename, mime_type = photos[angle]
            if not data:
                raise ValueError(f"A foto {angle} está vazia.")
            suffix = Path(filename).suffix.lower() or ".jpg"
            if suffix not in ALLOWED_SUFFIXES:
                raise ValueError("Use imagens PNG, JPG, JPEG ou WEBP.")
            for old in self.refs_dir.glob(f"{angle}.*"):
                old.unlink(missing_ok=True)
            target = self.refs_dir / f"{angle}{suffix}"
            target.write_bytes(data)
            references.append(
                ReferencePhoto(angle=angle, path=str(target), mime_type=mime_type or "image/jpeg")
            )

        previous = self.load()
        profile = AvatarMasterProfile(
            name=name.strip() or "Autor",
            role=role.strip() or "Autor e especialista",
            references=references,
            master_image_path="",
            master_mime_type="",
            visual_notes=visual_notes.strip(),
            consent_confirmed=True,
            approved=False,
            version=(previous.version + 1) if previous else 1,
            updated_at=datetime.now(timezone.utc).isoformat(),
        )
        self._write(profile)
        return profile

    def load(self) -> AvatarMasterProfile | None:
        if not self.metadata_path.exists():
            return None
        try:
            raw = json.loads(self.metadata_path.read_text(encoding="utf-8"))
            references = [ReferencePhoto(**item) for item in raw.pop("references", [])]
            profile = AvatarMasterProfile(references=references, **raw)
        except (json.JSONDecodeError, TypeError, ValueError):
            return None
        if len(profile.references) != 3:
            return None
        if not all(Path(item.path).exists() for item in profile.references):
            return None
        return profile

    def references(self, *, include_master: bool = True) -> list[tuple[bytes, str]]:
        profile = self.load()
        if not profile:
            return []
        result: list[tuple[bytes, str]] = []
        if include_master and profile.approved and profile.master_image_path:
            master = Path(profile.master_image_path)
            if master.exists():
                result.append((master.read_bytes(), profile.master_mime_type or "image/png"))
        result.extend((Path(item.path).read_bytes(), item.mime_type) for item in profile.references)
        return result

    def generate_candidate(self) -> Path:
        profile = self.load()
        if not profile:
            raise ValueError("Envie e salve as três fotos antes de criar a Imagem Mestre.")
        provider = GeminiImageProvider()
        prompt = (
            f"Crie uma Imagem Mestre fotográfica e realista de {profile.name}, {profile.role}, "
            "usando as três imagens como referências da mesma pessoa: frente, perfil esquerdo e perfil direito. "
            "Preserve com alta fidelidade a identidade facial, proporções, cabelo, idade aparente, tom de pele e traços individuais. "
            "Enquadramento do peito para cima, olhando para a câmera, expressão segura e acolhedora, roupa profissional elegante, "
            "fundo neutro discretamente desfocado, iluminação frontal suave, composição vertical 4:5, sem texto ou logotipo. "
            "Não misture rostos, não rejuvenesça excessivamente e não crie outra pessoa."
        )
        if profile.visual_notes:
            prompt += f" Diretrizes adicionais: {profile.visual_notes}."
        generated = provider.generate(
            prompt,
            aspect_ratio="4:5",
            image_size="1K",
            reference_images=self.references(include_master=False),
        )
        target = self.candidates_dir / f"candidate-v{profile.version}{generated.extension}"
        target.write_bytes(generated.data)
        return target

    def approve_candidate(self, candidate_path: str | Path) -> AvatarMasterProfile:
        profile = self.load()
        if not profile:
            raise ValueError("Perfil de Avatar IA não encontrado.")
        candidate = Path(candidate_path)
        if not candidate.exists() or candidate.parent != self.candidates_dir:
            raise ValueError("Imagem candidata inválida.")
        suffix = candidate.suffix.lower() or ".png"
        for old in self.root.glob("master.*"):
            old.unlink(missing_ok=True)
        master = self.root / f"master{suffix}"
        master.write_bytes(candidate.read_bytes())
        mime = {".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".webp": "image/webp"}.get(suffix, "image/png")
        approved = AvatarMasterProfile(
            name=profile.name,
            role=profile.role,
            references=profile.references,
            master_image_path=str(master),
            master_mime_type=mime,
            visual_notes=profile.visual_notes,
            consent_confirmed=profile.consent_confirmed,
            approved=True,
            version=profile.version,
            updated_at=datetime.now(timezone.utc).isoformat(),
        )
        self._write(approved)
        return approved

    def delete(self) -> None:
        for path in sorted(self.root.rglob("*"), reverse=True):
            if path.is_file():
                path.unlink(missing_ok=True)
            elif path.is_dir():
                path.rmdir()
        self.root.mkdir(parents=True, exist_ok=True)
        self.refs_dir.mkdir(parents=True, exist_ok=True)
        self.candidates_dir.mkdir(parents=True, exist_ok=True)

    def _write(self, profile: AvatarMasterProfile) -> None:
        self.metadata_path.write_text(
            json.dumps(profile.to_dict(), ensure_ascii=False, indent=2), encoding="utf-8"
        )


def avatar_prompt(profile: AvatarMasterProfile) -> str:
    text = (
        f"Represente exatamente {profile.name}, {profile.role}, usando a Imagem Mestre e as referências autorizadas. "
        "Preserve identidade facial, idade aparente, cabelo, tom de pele e características individuais. Não crie outra pessoa."
    )
    if profile.visual_notes:
        text += f" Diretrizes permanentes: {profile.visual_notes}."
    return text


__all__ = [
    "AvatarMasterProfile",
    "AvatarMasterStore",
    "ImageGenerationError",
    "ReferencePhoto",
    "avatar_prompt",
]

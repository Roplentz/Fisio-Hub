from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .asset_library import AssetLibrary, AssetRecord
from .author_profile import AuthorProfile, AuthorProfileStore
from .avatar_master import AvatarMasterProfile, AvatarMasterStore, avatar_prompt
from .image_provider import GeminiImageProvider, ImageGenerationError


@dataclass(frozen=True)
class SceneCreativePlan:
    scene_index: int
    scene_type: str
    title: str
    prompt: str
    aspect_ratio: str = "9:16"


def build_scene_prompt(
    scene: Any,
    *,
    theme: str = "",
    visual_style: str = "RP cinematográfico",
    author_profile: AuthorProfile | None = None,
    avatar_profile: AvatarMasterProfile | None = None,
) -> str:
    """Build a production-ready vertical-image prompt from a storyboard scene."""
    scene_type = str(getattr(scene, "scene_type", "broll"))
    direction = str(getattr(scene, "visual_direction", "")).strip()
    narration = str(getattr(scene, "narration", "")).strip()
    on_screen = str(getattr(scene, "on_screen_text", "")).strip()

    if scene_type == "avatar" and avatar_profile and avatar_profile.approved:
        base = avatar_prompt(avatar_profile)
    elif scene_type == "avatar" and author_profile:
        base = _author_identity_instruction(author_profile)
    else:
        type_rules = {
            "avatar": (
                "Retrato editorial realista de um professor fisioterapeuta brasileiro experiente, "
                "em ambiente profissional de saúde, olhando para a câmera, expressão segura e acolhedora."
            ),
            "broll": (
                "Fotografia documental realista de fisioterapia e cuidado em saúde, com interação humana natural, "
                "sem poses publicitárias artificiais."
            ),
            "screen_capture": (
                "Mockup vertical elegante de uma interface digital fictícia, limpa e legível, exibida em notebook ou tablet; "
                "não reproduzir marcas, logotipos ou dados pessoais reais."
            ),
            "proof": (
                "Composição visual de evidência ou demonstração profissional, clara e confiável, sem inventar números, "
                "resultados clínicos ou selos de certificação."
            ),
            "title_card": (
                "Arte editorial vertical minimalista de alto impacto, com área de respiro para inserir título posteriormente; "
                "não renderizar palavras dentro da imagem."
            ),
        }
        base = type_rules.get(scene_type, type_rules["broll"])

    prompt_parts = [
        base,
        f"Tema do conteúdo: {theme}." if theme else "",
        f"Direção da cena: {direction}." if direction else "",
        f"Contexto narrativo: {narration}." if narration else "",
        f"Conceito do texto na tela: {on_screen}. Não escrever esse texto na imagem."
        if on_screen
        else "",
        f"Identidade visual: {visual_style}; paleta azul-petróleo, ciano discreto e tons neutros; iluminação cinematográfica suave.",
        "Formato vertical 9:16, composição mobile-first, assunto principal centralizado, espaço seguro nas bordas para legendas.",
        "Alta qualidade, aparência humana natural, mãos anatomicamente corretas, sem texto ilegível, sem marca-d'água, sem logotipos.",
    ]
    return " ".join(part for part in prompt_parts if part).strip()


def _author_identity_instruction(profile: AuthorProfile) -> str:
    instruction = (
        f"Use a imagem de referência como identidade visual de {profile.name}, "
        f"{profile.role}. Preserve com alta fidelidade a identidade facial, formato do rosto, "
        "cabelo, idade aparente, tom de pele e características individuais. Não crie outra pessoa. "
        "Retrato editorial realista em ambiente profissional de saúde, olhando para a câmera, "
        "expressão segura, humana e acolhedora."
    )
    if profile.visual_notes:
        instruction += f" Diretrizes permanentes do autor: {profile.visual_notes}."
    return instruction


def generate_scene_asset(
    project_dir: str | Path,
    scene: Any,
    *,
    prompt: str,
    aspect_ratio: str = "9:16",
    image_size: str = "1K",
) -> AssetRecord:
    project_path = Path(project_dir)
    provider = GeminiImageProvider()
    references: list[tuple[bytes, str]] = []
    legacy_reference: bytes | None = None
    legacy_mime = "image/jpeg"
    legacy_profile: AuthorProfile | None = None
    avatar_profile: AvatarMasterProfile | None = None
    final_prompt = prompt

    if str(getattr(scene, "scene_type", "")) == "avatar":
        workspace = project_path.parent.parent
        avatar_store = AvatarMasterStore(workspace)
        avatar_profile = avatar_store.load()
        if avatar_profile and avatar_profile.approved:
            references = avatar_store.references(include_master=True)
            identity = avatar_prompt(avatar_profile)
            if identity not in final_prompt:
                final_prompt = f"{identity} {final_prompt}"
        else:
            legacy_store = AuthorProfileStore(workspace)
            legacy_profile = legacy_store.load()
            legacy = legacy_store.reference()
            if legacy:
                legacy_reference, legacy_mime = legacy
                identity = _author_identity_instruction(legacy_profile)
                if identity not in final_prompt:
                    final_prompt = f"{identity} {final_prompt}"

    generated = provider.generate(
        final_prompt,
        aspect_ratio=aspect_ratio,
        image_size=image_size,
        reference_image=legacy_reference,
        reference_mime_type=legacy_mime,
        reference_images=references,
    )
    library = AssetLibrary(project_path)
    return library.add_bytes(
        scene_index=int(getattr(scene, "index")),
        data=generated.data,
        extension=generated.extension,
        source="generated",
        provider=provider.name,
        prompt=final_prompt,
        metadata={
            "model": generated.model,
            "aspect_ratio": aspect_ratio,
            "image_size": image_size,
            "scene_type": str(getattr(scene, "scene_type", "")),
            "avatar_master": bool(avatar_profile and avatar_profile.approved),
            "avatar_version": avatar_profile.version if avatar_profile else 0,
            "author_reference": bool(references or legacy_reference),
            "author_name": (
                avatar_profile.name
                if avatar_profile
                else legacy_profile.name
                if legacy_profile
                else ""
            ),
        },
    )


def approved_assets(project_dir: str | Path) -> dict[int, AssetRecord]:
    library = AssetLibrary(project_dir)
    return {
        item.scene_index: item for item in library.load() if item.status == "approved"
    }


__all__ = [
    "ImageGenerationError",
    "SceneCreativePlan",
    "approved_assets",
    "build_scene_prompt",
    "generate_scene_asset",
]

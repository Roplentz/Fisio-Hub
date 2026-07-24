from __future__ import annotations

from dataclasses import asdict, dataclass

from .models import VideoPackage


@dataclass
class AvatarJob:
    scene_index: int
    avatar_name: str
    text: str
    duration_seconds: float
    delivery: str
    output_filename: str


def build_avatar_jobs(package: VideoPackage) -> list[AvatarJob]:
    jobs: list[AvatarJob] = []
    for scene in package.scenes:
        if scene.scene_type != "avatar" or not scene.narration.strip():
            continue
        jobs.append(
            AvatarJob(
                scene_index=scene.index,
                avatar_name=package.brief.avatar_name,
                text=scene.narration.strip(),
                duration_seconds=round(scene.end - scene.start, 2),
                delivery=_delivery_for_scene(scene.edit_direction),
                output_filename=f"avatar-scene-{scene.index:02d}.mp4",
            )
        )
    return jobs


def avatar_manifest(package: VideoPackage) -> dict[str, object]:
    return {
        "provider": "manual_or_api_adapter",
        "avatar": package.brief.avatar_name,
        "aspect_ratio": "9:16",
        "resolution": "1080x1920",
        "jobs": [asdict(job) for job in build_avatar_jobs(package)],
        "instructions": [
            "Gerar fundo limpo ou transparente quando o provedor permitir.",
            "Não adicionar legenda no provedor; o ViralLab aplica a legenda final.",
            "Manter enquadramento e iluminação consistentes entre cenas.",
            "Exportar cada fala como arquivo separado para facilitar cortes e substituições.",
        ],
    }


def _delivery_for_scene(edit_direction: str) -> str:
    direction = edit_direction.lower()
    if "pausa" in direction:
        return "firme, com pausa intencional antes da frase principal"
    if "zoom" in direction:
        return "confiante, direto e levemente enfático"
    return "didático, natural e conversacional"

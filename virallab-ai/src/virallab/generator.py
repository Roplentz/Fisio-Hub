from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .avatar import avatar_manifest
from .models import Scene, VideoBrief, VideoPackage
from .providers import ScriptProvider, select_provider
from .render_plan import build_render_plan
from .templates import TEMPLATES


_ALLOWED_SCENE_TYPES = {"avatar", "title_card", "broll", "screen_capture", "proof"}


def generate_video_package(
    brief: VideoBrief,
    provider: ScriptProvider | None = None,
) -> VideoPackage:
    selected_provider = provider or select_provider("auto")
    generated = selected_provider.generate(brief)
    hook = str(generated["hook"]).strip()
    thesis = str(generated["thesis"]).strip()

    scenes = _scenes_from_ai(generated.get("scenes"), brief)
    if not scenes:
        template = TEMPLATES.get(brief.format)
        if template is None:
            raise ValueError(f"Formato ainda não implementado: {brief.format}")
        scenes = template(brief, hook, thesis)

    warnings = _quality_guardrails(brief)
    return VideoPackage(
        brief=brief,
        hook=hook,
        thesis=thesis,
        scenes=scenes,
        caption=str(generated["caption"]).strip(),
        hashtags=_build_hashtags(brief),
        warnings=warnings,
        metadata={
            "format_version": "0.3.0",
            "workflow": "analysis-dna>ai-script>storyboard>human-review>production>render",
            "script_provider": selected_provider.name,
            "human_review_required": True,
            "creative_style": brief.creative_style,
            "reference_dna_used": bool(brief.reference_dna),
            "creative_rationale": str(generated.get("creative_rationale", "")).strip(),
        },
    )


def _scenes_from_ai(raw_scenes: Any, brief: VideoBrief) -> list[Scene]:
    if not isinstance(raw_scenes, list) or not raw_scenes:
        return []

    cleaned: list[dict[str, Any]] = []
    for item in raw_scenes[:12]:
        if not isinstance(item, dict):
            continue
        scene_type = str(item.get("scene_type", "avatar")).strip().lower()
        if scene_type not in _ALLOWED_SCENE_TYPES:
            scene_type = "avatar"
        try:
            duration = max(1.5, float(item.get("duration_seconds", 5)))
        except (TypeError, ValueError):
            duration = 5.0
        cleaned.append({**item, "scene_type": scene_type, "duration_seconds": duration})

    if not cleaned:
        return []

    requested = max(15.0, float(brief.duration_seconds))
    total = sum(float(item["duration_seconds"]) for item in cleaned)
    scale = requested / total if total > 0 else 1.0
    cursor = 0.0
    scenes: list[Scene] = []

    for index, item in enumerate(cleaned, start=1):
        duration = float(item["duration_seconds"]) * scale
        start = round(cursor, 2)
        end = round(requested if index == len(cleaned) else cursor + duration, 2)
        narration = str(item.get("narration", "")).strip()
        on_screen = str(item.get("on_screen_text", "")).strip()
        visual = str(item.get("visual_direction", "")).strip()
        edit = str(item.get("edit_direction", "")).strip()
        query = str(item.get("asset_query", "")).strip()
        scenes.append(
            Scene(
                index=index,
                start=start,
                end=end,
                scene_type=item["scene_type"],
                narration=narration,
                on_screen_text=on_screen,
                visual_direction=visual,
                edit_direction=edit,
                asset_query=query,
            )
        )
        cursor = end
    return scenes


def export_package(package: VideoPackage, output_dir: str | Path) -> Path:
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)

    json_path = out / "video-package.json"
    json_path.write_text(
        json.dumps(package.to_dict(), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    (out / "script.md").write_text(_script_markdown(package), encoding="utf-8")
    (out / "captions.srt").write_text(_to_srt(package), encoding="utf-8")
    (out / "caption.txt").write_text(package.caption, encoding="utf-8")
    (out / "asset-list.txt").write_text(_asset_list(package), encoding="utf-8")
    (out / "avatar-manifest.json").write_text(
        json.dumps(avatar_manifest(package), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    (out / "render-plan.json").write_text(
        json.dumps(build_render_plan(package), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return json_path


def _build_hashtags(brief: VideoBrief) -> list[str]:
    tags = ["#ViralLab", "#InteligenciaArtificial", "#Inovacao", "#FisioIA"]
    if "fisi" in brief.audience.lower() or "fisi" in brief.theme.lower():
        tags.append("#Fisioterapia")
    return tags


def _quality_guardrails(brief: VideoBrief) -> list[str]:
    warnings: list[str] = []
    if brief.duration_seconds > 90:
        warnings.append("Formato curto acima de 90 segundos pode reduzir a conclusão do vídeo.")
    if brief.evidence_level == "cientifico":
        warnings.append("Revisar afirmações, fontes e limites antes da publicação.")
    warnings.append("Não inserir dados identificáveis de pacientes em telas, áudio ou imagens.")
    return warnings


def _script_markdown(package: VideoPackage) -> str:
    rows = [
        f"# {package.brief.theme}",
        "",
        f"**Formato:** {package.brief.format}",
        f"**Duração:** {package.brief.duration_seconds}s",
        f"**Provedor:** {package.metadata.get('script_provider', 'desconhecido')}",
        f"**Estilo:** {package.metadata.get('creative_style', '—')}",
        f"**Hook:** {package.hook}",
        f"**Tese:** {package.thesis}",
        "",
    ]
    rationale = package.metadata.get("creative_rationale")
    if rationale:
        rows.extend(["## Decisão criativa", "", str(rationale), ""])
    rows.extend([
        "## Storyboard",
        "",
        "| Tempo | Tipo | Narração | Texto na tela | Direção visual | Edição |",
        "|---|---|---|---|---|---|",
    ])
    for scene in package.scenes:
        rows.append(
            f"| {scene.start:.1f}-{scene.end:.1f}s | {scene.scene_type} | "
            f"{scene.narration} | {scene.on_screen_text} | {scene.visual_direction} | {scene.edit_direction} |"
        )
    rows.extend(["", "## Legenda", "", package.caption, "", " ".join(package.hashtags)])
    return "\n".join(rows)


def _to_srt(package: VideoPackage) -> str:
    blocks: list[str] = []
    for scene in package.scenes:
        if not scene.narration.strip():
            continue
        blocks.append(
            f"{len(blocks) + 1}\n{_srt_time(scene.start)} --> {_srt_time(scene.end)}\n"
            f"{scene.narration.strip()}\n"
        )
    return "\n".join(blocks)


def _srt_time(seconds: float) -> str:
    milliseconds = int(round(seconds * 1000))
    hours, remainder = divmod(milliseconds, 3_600_000)
    minutes, remainder = divmod(remainder, 60_000)
    secs, millis = divmod(remainder, 1000)
    return f"{hours:02}:{minutes:02}:{secs:02},{millis:03}"


def _asset_list(package: VideoPackage) -> str:
    lines = []
    for scene in package.scenes:
        if scene.asset_query:
            lines.append(f"Cena {scene.index}: {scene.asset_query}")
    return "\n".join(lines)

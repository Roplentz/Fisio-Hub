from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .avatar import avatar_manifest
from .clinical_intelligence import write_clinical_safety_report
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
    provider_notice = str(generated.get("provider_notice", "")).strip()
    if provider_notice:
        warnings.append(provider_notice)

    return VideoPackage(
        brief=brief,
        hook=hook,
        thesis=thesis,
        scenes=scenes,
        caption=str(generated["caption"]).strip(),
        hashtags=_build_hashtags(brief),
        warnings=warnings,
        metadata={
            "format_version": "0.3.1",
            "workflow": "analysis-dna>ai-script>storyboard>human-review>production>render",
            "script_provider": selected_provider.name,
            "provider_model": str(generated.get("provider_model", "")).strip(),
            "provider_notice": provider_notice,
            "provider_error": str(generated.get("provider_error", "")).strip(),
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

    requested = max(5.0, float(brief.duration_seconds))
    raw_total = sum(float(item["duration_seconds"]) for item in cleaned)
    scale = requested / raw_total if raw_total > 0 else 1.0
    cursor = 0.0
    scenes: list[Scene] = []
    for index, item in enumerate(cleaned, start=1):
        duration = max(1.5, float(item["duration_seconds"]) * scale)
        end = requested if index == len(cleaned) else min(requested, cursor + duration)
        if end <= cursor:
            continue
        scenes.append(
            Scene(
                index=index,
                start=round(cursor, 2),
                end=round(end, 2),
                scene_type=str(item["scene_type"]),
                narration=str(item.get("narration", "")).strip(),
                on_screen_text=str(item.get("on_screen_text", "")).strip(),
                visual_direction=str(item.get("visual_direction", "")).strip(),
                edit_direction=str(item.get("edit_direction", "")).strip(),
                asset_query=str(item.get("asset_query", "")).strip(),
            )
        )
        cursor = end
    return scenes


def export_package(package: VideoPackage, output_dir: str | Path) -> Path:
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    json_path = out / "video-package.json"
    json_path.write_text(
        json.dumps(package.to_dict(), ensure_ascii=False, indent=2), encoding="utf-8"
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
    write_clinical_safety_report(package, out / "clinical-safety-report.json")
    return json_path


def _build_hashtags(brief: VideoBrief) -> list[str]:
    base = ["#fisioterapia", "#saude", "#inovacao"]
    if "ia" in brief.theme.lower() or "intelig" in brief.theme.lower():
        base.insert(0, "#inteligenciaartificial")
    return base


def _quality_guardrails(brief: VideoBrief) -> list[str]:
    warnings = ["Revisão humana obrigatória antes da publicação."]
    if brief.evidence_level == "cientifico":
        warnings.append("Validar referências e não inventar resultados ou citações.")
    warnings.append(
        "Não inserir dados clínicos identificáveis em serviços públicos de IA."
    )
    return warnings


def _script_markdown(package: VideoPackage) -> str:
    lines = [
        f"# {package.brief.theme}",
        "",
        f"**Formato:** {package.brief.format}",
        f"**Duração:** {package.brief.duration_seconds}s",
        f"**Provedor:** {package.metadata.get('script_provider', 'desconhecido')}",
        f"**Hook:** {package.hook}",
        "",
        "## Storyboard",
        "",
    ]
    for scene in package.scenes:
        lines.extend(
            [
                f"### Cena {scene.index} — {scene.start:.1f}s a {scene.end:.1f}s",
                f"- Tipo: {scene.scene_type}",
                f"- Narração: {scene.narration}",
                f"- Texto na tela: {scene.on_screen_text}",
                f"- Direção visual: {scene.visual_direction}",
                f"- Edição: {scene.edit_direction}",
                "",
            ]
        )
    return "\n".join(lines)


def _to_srt(package: VideoPackage) -> str:
    blocks = []
    for scene in package.scenes:
        if not scene.narration.strip():
            continue
        blocks.append(
            "\n".join(
                [
                    str(len(blocks) + 1),
                    f"{_srt_time(scene.start)} --> {_srt_time(scene.end)}",
                    scene.narration.strip(),
                ]
            )
        )
    return "\n\n".join(blocks) + ("\n" if blocks else "")


def _srt_time(seconds: float) -> str:
    milliseconds = int(round(seconds * 1000))
    hours, remainder = divmod(milliseconds, 3_600_000)
    minutes, remainder = divmod(remainder, 60_000)
    secs, ms = divmod(remainder, 1000)
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{ms:03d}"


def _asset_list(package: VideoPackage) -> str:
    lines = []
    for scene in package.scenes:
        if scene.asset_query:
            lines.append(f"Cena {scene.index}: {scene.asset_query}")
    return "\n".join(lines)

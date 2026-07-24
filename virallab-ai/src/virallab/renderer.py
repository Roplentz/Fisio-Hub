from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path
from typing import Any


class RenderError(RuntimeError):
    """Falha controlada durante a renderização do vídeo."""


def render_video(
    package_dir: str | Path,
    *,
    output_file: str | Path | None = None,
    ffmpeg_bin: str = "ffmpeg",
    dry_run: bool = False,
) -> Path:
    """Renderiza um vídeo vertical a partir de ``render-plan.json``.

    Usa o asset real quando disponível e cria um cartão substituto quando ainda
    falta avatar, B-roll ou captura. Isso permite validar o fluxo antes de todos
    os materiais finais existirem.
    """
    root = Path(package_dir).resolve()
    plan_path = root / "render-plan.json"
    if not plan_path.exists():
        raise RenderError(f"Plano não encontrado: {plan_path}")

    if not dry_run and shutil.which(ffmpeg_bin) is None:
        raise RenderError(
            "FFmpeg não encontrado. Instale o FFmpeg ou use --dry-run para gerar apenas o comando."
        )

    plan = json.loads(plan_path.read_text(encoding="utf-8"))
    _validate_plan(plan)

    generated_dir = root / "generated"
    segments_dir = generated_dir / "segments"
    generated_dir.mkdir(parents=True, exist_ok=True)
    segments_dir.mkdir(parents=True, exist_ok=True)

    segment_paths: list[Path] = []
    commands: list[list[str]] = []
    for layer in plan["layers"]:
        segment_path = segments_dir / f"scene-{int(layer['scene_index']):02d}.mp4"
        command = _segment_command(root, layer, plan["canvas"], segment_path, ffmpeg_bin)
        commands.append(command)
        segment_paths.append(segment_path)
        if not dry_run:
            _run(command)

    concat_file = generated_dir / "concat.txt"
    concat_file.write_text(
        "\n".join(f"file '{_concat_escape(path)}'" for path in segment_paths) + "\n",
        encoding="utf-8",
    )

    target = Path(output_file).resolve() if output_file else root / plan["output"]["filename"]
    final_command = [
        ffmpeg_bin,
        "-y",
        "-f",
        "concat",
        "-safe",
        "0",
        "-i",
        str(concat_file),
        "-c:v",
        "libx264",
        "-preset",
        "medium",
        "-crf",
        "20",
        "-pix_fmt",
        "yuv420p",
        "-movflags",
        "+faststart",
        str(target),
    ]
    commands.append(final_command)

    command_log = generated_dir / "ffmpeg-commands.json"
    command_log.write_text(json.dumps(commands, ensure_ascii=False, indent=2), encoding="utf-8")
    if not dry_run:
        _run(final_command)
    return target


def _validate_plan(plan: dict[str, Any]) -> None:
    required = {"canvas", "layers", "output"}
    missing = required.difference(plan)
    if missing:
        raise RenderError(f"render-plan.json incompleto: {', '.join(sorted(missing))}")
    if not plan["layers"]:
        raise RenderError("O plano de renderização não contém cenas.")


def _segment_command(
    root: Path,
    layer: dict[str, Any],
    canvas: dict[str, Any],
    output: Path,
    ffmpeg_bin: str,
) -> list[str]:
    duration = max(0.1, float(layer["end"]) - float(layer["start"]))
    width = int(canvas.get("width", 1080))
    height = int(canvas.get("height", 1920))
    fps = int(canvas.get("fps", 30))
    source = root / str(layer.get("source", ""))
    media = _resolve_media(source)
    text = str(layer.get("overlay_text", "")).strip()

    base = [ffmpeg_bin, "-y"]
    if media and media.suffix.lower() in {".mp4", ".mov", ".mkv", ".webm"}:
        base += ["-stream_loop", "-1", "-i", str(media), "-t", f"{duration:.3f}"]
        video_filter = _cover_filter(width, height, fps)
    elif media and media.suffix.lower() in {".png", ".jpg", ".jpeg", ".webp"}:
        base += ["-loop", "1", "-i", str(media), "-t", f"{duration:.3f}"]
        video_filter = _cover_filter(width, height, fps)
    else:
        background = _background_for(str(layer.get("source_type", "")))
        base += [
            "-f",
            "lavfi",
            "-i",
            f"color=c={background}:s={width}x{height}:r={fps}:d={duration:.3f}",
        ]
        video_filter = f"fps={fps},format=yuv420p"

    if text:
        video_filter += "," + _drawtext_filter(text, width, height)

    return base + [
        "-vf",
        video_filter,
        "-an",
        "-c:v",
        "libx264",
        "-preset",
        "veryfast",
        "-crf",
        "20",
        "-pix_fmt",
        "yuv420p",
        "-r",
        str(fps),
        str(output),
    ]


def _cover_filter(width: int, height: int, fps: int) -> str:
    return (
        f"scale={width}:{height}:force_original_aspect_ratio=increase,"
        f"crop={width}:{height},fps={fps},format=yuv420p"
    )


def _drawtext_filter(text: str, width: int, height: int) -> str:
    escaped = _ffmpeg_escape(text)
    font_size = max(44, int(width * 0.065))
    return (
        "drawtext="
        f"text='{escaped}':"
        "fontcolor=white:"
        f"fontsize={font_size}:"
        "borderw=4:bordercolor=black@0.75:"
        "box=1:boxcolor=black@0.38:boxborderw=24:"
        "x=(w-text_w)/2:"
        f"y={int(height * 0.72)}"
    )


def _resolve_media(source: Path) -> Path | None:
    if source.is_file():
        return source
    if source.suffix:
        return None
    for suffix in (".mp4", ".mov", ".png", ".jpg", ".jpeg", ".webp"):
        candidate = source.with_suffix(suffix)
        if candidate.is_file():
            return candidate
    return None


def _background_for(source_type: str) -> str:
    return {
        "generated_card": "0x111111",
        "video": "0x18202A",
        "image_or_video": "0x252525",
    }.get(source_type, "0x111111")


def _ffmpeg_escape(value: str) -> str:
    return (
        value.replace("\\", r"\\")
        .replace(":", r"\:")
        .replace("'", r"\'")
        .replace("%", r"\%")
        .replace("\n", " ")
    )


def _concat_escape(path: Path) -> str:
    return str(path).replace("'", "'\\''")


def _run(command: list[str]) -> None:
    completed = subprocess.run(command, capture_output=True, text=True, check=False)
    if completed.returncode != 0:
        detail = completed.stderr.strip()[-3000:]
        raise RenderError(f"FFmpeg falhou.\n{detail}")

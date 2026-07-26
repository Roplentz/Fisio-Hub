from __future__ import annotations

import json
import os
import shutil
import subprocess
from pathlib import Path
from typing import Any

from .visual_quality import get_preset, normalize_srt_text, subtitle_force_style


class RenderError(RuntimeError):
    """Falha controlada durante a renderização do vídeo."""


VIDEO_EXTENSIONS = {".mp4", ".mov", ".mkv", ".webm"}
IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp"}
AUDIO_EXTENSIONS = {".mp3", ".wav", ".m4a", ".aac", ".ogg", ".flac", ".webm"}
MAX_TEXT_LENGTH = 500


def render_video(
    package_dir: str | Path,
    *,
    output_file: str | Path | None = None,
    ffmpeg_bin: str = "ffmpeg",
    ffprobe_bin: str = "ffprobe",
    music_file: str | Path | None = None,
    burn_captions: bool = True,
    music_level_db: float = -25.0,
    dry_run: bool = False,
) -> Path:
    """Renderiza um vídeo vertical a partir de ``render-plan.json``."""
    root = _validate_root(package_dir)
    plan_path = _resolve_within(root, "render-plan.json", must_exist=True)

    if not dry_run:
        _require_binary(ffmpeg_bin, "FFmpeg")
        _require_binary(ffprobe_bin, "FFprobe")

    try:
        plan = json.loads(plan_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise RenderError(f"render-plan.json inválido: {exc.msg}") from exc

    _validate_plan(plan)

    generated_dir = _resolve_within(root, "generated")
    segments_dir = _resolve_within(generated_dir, "segments")
    generated_dir.mkdir(parents=True, exist_ok=True)
    segments_dir.mkdir(parents=True, exist_ok=True)

    commands: list[list[str]] = []
    segment_paths: list[Path] = []
    for layer in plan["layers"]:
        segment_path = _resolve_within(
            segments_dir, f"scene-{int(layer['scene_index']):02d}.mp4"
        )
        command = _segment_command(
            root=root,
            layer=layer,
            canvas=plan["canvas"],
            output=segment_path,
            ffmpeg_bin=ffmpeg_bin,
            ffprobe_bin=ffprobe_bin,
            dry_run=dry_run,
        )
        commands.append(command)
        segment_paths.append(segment_path)
        if not dry_run:
            _run(command)

    concat_file = _resolve_within(generated_dir, "concat.txt")
    concat_file.write_text(
        "\n".join(f"file '{_concat_escape(path)}'" for path in segment_paths) + "\n",
        encoding="utf-8",
    )

    stitched = _resolve_within(generated_dir, "stitched.mp4")
    concat_command = [
        ffmpeg_bin,
        "-y",
        "-f",
        "concat",
        "-safe",
        "0",
        "-i",
        str(concat_file),
        "-c",
        "copy",
        str(stitched),
    ]
    commands.append(concat_command)
    if not dry_run:
        _run(concat_command)

    if output_file is None:
        filename = _validate_filename(str(plan["output"]["filename"]))
        target = _resolve_within(root, filename)
    else:
        target = _validate_external_output(output_file)
    target.parent.mkdir(parents=True, exist_ok=True)

    final_command = _final_mix_command(
        root=root,
        stitched=stitched,
        target=target,
        ffmpeg_bin=ffmpeg_bin,
        music_file=music_file,
        burn_captions=burn_captions,
        music_level_db=music_level_db,
    )
    commands.append(final_command)

    command_log = _resolve_within(generated_dir, "ffmpeg-commands.json")
    command_log.write_text(
        json.dumps(commands, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    if not dry_run:
        _run(final_command)
    return target


def _validate_plan(plan: dict[str, Any]) -> None:
    if not isinstance(plan, dict):
        raise RenderError("render-plan.json deve conter um objeto JSON.")

    required = {"canvas", "layers", "output"}
    missing = required.difference(plan)
    if missing:
        raise RenderError(f"render-plan.json incompleto: {', '.join(sorted(missing))}")

    canvas = plan["canvas"]
    if not isinstance(canvas, dict):
        raise RenderError("canvas deve ser um objeto.")
    for key, default in (("width", 1080), ("height", 1920), ("fps", 30)):
        value = canvas.get(key, default)
        if not isinstance(value, (int, float)) or value <= 0:
            raise RenderError(f"canvas.{key} deve ser maior que zero.")

    layers = plan["layers"]
    if not isinstance(layers, list) or not layers:
        raise RenderError("O plano de renderização não contém cenas.")

    previous_start = -1.0
    seen_indexes: set[int] = set()
    for position, layer in enumerate(layers, start=1):
        if not isinstance(layer, dict):
            raise RenderError(f"A camada {position} deve ser um objeto.")
        try:
            scene_index = int(layer["scene_index"])
            start = float(layer["start"])
            end = float(layer["end"])
        except (KeyError, TypeError, ValueError) as exc:
            raise RenderError(f"A camada {position} possui campos inválidos.") from exc
        if scene_index < 0 or scene_index in seen_indexes:
            raise RenderError(f"scene_index inválido ou duplicado: {scene_index}.")
        if start < 0 or end <= start:
            raise RenderError(
                f"Intervalo inválido na cena {scene_index}: start={start}, end={end}."
            )
        if start < previous_start:
            raise RenderError("As camadas devem estar ordenadas por tempo inicial.")
        seen_indexes.add(scene_index)
        previous_start = start
        _validate_text(str(layer.get("overlay_text", "")), "overlay_text")

    output = plan["output"]
    if not isinstance(output, dict) or not output.get("filename"):
        raise RenderError("output.filename é obrigatório.")
    _validate_filename(str(output["filename"]))


def _segment_command(
    *,
    root: Path,
    layer: dict[str, Any],
    canvas: dict[str, Any],
    output: Path,
    ffmpeg_bin: str,
    ffprobe_bin: str,
    dry_run: bool,
) -> list[str]:
    duration = float(layer["end"]) - float(layer["start"])
    width = int(canvas.get("width", 1080))
    height = int(canvas.get("height", 1920))
    fps = int(canvas.get("fps", 30))
    text = _validate_text(str(layer.get("overlay_text", "")).strip(), "overlay_text")

    source_value = str(layer.get("source", "")).strip()
    source = _resolve_within(root, source_value) if source_value else root
    media = _resolve_media(source)

    command = [ffmpeg_bin, "-y"]
    has_source_audio = False
    if media and media.suffix.lower() in VIDEO_EXTENSIONS:
        command += ["-stream_loop", "-1", "-i", str(media), "-t", f"{duration:.3f}"]
        video_filter = _cover_filter(width, height, fps)
        has_source_audio = False if dry_run else _has_audio_stream(media, ffprobe_bin)
    elif media and media.suffix.lower() in IMAGE_EXTENSIONS:
        command += ["-loop", "1", "-i", str(media), "-t", f"{duration:.3f}"]
        video_filter = _cover_filter(width, height, fps)
    else:
        background = _background_for(str(layer.get("source_type", "")))
        command += [
            "-f",
            "lavfi",
            "-i",
            f"color=c={background}:s={width}x{height}:r={fps}:d={duration:.3f}",
        ]
        video_filter = f"fps={fps},format=yuv420p"

    if text:
        video_filter += "," + _drawtext_filter(text, width, height)

    audio_map = "0:a:0"
    if not has_source_audio:
        command += [
            "-f",
            "lavfi",
            "-t",
            f"{duration:.3f}",
            "-i",
            "anullsrc=channel_layout=stereo:sample_rate=48000",
        ]
        audio_map = "1:a:0"

    command += [
        "-vf",
        video_filter,
        "-map",
        "0:v:0",
        "-map",
        audio_map,
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
        "-c:a",
        "aac",
        "-ar",
        "48000",
        "-ac",
        "2",
        "-b:a",
        "160k",
        "-shortest",
        str(output),
    ]
    return command


def _final_mix_command(
    *,
    root: Path,
    stitched: Path,
    target: Path,
    ffmpeg_bin: str,
    music_file: str | Path | None,
    burn_captions: bool,
    music_level_db: float,
) -> list[str]:
    music = _resolve_music(root, music_file)
    captions = _resolve_within(root, "captions.srt")

    command = [ffmpeg_bin, "-y", "-i", str(stitched)]
    audio_filters: list[str] = []
    audio_map = "0:a:0"

    if music:
        command += ["-stream_loop", "-1", "-i", str(music)]
        gain = 10 ** (float(music_level_db) / 20.0)
        audio_filters.extend(
            [
                f"[1:a]volume={gain:.6f}[music]",
                "[0:a][music]amix=inputs=2:duration=first:dropout_transition=2[aout]",
            ]
        )
        audio_map = "[aout]"

    video_filters: list[str] = []
    if burn_captions and captions.exists():
        preset = get_preset()
        normalize_srt_text(captions, preset)
        subtitle_path = _subtitle_escape(captions)
        video_filters.append(
            f"subtitles='{subtitle_path}':force_style='{subtitle_force_style(preset)}'"
        )

    brand = _validate_text(
        os.getenv("VIRALLAB_BRAND_TEXT", "Prof. Dr. Rodrigo Plentz").strip(),
        "marca",
    )
    if brand:
        video_filters.append(_brand_drawtext_filter(brand))

    if audio_filters:
        command += ["-filter_complex", ";".join(audio_filters)]
    if video_filters:
        command += ["-vf", ",".join(video_filters)]

    command += ["-map", "0:v:0", "-map", audio_map]
    command += [
        "-c:v",
        "libx264",
        "-preset",
        "medium",
        "-crf",
        "20",
        "-pix_fmt",
        "yuv420p",
        "-c:a",
        "aac",
        "-b:a",
        "192k",
        "-movflags",
        "+faststart",
        "-shortest",
        str(target),
    ]
    return command


def _validate_root(value: str | Path) -> Path:
    raw = str(value)
    if "\x00" in raw:
        raise RenderError("Caminho inválido: contém byte nulo.")
    root = Path(value).expanduser().resolve()
    if not root.is_dir():
        raise RenderError(f"Diretório do projeto não encontrado: {root}")
    return root


def _resolve_within(root: Path, value: str | Path, *, must_exist: bool = False) -> Path:
    raw = str(value)
    if "\x00" in raw:
        raise RenderError("Caminho inválido: contém byte nulo.")
    candidate = (root / Path(value)).expanduser().resolve()
    try:
        candidate.relative_to(root.resolve())
    except ValueError as exc:
        raise RenderError(f"Caminho fora do projeto bloqueado: {value}") from exc
    if must_exist and not candidate.exists():
        raise RenderError(f"Arquivo não encontrado: {candidate}")
    return candidate


def _validate_external_output(value: str | Path) -> Path:
    raw = str(value)
    if "\x00" in raw:
        raise RenderError("Caminho de saída inválido.")
    path = Path(value).expanduser().resolve()
    if path.suffix.lower() != ".mp4":
        raise RenderError("O arquivo de saída deve usar a extensão .mp4.")
    return path


def _validate_filename(value: str) -> str:
    if not value or "\x00" in value:
        raise RenderError("Nome de arquivo de saída inválido.")
    path = Path(value)
    if path.is_absolute() or len(path.parts) != 1 or path.name in {".", ".."}:
        raise RenderError("output.filename deve ser apenas um nome de arquivo.")
    if path.suffix.lower() != ".mp4":
        raise RenderError("output.filename deve terminar em .mp4.")
    return path.name


def _validate_text(value: str, field: str) -> str:
    if len(value) > MAX_TEXT_LENGTH:
        raise RenderError(f"{field} excede {MAX_TEXT_LENGTH} caracteres.")
    if any(ord(char) < 32 and char not in {"\n", "\r", "\t"} for char in value):
        raise RenderError(f"{field} contém caracteres de controle inválidos.")
    return " ".join(value.replace("\r", " ").replace("\n", " ").replace("\t", " ").split())


def _require_binary(binary: str, label: str) -> None:
    if not binary or "\x00" in binary or shutil.which(binary) is None:
        raise RenderError(f"{label} não encontrado ou inválido: {binary!r}.")


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
        "expansion=none:fontcolor=white:"
        f"fontsize={font_size}:"
        "borderw=4:bordercolor=black@0.75:"
        "box=1:boxcolor=black@0.38:boxborderw=24:"
        "x=(w-text_w)/2:"
        f"y={int(height * 0.72)}"
    )


def _brand_drawtext_filter(text: str) -> str:
    escaped = _ffmpeg_escape(text)
    return (
        "drawtext="
        f"text='{escaped}':expansion=none:font='DejaVu Sans':"
        "fontcolor=white@0.58:fontsize=27:shadowx=1:shadowy=1:"
        "shadowcolor=black@0.35:x=w-text_w-54:y=106"
    )


def _has_audio_stream(media: Path, ffprobe_bin: str) -> bool:
    try:
        completed = subprocess.run(
            [
                ffprobe_bin,
                "-v",
                "error",
                "-select_streams",
                "a:0",
                "-show_entries",
                "stream=index",
                "-of",
                "csv=p=0",
                str(media),
            ],
            capture_output=True,
            text=True,
            check=False,
            timeout=30,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise RenderError(f"Falha ao executar FFprobe: {exc}") from exc
    return completed.returncode == 0 and bool(completed.stdout.strip())


def _resolve_media(source: Path) -> Path | None:
    if source.is_file() and source.suffix.lower() in VIDEO_EXTENSIONS | IMAGE_EXTENSIONS:
        return source
    if source.suffix:
        return None
    for suffix in (*VIDEO_EXTENSIONS, *IMAGE_EXTENSIONS):
        candidate = source.with_suffix(suffix)
        if candidate.is_file():
            return candidate
    return None


def _resolve_music(root: Path, music_file: str | Path | None) -> Path | None:
    if music_file:
        path = _resolve_within(root, music_file, must_exist=True)
        if path.suffix.lower() not in AUDIO_EXTENSIONS:
            raise RenderError(f"Formato de trilha não permitido: {path.suffix}")
        return path
    for relative in ("assets/music.mp3", "assets/music.wav"):
        candidate = _resolve_within(root, relative)
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
    replacements = {
        "\\": r"\\",
        "'": r"\'",
        ":": r"\:",
        "%": r"\%",
        "=": r"\=",
        ";": r"\;",
        "|": r"\|",
        "&": r"\&",
        '"': r'\"',
        "$": r"\$",
        "`": r"\`",
        "[": r"\[",
        "]": r"\]",
        ",": r"\,",
    }
    return "".join(replacements.get(char, char) for char in value)


def _subtitle_escape(path: Path) -> str:
    return (
        str(path)
        .replace("\\", "/")
        .replace(":", r"\:")
        .replace("'", r"\'")
        .replace("[", r"\[")
        .replace("]", r"\]")
    )


def _concat_escape(path: Path) -> str:
    return str(path).replace("'", "'\\''")


def _run(command: list[str]) -> None:
    if not command or any("\x00" in argument for argument in command):
        raise RenderError("Comando FFmpeg inválido.")
    try:
        completed = subprocess.run(
            command,
            capture_output=True,
            text=True,
            check=False,
            timeout=600,
        )
    except subprocess.TimeoutExpired as exc:
        raise RenderError("FFmpeg excedeu o tempo limite de 10 minutos.") from exc
    except OSError as exc:
        raise RenderError(f"Não foi possível iniciar o FFmpeg: {exc}") from exc
    if completed.returncode != 0:
        detail = completed.stderr.strip()[-3000:] or "sem detalhes"
        raise RenderError(f"FFmpeg falhou.\n{detail}")

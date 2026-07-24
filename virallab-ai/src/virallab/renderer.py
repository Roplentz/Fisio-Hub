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
    ffprobe_bin: str = "ffprobe",
    music_file: str | Path | None = None,
    burn_captions: bool = True,
    music_level_db: float = -25.0,
    dry_run: bool = False,
) -> Path:
    """Renderiza um vídeo vertical completo a partir de ``render-plan.json``.

    Recursos do renderizador v0.3:
    - preserva o áudio dos clipes de avatar;
    - cria silêncio nos trechos sem áudio para manter a concatenação estável;
    - aceita trilha opcional com redução automática de volume;
    - queima ``captions.srt`` no vídeo final;
    - usa cartões substitutos quando algum asset ainda não existe.
    """
    root = Path(package_dir).resolve()
    plan_path = root / "render-plan.json"
    if not plan_path.exists():
        raise RenderError(f"Plano não encontrado: {plan_path}")

    if not dry_run:
        if shutil.which(ffmpeg_bin) is None:
            raise RenderError("FFmpeg não encontrado. Instale o FFmpeg ou use --render-dry-run.")
        if shutil.which(ffprobe_bin) is None:
            raise RenderError("FFprobe não encontrado. Ele normalmente é instalado junto com o FFmpeg.")

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
        command = _segment_command(
            root,
            layer,
            plan["canvas"],
            segment_path,
            ffmpeg_bin,
            ffprobe_bin,
            dry_run,
        )
        commands.append(command)
        segment_paths.append(segment_path)
        if not dry_run:
            _run(command)

    concat_file = generated_dir / "concat.txt"
    concat_file.write_text(
        "\n".join(f"file '{_concat_escape(path)}'" for path in segment_paths) + "\n",
        encoding="utf-8",
    )

    stitched = generated_dir / "stitched.mp4"
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

    target = Path(output_file).resolve() if output_file else root / plan["output"]["filename"]
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
    ffprobe_bin: str,
    dry_run: bool,
) -> list[str]:
    duration = max(0.1, float(layer["end"]) - float(layer["start"]))
    width = int(canvas.get("width", 1080))
    height = int(canvas.get("height", 1920))
    fps = int(canvas.get("fps", 30))
    source = root / str(layer.get("source", ""))
    media = _resolve_media(source)
    text = str(layer.get("overlay_text", "")).strip()

    base = [ffmpeg_bin, "-y"]
    has_source_audio = False
    if media and media.suffix.lower() in {".mp4", ".mov", ".mkv", ".webm"}:
        base += ["-stream_loop", "-1", "-i", str(media), "-t", f"{duration:.3f}"]
        video_filter = _cover_filter(width, height, fps)
        has_source_audio = False if dry_run else _has_audio_stream(media, ffprobe_bin)
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

    if has_source_audio:
        audio_inputs: list[str] = []
        audio_map = ["-map", "0:a:0"]
    else:
        base += [
            "-f",
            "lavfi",
            "-t",
            f"{duration:.3f}",
            "-i",
            "anullsrc=channel_layout=stereo:sample_rate=48000",
        ]
        audio_inputs = []
        audio_map = ["-map", "1:a:0"]

    return base + audio_inputs + [
        "-vf",
        video_filter,
        "-map",
        "0:v:0",
        *audio_map,
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
    captions = root / "captions.srt"

    command = [ffmpeg_bin, "-y", "-i", str(stitched)]
    filters: list[str] = []
    audio_map = "0:a:0"

    if music:
        command += ["-stream_loop", "-1", "-i", str(music)]
        gain = 10 ** (music_level_db / 20.0)
        filters.append(f"[1:a]volume={gain:.6f}[music]")
        filters.append("[0:a][music]amix=inputs=2:duration=first:dropout_transition=2[aout]")
        audio_map = "[aout]"

    video_filter = None
    if burn_captions and captions.exists():
        subtitle_path = _subtitle_escape(captions)
        video_filter = (
            f"subtitles='{subtitle_path}':"
            "force_style='FontName=Arial,FontSize=18,PrimaryColour=&H00FFFFFF,"
            "OutlineColour=&H00000000,BorderStyle=1,Outline=3,Shadow=0,"
            "Alignment=2,MarginV=180'"
        )

    if filters:
        command += ["-filter_complex", ";".join(filters)]
    if video_filter:
        command += ["-vf", video_filter]

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


def _has_audio_stream(media: Path, ffprobe_bin: str) -> bool:
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
    )
    return completed.returncode == 0 and bool(completed.stdout.strip())


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


def _resolve_music(root: Path, music_file: str | Path | None) -> Path | None:
    if music_file:
        path = Path(music_file)
        if not path.is_absolute():
            path = root / path
        if not path.is_file():
            raise RenderError(f"Trilha não encontrada: {path}")
        return path
    for candidate in (root / "assets" / "music.mp3", root / "assets" / "music.wav"):
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


def _subtitle_escape(path: Path) -> str:
    return str(path).replace("\\", "/").replace(":", r"\:").replace("'", r"\'")


def _concat_escape(path: Path) -> str:
    return str(path).replace("'", "'\\''")


def _run(command: list[str]) -> None:
    completed = subprocess.run(command, capture_output=True, text=True, check=False)
    if completed.returncode != 0:
        detail = completed.stderr.strip()[-3000:]
        raise RenderError(f"FFmpeg falhou.\n{detail}")

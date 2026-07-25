from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

from .renderer import RenderError, render_video
from .voice import narration_path


def render_video_with_voice(
    package_dir: str | Path,
    *,
    output_file: str | Path | None = None,
    burn_captions: bool = True,
    music_level_db: float = -25.0,
    dry_run: bool = False,
    narration_gain_db: float = 0.0,
    ffmpeg_bin: str = "ffmpeg",
) -> Path:
    """Renderiza o vídeo e aplica a narração gravada como faixa principal."""
    root = Path(package_dir).resolve()
    narration = narration_path(root)
    if narration is None:
        return render_video(
            root,
            output_file=output_file,
            burn_captions=burn_captions,
            music_level_db=music_level_db,
            dry_run=dry_run,
        )

    silent_target = root / "generated" / "video-without-narration.mp4"
    base_video = render_video(
        root,
        output_file=silent_target,
        burn_captions=burn_captions,
        music_level_db=music_level_db,
        dry_run=dry_run,
    )
    target = Path(output_file).resolve() if output_file else root / "video-final.mp4"
    if dry_run:
        return target
    if shutil.which(ffmpeg_bin) is None:
        raise RenderError("FFmpeg não encontrado para aplicar a narração.")

    gain = 10 ** (narration_gain_db / 20.0)
    command = [
        ffmpeg_bin,
        "-y",
        "-i",
        str(base_video),
        "-i",
        str(narration),
        "-filter_complex",
        f"[1:a]volume={gain:.6f},aresample=48000[narration]",
        "-map",
        "0:v:0",
        "-map",
        "[narration]",
        "-c:v",
        "copy",
        "-c:a",
        "aac",
        "-b:a",
        "192k",
        "-movflags",
        "+faststart",
        "-shortest",
        str(target),
    ]
    completed = subprocess.run(command, capture_output=True, text=True, check=False)
    if completed.returncode != 0:
        raise RenderError(
            f"Falha ao aplicar a narração.\n{completed.stderr.strip()[-3000:]}"
        )
    return target


__all__ = ["render_video_with_voice"]

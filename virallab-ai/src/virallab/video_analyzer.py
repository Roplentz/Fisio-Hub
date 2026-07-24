from __future__ import annotations

import json
import re
import shutil
import subprocess
from dataclasses import asdict, dataclass
from pathlib import Path


class VideoAnalysisError(RuntimeError):
    """Raised when a video cannot be inspected safely."""


@dataclass(slots=True)
class VideoAnalysis:
    duration_seconds: float
    width: int
    height: int
    fps: float
    video_codec: str
    has_audio: bool
    audio_codec: str | None
    orientation: str
    aspect_ratio: float
    cut_times: list[float]
    estimated_scenes: int
    average_scene_seconds: float
    cuts_first_3_seconds: int
    hook_score: int
    pacing_score: int
    format_score: int
    technical_score: int
    viral_potential_score: int
    summary: str
    strengths: list[str]
    improvements: list[str]

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


def _run(command: list[str]) -> subprocess.CompletedProcess[str]:
    try:
        return subprocess.run(command, check=True, capture_output=True, text=True)
    except FileNotFoundError as exc:
        raise VideoAnalysisError("FFmpeg/FFprobe não está disponível neste ambiente.") from exc
    except subprocess.CalledProcessError as exc:
        detail = (exc.stderr or exc.stdout or "Erro desconhecido").strip()
        raise VideoAnalysisError(detail[-1000:]) from exc


def _parse_fps(value: str | None) -> float:
    if not value or value in {"0/0", "N/A"}:
        return 0.0
    if "/" in value:
        numerator, denominator = value.split("/", 1)
        try:
            return float(numerator) / float(denominator)
        except (ValueError, ZeroDivisionError):
            return 0.0
    try:
        return float(value)
    except ValueError:
        return 0.0


def _probe(path: Path) -> dict[str, object]:
    if shutil.which("ffprobe") is None:
        raise VideoAnalysisError("FFprobe não foi encontrado.")
    result = _run(
        [
            "ffprobe",
            "-v",
            "error",
            "-show_streams",
            "-show_format",
            "-of",
            "json",
            str(path),
        ]
    )
    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError as exc:
        raise VideoAnalysisError("O FFprobe retornou dados inválidos.") from exc


def _detect_cuts(path: Path, threshold: float = 0.30, max_seconds: float = 120.0) -> list[float]:
    if shutil.which("ffmpeg") is None:
        raise VideoAnalysisError("FFmpeg não foi encontrado.")
    command = [
        "ffmpeg",
        "-hide_banner",
        "-t",
        str(max_seconds),
        "-i",
        str(path),
        "-filter:v",
        f"select='gt(scene,{threshold})',showinfo",
        "-f",
        "null",
        "-",
    ]
    try:
        result = subprocess.run(command, check=False, capture_output=True, text=True)
    except FileNotFoundError as exc:
        raise VideoAnalysisError("FFmpeg não foi encontrado.") from exc
    matches = re.findall(r"pts_time:([0-9]+(?:\.[0-9]+)?)", result.stderr or "")
    return sorted({round(float(item), 3) for item in matches if float(item) > 0.05})


def _clamp(value: float) -> int:
    return max(0, min(100, round(value)))


def analyze_video(path: str | Path, scene_threshold: float = 0.30) -> VideoAnalysis:
    video_path = Path(path)
    if not video_path.exists() or not video_path.is_file():
        raise VideoAnalysisError("Arquivo de vídeo não encontrado.")

    data = _probe(video_path)
    streams = data.get("streams", [])
    if not isinstance(streams, list):
        raise VideoAnalysisError("Não foi possível ler as faixas do vídeo.")

    video_stream = next((item for item in streams if item.get("codec_type") == "video"), None)
    audio_stream = next((item for item in streams if item.get("codec_type") == "audio"), None)
    if not isinstance(video_stream, dict):
        raise VideoAnalysisError("O arquivo enviado não contém uma faixa de vídeo válida.")

    format_data = data.get("format", {}) if isinstance(data.get("format"), dict) else {}
    duration_raw = format_data.get("duration") or video_stream.get("duration") or 0
    try:
        duration = max(0.01, float(duration_raw))
    except (TypeError, ValueError):
        duration = 0.01

    width = int(video_stream.get("width") or 0)
    height = int(video_stream.get("height") or 0)
    ratio = width / height if height else 0.0
    orientation = "vertical" if height > width else "horizontal" if width > height else "quadrado"
    fps = _parse_fps(str(video_stream.get("avg_frame_rate") or video_stream.get("r_frame_rate") or "0"))
    cut_times = _detect_cuts(video_path, threshold=scene_threshold)
    scene_count = max(1, len(cut_times) + 1)
    average_scene = duration / scene_count
    early_cuts = sum(1 for cut in cut_times if cut <= 3.0)

    hook_score = _clamp(52 + early_cuts * 16 + (8 if duration <= 75 else -5))
    ideal_scene = 3.2
    pacing_score = _clamp(100 - abs(average_scene - ideal_scene) * 17)
    format_score = _clamp(95 if orientation == "vertical" and 0.50 <= ratio <= 0.67 else 70 if orientation == "quadrado" else 42)
    technical_score = _clamp(50 + (15 if width >= 1080 else 8 if width >= 720 else 0) + (12 if fps >= 29 else 5) + (12 if audio_stream else 0))
    viral_score = _clamp(hook_score * 0.30 + pacing_score * 0.30 + format_score * 0.20 + technical_score * 0.20)

    strengths: list[str] = []
    improvements: list[str] = []
    if orientation == "vertical":
        strengths.append("Formato vertical adequado para Reels, Shorts e TikTok.")
    else:
        improvements.append("Adaptar o enquadramento para 9:16 para melhorar o uso em redes verticais.")
    if early_cuts >= 1:
        strengths.append("Há mudança visual nos primeiros 3 segundos, favorecendo o hook.")
    else:
        improvements.append("Inserir uma mudança visual ou texto de impacto nos primeiros 3 segundos.")
    if 1.8 <= average_scene <= 5.5:
        strengths.append("O ritmo médio de cenas está dentro de uma faixa dinâmica.")
    elif average_scene > 5.5:
        improvements.append("Reduzir a duração média das cenas ou adicionar B-roll para evitar monotonia.")
    else:
        improvements.append("Alguns cortes podem estar rápidos demais; preserve tempo para compreensão.")
    if audio_stream:
        strengths.append("O arquivo contém faixa de áudio, permitindo futura transcrição e análise da fala.")
    else:
        improvements.append("O vídeo não possui áudio detectável; a análise semântica ficará limitada.")

    summary = (
        f"Vídeo {orientation}, com {duration:.1f}s e aproximadamente {scene_count} cenas. "
        f"A duração média estimada por cena é {average_scene:.1f}s. "
        f"O potencial estrutural calculado para conteúdo curto é {viral_score}/100."
    )

    return VideoAnalysis(
        duration_seconds=round(duration, 2),
        width=width,
        height=height,
        fps=round(fps, 2),
        video_codec=str(video_stream.get("codec_name") or "desconhecido"),
        has_audio=audio_stream is not None,
        audio_codec=str(audio_stream.get("codec_name")) if isinstance(audio_stream, dict) else None,
        orientation=orientation,
        aspect_ratio=round(ratio, 3),
        cut_times=cut_times,
        estimated_scenes=scene_count,
        average_scene_seconds=round(average_scene, 2),
        cuts_first_3_seconds=early_cuts,
        hook_score=hook_score,
        pacing_score=pacing_score,
        format_score=format_score,
        technical_score=technical_score,
        viral_potential_score=viral_score,
        summary=summary,
        strengths=strengths,
        improvements=improvements,
    )

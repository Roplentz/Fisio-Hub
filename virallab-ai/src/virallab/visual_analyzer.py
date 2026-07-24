from __future__ import annotations

import json
import shutil
import subprocess
import tempfile
from dataclasses import asdict, dataclass
from pathlib import Path


class VisualAnalysisError(RuntimeError):
    """Raised when visual reverse engineering cannot be completed."""


@dataclass(slots=True)
class VisualMoment:
    start: float
    end: float
    frame_path: str
    face_count: int
    face_area_ratio: float
    brightness: float
    sharpness: float
    text_density: float
    detected_text: str | None
    shot_type: str
    visual_role: str

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(slots=True)
class VisualAnalysis:
    moments: list[VisualMoment]
    face_presence_ratio: float
    text_presence_ratio: float
    average_brightness: float
    average_sharpness: float
    framing_changes: int
    dominant_shot_type: str
    key_frame_paths: list[str]
    summary: str
    strengths: list[str]
    improvements: list[str]

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


def _run(command: list[str]) -> subprocess.CompletedProcess[str]:
    try:
        return subprocess.run(command, check=True, capture_output=True, text=True)
    except FileNotFoundError as exc:
        raise VisualAnalysisError(f"Dependência não encontrada: {command[0]}.") from exc
    except subprocess.CalledProcessError as exc:
        detail = (exc.stderr or exc.stdout or "Erro desconhecido").strip()
        raise VisualAnalysisError(detail[-1200:]) from exc


def _duration(path: Path) -> float:
    result = _run([
        "ffprobe", "-v", "error", "-show_entries", "format=duration",
        "-of", "json", str(path),
    ])
    try:
        value = json.loads(result.stdout)["format"]["duration"]
        return max(0.01, float(value))
    except (KeyError, TypeError, ValueError, json.JSONDecodeError) as exc:
        raise VisualAnalysisError("Não foi possível determinar a duração do vídeo.") from exc


def _scene_boundaries(path: Path, threshold: float, duration: float) -> list[tuple[float, float]]:
    command = [
        "ffmpeg", "-hide_banner", "-i", str(path), "-filter:v",
        f"select='gt(scene,{threshold})',metadata=print:file=-", "-an", "-f", "null", "-",
    ]
    result = subprocess.run(command, check=False, capture_output=True, text=True)
    times: list[float] = []
    for line in (result.stdout + "\n" + result.stderr).splitlines():
        if "pts_time:" in line:
            try:
                times.append(float(line.split("pts_time:", 1)[1].split()[0]))
            except (ValueError, IndexError):
                continue
    boundaries = sorted({round(item, 3) for item in times if 0.15 < item < duration - 0.15})
    points = [0.0, *boundaries, duration]
    return [(points[index], points[index + 1]) for index in range(len(points) - 1)]


def _extract_frame(path: Path, timestamp: float, target: Path) -> None:
    _run([
        "ffmpeg", "-hide_banner", "-loglevel", "error", "-ss", f"{timestamp:.3f}",
        "-i", str(path), "-frames:v", "1", "-q:v", "2", "-y", str(target),
    ])


def _load_cv2():
    try:
        import cv2
        import numpy as np
    except ImportError as exc:
        raise VisualAnalysisError(
            "A análise visual requer opencv-python-headless e numpy."
        ) from exc
    return cv2, np


def _ocr_text(image) -> str | None:
    if shutil.which("tesseract") is None:
        return None
    try:
        import pytesseract
    except ImportError:
        return None
    try:
        text = " ".join(pytesseract.image_to_string(image, lang="por+eng").split())
        return text[:500] or None
    except Exception:
        return None


def _visual_role(index: int, total: int, face_count: int, text_density: float) -> str:
    fraction = index / max(total - 1, 1)
    if index == 0:
        return "Hook visual"
    if fraction >= 0.82:
        return "Fechamento/CTA"
    if face_count == 0 and text_density >= 0.08:
        return "Tela de apoio ou evidência"
    if face_count == 0:
        return "B-roll ou demonstração"
    return "Apresentação principal"


def _inspect_frame(frame_path: Path, start: float, end: float, index: int, total: int) -> VisualMoment:
    cv2, np = _load_cv2()
    image = cv2.imread(str(frame_path))
    if image is None:
        raise VisualAnalysisError(f"Não foi possível ler o frame {frame_path.name}.")

    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    height, width = gray.shape[:2]
    brightness = float(np.mean(gray))
    sharpness = float(cv2.Laplacian(gray, cv2.CV_64F).var())

    cascade_path = cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
    cascade = cv2.CascadeClassifier(cascade_path)
    faces = cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(40, 40))
    face_count = len(faces)
    largest_face = max((w * h for _, _, w, h in faces), default=0)
    face_area_ratio = largest_face / max(width * height, 1)

    edges = cv2.Canny(gray, 80, 180)
    upper = edges[: max(1, height // 3)]
    lower = edges[min(height - 1, (height * 2) // 3) :]
    text_density = float((np.mean(upper > 0) + np.mean(lower > 0)) / 2)

    if face_area_ratio >= 0.20:
        shot_type = "close-up"
    elif face_area_ratio >= 0.07:
        shot_type = "plano médio"
    elif face_count:
        shot_type = "plano aberto"
    else:
        shot_type = "sem rosto"

    detected_text = _ocr_text(image)
    role = _visual_role(index, total, face_count, text_density)
    return VisualMoment(
        start=round(start, 2),
        end=round(end, 2),
        frame_path=str(frame_path),
        face_count=face_count,
        face_area_ratio=round(face_area_ratio, 4),
        brightness=round(brightness, 1),
        sharpness=round(sharpness, 1),
        text_density=round(text_density, 4),
        detected_text=detected_text,
        shot_type=shot_type,
        visual_role=role,
    )


def analyze_visuals(
    path: str | Path,
    output_dir: str | Path | None = None,
    scene_threshold: float = 0.30,
    max_moments: int = 18,
) -> VisualAnalysis:
    video_path = Path(path)
    if not video_path.exists() or not video_path.is_file():
        raise VisualAnalysisError("Arquivo de vídeo não encontrado.")
    if shutil.which("ffmpeg") is None or shutil.which("ffprobe") is None:
        raise VisualAnalysisError("FFmpeg e FFprobe precisam estar instalados.")

    duration = _duration(video_path)
    scenes = _scene_boundaries(video_path, scene_threshold, duration)
    if len(scenes) > max_moments:
        step = len(scenes) / max_moments
        scenes = [scenes[min(round(index * step), len(scenes) - 1)] for index in range(max_moments)]

    if output_dir is None:
        output_root = Path(tempfile.mkdtemp(prefix="virallab-frames-"))
    else:
        output_root = Path(output_dir)
        output_root.mkdir(parents=True, exist_ok=True)

    moments: list[VisualMoment] = []
    for index, (start, end) in enumerate(scenes):
        timestamp = start + max(0.05, (end - start) / 2)
        frame_path = output_root / f"frame-{index + 1:03d}-{timestamp:.2f}s.jpg"
        _extract_frame(video_path, timestamp, frame_path)
        moments.append(_inspect_frame(frame_path, start, end, index, len(scenes)))

    if not moments:
        raise VisualAnalysisError("Nenhum momento visual pôde ser analisado.")

    face_presence = sum(item.face_count > 0 for item in moments) / len(moments)
    text_presence = sum(bool(item.detected_text) or item.text_density >= 0.08 for item in moments) / len(moments)
    average_brightness = sum(item.brightness for item in moments) / len(moments)
    average_sharpness = sum(item.sharpness for item in moments) / len(moments)
    framing_changes = sum(
        moments[index].shot_type != moments[index - 1].shot_type
        for index in range(1, len(moments))
    )
    shot_counts: dict[str, int] = {}
    for item in moments:
        shot_counts[item.shot_type] = shot_counts.get(item.shot_type, 0) + 1
    dominant_shot = max(shot_counts, key=shot_counts.get)

    strengths: list[str] = []
    improvements: list[str] = []
    if face_presence >= 0.55:
        strengths.append("A presença humana é consistente e favorece conexão e autoridade.")
    else:
        improvements.append("Avaliar maior presença do apresentador ou uma alternância mais intencional com B-roll.")
    if text_presence >= 0.40:
        strengths.append("Há apoio visual frequente por textos ou elementos gráficos.")
    else:
        improvements.append("Adicionar palavras-chave na tela para reforçar compreensão sem áudio.")
    if framing_changes >= max(1, len(moments) // 4):
        strengths.append("O enquadramento apresenta variação visual ao longo do vídeo.")
    else:
        improvements.append("Criar mudanças de enquadramento, zoom ou B-roll em pontos narrativos importantes.")
    if average_brightness < 55:
        improvements.append("A imagem parece escura em parte relevante do vídeo; revisar iluminação e exposição.")
    if average_sharpness < 45:
        improvements.append("Alguns frames parecem pouco nítidos; revisar foco, compressão ou estabilidade.")

    summary = (
        f"Foram examinados {len(moments)} momentos visuais. Há rosto em {face_presence:.0%} deles, "
        f"apoio textual estimado em {text_presence:.0%} e {framing_changes} mudanças de enquadramento. "
        f"O enquadramento dominante é {dominant_shot}."
    )
    return VisualAnalysis(
        moments=moments,
        face_presence_ratio=round(face_presence, 3),
        text_presence_ratio=round(text_presence, 3),
        average_brightness=round(average_brightness, 1),
        average_sharpness=round(average_sharpness, 1),
        framing_changes=framing_changes,
        dominant_shot_type=dominant_shot,
        key_frame_paths=[item.frame_path for item in moments],
        summary=summary,
        strengths=strengths,
        improvements=improvements,
    )

from __future__ import annotations

import json
import shutil
import subprocess
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Iterable


class VoiceError(RuntimeError):
    """Falha controlada no fluxo de narração."""


AUDIO_EXTENSIONS = {".wav", ".mp3", ".m4a", ".aac", ".ogg", ".webm", ".flac"}
MIN_AUDIO_BYTES = 1024


@dataclass(frozen=True)
class SceneVoiceTiming:
    scene_index: int
    start: float
    end: float
    text: str


@dataclass(frozen=True)
class VoicePlan:
    audio_file: str
    duration: float
    mode: str
    scenes: list[SceneVoiceTiming]

    def to_dict(self) -> dict[str, Any]:
        return {
            "audio_file": self.audio_file,
            "duration": self.duration,
            "mode": self.mode,
            "scenes": [asdict(item) for item in self.scenes],
        }


def save_narration(
    project_dir: str | Path,
    data: bytes,
    *,
    filename: str = "narration.wav",
    ffprobe_bin: str = "ffprobe",
) -> VoicePlan:
    root = Path(project_dir).expanduser().resolve()
    if not root.is_dir():
        raise VoiceError(f"Diretório do projeto não encontrado: {root}")
    if len(data) < MIN_AUDIO_BYTES:
        raise VoiceError("O arquivo de áudio está vazio ou incompleto.")

    suffix = Path(filename).suffix.lower() or ".wav"
    if suffix not in AUDIO_EXTENSIONS:
        raise VoiceError(f"Formato de áudio não permitido: {suffix}")

    assets = (root / "assets").resolve()
    _ensure_within(root, assets)
    assets.mkdir(parents=True, exist_ok=True)
    target = (assets / f"narration{suffix}").resolve()
    _ensure_within(root, target)

    for extension in AUDIO_EXTENSIONS:
        existing = assets / f"narration{extension}"
        if existing.is_file():
            existing.unlink()

    target.write_bytes(data)
    if target.stat().st_size < MIN_AUDIO_BYTES:
        target.unlink(missing_ok=True)
        raise VoiceError("O arquivo de narração salvo está incompleto.")

    duration = probe_duration(target, ffprobe_bin=ffprobe_bin)
    plan = VoicePlan(
        audio_file=str(target.relative_to(root)),
        duration=duration,
        mode="full",
        scenes=[],
    )
    save_voice_plan(root, plan)
    return plan


def probe_duration(path: str | Path, *, ffprobe_bin: str = "ffprobe") -> float:
    media = Path(path).expanduser().resolve()
    if not media.is_file():
        raise VoiceError(f"Áudio não encontrado: {media}")
    if media.suffix.lower() not in AUDIO_EXTENSIONS:
        raise VoiceError(f"Formato de áudio não permitido: {media.suffix}")
    if media.stat().st_size < MIN_AUDIO_BYTES:
        raise VoiceError("O arquivo de áudio está vazio ou incompleto.")
    if shutil.which(ffprobe_bin) is None:
        raise VoiceError(
            "FFprobe não encontrado. Instale o FFmpeg para medir a duração da narração."
        )

    try:
        completed = subprocess.run(
            [
                ffprobe_bin,
                "-v",
                "error",
                "-show_entries",
                "format=duration",
                "-of",
                "default=noprint_wrappers=1:nokey=1",
                str(media),
            ],
            capture_output=True,
            text=True,
            check=False,
            timeout=30,
        )
    except subprocess.TimeoutExpired as exc:
        raise VoiceError("FFprobe excedeu o tempo limite ao analisar o áudio.") from exc
    except OSError as exc:
        raise VoiceError(f"Não foi possível executar o FFprobe: {exc}") from exc

    if completed.returncode != 0:
        raise VoiceError(
            completed.stderr.strip()[-1000:] or "Não foi possível medir o áudio."
        )
    try:
        duration = float(completed.stdout.strip())
    except ValueError as exc:
        raise VoiceError("Duração de áudio inválida.") from exc
    if duration <= 0:
        raise VoiceError("A duração do áudio deve ser maior que zero.")
    return duration


def align_scenes_by_script(
    scenes: Iterable[Any],
    *,
    duration: float,
) -> list[SceneVoiceTiming]:
    scene_list = list(scenes)
    if not scene_list:
        return []
    if duration <= 0:
        raise VoiceError("A duração total da narração deve ser maior que zero.")

    weights: list[int] = []
    for scene in scene_list:
        text = str(getattr(scene, "narration", "") or "").strip()
        weights.append(max(1, len(text.split())))
    total = sum(weights)
    cursor = 0.0
    result: list[SceneVoiceTiming] = []
    for position, (scene, weight) in enumerate(zip(scene_list, weights, strict=True)):
        share = duration * weight / total
        end = duration if position == len(scene_list) - 1 else cursor + share
        result.append(
            SceneVoiceTiming(
                scene_index=int(getattr(scene, "index", position + 1)),
                start=round(cursor, 3),
                end=round(end, 3),
                text=str(getattr(scene, "narration", "") or "").strip(),
            )
        )
        cursor = end
    return result


def save_voice_plan(project_dir: str | Path, plan: VoicePlan) -> Path:
    root = Path(project_dir).expanduser().resolve()
    if not root.is_dir():
        raise VoiceError(f"Diretório do projeto não encontrado: {root}")
    target = (root / "voice-plan.json").resolve()
    _ensure_within(root, target)
    target.write_text(
        json.dumps(plan.to_dict(), ensure_ascii=False, indent=2), encoding="utf-8"
    )
    return target


def update_voice_plan_with_scenes(
    project_dir: str | Path,
    scenes: Iterable[Any],
    *,
    duration: float,
    audio_file: str,
    mode: str = "full",
) -> VoicePlan:
    plan = VoicePlan(
        audio_file=audio_file,
        duration=duration,
        mode=mode,
        scenes=align_scenes_by_script(scenes, duration=duration),
    )
    save_voice_plan(project_dir, plan)
    return plan


def load_voice_plan(project_dir: str | Path) -> VoicePlan | None:
    root = Path(project_dir).expanduser().resolve()
    path = (root / "voice-plan.json").resolve()
    _ensure_within(root, path)
    if not path.is_file():
        return None
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
        duration = float(raw.get("duration", 0.0))
        if duration <= 0:
            raise VoiceError("voice-plan.json possui duração inválida.")
        return VoicePlan(
            audio_file=str(raw.get("audio_file", "")),
            duration=duration,
            mode=str(raw.get("mode", "full")),
            scenes=[SceneVoiceTiming(**item) for item in raw.get("scenes", [])],
        )
    except (json.JSONDecodeError, TypeError, ValueError, KeyError) as exc:
        raise VoiceError("voice-plan.json inválido.") from exc


def narration_path(project_dir: str | Path) -> Path | None:
    root = Path(project_dir).expanduser().resolve()
    plan = load_voice_plan(root)
    if plan and plan.audio_file:
        candidate = (root / plan.audio_file).resolve()
        _ensure_within(root, candidate)
        if (
            candidate.is_file()
            and candidate.suffix.lower() in AUDIO_EXTENSIONS
            and candidate.stat().st_size >= MIN_AUDIO_BYTES
        ):
            return candidate
    assets = (root / "assets").resolve()
    _ensure_within(root, assets)
    for extension in sorted(AUDIO_EXTENSIONS):
        candidate = assets / f"narration{extension}"
        if candidate.is_file() and candidate.stat().st_size >= MIN_AUDIO_BYTES:
            return candidate
    return None


def _ensure_within(root: Path, candidate: Path) -> None:
    try:
        candidate.resolve().relative_to(root.resolve())
    except ValueError as exc:
        raise VoiceError(f"Caminho fora do projeto bloqueado: {candidate}") from exc


__all__ = [
    "SceneVoiceTiming",
    "VoiceError",
    "VoicePlan",
    "align_scenes_by_script",
    "load_voice_plan",
    "narration_path",
    "probe_duration",
    "save_narration",
    "save_voice_plan",
    "update_voice_plan_with_scenes",
]

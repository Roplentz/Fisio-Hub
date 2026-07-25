from __future__ import annotations

import json
import shutil
import subprocess
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Iterable


class VoiceError(RuntimeError):
    """Falha controlada no fluxo de narração."""


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
    root = Path(project_dir)
    assets = root / "assets"
    assets.mkdir(parents=True, exist_ok=True)
    suffix = Path(filename).suffix.lower() or ".wav"
    target = assets / f"narration{suffix}"
    for existing in assets.glob("narration.*"):
        existing.unlink(missing_ok=True)
    target.write_bytes(data)
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
    media = Path(path)
    if not media.is_file():
        raise VoiceError(f"Áudio não encontrado: {media}")
    if shutil.which(ffprobe_bin) is None:
        return 0.0
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
    )
    if completed.returncode != 0:
        raise VoiceError(
            completed.stderr.strip()[-1000:] or "Não foi possível medir o áudio."
        )
    try:
        return max(0.0, float(completed.stdout.strip()))
    except ValueError as exc:
        raise VoiceError("Duração de áudio inválida.") from exc


def align_scenes_by_script(
    scenes: Iterable[Any],
    *,
    duration: float,
) -> list[SceneVoiceTiming]:
    scene_list = list(scenes)
    if not scene_list:
        return []
    weights = []
    for scene in scene_list:
        text = str(getattr(scene, "narration", "") or "").strip()
        weights.append(max(1, len(text.split())))
    total = sum(weights)
    cursor = 0.0
    result: list[SceneVoiceTiming] = []
    for position, (scene, weight) in enumerate(zip(scene_list, weights, strict=True)):
        share = duration * weight / total if duration > 0 else 0.0
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
    target = Path(project_dir) / "voice-plan.json"
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
    path = Path(project_dir) / "voice-plan.json"
    if not path.is_file():
        return None
    raw = json.loads(path.read_text(encoding="utf-8"))
    return VoicePlan(
        audio_file=str(raw.get("audio_file", "")),
        duration=float(raw.get("duration", 0.0)),
        mode=str(raw.get("mode", "full")),
        scenes=[SceneVoiceTiming(**item) for item in raw.get("scenes", [])],
    )


def narration_path(project_dir: str | Path) -> Path | None:
    root = Path(project_dir)
    plan = load_voice_plan(root)
    if plan and plan.audio_file:
        candidate = root / plan.audio_file
        if candidate.is_file():
            return candidate
    for candidate in sorted((root / "assets").glob("narration.*")):
        if candidate.is_file():
            return candidate
    return None


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

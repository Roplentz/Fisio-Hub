from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Protocol

from .voice import VoiceError, probe_duration, update_voice_plan_with_scenes


@dataclass(frozen=True)
class VoiceSettings:
    """Configuração comum inspirada em plataformas de referência como ElevenLabs."""

    voice: str = "pm_alex"
    language: str = "pt-BR"
    speed: float = 1.0
    stability: float = 0.65
    similarity: float = 0.75
    style: float = 0.25
    speaker_boost: bool = True

    def normalized(self) -> "VoiceSettings":
        return VoiceSettings(
            voice=self.voice.strip() or "pm_alex",
            language=self.language.strip() or "pt-BR",
            speed=min(1.5, max(0.7, float(self.speed))),
            stability=min(1.0, max(0.0, float(self.stability))),
            similarity=min(1.0, max(0.0, float(self.similarity))),
            style=min(1.0, max(0.0, float(self.style))),
            speaker_boost=bool(self.speaker_boost),
        )


@dataclass(frozen=True)
class GeneratedVoice:
    audio_path: Path
    duration: float
    provider: str
    cache_hit: bool
    settings: VoiceSettings


class VoiceProvider(Protocol):
    name: str

    def generate(
        self, text: str, output_path: Path, settings: VoiceSettings
    ) -> None: ...


class KokoroProvider:
    name = "kokoro"

    def generate(self, text: str, output_path: Path, settings: VoiceSettings) -> None:
        try:
            import soundfile as sf
            from kokoro import KPipeline
        except ImportError as exc:
            raise VoiceError(
                "O Kokoro ainda não está instalado. Instale o extra de voz: pip install -e '.[voice]'."
            ) from exc

        lang_code = "p" if settings.language.lower().startswith("pt") else "a"
        pipeline = KPipeline(lang_code=lang_code)
        chunks: list[Any] = []
        for _, _, audio in pipeline(text, voice=settings.voice, speed=settings.speed):
            chunks.append(audio)
        if not chunks:
            raise VoiceError("O Kokoro não retornou áudio.")

        try:
            import numpy as np
        except ImportError as exc:
            raise VoiceError(
                "NumPy é necessário para unir os segmentos de voz."
            ) from exc

        output_path.parent.mkdir(parents=True, exist_ok=True)
        sf.write(output_path, np.concatenate(chunks), 24000)


class VoiceEngine:
    """Camada única para TTS, cache e sincronização com as cenas."""

    def __init__(self, providers: dict[str, VoiceProvider] | None = None) -> None:
        self.providers = providers or {"kokoro": KokoroProvider()}

    @staticmethod
    def script_from_scenes(scenes: Any) -> str:
        parts = [str(getattr(scene, "narration", "") or "").strip() for scene in scenes]
        return "\n\n".join(part for part in parts if part)

    @staticmethod
    def cache_key(text: str, provider: str, settings: VoiceSettings) -> str:
        payload = json.dumps(
            {
                "text": text,
                "provider": provider,
                "settings": asdict(settings.normalized()),
            },
            ensure_ascii=False,
            sort_keys=True,
        )
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:24]

    def generate_project_voice(
        self,
        project_dir: str | Path,
        scenes: Any,
        *,
        provider: str = "kokoro",
        settings: VoiceSettings | None = None,
        ffprobe_bin: str = "ffprobe",
    ) -> GeneratedVoice:
        selected = (settings or VoiceSettings()).normalized()
        text = self.script_from_scenes(scenes)
        if not text:
            raise VoiceError("O roteiro não contém narração para gerar voz.")
        if provider not in self.providers:
            raise VoiceError(f"Provedor de voz não disponível: {provider}")

        root = Path(project_dir)
        cache_dir = root / "assets" / "voice-cache"
        key = self.cache_key(text, provider, selected)
        cached = cache_dir / f"{key}.wav"
        cache_hit = cached.exists()
        if not cache_hit:
            self.providers[provider].generate(text, cached, selected)

        narration = root / "assets" / "narration.wav"
        narration.parent.mkdir(parents=True, exist_ok=True)
        narration.write_bytes(cached.read_bytes())
        duration = probe_duration(narration, ffprobe_bin=ffprobe_bin)
        relative = str(narration.relative_to(root))
        update_voice_plan_with_scenes(
            root,
            scenes,
            duration=duration,
            audio_file=relative,
            mode=f"tts:{provider}",
        )
        metadata = {
            "provider": provider,
            "cache_key": key,
            "cache_hit": cache_hit,
            "settings": asdict(selected),
        }
        (root / "voice-generation.json").write_text(
            json.dumps(metadata, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        return GeneratedVoice(narration, duration, provider, cache_hit, selected)


__all__ = [
    "GeneratedVoice",
    "KokoroProvider",
    "VoiceEngine",
    "VoiceProvider",
    "VoiceSettings",
]

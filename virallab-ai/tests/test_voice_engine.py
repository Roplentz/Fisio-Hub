from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

import pytest

from virallab import voice_engine
from virallab.voice import VoiceError
from virallab.voice_engine import VoiceEngine, VoiceSettings


class FakeProvider:
    name = "fake"

    def __init__(self) -> None:
        self.calls = 0

    def generate(self, text: str, output_path: Path, settings: VoiceSettings) -> None:
        self.calls += 1
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_bytes(b"RIFF" + (b"0" * 2048))


class FakeParameter:
    device = "cpu"


class FakeModel:
    def parameters(self):
        yield FakeParameter()


class FakePipeline:
    def __init__(self) -> None:
        self.model = FakeModel()


def test_voice_settings_are_normalized() -> None:
    value = VoiceSettings(speed=9, stability=-1, similarity=3, style=2).normalized()
    assert value.speed == 1.5
    assert value.stability == 0.0
    assert value.similarity == 1.0
    assert value.style == 1.0


def test_generation_reuses_cache_and_writes_plan(tmp_path: Path, monkeypatch) -> None:
    provider = FakeProvider()
    engine = VoiceEngine({"fake": provider})
    scenes = [
        SimpleNamespace(index=1, narration="Primeira frase."),
        SimpleNamespace(index=2, narration="Segunda frase mais longa."),
    ]
    monkeypatch.setattr(voice_engine, "probe_duration", lambda *_args, **_kwargs: 7.5)

    first = engine.generate_project_voice(tmp_path, scenes, provider="fake")
    second = engine.generate_project_voice(tmp_path, scenes, provider="fake")

    assert first.cache_hit is False
    assert second.cache_hit is True
    assert provider.calls == 1
    assert first.audio_path.stat().st_size > 1024
    assert (tmp_path / "voice-plan.json").exists()
    assert (tmp_path / "voice-generation.json").exists()


def test_cache_changes_when_speed_changes() -> None:
    text = "Uma narração"
    slow = VoiceEngine.cache_key(text, "kokoro", VoiceSettings(speed=0.9))
    fast = VoiceEngine.cache_key(text, "kokoro", VoiceSettings(speed=1.1))
    assert slow != fast


def test_kokoro_model_without_device_receives_parameter_device() -> None:
    pipeline = FakePipeline()
    assert not hasattr(pipeline.model, "device")

    returned = voice_engine._ensure_kokoro_model_device(pipeline)

    assert returned is pipeline
    assert pipeline.model.device == "cpu"


def test_portuguese_rejects_incompatible_voice() -> None:
    with pytest.raises(VoiceError, match="compatível com português"):
        voice_engine._validate_voice_for_language("af_heart", "p")


def test_invalid_small_provider_output_is_removed(tmp_path: Path, monkeypatch) -> None:
    class SmallProvider:
        name = "small"

        def generate(self, text: str, output_path: Path, settings: VoiceSettings) -> None:
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_bytes(b"tiny")

    monkeypatch.setattr(voice_engine, "probe_duration", lambda *_args, **_kwargs: 1.0)
    engine = VoiceEngine({"small": SmallProvider()})
    scenes = [SimpleNamespace(index=1, narration="Teste")]

    with pytest.raises(VoiceError, match="arquivo de áudio válido"):
        engine.generate_project_voice(tmp_path, scenes, provider="small")

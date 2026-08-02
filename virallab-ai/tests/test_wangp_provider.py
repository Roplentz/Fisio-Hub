from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

import pytest

from virallab.wangp_provider import WanGPConfig, WanGPError, WanGPProvider


class FakeJob:
    def __init__(self, result):
        self._result = result
        self.events = SimpleNamespace(iter=lambda timeout=0.2: iter(()))

    def result(self):
        return self._result


class FakeSession:
    def __init__(self, result):
        self.result = result
        self.settings = None

    def submit_task(self, settings):
        self.settings = settings
        return FakeJob(self.result)


def test_generate_video_returns_generated_file(tmp_path: Path) -> None:
    wangp_root = tmp_path / "WanGP"
    wangp_root.mkdir()
    output = tmp_path / "clip.mp4"
    output.write_bytes(b"video")
    fake_session = FakeSession(
        SimpleNamespace(success=True, generated_files=[str(output)], errors=[])
    )

    provider = WanGPProvider(
        WanGPConfig(root=wangp_root),
        session_factory=lambda **kwargs: fake_session,
    )

    generated = provider.generate_video(prompt="Cena clínica cinematográfica")

    assert generated == output
    assert fake_session.settings["model_type"] == "ltx2_22B_distilled"
    assert fake_session.settings["resolution"] == "704x1280"
    assert fake_session.settings["duration_seconds"] == 4


def test_provider_keeps_session_loaded_between_requests(tmp_path: Path) -> None:
    wangp_root = tmp_path / "WanGP"
    wangp_root.mkdir()
    output = tmp_path / "clip.mp4"
    output.write_bytes(b"video")
    fake_session = FakeSession(
        SimpleNamespace(success=True, generated_files=[str(output)], errors=[])
    )
    calls = []

    def factory(**kwargs):
        calls.append(kwargs)
        return fake_session

    provider = WanGPProvider(WanGPConfig(root=wangp_root), session_factory=factory)
    provider.generate_video(prompt="Primeira cena")
    provider.generate_video(prompt="Segunda cena")

    assert len(calls) == 1


def test_generate_video_surfaces_wangp_error(tmp_path: Path) -> None:
    wangp_root = tmp_path / "WanGP"
    wangp_root.mkdir()
    fake_session = FakeSession(
        SimpleNamespace(
            success=False,
            generated_files=[],
            errors=[SimpleNamespace(message="GPU sem memória")],
        )
    )
    provider = WanGPProvider(
        WanGPConfig(root=wangp_root),
        session_factory=lambda **kwargs: fake_session,
    )

    with pytest.raises(WanGPError, match="GPU sem memória"):
        provider.generate_video(prompt="Cena pesada")


def test_empty_prompt_is_rejected(tmp_path: Path) -> None:
    wangp_root = tmp_path / "WanGP"
    wangp_root.mkdir()
    provider = WanGPProvider(
        WanGPConfig(root=wangp_root),
        session_factory=lambda **kwargs: None,
    )

    with pytest.raises(WanGPError, match="prompt"):
        provider.generate_video(prompt="  ")

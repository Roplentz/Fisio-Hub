from __future__ import annotations

import json
from pathlib import Path

from virallab.voice import VoicePlan, save_voice_plan
from virallab.voice_ui import AUTOTEST_KEYS, apply_autotest_defaults, autotest_report


def test_apply_autotest_defaults_fills_all_voice_fields() -> None:
    state: dict[str, object] = {}

    apply_autotest_defaults(state)

    assert state["voice_autotest_enabled"] is True
    for key, value in AUTOTEST_KEYS.items():
        assert state[key] == value


def test_autotest_report_detects_complete_voice_artifacts(tmp_path: Path) -> None:
    assets = tmp_path / "assets"
    assets.mkdir()
    (assets / "narration.wav").write_bytes(b"valid-wave-placeholder")
    save_voice_plan(
        tmp_path,
        VoicePlan(
            audio_file="assets/narration.wav",
            duration=12.5,
            mode="tts:kokoro",
            scenes=[],
        ),
    )
    (tmp_path / "voice-generation.json").write_text(
        json.dumps({"provider": "kokoro", "cache_key": "abc123"}),
        encoding="utf-8",
    )

    report = autotest_report(tmp_path)

    assert report["audio"] is True
    assert report["voice_plan"] is True
    assert report["metadata"] is True
    assert report["scenes"] is False


def test_autotest_report_is_false_without_artifacts(tmp_path: Path) -> None:
    assert autotest_report(tmp_path) == {
        "audio": False,
        "voice_plan": False,
        "metadata": False,
        "scenes": False,
    }

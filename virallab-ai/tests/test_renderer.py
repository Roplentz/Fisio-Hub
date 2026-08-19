from __future__ import annotations

import json

from virallab.generator import export_package, generate_video_package
from virallab.models import VideoBrief
from virallab.providers import LocalRuleProvider
from pathlib import Path

from virallab.renderer import _concat_escape, render_video


def test_renderer_dry_run_creates_concat_and_command_manifest(tmp_path):
    brief = VideoBrief(
        theme="IA na fisioterapia",
        duration_seconds=60,
        format="professor_cinematico",
        cta="Siga o Professor RP.",
    )
    package = generate_video_package(brief, provider=LocalRuleProvider())
    export_package(package, tmp_path)

    target = render_video(tmp_path, dry_run=True)

    assert target == tmp_path / "video-final.mp4"
    concat_file = tmp_path / "generated" / "concat.txt"
    command_file = tmp_path / "generated" / "ffmpeg-commands.json"
    assert concat_file.exists()
    assert command_file.exists()

    commands = json.loads(command_file.read_text(encoding="utf-8"))
    assert len(commands) == len(package.scenes) + 2
    assert commands[-1][-1].endswith("video-final.mp4")
    assert "libx264" in commands[-1]
    assert any("subtitles=" in argument for argument in commands[-1])


def test_renderer_uses_placeholder_and_silent_audio_for_missing_assets(tmp_path):
    brief = VideoBrief(theme="Inovação em saúde", duration_seconds=45)
    package = generate_video_package(brief, provider=LocalRuleProvider())
    export_package(package, tmp_path)

    render_video(tmp_path, dry_run=True)
    commands = json.loads(
        (tmp_path / "generated" / "ffmpeg-commands.json").read_text(encoding="utf-8")
    )

    first_scene = commands[0]
    assert "lavfi" in first_scene
    assert any("color=c=" in argument for argument in first_scene)
    assert any("drawtext=" in argument for argument in first_scene)
    assert any("anullsrc=" in argument for argument in first_scene)
    assert "aac" in first_scene


def test_renderer_can_disable_burned_captions(tmp_path):
    brief = VideoBrief(theme="IA responsável", duration_seconds=30)
    package = generate_video_package(brief, provider=LocalRuleProvider())
    export_package(package, tmp_path)

    render_video(tmp_path, burn_captions=False, dry_run=True)
    commands = json.loads(
        (tmp_path / "generated" / "ffmpeg-commands.json").read_text(encoding="utf-8")
    )

    assert not any("subtitles=" in argument for argument in commands[-1])


def test_concat_manifest_normalizes_windows_paths():
    escaped = _concat_escape(Path(r"C:\Users\plent\video scene.mp4"))

    assert escaped == "C:/Users/plent/video scene.mp4"

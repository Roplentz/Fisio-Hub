from __future__ import annotations

import json

import pytest

from virallab.generator import export_package, generate_video_package
from virallab.models import VideoBrief
from virallab.providers import LocalRuleProvider
from virallab.render_engine import FFmpegVideoRenderer, RenderJob, get_video_renderer
from virallab.subtitle_renderer import get_subtitle_preset


def test_render_job_dry_run_writes_auditable_report(tmp_path):
    package = generate_video_package(
        VideoBrief(theme="Fisioterapia baseada em evidências", duration_seconds=30),
        provider=LocalRuleProvider(),
    )
    export_package(package, tmp_path)

    job = FFmpegVideoRenderer().render(RenderJob(package_dir=str(tmp_path)), dry_run=True)

    assert job.state == "succeeded"
    assert job.progress == 100
    report = json.loads(
        (tmp_path / "generated" / "render-report.json").read_text(encoding="utf-8")
    )
    assert report["engine"] == "virallab_ffmpeg"
    assert report["job_id"] == job.job_id


def test_cancelled_job_does_not_render(tmp_path):
    job = RenderJob(package_dir=str(tmp_path), state="cancelled")
    assert FFmpegVideoRenderer().render(job, dry_run=True).state == "cancelled"


def test_failed_job_keeps_actionable_error_message(tmp_path):
    job = FFmpegVideoRenderer().render(RenderJob(package_dir=str(tmp_path)))

    assert job.state == "failed"
    assert job.error_code == "RenderError"
    assert "Plano não encontrado" in job.error_message


def test_feature_flag_rejects_unknown_engine(monkeypatch):
    monkeypatch.setenv("MPT_RENDER_ENGINE", "unknown")
    with pytest.raises(ValueError):
        get_video_renderer()


def test_accessible_subtitle_presets():
    style = get_subtitle_preset("high_contrast").ffmpeg_style()
    assert "Outline=4" in style
    assert "MarginV=200" in style

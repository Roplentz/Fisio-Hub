from __future__ import annotations

import json

import pytest

from virallab.generator import export_package, generate_video_package
from virallab.models import VideoBrief
from virallab.providers import LocalRuleProvider
from virallab.renderer import RenderError, _ffmpeg_escape, render_video


def _package(tmp_path):
    brief = VideoBrief(theme="Segurança em IA", duration_seconds=30)
    package = generate_video_package(brief, provider=LocalRuleProvider())
    export_package(package, tmp_path)
    return package


def test_renderer_blocks_source_path_traversal(tmp_path) -> None:
    _package(tmp_path)
    plan_path = tmp_path / "render-plan.json"
    plan = json.loads(plan_path.read_text(encoding="utf-8"))
    plan["layers"][0]["source"] = "../../segredo.mp4"
    plan_path.write_text(json.dumps(plan), encoding="utf-8")

    with pytest.raises(RenderError, match="fora do projeto"):
        render_video(tmp_path, dry_run=True)


def test_renderer_rejects_invalid_scene_interval(tmp_path) -> None:
    _package(tmp_path)
    plan_path = tmp_path / "render-plan.json"
    plan = json.loads(plan_path.read_text(encoding="utf-8"))
    plan["layers"][0]["end"] = plan["layers"][0]["start"]
    plan_path.write_text(json.dumps(plan), encoding="utf-8")

    with pytest.raises(RenderError, match="Intervalo inválido"):
        render_video(tmp_path, dry_run=True)


def test_renderer_rejects_output_path_in_plan(tmp_path) -> None:
    _package(tmp_path)
    plan_path = tmp_path / "render-plan.json"
    plan = json.loads(plan_path.read_text(encoding="utf-8"))
    plan["output"]["filename"] = "../video-final.mp4"
    plan_path.write_text(json.dumps(plan), encoding="utf-8")

    with pytest.raises(RenderError, match="apenas um nome"):
        render_video(tmp_path, dry_run=True)


def test_ffmpeg_escape_covers_filtergraph_metacharacters() -> None:
    malicious = "a='b';[x]|&$`%,:"
    escaped = _ffmpeg_escape(malicious)

    for token in (r"\=", r"\'", r"\;", r"\[", r"\]", r"\|", r"\&", r"\$", r"\`", r"\%", r"\,", r"\:"):
        assert token in escaped


def test_renderer_rejects_control_characters(tmp_path) -> None:
    _package(tmp_path)
    plan_path = tmp_path / "render-plan.json"
    plan = json.loads(plan_path.read_text(encoding="utf-8"))
    plan["layers"][0]["overlay_text"] = "texto\x00malicioso"
    plan_path.write_text(json.dumps(plan), encoding="utf-8")

    with pytest.raises(RenderError, match="controle"):
        render_video(tmp_path, dry_run=True)

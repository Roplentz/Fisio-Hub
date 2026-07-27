from __future__ import annotations

from pathlib import Path

from virallab import renderer


def test_entrypoint_does_not_install_quality_patch() -> None:
    app_path = Path(__file__).resolve().parents[1] / "app.py"
    source = app_path.read_text(encoding="utf-8")

    assert "quality_patch" not in source
    assert "install_quality_patch" not in source


def test_renderer_uses_visual_quality_directly() -> None:
    source = Path(renderer.__file__).read_text(encoding="utf-8")

    assert "overlay_drawtext_filter" in source
    assert "subtitle_force_style" in source
    assert "brand_drawtext_filter" in source
    assert "renderer._drawtext_filter =" not in source
    assert "renderer._final_mix_command =" not in source


def test_overlay_filter_uses_selected_preset() -> None:
    result = renderer._drawtext_filter("Legenda profissional", 1080, 1920)

    assert "fontsize=51" in result
    assert "y=1440" in result
    assert "boxcolor=black@0.22" in result

from __future__ import annotations

from virallab.visual_quality import (
    PRESETS,
    brand_drawtext_filter,
    get_preset,
    overlay_drawtext_filter,
    subtitle_force_style,
    wrap_caption,
)


def test_all_caption_presets_are_available() -> None:
    assert set(PRESETS) == {"cinematic", "educational", "viral", "corporate", "minimal"}
    assert get_preset("unknown").key == "educational"


def test_wrap_caption_limits_to_two_lines() -> None:
    value = wrap_caption(
        "Pare de rasgar dinheiro com assinaturas caras de inteligência artificial",
        max_chars=24,
        max_lines=2,
    )
    assert value.count("\\N") <= 1
    assert value.endswith("…")


def test_subtitle_style_uses_safe_margins_and_soft_outline() -> None:
    style = subtitle_force_style(get_preset("educational"))
    assert "FontName=DejaVu Sans" in style
    assert "MarginL=90" in style
    assert "MarginR=90" in style
    assert "Outline=1" in style
    assert "Alignment=2" in style


def test_overlay_is_smaller_and_lower_than_old_layout() -> None:
    result = overlay_drawtext_filter(
        "Uma legenda profissional que não cobre o rosto",
        1080,
        1920,
        get_preset("educational"),
    )
    assert "fontsize=51" in result
    assert "y=1440" in result
    assert "borderw=2" in result
    assert "boxcolor=black@0.22" in result


def test_brand_is_discreet_and_top_aligned() -> None:
    result = brand_drawtext_filter()
    assert "Prof. Dr. Rodrigo Plentz" in result
    assert "white@0.58" in result
    assert "y=105" in result

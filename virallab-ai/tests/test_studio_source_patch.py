from pathlib import Path


def test_studio_voice_ui_is_native_and_source_patch_is_not_used() -> None:
    root = Path(__file__).resolve().parents[1]
    app_source = (root / "app.py").read_text(encoding="utf-8")
    studio_source = (root / "app_v3.py").read_text(encoding="utf-8")

    assert "studio_source_patch" not in app_source
    assert "def render_voice(package, package_path: Path) -> None:" in studio_source
    assert "st.audio_input" in studio_source
    assert "install_voice_ui(" not in app_source

from pathlib import Path


def test_entrypoint_does_not_replace_streamlit_page_config() -> None:
    app_path = Path(__file__).resolve().parents[1] / "app.py"
    source = app_path.read_text(encoding="utf-8")

    assert "st.set_page_config =" not in source
    assert "original_page_config" not in source
    assert '"__file__": str(studio_path)' in source
    compile(source, str(app_path), "exec")

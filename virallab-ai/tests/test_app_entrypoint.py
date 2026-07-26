from pathlib import Path


def test_entrypoint_imports_studio_without_dynamic_execution() -> None:
    app_path = Path(__file__).resolve().parents[1] / "app.py"
    source = app_path.read_text(encoding="utf-8")

    assert "st.set_page_config =" not in source
    assert "original_page_config" not in source
    assert "exec(" not in source
    assert "compile(" not in source
    assert "studio_source_patch" not in source
    assert "quality_patch" not in source
    assert "import app_v3" in source
    compile(source, str(app_path), "exec")

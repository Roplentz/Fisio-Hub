from pathlib import Path


def test_entrypoint_uses_static_python_import() -> None:
    app_path = Path(__file__).resolve().parents[1] / "app.py"
    source = app_path.read_text(encoding="utf-8")

    assert "from app_v3 import main" in source
    assert "main()" in source
    assert "studio_path" not in source
    assert "read_text" not in source
    assert "studio_source_patch" not in source
    assert "st.set_page_config =" not in source
    assert "original_page_config" not in source

    compile(source, str(app_path), "exec")

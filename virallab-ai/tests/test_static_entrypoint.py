from pathlib import Path


APP_PATH = Path(__file__).resolve().parents[1] / "app.py"


def test_entrypoint_does_not_execute_dynamic_source() -> None:
    source = APP_PATH.read_text(encoding="utf-8")

    assert "exec(" not in source
    assert "compile(" not in source
    assert "read_text(" not in source
    assert "studio_source_patch" not in source
    assert "from app_v3 import main" in source
    assert "main()" in source

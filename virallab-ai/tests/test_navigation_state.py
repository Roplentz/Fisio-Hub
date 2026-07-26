from pathlib import Path


def test_navigation_uses_distinct_logical_and_widget_keys() -> None:
    app_path = Path(__file__).resolve().parents[1] / "app_v3.py"
    source = app_path.read_text(encoding="utf-8")

    assert "\"studio_step\": \"analysis\"" in source
    assert "\"step_selector\": \"analysis\"" in source
    assert "key=\"step_selector\"" in source
    assert "key=\"studio_step\"" not in source
    assert "on_change=sync_step_from_selector" in source
    assert "def go_to_step(step: str)" in source
    compile(source, str(app_path), "exec")

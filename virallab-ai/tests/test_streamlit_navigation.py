from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RUNTIME_PATH = ROOT / "studio_runtime.py"


def test_entrypoint_does_not_patch_streamlit_selectbox() -> None:
    source = (ROOT / "app.py").read_text(encoding="utf-8")

    assert "streamlit_navigation" not in source
    assert "install_safe_step_selectbox" not in source
    assert "st.selectbox =" not in source


def test_studio_uses_separate_logical_and_widget_keys() -> None:
    source = RUNTIME_PATH.read_text(encoding="utf-8")

    assert 'LOGICAL_STEP_KEY = "studio_step"' in source
    assert 'WIDGET_STEP_KEY = "_studio_step_selector"' in source
    assert "key=WIDGET_STEP_KEY" in source
    assert "on_change=sync_step_from_widget" in source
    assert "st.session_state[LOGICAL_STEP_KEY] = selected" in source


def test_continue_actions_change_only_the_logical_route() -> None:
    source = RUNTIME_PATH.read_text(encoding="utf-8")

    assert 'st.session_state[LOGICAL_STEP_KEY] = "strategy"' in source
    assert 'st.session_state[LOGICAL_STEP_KEY] = "script"' in source
    assert 'st.session_state[LOGICAL_STEP_KEY] = "avatar"' in source
    assert 'st.session_state[LOGICAL_STEP_KEY] = "voice"' in source
    assert "st.session_state[WIDGET_STEP_KEY] = selected" not in source

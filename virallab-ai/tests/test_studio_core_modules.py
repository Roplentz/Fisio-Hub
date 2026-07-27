from __future__ import annotations

from pathlib import Path

from virallab.studio.navigation import (
    STEPS,
    prepare_widget_step,
    progress_value,
    render_step_selector,
    sync_step_from_widget,
)
from virallab.studio.paths import StudioPaths
from virallab.studio.state import (
    LOGICAL_STEP_KEY,
    WIDGET_STEP_KEY,
    initialize_state,
    reset_project,
    set_step,
)


def test_paths_are_derived_from_one_app_root(tmp_path: Path) -> None:
    paths = StudioPaths.from_app_root(tmp_path)
    paths.ensure_directories()

    assert paths.workspace == tmp_path / "workspace"
    assert paths.analysis.is_dir()
    assert paths.projects.is_dir()
    assert paths.learning_store.parent.is_dir()
    assert paths.project_dir("abc") == tmp_path / "workspace" / "projects" / "abc"


def test_state_initialization_preserves_existing_values() -> None:
    state = {"project_id": "existing", LOGICAL_STEP_KEY: "voice"}
    initialize_state(state)

    assert state["project_id"] == "existing"
    assert state[LOGICAL_STEP_KEY] == "voice"
    assert state[WIDGET_STEP_KEY] == "analysis"
    assert state["package"] is None


def test_reset_project_clears_project_data_and_returns_to_analysis() -> None:
    state = {
        "project_id": "old",
        "package": object(),
        "package_dir": "/tmp/project",
        "preferred_hook": "hook",
        "avatar_candidate": "/tmp/avatar.png",
        LOGICAL_STEP_KEY: "render",
    }
    reset_project(state)

    assert state["project_id"] != "old"
    assert state["package"] is None
    assert state["package_dir"] is None
    assert state["preferred_hook"] == ""
    assert state["avatar_candidate"] is None
    assert state[LOGICAL_STEP_KEY] == "analysis"


def test_navigation_sync_and_progress_are_ui_independent() -> None:
    state = {LOGICAL_STEP_KEY: "script", WIDGET_STEP_KEY: "analysis"}
    prepare_widget_step(state)
    assert state[WIDGET_STEP_KEY] == "script"

    state[WIDGET_STEP_KEY] = "avatar"
    sync_step_from_widget(state)
    assert state[LOGICAL_STEP_KEY] == "avatar"
    assert progress_value(state) == 4 / len(STEPS)

    set_step(state, "voice")
    assert state[LOGICAL_STEP_KEY] == "voice"


class FakeStreamlit:
    def __init__(self, state: dict[str, str]) -> None:
        self.state = state
        self.kwargs: dict = {}

    def selectbox(self, _label, **kwargs):
        self.kwargs = kwargs
        return self.state[kwargs["key"]]


def test_selector_uses_private_widget_key_and_explicit_callback() -> None:
    state = {LOGICAL_STEP_KEY: "strategy", WIDGET_STEP_KEY: "analysis"}
    fake = FakeStreamlit(state)

    selected = render_step_selector(fake, state)

    assert selected == "strategy"
    assert fake.kwargs["key"] == WIDGET_STEP_KEY
    state[WIDGET_STEP_KEY] = "script"
    fake.kwargs["on_change"]()
    assert state[LOGICAL_STEP_KEY] == "script"

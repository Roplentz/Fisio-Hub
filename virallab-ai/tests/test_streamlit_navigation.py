from __future__ import annotations

from types import SimpleNamespace

from virallab.streamlit_navigation import (
    LOGICAL_STEP_KEY,
    WIDGET_STEP_KEY,
    install_safe_step_selectbox,
)


class FakeStreamlit:
    def __init__(self) -> None:
        self.session_state: dict[str, str] = {LOGICAL_STEP_KEY: "script"}
        self.calls: list[dict] = []

    def selectbox(self, *args, **kwargs):
        self.calls.append(kwargs.copy())
        key = kwargs["key"]
        return self.session_state[key]


def test_programmatic_step_is_mirrored_to_private_widget_key() -> None:
    fake = FakeStreamlit()
    install_safe_step_selectbox(fake)

    selected = fake.selectbox("Etapa", options=["script", "avatar"], key=LOGICAL_STEP_KEY)

    assert selected == "script"
    assert fake.session_state[WIDGET_STEP_KEY] == "script"
    assert fake.calls[-1]["key"] == WIDGET_STEP_KEY


def test_user_selection_updates_logical_route_through_callback() -> None:
    fake = FakeStreamlit()
    install_safe_step_selectbox(fake)
    fake.selectbox("Etapa", options=["script", "avatar"], key=LOGICAL_STEP_KEY)

    callback = fake.calls[-1]["on_change"]
    fake.session_state[WIDGET_STEP_KEY] = "avatar"
    callback()

    assert fake.session_state[LOGICAL_STEP_KEY] == "avatar"


def test_continue_button_can_change_logical_key_without_touching_widget_key() -> None:
    fake = FakeStreamlit()
    install_safe_step_selectbox(fake)
    fake.selectbox("Etapa", options=["script", "avatar"], key=LOGICAL_STEP_KEY)

    fake.session_state[LOGICAL_STEP_KEY] = "avatar"
    fake.selectbox("Etapa", options=["script", "avatar"], key=LOGICAL_STEP_KEY)

    assert fake.session_state[WIDGET_STEP_KEY] == "avatar"
    assert fake.session_state[LOGICAL_STEP_KEY] == "avatar"

from __future__ import annotations

from contextlib import nullcontext

from virallab.studio.layout import (
    FOOTER_TEXT,
    HERO_HTML,
    PAGE_TITLE,
    THEME_CSS,
    configure_page,
    render_footer,
    render_hero,
    render_progress,
    render_sidebar,
)


class FakeUI:
    def __init__(self, *, button_pressed: bool = False) -> None:
        self.sidebar = nullcontext()
        self.button_pressed = button_pressed
        self.calls: list[tuple[str, object]] = []

    def set_page_config(self, **kwargs) -> None:
        self.calls.append(("config", kwargs))

    def markdown(self, value, **kwargs) -> None:
        self.calls.append(("markdown", (value, kwargs)))

    def caption(self, value) -> None:
        self.calls.append(("caption", value))

    def code(self, value) -> None:
        self.calls.append(("code", value))

    def button(self, label, **kwargs) -> bool:
        self.calls.append(("button", (label, kwargs)))
        return self.button_pressed

    def metric(self, label, value) -> None:
        self.calls.append(("metric", (label, value)))

    def rerun(self) -> None:
        self.calls.append(("rerun", None))

    def progress(self, value) -> None:
        self.calls.append(("progress", value))


def test_configure_page_applies_metadata_and_theme() -> None:
    ui = FakeUI()

    configure_page(ui)

    assert ui.calls[0][0] == "config"
    assert ui.calls[0][1]["page_title"] == PAGE_TITLE
    assert ("markdown", (THEME_CSS, {"unsafe_allow_html": True})) in ui.calls


def test_sidebar_does_not_reset_project_when_button_is_idle() -> None:
    ui = FakeUI()
    resets: list[bool] = []

    render_sidebar(ui, {"project_id": "abc123"}, {"approval_rate": 75}, lambda: resets.append(True))

    assert resets == []
    assert ("code", "abc123") in ui.calls
    assert ("metric", ("Taxa de aprovação", "75%")) in ui.calls


def test_sidebar_resets_project_and_reruns_when_requested() -> None:
    ui = FakeUI(button_pressed=True)
    resets: list[bool] = []

    render_sidebar(ui, {"project_id": "abc123"}, {"approval_rate": 0}, lambda: resets.append(True))

    assert resets == [True]
    assert ("rerun", None) in ui.calls


def test_hero_progress_and_footer_are_independent_components() -> None:
    ui = FakeUI()

    render_hero(ui)
    render_progress(ui, 0.5)
    render_footer(ui)

    assert ("markdown", (HERO_HTML, {"unsafe_allow_html": True})) in ui.calls
    assert ("progress", 0.5) in ui.calls
    assert ("caption", FOOTER_TEXT) in ui.calls

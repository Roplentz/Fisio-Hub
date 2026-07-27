from __future__ import annotations

import inspect
from types import SimpleNamespace

from virallab.studio.steps.script import ScriptResult, render_script


class FakeStreamlit:
    def __init__(self, *, hook: str = "Gancho editado", continue_to_avatar: bool = False):
        self.hook = hook
        self.continue_to_avatar = continue_to_avatar
        self.markdowns = []
        self.download = None

    def subheader(self, *_args, **_kwargs):
        return None

    def metric(self, *_args, **_kwargs):
        return None

    def text_area(self, *_args, **_kwargs):
        return self.hook

    def markdown(self, value, **_kwargs):
        self.markdowns.append(value)

    def download_button(self, *args, **kwargs):
        self.download = (args, kwargs)

    def button(self, *_args, **_kwargs):
        return self.continue_to_avatar


def package_fixture():
    scene = SimpleNamespace(
        index=1,
        scene_type="avatar",
        start=0.0,
        end=5.0,
        narration="Use <evidência>",
        on_screen_text="Texto & prova",
        visual_direction="Plano próximo",
    )
    return SimpleNamespace(
        hook="Gancho original",
        thesis="Tese principal",
        scenes=[scene],
        to_dict=lambda: {"hook": "Gancho original"},
    )


def test_script_returns_edited_hook_without_touching_session_state():
    st = FakeStreamlit()

    result = render_script(st, package_fixture(), preferred_hook="Gancho anterior")

    assert result == ScriptResult(preferred_hook="Gancho editado", continue_to_avatar=False)
    assert "session_state" not in inspect.getsource(render_script)
    assert st.download is not None
    assert "&lt;evidência&gt;" in st.markdowns[-1]
    assert "Texto &amp; prova" in st.markdowns[-1]


def test_script_requests_avatar_navigation():
    result = render_script(
        FakeStreamlit(continue_to_avatar=True),
        package_fixture(),
    )

    assert result.continue_to_avatar is True

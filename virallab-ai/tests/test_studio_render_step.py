from __future__ import annotations

import inspect
from contextlib import nullcontext
from types import SimpleNamespace

from virallab.studio.steps.render import RenderAction, render_output


class Widget:
    def metric(self, *_args, **_kwargs):
        return None


class FakeStreamlit:
    def __init__(self, *, buttons=None):
        self.buttons = buttons or {}
        self.videos = []
        self.downloads = []
        self.errors = []

    def subheader(self, *_args, **_kwargs):
        return None

    def columns(self, count):
        return tuple(Widget() for _ in range(count))

    def checkbox(self, _label, value=False, **_kwargs):
        return value

    def slider(self, _label, _minimum, _maximum, value, **_kwargs):
        return value

    def button(self, label, **kwargs):
        if kwargs.get("disabled", False):
            return False
        return self.buttons.get(label, False)

    def spinner(self, *_args, **_kwargs):
        return nullcontext()

    def video(self, value, **_kwargs):
        self.videos.append(value)

    def download_button(self, *args, **kwargs):
        self.downloads.append((args, kwargs))

    def error(self, value, **_kwargs):
        self.errors.append(value)


class FakeLibrary:
    def __init__(self, approved=True):
        status = "approved" if approved else "pending"
        self.records = [SimpleNamespace(status=status)]

    def load(self):
        return self.records


def test_render_uses_silent_renderer_without_voice(tmp_path):
    output = tmp_path / "video-final.mp4"
    calls = []

    def renderer(package_path, **kwargs):
        calls.append((package_path, kwargs))
        output.write_bytes(b"video")
        return output

    st = FakeStreamlit(buttons={"Renderizar vídeo": True})
    result = render_output(
        st,
        tmp_path,
        library_factory=lambda _path: FakeLibrary(),
        voice_plan_loader=lambda _path: None,
        silent_renderer=renderer,
    )

    assert result.video_path == output
    assert calls[0][1]["burn_captions"] is True
    assert calls[0][1]["music_level_db"] == -25
    assert st.downloads


def test_render_uses_voice_renderer_when_plan_exists(tmp_path):
    output = tmp_path / "video-final.mp4"
    calls = []

    def renderer(package_path, **kwargs):
        calls.append((package_path, kwargs))
        output.write_bytes(b"video")
        return output

    result = render_output(
        FakeStreamlit(buttons={"Renderizar vídeo": True}),
        tmp_path,
        library_factory=lambda _path: FakeLibrary(),
        voice_plan_loader=lambda _path: SimpleNamespace(audio_file="voice.wav"),
        voice_renderer=renderer,
    )

    assert result.video_path == output
    assert calls[0][1]["narration_gain_db"] == 0


def test_render_disables_generation_without_approved_assets(tmp_path):
    st = FakeStreamlit(buttons={"Renderizar vídeo": True})
    called = False

    def renderer(*_args, **_kwargs):
        nonlocal called
        called = True
        return tmp_path / "video-final.mp4"

    result = render_output(
        st,
        tmp_path,
        library_factory=lambda _path: FakeLibrary(approved=False),
        voice_plan_loader=lambda _path: None,
        silent_renderer=renderer,
    )

    assert result.video_path is None
    assert called is False


def test_render_requests_publication_navigation(tmp_path):
    output = tmp_path / "video-final.mp4"
    output.write_bytes(b"video")
    st = FakeStreamlit(buttons={"Continuar para Publicação →": True})

    result = render_output(
        st,
        tmp_path,
        library_factory=lambda _path: FakeLibrary(),
        voice_plan_loader=lambda _path: None,
    )

    assert result.action is RenderAction.GO_TO_PUBLICATION
    assert result.video_path == output
    executable_source = inspect.getsource(render_output).split('"""', 2)[-1]
    assert "session_state" not in executable_source

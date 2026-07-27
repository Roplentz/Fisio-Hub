from __future__ import annotations

import inspect
from contextlib import nullcontext
from types import SimpleNamespace

import virallab.studio.steps.voice as voice_step
from virallab.studio.steps.voice import VoiceAction, render_voice


class Widget:
    def __init__(self, owner):
        self.owner = owner

    def markdown(self, *_args, **_kwargs):
        return None

    def caption(self, *_args, **_kwargs):
        return None

    def button(self, label, **_kwargs):
        return self.owner.buttons.get(label, False)

    def selectbox(self, *_args, **_kwargs):
        return "pm_alex"

    def slider(self, *_args, **_kwargs):
        return 1.0

    def metric(self, *_args, **_kwargs):
        return None


class FakeStreamlit:
    def __init__(self, *, buttons=None, mode="Gerar com IA"):
        self.buttons = buttons or {}
        self.mode = mode
        self.successes = []

    def subheader(self, *_args, **_kwargs):
        return None

    def caption(self, *_args, **_kwargs):
        return None

    def expander(self, *_args, **_kwargs):
        return nullcontext()

    def text_area(self, *_args, **_kwargs):
        return None

    def radio(self, *_args, **_kwargs):
        return self.mode

    def info(self, *_args, **_kwargs):
        return None

    def container(self, *_args, **_kwargs):
        return nullcontext()

    def columns(self, spec):
        count = spec if isinstance(spec, int) else len(spec)
        return tuple(Widget(self) for _ in range(count))

    def checkbox(self, label, value=False, **_kwargs):
        return value

    def slider(self, label, _minimum, _maximum, value, *_args, **_kwargs):
        return value

    def button(self, label, **_kwargs):
        return self.buttons.get(label, False)

    def spinner(self, *_args, **_kwargs):
        return nullcontext()

    def success(self, value, **_kwargs):
        self.successes.append(value)

    def error(self, *_args, **_kwargs):
        return None

    def audio(self, *_args, **_kwargs):
        return None

    def download_button(self, *_args, **_kwargs):
        return None


class FakeEngine:
    def generate_project_voice(self, *_args, **_kwargs):
        return SimpleNamespace(duration=12.5, cache_hit=True)


def package_fixture():
    scene = SimpleNamespace(index=1, narration="Narração da cena")
    brief = SimpleNamespace(duration_seconds=15)
    return SimpleNamespace(scenes=[scene], brief=brief)


def test_voice_autotest_requests_rerun_without_streamlit_session_state(tmp_path):
    state = {}
    st = FakeStreamlit(buttons={"Preencher autoteste": True})

    result = render_voice(st, package_fixture(), tmp_path, state=state)

    assert result.action is VoiceAction.RERUN
    assert state["voice_autotest_enabled"] is True
    assert "st.session_state" not in inspect.getsource(render_voice)


def test_voice_generation_returns_metadata_to_runtime(monkeypatch, tmp_path):
    monkeypatch.setattr(voice_step, "load_voice_plan", lambda _path: None)
    st = FakeStreamlit(buttons={"Gerar narração com IA": True})

    result = render_voice(
        st,
        package_fixture(),
        tmp_path,
        state={},
        engine_factory=FakeEngine,
    )

    assert result.action is VoiceAction.RERUN
    assert result.last_generation == {"duration": 12.5, "cache_hit": True}


def test_voice_requests_creatives_navigation(monkeypatch, tmp_path):
    audio_path = tmp_path / "narration.wav"
    audio_path.write_bytes(b"audio")
    plan = SimpleNamespace(
        audio_file="narration.wav",
        duration=12.5,
        scenes=[SimpleNamespace(index=1)],
    )
    monkeypatch.setattr(voice_step, "load_voice_plan", lambda _path: plan)
    st = FakeStreamlit(buttons={"Continuar para Criativos →": True})

    result = render_voice(st, package_fixture(), tmp_path, state={})

    assert result.action is VoiceAction.GO_TO_CREATIVES

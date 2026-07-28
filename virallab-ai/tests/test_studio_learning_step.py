from __future__ import annotations

import inspect
from pathlib import Path
from types import SimpleNamespace

from virallab.studio.steps.learning import LearningAction, render_learning


class FakeStreamlit:
    def __init__(self, *, save: bool = False):
        self.save = save
        self.successes = []
        self.warnings = []

    def subheader(self, *_args, **_kwargs):
        return None

    def warning(self, value, **_kwargs):
        self.warnings.append(value)

    def slider(self, *_args, **_kwargs):
        return 9

    def checkbox(self, *_args, **_kwargs):
        return True

    def text_area(self, *_args, **_kwargs):
        return "Usar um início mais direto."

    def button(self, *_args, **_kwargs):
        return self.save

    def success(self, value, **_kwargs):
        self.successes.append(value)


def make_package():
    return SimpleNamespace(
        hook="Hook original",
        brief=SimpleNamespace(theme="IA na fisioterapia"),
    )


def test_learning_persists_explicit_feedback(tmp_path):
    calls = []

    def saver(feedback, store_path):
        calls.append((feedback, store_path))
        return Path(store_path)

    store = tmp_path / "learning" / "feedback.jsonl"
    result = render_learning(
        FakeStreamlit(save=True),
        make_package(),
        project_id="project-123",
        preferred_hook="Hook revisado",
        learning_store=store,
        feedback_saver=saver,
    )

    assert result.action is LearningAction.SAVED
    assert result.saved_path == store
    assert result.feedback is not None
    assert result.feedback.project_id == "project-123"
    assert result.feedback.theme == "IA na fisioterapia"
    assert result.feedback.rating == 9
    assert result.feedback.approved is True
    assert result.feedback.preferred_hook == "Hook revisado"
    assert result.feedback.notes == "Usar um início mais direto."
    assert calls[0][1] == store


def test_learning_does_not_persist_without_confirmation(tmp_path):
    called = False

    def saver(*_args, **_kwargs):
        nonlocal called
        called = True
        return tmp_path / "feedback.jsonl"

    result = render_learning(
        FakeStreamlit(save=False),
        make_package(),
        project_id="project-123",
        preferred_hook="",
        learning_store=tmp_path / "feedback.jsonl",
        feedback_saver=saver,
    )

    assert result.action is LearningAction.NONE
    assert called is False


def test_learning_handles_missing_package_without_session_state(tmp_path):
    st = FakeStreamlit(save=True)

    result = render_learning(
        st,
        None,
        project_id="project-123",
        preferred_hook="",
        learning_store=tmp_path / "feedback.jsonl",
    )

    assert result.action is LearningAction.NONE
    assert st.warnings == ["Crie o roteiro primeiro."]
    executable_source = inspect.getsource(render_learning).split('"""', 2)[-1]
    assert "session_state" not in executable_source

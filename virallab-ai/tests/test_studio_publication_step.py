from __future__ import annotations

import inspect
import json
from types import SimpleNamespace

from virallab.studio.steps.publication import (
    PublicationAction,
    render_publication,
)


class FakeStreamlit:
    def __init__(self, *, continue_to_learning: bool = False):
        self.continue_to_learning = continue_to_learning
        self.downloads = []
        self.warnings = []

    def subheader(self, *_args, **_kwargs):
        return None

    def warning(self, value, **_kwargs):
        self.warnings.append(value)

    def text_input(self, label, value="", **_kwargs):
        values = {
            "Título": "Título revisado",
            "Hashtags": "#fisio #ia",
        }
        return values.get(label, value)

    def text_area(self, _label, value="", **_kwargs):
        return "Legenda revisada" if value else value

    def download_button(self, *args, **kwargs):
        self.downloads.append((args, kwargs))

    def button(self, label, **_kwargs):
        return label == "Continuar para Aprendizado →" and self.continue_to_learning


def make_package():
    return SimpleNamespace(
        hook="Hook original",
        thesis="Tese",
        brief=SimpleNamespace(cta="Siga o perfil."),
    )


def test_publication_exports_edited_package():
    st = FakeStreamlit()

    result = render_publication(st, make_package())

    assert result.publication is not None
    assert result.publication.title == "Título revisado"
    assert result.publication.caption == "Legenda revisada"
    assert result.publication.hashtags == "#fisio #ia"
    payload = json.loads(st.downloads[0][0][1])
    assert payload == {
        "title": "Título revisado",
        "caption": "Legenda revisada",
        "hashtags": "#fisio #ia",
    }


def test_publication_requests_learning_navigation():
    result = render_publication(
        FakeStreamlit(continue_to_learning=True),
        make_package(),
    )

    assert result.action is PublicationAction.GO_TO_LEARNING


def test_publication_handles_missing_package_without_session_state():
    st = FakeStreamlit()

    result = render_publication(st, None)

    assert result.publication is None
    assert st.warnings == ["Crie o roteiro primeiro."]
    executable_source = inspect.getsource(render_publication).split('"""', 2)[-1]
    assert "session_state" not in executable_source

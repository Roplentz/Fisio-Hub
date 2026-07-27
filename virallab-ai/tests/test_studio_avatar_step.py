from __future__ import annotations

import inspect
from contextlib import nullcontext
from pathlib import Path
from types import SimpleNamespace

from virallab.studio.steps.avatar import AvatarAction, render_avatar


class Column:
    def __init__(self, owner, index: int):
        self.owner = owner
        self.index = index

    def button(self, label, **_kwargs):
        return self.owner.buttons.get(label, False)

    def file_uploader(self, label, **_kwargs):
        return self.owner.uploads.get(label)


class FakeStreamlit:
    def __init__(self, *, buttons=None, uploads=None, consent=False):
        self.buttons = buttons or {}
        self.uploads = uploads or {}
        self.consent = consent
        self.errors = []
        self.successes = []

    def subheader(self, *_args, **_kwargs):
        return None

    def caption(self, *_args, **_kwargs):
        return None

    def info(self, *_args, **_kwargs):
        return None

    def success(self, value, **_kwargs):
        self.successes.append(value)

    def image(self, *_args, **_kwargs):
        return None

    def columns(self, count):
        return tuple(Column(self, index) for index in range(count))

    def text_input(self, label, value="", **_kwargs):
        return value

    def text_area(self, label, value="", **_kwargs):
        return value

    def checkbox(self, *_args, **_kwargs):
        return self.consent

    def button(self, label, **_kwargs):
        return self.buttons.get(label, False)

    def spinner(self, *_args, **_kwargs):
        return nullcontext()

    def markdown(self, *_args, **_kwargs):
        return None

    def error(self, value):
        self.errors.append(value)


class FakeStore:
    def __init__(self, profile=None, generated: Path | None = None):
        self.profile = profile
        self.generated = generated
        self.deleted = False
        self.saved = None
        self.approved = None

    def load(self):
        return self.profile

    def delete(self):
        self.deleted = True

    def save_references(self, **kwargs):
        self.saved = kwargs

    def generate_candidate(self):
        return self.generated

    def approve_candidate(self, path):
        self.approved = path


class Upload:
    def __init__(self, name: str):
        self.name = name
        self.type = "image/jpeg"

    def getvalue(self):
        return b"photo"


def test_avatar_requests_voice_navigation_without_session_state(tmp_path):
    profile = SimpleNamespace(
        approved=True,
        master_image_path="master.png",
        version=2,
        name="Professor RP",
        role="Especialista",
    )
    store = FakeStore(profile=profile)
    st = FakeStreamlit(buttons={"Continuar para Voz →": True})

    result = render_avatar(st, tmp_path, store_factory=lambda _workspace: store)

    assert result.action is AvatarAction.GO_TO_VOICE
    assert "session_state" not in inspect.getsource(render_avatar)


def test_avatar_returns_generated_candidate(tmp_path):
    generated = tmp_path / "candidate.png"
    generated.write_bytes(b"image")
    store = FakeStore(generated=generated)
    uploads = {
        "Foto de frente": Upload("front.jpg"),
        "Lado esquerdo": Upload("left.jpg"),
        "Lado direito": Upload("right.jpg"),
    }
    st = FakeStreamlit(
        buttons={"Salvar fotos e criar Imagem Mestre": True},
        uploads=uploads,
        consent=True,
    )

    result = render_avatar(st, tmp_path, store_factory=lambda _workspace: store)

    assert result.action is AvatarAction.RERUN
    assert result.candidate_path == generated
    assert store.saved["consent_confirmed"] is True


def test_avatar_approval_clears_candidate(tmp_path):
    candidate = tmp_path / "candidate.png"
    candidate.write_bytes(b"image")
    store = FakeStore()
    st = FakeStreamlit(buttons={"✓ Aprovar Imagem Mestre": True})

    result = render_avatar(
        st,
        tmp_path,
        candidate_path=candidate,
        store_factory=lambda _workspace: store,
    )

    assert result.action is AvatarAction.RERUN
    assert result.clear_candidate is True
    assert store.approved == candidate

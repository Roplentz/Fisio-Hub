from __future__ import annotations

import ast
import inspect
from contextlib import nullcontext
from pathlib import Path
from types import SimpleNamespace

from virallab.studio.steps.creatives import CreativesAction, render_creatives


class Widget:
    def __init__(self, owner):
        self.owner = owner

    def metric(self, *_args, **_kwargs):
        return None

    def button(self, label, **_kwargs):
        return self.owner.buttons.get(label, False)

    def file_uploader(self, *_args, **_kwargs):
        return self.owner.upload


class FakeStreamlit:
    def __init__(self, *, buttons=None, upload=None):
        self.buttons = buttons or {}
        self.upload = upload
        self.errors = []

    def subheader(self, *_args, **_kwargs):
        return None

    def success(self, *_args, **_kwargs):
        return None

    def warning(self, *_args, **_kwargs):
        return None

    def columns(self, spec):
        count = spec if isinstance(spec, int) else len(spec)
        return tuple(Widget(self) for _ in range(count))

    def selectbox(self, *_args, **_kwargs):
        return "RP cinematográfico"

    def container(self, *_args, **_kwargs):
        return nullcontext()

    def markdown(self, *_args, **_kwargs):
        return None

    def caption(self, *_args, **_kwargs):
        return None

    def text_area(self, *_args, value="", **_kwargs):
        return value

    def spinner(self, *_args, **_kwargs):
        return nullcontext()

    def error(self, value):
        self.errors.append(value)

    def image(self, *_args, **_kwargs):
        return None

    def video(self, *_args, **_kwargs):
        return None

    def button(self, label, **_kwargs):
        return self.buttons.get(label, False)


class FakeLibrary:
    def __init__(self, records=None, resolved=None):
        self.records = list(records or [])
        self.resolved = resolved or Path("asset.png")
        self.status_changes = []
        self.added = None

    def load(self):
        return self.records

    def for_scene(self, scene_index):
        return [record for record in self.records if record.scene_index == scene_index]

    def resolve(self, _record):
        return self.resolved

    def set_status(self, record_id, status):
        self.status_changes.append((record_id, status))

    def add_bytes(self, **kwargs):
        self.added = kwargs
        return SimpleNamespace(id="uploaded")


class FakeAvatarStore:
    def load(self):
        return None


class Upload:
    name = "material.png"

    def getvalue(self):
        return b"asset"


def package_fixture():
    scene = SimpleNamespace(
        index=1,
        visual_direction="Plano próximo",
        narration="Narração",
    )
    return SimpleNamespace(
        scenes=[scene],
        brief=SimpleNamespace(theme="IA na fisioterapia"),
    )


def avatar_factory(_workspace):
    return FakeAvatarStore()


def prompt_builder(*_args, **_kwargs):
    return "prompt"


def test_creatives_generation_requests_rerun(tmp_path):
    library = FakeLibrary()
    generated = []
    st = FakeStreamlit(buttons={"🎨 Gerar variação": True})

    result = render_creatives(
        st,
        package_fixture(),
        tmp_path,
        tmp_path,
        library_factory=lambda _path: library,
        avatar_store_factory=avatar_factory,
        prompt_builder=prompt_builder,
        asset_generator=lambda *args, **kwargs: generated.append((args, kwargs)),
    )

    assert result.action is CreativesAction.RERUN
    assert generated


def test_creatives_upload_is_saved_and_approved(tmp_path):
    library = FakeLibrary()
    st = FakeStreamlit(buttons={"Salvar upload": True}, upload=Upload())

    result = render_creatives(
        st,
        package_fixture(),
        tmp_path,
        tmp_path,
        library_factory=lambda _path: library,
        avatar_store_factory=avatar_factory,
        prompt_builder=prompt_builder,
    )

    assert result.action is CreativesAction.RERUN
    assert library.added["extension"] == ".png"
    assert library.status_changes == [("uploaded", "approved")]


def test_creatives_can_approve_asset_and_has_no_session_state_access(tmp_path):
    record = SimpleNamespace(id="asset-1", scene_index=1, status="pending")
    library = FakeLibrary(records=[record], resolved=tmp_path / "asset.png")
    st = FakeStreamlit(buttons={"⭐ Aprovar": True})

    result = render_creatives(
        st,
        package_fixture(),
        tmp_path,
        tmp_path,
        library_factory=lambda _path: library,
        avatar_store_factory=avatar_factory,
        prompt_builder=prompt_builder,
    )

    tree = ast.parse(inspect.getsource(render_creatives))
    attributes = [node.attr for node in ast.walk(tree) if isinstance(node, ast.Attribute)]
    assert "session_state" not in attributes
    assert result.action is CreativesAction.RERUN
    assert library.status_changes == [("asset-1", "approved")]


def test_creatives_requests_render_navigation(tmp_path):
    record = SimpleNamespace(id="asset-1", scene_index=1, status="approved")
    library = FakeLibrary(records=[record], resolved=tmp_path / "asset.png")
    st = FakeStreamlit(buttons={"Continuar para Render →": True})

    result = render_creatives(
        st,
        package_fixture(),
        tmp_path,
        tmp_path,
        library_factory=lambda _path: library,
        avatar_store_factory=avatar_factory,
        prompt_builder=prompt_builder,
    )

    assert result.action is CreativesAction.GO_TO_RENDER

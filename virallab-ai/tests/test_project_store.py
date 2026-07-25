from __future__ import annotations

from virallab.models import Scene, VideoBrief, VideoPackage
from virallab.project_store import ProjectStore


def sample_package() -> VideoPackage:
    return VideoPackage(
        brief=VideoBrief(theme="IA na fisioterapia", duration_seconds=30),
        hook="Hook de teste",
        thesis="Tese de teste",
        scenes=[
            Scene(
                index=1,
                start=0.0,
                end=3.0,
                scene_type="avatar",
                narration="Abertura",
                on_screen_text="Texto",
            )
        ],
    )


def test_numbered_save_load_and_zip(tmp_path):
    store = ProjectStore(tmp_path / "projects")
    assert store.next_id() == "001"

    saved = store.save(
        "001", name="Primeiro", package=sample_package(), preferred_hook="Minha voz"
    )
    assert saved.project_id == "001"
    assert store.next_id() == "002"

    loaded, package, preferred_hook = store.load("001")
    assert loaded.name == "Primeiro"
    assert package is not None
    assert package.brief.theme == "IA na fisioterapia"
    assert package.scenes[0].scene_type == "avatar"
    assert preferred_hook == "Minha voz"

    backup = store.export_zip("001")
    imported = store.import_zip(backup)
    assert imported.project_id == "002"
    assert store.load("002")[1] is not None

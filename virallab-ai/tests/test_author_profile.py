from types import SimpleNamespace

from virallab.author_profile import AuthorProfileStore
from virallab.creative_assets import build_scene_prompt


def test_author_profile_roundtrip(tmp_path):
    store = AuthorProfileStore(tmp_path)
    saved = store.save(
        name="Professor RP",
        role="Autor do canal",
        image_bytes=b"fake-image",
        extension=".jpg",
        mime_type="image/jpeg",
        visual_notes="Expressão acolhedora",
    )

    loaded = store.load()
    assert loaded == saved
    assert store.reference() == (b"fake-image", "image/jpeg")


def test_avatar_prompt_preserves_saved_identity(tmp_path):
    store = AuthorProfileStore(tmp_path)
    profile = store.save(
        name="Professor RP",
        role="Autor do canal",
        image_bytes=b"fake-image",
        extension=".png",
        mime_type="image/png",
    )
    scene = SimpleNamespace(
        scene_type="avatar",
        visual_direction="falando com a câmera",
        narration="A inovação começa pela pergunta.",
        on_screen_text="Mude a lente",
    )

    prompt = build_scene_prompt(scene, theme="inovação", author_profile=profile)

    assert "Professor RP" in prompt
    assert "Não crie outra pessoa" in prompt
    assert "Preserve com alta fidelidade" in prompt

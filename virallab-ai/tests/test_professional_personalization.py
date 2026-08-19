from __future__ import annotations

import json

import pytest

from virallab.brand_kit import BrandKitStore
from virallab.personal_media import PersonalMediaLibrary
from virallab.pronunciation import PronunciationDictionary


def test_brand_kit_is_versioned_and_persistent(tmp_path):
    logo = tmp_path / "logo.png"
    logo.write_bytes(b"logo")
    store = BrandKitStore(tmp_path)

    first = store.save(
        name="Fisio IA",
        primary_color="#123456",
        secondary_color="#ABCDEF",
        accent_color="#00AACC",
        tone=["científico", "humano"],
        logo_file=logo,
    )
    second = store.save(
        name="Fisio IA",
        primary_color="#123456",
        secondary_color="#ABCDEF",
        accent_color="#00AACC",
    )

    assert first.version == 1
    assert second.version == 2
    assert store.load().logo_path.endswith("logo.png")
    assert "Fisio IA" in second.prompt_instruction()


def test_brand_kit_rejects_invalid_color(tmp_path):
    with pytest.raises(ValueError):
        BrandKitStore(tmp_path).save(
            name="Marca",
            primary_color="azul",
            secondary_color="#000000",
            accent_color="#FFFFFF",
        )


def test_pronunciation_dictionary_changes_only_tts_copy(tmp_path):
    dictionary = PronunciationDictionary()
    dictionary.add("TENS", "téns")
    original = "A TENS pode ser utilizada conforme avaliação."
    spoken = dictionary.apply(original)

    assert original == "A TENS pode ser utilizada conforme avaliação."
    assert spoken == "A téns pode ser utilizada conforme avaliação."

    path = dictionary.save(tmp_path / "pronunciation.json")
    assert PronunciationDictionary.load(path).apply("TENS") == "téns"


def test_personal_media_requires_consent_and_tracks_hash(tmp_path):
    source = tmp_path / "aula.mp4"
    source.write_bytes(b"video")
    library = PersonalMediaLibrary(tmp_path / "workspace")

    with pytest.raises(ValueError):
        library.add(source, consent_confirmed=False)

    item = library.add(source, consent_confirmed=True)
    payload = json.loads(library.manifest.read_text(encoding="utf-8"))

    assert item.media_type == "video"
    assert item.sha256
    assert payload["media"][0]["consent_confirmed"] is True

    library.delete(item.media_id)
    assert library.list() == []

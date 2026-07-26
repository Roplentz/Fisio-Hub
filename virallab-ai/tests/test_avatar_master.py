from pathlib import Path

import pytest

from virallab.avatar_master import AvatarMasterStore


def _photo(label: str) -> tuple[bytes, str, str]:
    return f"fake-{label}".encode(), f"{label}.jpg", "image/jpeg"


def test_requires_three_photos_and_consent(tmp_path: Path) -> None:
    store = AvatarMasterStore(tmp_path)
    with pytest.raises(ValueError):
        store.save_references(
            name="Autor",
            role="Especialista",
            photos={"front": _photo("front")},
            consent_confirmed=True,
        )
    with pytest.raises(ValueError):
        store.save_references(
            name="Autor",
            role="Especialista",
            photos={angle: _photo(angle) for angle in store.ANGLES},
            consent_confirmed=False,
        )


def test_persists_three_angles_and_approves_candidate(tmp_path: Path) -> None:
    store = AvatarMasterStore(tmp_path)
    profile = store.save_references(
        name="Professor RP",
        role="Autor",
        photos={angle: _photo(angle) for angle in store.ANGLES},
        visual_notes="Manter aparência natural",
        consent_confirmed=True,
    )
    assert [item.angle for item in profile.references] == ["front", "left", "right"]
    assert profile.approved is False

    candidate = store.candidates_dir / "candidate-v1.png"
    candidate.write_bytes(b"fake-master")
    approved = store.approve_candidate(candidate)

    assert approved.approved is True
    assert Path(approved.master_image_path).read_bytes() == b"fake-master"
    references = store.references(include_master=True)
    assert len(references) == 4


def test_delete_removes_personal_references(tmp_path: Path) -> None:
    store = AvatarMasterStore(tmp_path)
    store.save_references(
        name="Professor RP",
        role="Autor",
        photos={angle: _photo(angle) for angle in store.ANGLES},
        consent_confirmed=True,
    )
    store.delete()
    assert store.load() is None
    assert list(store.refs_dir.iterdir()) == []

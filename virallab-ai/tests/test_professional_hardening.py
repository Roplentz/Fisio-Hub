from __future__ import annotations

import io
import zipfile

import pytest

from virallab.project_store import ProjectStore
from virallab.voice import MAX_NARRATION_BYTES, VoiceError, save_narration


def test_import_zip_rejects_oversized_member(tmp_path) -> None:
    payload = io.BytesIO()
    with zipfile.ZipFile(payload, "w") as archive:
        archive.writestr(
            "project-001/video-package.json",
            b"x" * (50 * 1024 * 1024 + 1),
        )

    store = ProjectStore(tmp_path / "projects")
    with pytest.raises(ValueError, match="50 MB"):
        store.import_zip(payload.getvalue())


def test_import_zip_rejects_too_many_members(tmp_path) -> None:
    payload = io.BytesIO()
    with zipfile.ZipFile(payload, "w") as archive:
        for index in range(5001):
            archive.writestr(f"project-001/assets/{index}.txt", b"x")

    store = ProjectStore(tmp_path / "projects")
    with pytest.raises(ValueError, match="5.000"):
        store.import_zip(payload.getvalue())


def test_save_narration_rejects_oversized_audio(tmp_path) -> None:
    with pytest.raises(VoiceError, match="100 MB"):
        save_narration(tmp_path, b"x" * (MAX_NARRATION_BYTES + 1))

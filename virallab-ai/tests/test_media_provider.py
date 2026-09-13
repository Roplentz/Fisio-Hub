from __future__ import annotations

import json

import pytest

from virallab.media_provider import (
    LocalMediaProvider,
    MediaProviderError,
    PexelsMediaProvider,
    write_media_manifest,
)


def test_local_provider_indexes_and_copies_authorized_media(tmp_path):
    library = tmp_path / "library"
    library.mkdir()
    source = library / "fisioterapia-respiratoria.mp4"
    source.write_bytes(b"video")

    provider = LocalMediaProvider(library)
    assets = provider.search("fisioterapia respiratoria")

    assert len(assets) == 1
    assert assets[0].provider == "local"
    assert assets[0].license_name == "user_supplied"
    assert assets[0].sha256

    copied = provider.download(assets[0], tmp_path / "output.mp4")
    assert copied.local_path.endswith("output.mp4")
    assert (tmp_path / "output.mp4").read_bytes() == b"video"


def test_local_provider_rejects_source_outside_authorized_library(tmp_path):
    library = tmp_path / "library"
    library.mkdir()
    outside = tmp_path / "outside.mp4"
    outside.write_bytes(b"video")
    provider = LocalMediaProvider(library)

    from virallab.media_provider import MediaAsset

    asset = MediaAsset(
        asset_id="x",
        provider="local",
        source_url=outside.as_uri(),
        media_type="video",
        local_path=str(outside),
    )
    with pytest.raises(MediaProviderError):
        provider.download(asset, tmp_path / "copy.mp4")


def test_pexels_requires_explicit_key():
    with pytest.raises(MediaProviderError):
        PexelsMediaProvider(api_key="").search("fisioterapia")


def test_manifest_records_provenance(tmp_path):
    library = tmp_path / "library"
    library.mkdir()
    (library / "exercicio-terapeutico.jpg").write_bytes(b"image")
    assets = LocalMediaProvider(library).search("exercicio terapeutico")

    path = write_media_manifest(assets, tmp_path / "media-manifest.json")
    payload = json.loads(path.read_text(encoding="utf-8"))

    assert payload["version"] == "1.0"
    assert payload["assets"][0]["provider"] == "local"
    assert payload["assets"][0]["sha256"]

from __future__ import annotations

import hashlib
import json
import mimetypes
import os
import shutil
import urllib.parse
import urllib.request
from abc import ABC, abstractmethod
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ALLOWED_MEDIA_SUFFIXES = {".mp4", ".mov", ".mkv", ".webm", ".png", ".jpg", ".jpeg", ".webp"}
MAX_DOWNLOAD_BYTES = 250 * 1024 * 1024


class MediaProviderError(RuntimeError):
    """Falha controlada ao localizar ou obter mídia."""


@dataclass(frozen=True)
class MediaAsset:
    asset_id: str
    provider: str
    source_url: str
    media_type: str
    width: int = 0
    height: int = 0
    duration_seconds: float = 0.0
    author: str = ""
    license_name: str = ""
    license_url: str = ""
    collected_at: str = ""
    sha256: str = ""
    local_path: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class MediaProvider(ABC):
    @abstractmethod
    def search(
        self,
        query: str,
        *,
        orientation: str = "portrait",
        duration_seconds: int = 15,
        limit: int = 10,
    ) -> list[MediaAsset]:
        raise NotImplementedError

    @abstractmethod
    def download(self, asset: MediaAsset, destination: str | Path) -> MediaAsset:
        raise NotImplementedError


class LocalMediaProvider(MediaProvider):
    """Indexa somente arquivos locais permitidos; não envia conteúdo a terceiros."""

    def __init__(self, root: str | Path) -> None:
        self.root = Path(root).resolve()

    def search(
        self,
        query: str,
        *,
        orientation: str = "portrait",
        duration_seconds: int = 15,
        limit: int = 10,
    ) -> list[MediaAsset]:
        if not self.root.is_dir():
            return []
        terms = [term.casefold() for term in query.split() if term.strip()]
        matches: list[MediaAsset] = []
        for path in sorted(self.root.rglob("*")):
            if not path.is_file() or path.suffix.casefold() not in ALLOWED_MEDIA_SUFFIXES:
                continue
            haystack = path.stem.replace("-", " ").replace("_", " ").casefold()
            if terms and not all(term in haystack for term in terms):
                continue
            matches.append(
                MediaAsset(
                    asset_id=_sha256(path),
                    provider="local",
                    source_url=path.as_uri(),
                    media_type=_media_type(path),
                    license_name="user_supplied",
                    collected_at=_now(),
                    sha256=_sha256(path),
                    local_path=str(path),
                )
            )
            if len(matches) >= max(1, limit):
                break
        return matches

    def download(self, asset: MediaAsset, destination: str | Path) -> MediaAsset:
        source = Path(asset.local_path).resolve()
        if not source.is_file() or self.root not in source.parents:
            raise MediaProviderError("Arquivo local ausente ou fora da biblioteca autorizada.")
        target = _safe_destination(destination, source.suffix)
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)
        return MediaAsset(**{**asset.to_dict(), "local_path": str(target), "sha256": _sha256(target)})


class PexelsMediaProvider(MediaProvider):
    """Cliente mínimo da API oficial do Pexels, desativado sem chave explícita."""

    api_url = "https://api.pexels.com/videos/search"
    license_url = "https://www.pexels.com/license/"

    def __init__(self, api_key: str | None = None, *, timeout_seconds: int = 20) -> None:
        self.api_key = (api_key or os.getenv("PEXELS_API_KEY", "")).strip()
        self.timeout_seconds = timeout_seconds

    def search(
        self,
        query: str,
        *,
        orientation: str = "portrait",
        duration_seconds: int = 15,
        limit: int = 10,
    ) -> list[MediaAsset]:
        if not self.api_key:
            raise MediaProviderError("PEXELS_API_KEY não configurada.")
        if not query.strip():
            raise MediaProviderError("A consulta de mídia não pode estar vazia.")
        params = urllib.parse.urlencode(
            {"query": query.strip(), "orientation": orientation, "per_page": min(max(limit, 1), 40)}
        )
        request = urllib.request.Request(
            f"{self.api_url}?{params}",
            headers={"Authorization": self.api_key, "User-Agent": "FisioIA-Creator/0.11"},
        )
        payload = _read_json(request, timeout=self.timeout_seconds)
        assets: list[MediaAsset] = []
        for video in payload.get("videos", []):
            candidate = _best_video_file(video.get("video_files", []), orientation)
            if not candidate:
                continue
            assets.append(
                MediaAsset(
                    asset_id=str(video.get("id", "")),
                    provider="pexels",
                    source_url=str(candidate["link"]),
                    media_type="video",
                    width=int(candidate.get("width") or 0),
                    height=int(candidate.get("height") or 0),
                    duration_seconds=float(video.get("duration") or 0),
                    author=str((video.get("user") or {}).get("name", "")),
                    license_name="Pexels License",
                    license_url=self.license_url,
                    collected_at=_now(),
                )
            )
        return assets

    def download(self, asset: MediaAsset, destination: str | Path) -> MediaAsset:
        if asset.provider != "pexels" or not asset.source_url.startswith("https://"):
            raise MediaProviderError("Ativo incompatível com o provedor Pexels.")
        target = _safe_destination(destination, ".mp4")
        target.parent.mkdir(parents=True, exist_ok=True)
        request = urllib.request.Request(asset.source_url, headers={"User-Agent": "FisioIA-Creator/0.11"})
        with urllib.request.urlopen(request, timeout=self.timeout_seconds) as response, target.open("wb") as out:
            total = 0
            while chunk := response.read(1024 * 1024):
                total += len(chunk)
                if total > MAX_DOWNLOAD_BYTES:
                    target.unlink(missing_ok=True)
                    raise MediaProviderError("Download excede o limite de 250 MB.")
                out.write(chunk)
        return MediaAsset(**{**asset.to_dict(), "local_path": str(target), "sha256": _sha256(target)})


def write_media_manifest(assets: list[MediaAsset], destination: str | Path) -> Path:
    target = Path(destination)
    target.parent.mkdir(parents=True, exist_ok=True)
    payload = {"version": "1.0", "generated_at": _now(), "assets": [asset.to_dict() for asset in assets]}
    target.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return target


def _best_video_file(files: list[dict[str, Any]], orientation: str) -> dict[str, Any] | None:
    candidates = [item for item in files if item.get("link") and item.get("file_type") == "video/mp4"]
    if not candidates:
        return None
    portrait = orientation == "portrait"
    oriented = [
        item for item in candidates
        if (int(item.get("height") or 0) >= int(item.get("width") or 0)) == portrait
    ]
    pool = oriented or candidates
    return min(pool, key=lambda item: abs(int(item.get("width") or 0) - 1080))


def _read_json(request: urllib.request.Request, *, timeout: int) -> dict[str, Any]:
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return json.loads(response.read().decode("utf-8"))
    except Exception as exc:
        raise MediaProviderError(f"Falha ao consultar o provedor: {type(exc).__name__}.") from exc


def _safe_destination(destination: str | Path, suffix: str) -> Path:
    target = Path(destination)
    if target.exists() and target.is_dir():
        target = target / f"asset{suffix}"
    if target.suffix.casefold() not in ALLOWED_MEDIA_SUFFIXES:
        raise MediaProviderError("Formato de destino não permitido.")
    return target.resolve()


def _media_type(path: Path) -> str:
    guessed, _ = mimetypes.guess_type(path.name)
    return "video" if (guessed or "").startswith("video/") else "image"


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()

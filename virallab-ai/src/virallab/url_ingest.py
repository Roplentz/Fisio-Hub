from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlparse


class URLIngestError(RuntimeError):
    """Raised when a remote video cannot be imported."""


@dataclass(slots=True)
class ImportedVideo:
    path: Path
    title: str
    source_url: str
    extractor: str


def _validate_url(url: str) -> str:
    normalized = url.strip()
    parsed = urlparse(normalized)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise URLIngestError(
            "Informe uma URL pública válida iniciada por http:// ou https://."
        )
    return normalized


def download_video_url(url: str, output_dir: str | Path) -> ImportedVideo:
    """Download a public video URL with yt-dlp.

    Platform pages may require authentication, cookies or permission from the owner.
    The function never bypasses access controls.
    """
    try:
        import yt_dlp
    except ImportError as exc:
        raise URLIngestError(
            "A importação por URL não está instalada neste ambiente."
        ) from exc

    source_url = _validate_url(url)
    destination = Path(output_dir)
    destination.mkdir(parents=True, exist_ok=True)
    output_template = str(destination / "%(id)s-%(title).80s.%(ext)s")

    options = {
        "outtmpl": output_template,
        "format": "bv*[height<=1080]+ba/b[height<=1080]/b",
        "merge_output_format": "mp4",
        "noplaylist": True,
        "quiet": True,
        "no_warnings": True,
        "restrictfilenames": True,
        "socket_timeout": 30,
    }

    try:
        with yt_dlp.YoutubeDL(options) as downloader:
            info = downloader.extract_info(source_url, download=True)
            prepared = Path(downloader.prepare_filename(info))
    except Exception as exc:
        raise URLIngestError(
            "Não foi possível importar essa URL. O conteúdo pode ser privado, exigir login, "
            "bloquear downloads ou não disponibilizar um arquivo de vídeo compatível."
        ) from exc

    candidates = [prepared]
    if prepared.suffix.lower() != ".mp4":
        candidates.insert(0, prepared.with_suffix(".mp4"))
    video_path = next(
        (candidate for candidate in candidates if candidate.exists()), None
    )
    if video_path is None:
        matches = sorted(
            destination.glob(f"{info.get('id', '')}-*"),
            key=lambda item: item.stat().st_mtime,
            reverse=True,
        )
        video_path = next(
            (
                item
                for item in matches
                if item.suffix.lower() in {".mp4", ".mov", ".mkv", ".webm", ".m4v"}
            ),
            None,
        )
    if video_path is None:
        raise URLIngestError(
            "O download terminou, mas nenhum arquivo de vídeo compatível foi encontrado."
        )

    return ImportedVideo(
        path=video_path,
        title=str(info.get("title") or video_path.stem),
        source_url=source_url,
        extractor=str(info.get("extractor_key") or info.get("extractor") or "web"),
    )

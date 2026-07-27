"""Interface da etapa de análise de referências em vídeo."""

from __future__ import annotations

import uuid
from enum import StrEnum
from pathlib import Path
from typing import Any, Callable

from virallab.url_ingest import URLIngestError, download_video_url


class AnalysisAction(StrEnum):
    """Ações que precisam ser tratadas pelo orquestrador do Studio."""

    CREATE_FROM_SCRATCH = "create_from_scratch"


AnalysisCallback = Callable[[Path, str, str], None]
DownloadVideo = Callable[[str, Path], Any]
IdFactory = Callable[[], str]


def save_uploaded_file(uploaded_file: Any, destination: Path) -> Path:
    """Persiste um upload no diretório informado e devolve seu caminho."""

    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_bytes(uploaded_file.getbuffer())
    return destination


def _default_id() -> str:
    return uuid.uuid4().hex[:10]


def render_analysis(
    st: Any,
    analysis_dir: Path,
    on_analysis_requested: AnalysisCallback,
    *,
    downloader: DownloadVideo = download_video_url,
    id_factory: IdFactory = _default_id,
) -> AnalysisAction | None:
    """Renderiza a etapa sem conhecer estado, rotas ou workspace global."""

    st.subheader("Analisar vídeo")
    st.caption("Use uma referência para entender estrutura, hook, ritmo e CTA — sem copiar literalmente.")
    upload_tab, url_tab = st.tabs(["📁 Enviar vídeo", "🔗 Importar URL"])

    with upload_tab:
        uploaded = st.file_uploader(
            "Vídeo",
            type=["mp4", "mov", "m4v", "webm", "mkv"],
            key="v3-analysis-upload",
        )
        if uploaded is not None:
            st.video(uploaded.getvalue())
            if st.button("Analisar este vídeo →", type="primary", use_container_width=True):
                suffix = Path(uploaded.name).suffix or ".mp4"
                path = save_uploaded_file(uploaded, analysis_dir / f"{id_factory()}{suffix}")
                on_analysis_requested(path, uploaded.name, "upload")

    with url_tab:
        url = st.text_input("URL pública", key="v3-analysis-url")
        if st.button("Importar e analisar →", disabled=not url.strip(), use_container_width=True):
            try:
                imported = downloader(url, analysis_dir / "urls")
                on_analysis_requested(imported.path, imported.title, imported.source_url)
            except URLIngestError as exc:
                st.error(str(exc))

    st.divider()
    if st.button("✨ Criar do zero, sem vídeo", use_container_width=True):
        return AnalysisAction.CREATE_FROM_SCRATCH
    return None


__all__ = ["AnalysisAction", "render_analysis", "save_uploaded_file"]

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any, Callable

from virallab.asset_library import AssetLibrary
from virallab.renderer import RenderError, render_video
from virallab.voice import load_voice_plan
from virallab.voice_renderer import render_video_with_voice


class RenderAction(str, Enum):
    NONE = "none"
    GO_TO_PUBLICATION = "go_to_publication"


@dataclass(frozen=True)
class RenderResult:
    """Outcome requested by the render step."""

    action: RenderAction = RenderAction.NONE
    video_path: Path | None = None


def render_output(
    st: Any,
    package_path: Path,
    *,
    library_factory: Callable[[Path], Any] = AssetLibrary,
    voice_plan_loader: Callable[[Path], Any] = load_voice_plan,
    silent_renderer: Callable[..., Path] = render_video,
    voice_renderer: Callable[..., Path] = render_video_with_voice,
) -> RenderResult:
    """Render and expose the final video without touching session state."""

    st.subheader("Render")
    library = library_factory(package_path)
    approved = [item for item in library.load() if item.status == "approved"]
    voice_plan = voice_plan_loader(package_path)

    first, second = st.columns(2)
    first.metric("Criativos aprovados", len(approved))
    second.metric("Voz", "Pronta" if voice_plan else "Não gravada")

    burn_captions = st.checkbox("Legendas incorporadas", value=True)
    music_level = st.slider("Trilha (dB)", -40, -12, -25)
    voice_gain = st.slider("Voz (dB)", -6, 6, 0)

    video_path = package_path / "video-final.mp4"
    if st.button(
        "Renderizar vídeo",
        type="primary",
        use_container_width=True,
        disabled=not approved,
    ):
        try:
            with st.spinner("Renderizando..."):
                rendered = (
                    voice_renderer(
                        package_path,
                        burn_captions=burn_captions,
                        music_level_db=music_level,
                        narration_gain_db=voice_gain,
                    )
                    if voice_plan
                    else silent_renderer(
                        package_path,
                        burn_captions=burn_captions,
                        music_level_db=music_level,
                    )
                )
            video_path = Path(rendered)
            if not video_path.exists():
                st.error("O renderizador terminou sem produzir o arquivo final.")
                return RenderResult()
        except RenderError as exc:
            st.error(str(exc))
            return RenderResult()

    if video_path.exists():
        st.video(str(video_path))
        st.download_button(
            "Baixar vídeo final",
            video_path.read_bytes(),
            "video-final.mp4",
            "video/mp4",
            use_container_width=True,
        )
        if st.button(
            "Continuar para Publicação →",
            type="primary",
            use_container_width=True,
        ):
            return RenderResult(
                action=RenderAction.GO_TO_PUBLICATION,
                video_path=video_path,
            )
        return RenderResult(video_path=video_path)

    return RenderResult()

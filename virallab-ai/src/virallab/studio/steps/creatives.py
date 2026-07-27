from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any, Callable

from virallab.asset_library import AssetLibrary
from virallab.avatar_master import AvatarMasterStore, ImageGenerationError
from virallab.creative_assets import build_scene_prompt, generate_scene_asset


VISUAL_STYLES = [
    "RP cinematográfico",
    "Clínico premium",
    "Editorial científico",
    "Humano documental",
    "Minimalista tecnológico",
]


class CreativesAction(str, Enum):
    NONE = "none"
    RERUN = "rerun"
    GO_TO_RENDER = "go_to_render"


@dataclass(frozen=True)
class CreativesResult:
    """State changes requested by the creatives step."""

    action: CreativesAction = CreativesAction.NONE


def _render_asset(st: Any, library: Any, record: Any) -> CreativesResult:
    path = library.resolve(record)
    suffix = path.suffix.lower()
    if suffix in {".png", ".jpg", ".jpeg", ".webp"}:
        st.image(str(path), use_container_width=True)
    elif suffix in {".mp4", ".mov", ".webm"}:
        st.video(str(path))

    approve, reject = st.columns(2)
    if approve.button(
        "⭐ Aprovar",
        key=f"approve-v3-{record.id}",
        disabled=record.status == "approved",
        use_container_width=True,
    ):
        library.set_status(record.id, "approved")
        return CreativesResult(action=CreativesAction.RERUN)
    if reject.button(
        "Rejeitar",
        key=f"reject-v3-{record.id}",
        disabled=record.status == "rejected",
        use_container_width=True,
    ):
        library.set_status(record.id, "rejected")
        return CreativesResult(action=CreativesAction.RERUN)
    return CreativesResult()


def render_creatives(
    st: Any,
    package: Any,
    package_path: Path,
    workspace: Path,
    *,
    library_factory: Callable[[Path], Any] = AssetLibrary,
    avatar_store_factory: Callable[[Path], Any] = AvatarMasterStore,
    prompt_builder: Callable[..., str] = build_scene_prompt,
    asset_generator: Callable[..., Any] = generate_scene_asset,
) -> CreativesResult:
    """Render creative asset management without touching session state."""

    st.subheader("Criativos")
    avatar_profile = avatar_store_factory(workspace).load()
    if avatar_profile and avatar_profile.approved:
        st.success(
            f"Avatar IA ativo: {avatar_profile.name} · versão {avatar_profile.version}"
        )
    else:
        st.warning(
            "Nenhuma Imagem Mestre aprovada. Cenas do autor usarão o modo "
            "genérico ou a referência antiga."
        )

    library = library_factory(package_path)
    approved_count = sum(1 for item in library.load() if item.status == "approved")
    first, second = st.columns(2)
    first.metric("Cenas", len(package.scenes))
    second.metric("Aprovadas", f"{approved_count}/{len(package.scenes)}")
    style = st.selectbox("DNA visual", VISUAL_STYLES)

    for scene in package.scenes:
        records = library.for_scene(scene.index)
        approved = next((item for item in records if item.status == "approved"), None)
        prompt = prompt_builder(
            scene,
            theme=package.brief.theme,
            visual_style=style,
            avatar_profile=avatar_profile,
        )
        with st.container(border=True):
            status = "✓ aprovada" if approved else "aguardando"
            st.markdown(f"**Cena {scene.index}** · {status}")
            st.caption(scene.visual_direction or scene.narration)
            edited = st.text_area(
                "Direção da imagem",
                value=prompt,
                height=130,
                key=f"prompt-v3-{scene.index}",
            )
            generate_col, upload_col = st.columns(2)
            if generate_col.button(
                "🎨 Gerar variação",
                key=f"gen-v3-{scene.index}",
                type="primary",
                use_container_width=True,
            ):
                try:
                    with st.spinner("Criando..."):
                        asset_generator(package_path, scene, prompt=edited)
                    return CreativesResult(action=CreativesAction.RERUN)
                except (ImageGenerationError, ValueError) as exc:
                    st.error(str(exc))

            upload = upload_col.file_uploader(
                "Enviar material",
                type=["mp4", "mov", "webm", "png", "jpg", "jpeg", "webp"],
                key=f"upload-v3-{scene.index}",
                label_visibility="collapsed",
            )
            if upload is not None and upload_col.button(
                "Salvar upload",
                key=f"save-v3-{scene.index}",
                use_container_width=True,
            ):
                record = library.add_bytes(
                    scene_index=scene.index,
                    data=upload.getvalue(),
                    extension=Path(upload.name).suffix or ".png",
                    source="upload",
                    provider="human",
                    prompt=edited,
                    metadata={"original_name": upload.name},
                )
                library.set_status(record.id, "approved")
                return CreativesResult(action=CreativesAction.RERUN)

            for record in reversed(library.for_scene(scene.index)):
                result = _render_asset(st, library, record)
                if result.action is not CreativesAction.NONE:
                    return result

    if approved_count and st.button(
        "Continuar para Render →",
        type="primary",
        use_container_width=True,
    ):
        return CreativesResult(action=CreativesAction.GO_TO_RENDER)
    return CreativesResult()

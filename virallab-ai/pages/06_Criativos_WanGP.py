from __future__ import annotations

import os
from pathlib import Path

import streamlit as st

from virallab.asset_library import AssetLibrary
from virallab.avatar_master import AvatarMasterStore
from virallab.creative_assets import build_scene_prompt
from virallab.wangp_provider import WanGPError, WanGPProvider


st.set_page_config(
    page_title="Criativos WanGP · RP ViralLab",
    page_icon="🎬",
    layout="wide",
)

WORKSPACE = Path(__file__).resolve().parents[1] / "workspace"


def _current_project() -> tuple[object | None, Path | None]:
    package = st.session_state.get("package")
    raw_path = st.session_state.get("package_dir")
    return package, Path(raw_path) if raw_path else None


def _wangp_status() -> tuple[bool, str]:
    root = os.getenv("WANGP_ROOT", "").strip()
    if not root:
        return False, "Defina WANGP_ROOT com a pasta da instalação local do WanGP."
    path = Path(root).expanduser()
    if not path.is_dir():
        return False, f"A pasta configurada não existe: {path}"
    if not (path / "shared" / "api.py").is_file():
        return False, f"A instalação não contém shared/api.py: {path}"
    return True, f"WanGP localizado em {path}"


def _progress_callback(progress_bar, status_box):
    def update(data) -> None:
        raw = float(getattr(data, "progress", 0.0) or 0.0)
        ratio = raw / 100.0 if raw > 1 else raw
        ratio = max(0.0, min(1.0, ratio))
        label = str(
            getattr(data, "status", "")
            or getattr(data, "phase", "")
            or "Gerando vídeo..."
        )
        progress_bar.progress(ratio, text=label)
        status_box.caption(label)

    return update


st.title("🎬 Criativos com WanGP")
st.caption(
    "Gere clipes verticais por cena usando o WanGP instalado no computador com GPU. "
    "Os resultados entram na mesma biblioteca de criativos do ViralLab."
)

package, package_path = _current_project()
configured, status = _wangp_status()

if configured:
    st.success(status)
else:
    st.warning(status)
    st.code(
        "WANGP_ROOT=C:\\WanGP\n"
        "WANGP_MODEL=ltx2_22B_distilled\n"
        "WANGP_OUTPUT_DIR=C:\\WanGP\\outputs",
        language="text",
    )

if package is None or package_path is None:
    st.error(
        "Nenhum projeto ativo. Volte ao Studio, gere o roteiro e depois abra esta página."
    )
    st.stop()

library = AssetLibrary(package_path)
avatar_profile = AvatarMasterStore(WORKSPACE).load()

approved_count = sum(1 for item in library.load() if item.status == "approved")
metric_a, metric_b, metric_c = st.columns(3)
metric_a.metric("Projeto", st.session_state.get("project_id", "—"))
metric_b.metric("Cenas", len(package.scenes))
metric_c.metric("Aprovadas", f"{approved_count}/{len(package.scenes)}")

with st.expander("Configuração da geração", expanded=True):
    col_a, col_b, col_c = st.columns(3)
    resolution = col_a.selectbox(
        "Resolução",
        ["704x1280", "576x1024", "768x1344"],
        index=0,
    )
    steps = col_b.slider("Passos de inferência", 4, 30, 8)
    default_duration = col_c.slider("Duração padrão", 1, 12, 4)
    style = st.selectbox(
        "DNA visual",
        [
            "RP cinematográfico",
            "Clínico premium",
            "Editorial científico",
            "Humano documental",
            "Minimalista tecnológico",
        ],
    )

for scene in package.scenes:
    records = library.for_scene(scene.index)
    approved = next((item for item in records if item.status == "approved"), None)
    prompt = build_scene_prompt(
        scene,
        theme=package.brief.theme,
        visual_style=style,
        avatar_profile=avatar_profile,
    )
    scene_duration = max(
        1,
        min(30, round(float(scene.end) - float(scene.start)) or default_duration),
    )

    with st.container(border=True):
        st.markdown(
            f"### Cena {scene.index} · "
            f"{'✓ aprovada' if approved else 'aguardando aprovação'}"
        )
        st.caption(scene.visual_direction or scene.narration or "Cena sem direção visual")

        edited_prompt = st.text_area(
            "Prompt do vídeo",
            value=prompt,
            height=150,
            key=f"wangp-prompt-{scene.index}",
        )

        config_a, config_b = st.columns(2)
        duration = config_a.slider(
            "Duração da cena",
            1,
            30,
            scene_duration,
            key=f"wangp-duration-{scene.index}",
        )
        use_reference = config_b.checkbox(
            "Usar Imagem Mestre como referência",
            value=bool(
                str(getattr(scene, "scene_type", "")) == "avatar"
                and avatar_profile
                and avatar_profile.approved
                and avatar_profile.master_image_path
            ),
            key=f"wangp-reference-{scene.index}",
        )

        reference_image = None
        if use_reference:
            if avatar_profile and avatar_profile.approved and avatar_profile.master_image_path:
                reference_image = avatar_profile.master_image_path
                st.image(
                    str(reference_image),
                    caption="Imagem Mestre usada como quadro inicial",
                    width=220,
                )
            else:
                st.warning("Não existe uma Imagem Mestre aprovada para este projeto.")

        generate_col, approve_latest_col = st.columns(2)
        generate_clicked = generate_col.button(
            "🎬 Gerar vídeo com WanGP",
            key=f"wangp-generate-{scene.index}",
            type="primary",
            use_container_width=True,
            disabled=not configured,
        )

        latest_candidate = next(
            (item for item in reversed(records) if item.status == "candidate"),
            None,
        )
        if approve_latest_col.button(
            "⭐ Aprovar última candidata",
            key=f"wangp-approve-latest-{scene.index}",
            use_container_width=True,
            disabled=latest_candidate is None,
        ):
            library.set_status(latest_candidate.id, "approved")
            st.rerun()

        if generate_clicked:
            progress = st.progress(0.0, text="Preparando WanGP...")
            status_box = st.empty()
            try:
                provider = WanGPProvider()
                with st.spinner("Gerando o clipe na GPU local..."):
                    generated = provider.generate_video(
                        prompt=edited_prompt,
                        duration_seconds=duration,
                        resolution=resolution,
                        num_inference_steps=steps,
                        reference_image=reference_image,
                        progress_callback=_progress_callback(progress, status_box),
                    )
                    record = library.add_file(
                        scene_index=int(scene.index),
                        source_file=generated,
                        source="generated",
                        provider=provider.name,
                        prompt=edited_prompt,
                    )
                progress.progress(1.0, text="Vídeo concluído")
                st.success(f"Nova candidata criada: {record.id}")
                st.rerun()
            except WanGPError as exc:
                st.error(str(exc))
            except Exception as exc:
                st.error(f"Erro inesperado ao gerar a cena: {exc}")

        for record in reversed(library.for_scene(scene.index)):
            path = library.resolve(record)
            st.markdown(
                f"**{record.provider}** · `{record.status}` · `{path.name}`"
            )
            if path.suffix.lower() in {".mp4", ".mov", ".webm", ".mkv"}:
                st.video(str(path))
            elif path.suffix.lower() in {".png", ".jpg", ".jpeg", ".webp"}:
                st.image(str(path), use_container_width=True)
            action_a, action_b = st.columns(2)
            if action_a.button(
                "⭐ Aprovar",
                key=f"wangp-approve-{record.id}",
                disabled=record.status == "approved",
                use_container_width=True,
            ):
                library.set_status(record.id, "approved")
                st.rerun()
            if action_b.button(
                "Rejeitar",
                key=f"wangp-reject-{record.id}",
                disabled=record.status == "rejected",
                use_container_width=True,
            ):
                library.set_status(record.id, "rejected")
                st.rerun()

st.info(
    "Ao aprovar um clipe, a AssetLibrary atualiza o render-plan.json. "
    "Depois, volte à etapa Render do Studio para montar o Reel final."
)

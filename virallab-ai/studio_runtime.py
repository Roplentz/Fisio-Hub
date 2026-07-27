from __future__ import annotations

import json
from pathlib import Path

import streamlit as st

from virallab.asset_library import AssetLibrary
from virallab.avatar_master import AvatarMasterStore, ImageGenerationError
from virallab.creative_assets import build_scene_prompt, generate_scene_asset
from virallab.learning import FeedbackRecord, load_feedback, save_feedback, summarize_preferences
from virallab.renderer import RenderError, render_video
from virallab.studio.layout import (
    configure_page,
    render_footer,
    render_hero,
    render_progress,
    render_sidebar,
)
from virallab.studio.navigation import (
    progress_value as navigation_progress_value,
    render_step_selector as navigation_step_selector,
)
from virallab.studio.paths import DEFAULT_PATHS
from virallab.studio.state import (
    LOGICAL_STEP_KEY,
    initialize_state as initialize_session_state,
    reset_project,
)
from virallab.studio.steps import AnalysisAction, AvatarAction, VoiceAction
from virallab.studio.steps.analysis import render_analysis as render_analysis_step
from virallab.studio.steps.avatar import render_avatar as render_avatar_step
from virallab.studio.steps.script import render_script as render_script_step
from virallab.studio.steps.strategy import render_strategy as render_strategy_step
from virallab.studio.steps.voice import render_voice as render_voice_step
from virallab.voice import load_voice_plan
from virallab.voice_renderer import render_video_with_voice

APP_ROOT = DEFAULT_PATHS.app_root
WORKSPACE = DEFAULT_PATHS.workspace
ANALYSIS_DIR = DEFAULT_PATHS.analysis
PROJECTS_DIR = DEFAULT_PATHS.projects
LEARNING_STORE = DEFAULT_PATHS.learning_store
DEFAULT_PATHS.ensure_directories()
configure_page(st)


def initialize_state() -> None:
    initialize_session_state(st.session_state)


def render_step_selector() -> str:
    return navigation_step_selector(st, st.session_state)


def project_dir(project_id: str) -> Path:
    return DEFAULT_PATHS.project_dir(project_id)


def new_project() -> None:
    reset_project(st.session_state)


def open_analysis(path: Path, name: str, source: str) -> None:
    st.session_state.pending_video_path = str(path)
    st.session_state.pending_video_name = name
    st.session_state.pending_video_source = source
    st.switch_page("pages/01_Analisar_Video.py")


def progress_value() -> float:
    return navigation_progress_value(st.session_state)


def render_analysis() -> None:
    action = render_analysis_step(st, ANALYSIS_DIR, open_analysis)
    if action is AnalysisAction.CREATE_FROM_SCRATCH:
        st.session_state[LOGICAL_STEP_KEY] = "strategy"
        st.rerun()


def render_strategy() -> None:
    result = render_strategy_step(
        st,
        project_id=st.session_state.project_id,
        project_dir_factory=project_dir,
    )
    if result is None:
        return
    st.session_state.package = result.package
    st.session_state.package_dir = str(result.output_directory)
    st.session_state.preferred_hook = result.package.hook
    st.session_state[LOGICAL_STEP_KEY] = "script"
    st.rerun()


def render_script(package) -> None:
    result = render_script_step(
        st,
        package,
        preferred_hook=st.session_state.preferred_hook,
    )
    st.session_state.preferred_hook = result.preferred_hook
    if result.continue_to_avatar:
        st.session_state[LOGICAL_STEP_KEY] = "avatar"
        st.rerun()


def render_avatar() -> None:
    candidate = Path(st.session_state.avatar_candidate) if st.session_state.avatar_candidate else None
    result = render_avatar_step(st, WORKSPACE, candidate_path=candidate)
    if result.clear_candidate:
        st.session_state.avatar_candidate = None
    elif result.candidate_path is not None:
        st.session_state.avatar_candidate = str(result.candidate_path)
    if result.action is AvatarAction.GO_TO_VOICE:
        st.session_state[LOGICAL_STEP_KEY] = "voice"
        st.rerun()
    elif result.action is AvatarAction.RERUN:
        st.rerun()


def render_voice(package, package_path: Path) -> None:
    result = render_voice_step(
        st,
        package,
        package_path,
        state=st.session_state,
    )
    if result.last_generation is not None:
        st.session_state["voice_last_generation"] = result.last_generation
    if result.action is VoiceAction.GO_TO_CREATIVES:
        st.session_state[LOGICAL_STEP_KEY] = "creatives"
        st.rerun()
    elif result.action is VoiceAction.RERUN:
        st.rerun()


def render_creatives(package, package_path: Path) -> None:
    st.subheader("Criativos")
    avatar_store = AvatarMasterStore(WORKSPACE)
    avatar_profile = avatar_store.load()
    if avatar_profile and avatar_profile.approved:
        st.success(f"Avatar IA ativo: {avatar_profile.name} · versão {avatar_profile.version}")
    else:
        st.warning("Nenhuma Imagem Mestre aprovada. Cenas do autor usarão o modo genérico ou a referência antiga.")
    library = AssetLibrary(package_path)
    approved_count = sum(1 for item in library.load() if item.status == "approved")
    c1, c2 = st.columns(2)
    c1.metric("Cenas", len(package.scenes))
    c2.metric("Aprovadas", f"{approved_count}/{len(package.scenes)}")
    style = st.selectbox("DNA visual", ["RP cinematográfico", "Clínico premium", "Editorial científico", "Humano documental", "Minimalista tecnológico"])
    for scene in package.scenes:
        records = library.for_scene(scene.index)
        approved = next((item for item in records if item.status == "approved"), None)
        prompt = build_scene_prompt(scene, theme=package.brief.theme, visual_style=style, avatar_profile=avatar_profile)
        with st.container(border=True):
            st.markdown(f"**Cena {scene.index}** · {'✓ aprovada' if approved else 'aguardando'}")
            st.caption(scene.visual_direction or scene.narration)
            edited = st.text_area("Direção da imagem", value=prompt, height=130, key=f"prompt-v3-{scene.index}")
            generate_col, upload_col = st.columns(2)
            if generate_col.button("🎨 Gerar variação", key=f"gen-v3-{scene.index}", type="primary", use_container_width=True):
                try:
                    with st.spinner("Criando..."):
                        generate_scene_asset(package_path, scene, prompt=edited)
                    st.rerun()
                except (ImageGenerationError, ValueError) as exc:
                    st.error(str(exc))
            upload = upload_col.file_uploader(
                "Enviar material",
                type=["mp4", "mov", "webm", "png", "jpg", "jpeg", "webp"],
                key=f"upload-v3-{scene.index}",
                label_visibility="collapsed",
            )
            if upload is not None and upload_col.button("Salvar upload", key=f"save-v3-{scene.index}", use_container_width=True):
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
                st.rerun()
            for record in reversed(library.for_scene(scene.index)):
                path = library.resolve(record)
                if path.suffix.lower() in {".png", ".jpg", ".jpeg", ".webp"}:
                    st.image(str(path), use_container_width=True)
                elif path.suffix.lower() in {".mp4", ".mov", ".webm"}:
                    st.video(str(path))
                a, b = st.columns(2)
                if a.button("⭐ Aprovar", key=f"approve-v3-{record.id}", disabled=record.status == "approved", use_container_width=True):
                    library.set_status(record.id, "approved")
                    st.rerun()
                if b.button("Rejeitar", key=f"reject-v3-{record.id}", disabled=record.status == "rejected", use_container_width=True):
                    library.set_status(record.id, "rejected")
                    st.rerun()


def render_output(package_path: Path) -> None:
    st.subheader("Render")
    library = AssetLibrary(package_path)
    approved = [item for item in library.load() if item.status == "approved"]
    voice_plan = load_voice_plan(package_path)
    c1, c2 = st.columns(2)
    c1.metric("Criativos aprovados", len(approved))
    c2.metric("Voz", "Pronta" if voice_plan else "Não gravada")
    burn = st.checkbox("Legendas incorporadas", value=True)
    music = st.slider("Trilha (dB)", -40, -12, -25)
    voice_gain = st.slider("Voz (dB)", -6, 6, 0)
    if st.button("Renderizar vídeo", type="primary", use_container_width=True, disabled=not approved):
        try:
            with st.spinner("Renderizando..."):
                video = (
                    render_video_with_voice(package_path, burn_captions=burn, music_level_db=music, narration_gain_db=voice_gain)
                    if voice_plan
                    else render_video(package_path, burn_captions=burn, music_level_db=music)
                )
            if video.exists():
                st.video(str(video))
                st.download_button("Baixar vídeo final", video.read_bytes(), "video-final.mp4", "video/mp4", use_container_width=True)
        except RenderError as exc:
            st.error(str(exc))


def render_publication(package) -> None:
    st.subheader("Pacote de publicação")
    if package is None:
        st.warning("Crie o roteiro primeiro.")
        return
    title = st.text_input("Título", value=package.hook)
    caption = st.text_area("Legenda", value=f"{package.thesis}\n\n{package.brief.cta}", height=180)
    hashtags = st.text_input("Hashtags", value="#fisioterapia #inteligenciaartificial #inovacaoemsaude")
    st.download_button(
        "Baixar pacote de publicação",
        json.dumps({"title": title, "caption": caption, "hashtags": hashtags}, ensure_ascii=False, indent=2),
        "publication-package.json",
        "application/json",
        use_container_width=True,
    )


def render_learning(package) -> None:
    st.subheader("Aprendizado")
    if package is None:
        st.warning("Crie o roteiro primeiro.")
        return
    rating = st.slider("Qualidade", 1, 10, 8)
    approved = st.checkbox("Eu publicaria", value=True)
    notes = st.text_area("O que o ViralLab deve aprender?")
    if st.button("Salvar aprendizado", type="primary", use_container_width=True):
        save_feedback(
            FeedbackRecord(
                project_id=st.session_state.project_id,
                theme=package.brief.theme,
                rating=rating,
                approved=approved,
                original_hook=package.hook,
                preferred_hook=st.session_state.preferred_hook or package.hook,
                notes=notes,
                preferred_style="Studio 3.0",
            ),
            LEARNING_STORE,
        )
        st.success("Aprendizado salvo.")


initialize_state()
records = load_feedback(LEARNING_STORE)
summary = summarize_preferences(records)
render_sidebar(st, st.session_state, summary, new_project)
render_hero(st)
render_progress(st, progress_value())

selected = render_step_selector()
package = st.session_state.package
package_path = Path(st.session_state.package_dir) if st.session_state.package_dir else None

if selected == "analysis":
    render_analysis()
elif selected == "strategy":
    render_strategy()
elif selected == "script":
    render_script(package) if package else st.warning("Gere a estratégia primeiro.")
elif selected == "avatar":
    render_avatar()
elif selected == "voice":
    render_voice(package, package_path) if package and package_path else st.warning("Gere o roteiro primeiro.")
elif selected == "creatives":
    render_creatives(package, package_path) if package and package_path else st.warning("Gere o roteiro primeiro.")
elif selected == "render":
    render_output(package_path) if package_path else st.warning("Crie o projeto primeiro.")
elif selected == "publication":
    render_publication(package)
else:
    render_learning(package)

render_footer(st)
